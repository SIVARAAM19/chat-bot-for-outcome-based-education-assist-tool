import re
import logging
import requests
import json
from typing import Any, Dict, List, Text, Optional

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

from actions.utils.database import (
    get_student_by_name,
    get_student_by_register_number,
    get_students_by_year,
    get_students_by_semester,
    get_students_by_section,
    get_students_by_batch,
    get_students_by_type,
    extract_type,
    format_student_details
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PDF_THRESHOLD = 5

class ActionStudentQuery(Action):
    """Handle all student-related queries"""

    def name(self) -> Text:
        return "action_student_query"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Process student-related queries based on intent and entities"""
        
        
        intent = tracker.latest_message.get('intent', {}).get('name')
        message = tracker.latest_message.get('text', '')
        
        logger.info(f"Processing student query with intent: {intent}, message: {message}")
        
       
        if ("course" in message.lower() or "courses" in message.lower()):
            logger.info("Detected course query misclassified as student query, deferring to course handler")
           
            return []
        
        
        if (("btech" in message.lower() or "b.tech" in message.lower() or "b tech" in message.lower() or 
             "mtech" in message.lower() or "m.tech" in message.lower() or "m tech" in message.lower() or
             "mca" in message.lower() or "phd" in message.lower()) and 
            "student" not in message.lower() and "students" not in message.lower()):
            logger.info("Detected potential degree query without student context, deferring")
            return []
        
        
        entities = tracker.latest_message.get('entities', [])
        entity_dict = {e['entity']: e['value'] for e in entities if 'entity' in e and 'value' in e}
        
       
        if intent == "student_by_name":
            return self._handle_student_by_name(dispatcher, entity_dict, message)
        elif intent == "student_info":
            return self._handle_student_info(dispatcher, entity_dict, message)
        elif intent == "students_by_year":
            return self._handle_students_by_year(dispatcher, entity_dict, message)
        elif intent == "students_by_semester":
            return self._handle_students_by_semester(dispatcher, entity_dict, message)
        elif intent == "students_by_section":
            return self._handle_students_by_section(dispatcher, entity_dict, message)
        elif intent == "students_by_batch":
            return self._handle_students_by_batch(dispatcher, entity_dict, message)
        elif intent == "students_by_type":
            return self._handle_students_by_type(dispatcher, entity_dict, message)
        else:
           
            return self._handle_generic_student_query(dispatcher, message)
    
    def _generate_pdf_for_results(self, students: List[Dict[str, Any]], query_type: str, query_value: str) -> Optional[str]:
        """Generate a PDF for large result sets and return the download URL"""
        try:
            
            from actions.utils.pdf_generator import PDFGenerator
            pdf_generator = PDFGenerator()
            pdf_url = pdf_generator.generate_student_report(students, query_type, query_value)
            return pdf_url
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return None
    
    def _handle_student_by_name(self, dispatcher: CollectingDispatcher, entity_dict: Dict[str, Any], message: str) -> List[Dict[Text, Any]]:
        """Handle queries for student by name"""
        student_name = entity_dict.get('student_name')
        
        if not student_name:
           
            name_match = re.search(r"(?:who|about|tell me about)\s+(?:is|are)?\s*([A-Za-z\s]+)(?:\?)?$", message, re.IGNORECASE)
            if name_match:
                student_name = name_match.group(1).strip()
        
        if student_name:
            students = get_student_by_name(student_name)
            if students:
                for student in students:
                    dispatcher.utter_message(text=format_student_details(student))
                return [SlotSet("student_name", student_name)]
            else:
                dispatcher.utter_message(text=f"No student found with name containing '{student_name}'. Please check the name.")
        else:
            dispatcher.utter_message(text="I couldn't identify a student name in your query. Please provide a name.")
        
        return []
    
    def _handle_student_info(self, dispatcher: CollectingDispatcher, entity_dict: Dict[str, Any], message: str) -> List[Dict[Text, Any]]:
        """Handle queries for student information by register number"""
        reg_no = entity_dict.get('register_number') or entity_dict.get('register_no')
        
        if not reg_no:
            reg_match = re.search(r"(?:about|tell me about|find|get)\s+(?:student|register number|reg no)?\s*([0-9]{2}[A-Za-z]{2}[0-9]{4})(?:\?)?", message, re.IGNORECASE)
            if reg_match:
                reg_no = reg_match.group(1).strip()
        
        course_code_match = re.search(r"\b([A-Z]{2,3}\s*\d{3})\b", message, re.IGNORECASE)
        if course_code_match and not reg_no:
            # This looks like a course code, not a register number
            logger.info(f"Detected potential course code: {course_code_match.group(1)}, redirecting to course handler")
            dispatcher.utter_message(text=f"It looks like you're asking about a course code ({course_code_match.group(1)}). Please try asking 'What is {course_code_match.group(1)}?' or 'Tell me about {course_code_match.group(1)}'.")
            return []
            
        if reg_no:
            students = get_student_by_register_number(reg_no)
            if students:
                for student in students:
                    dispatcher.utter_message(text=format_student_details(student))
                return [SlotSet("register_number", reg_no)]
            else:
                dispatcher.utter_message(text=f"No student found with register number '{reg_no}'. Please check the register number.")
                return []
        else:
            dispatcher.utter_message(text="I couldn't identify a register number in your query. Please provide a valid register number.")
            return []
    
    def _handle_students_by_year(self, dispatcher: CollectingDispatcher, entity_dict: Dict[str, Any], message: str) -> List[Dict[Text, Any]]:
        """Handle queries for students by year"""
        year = entity_dict.get('year')
        
        if not year:
           
            year_match = re.search(r"(?:students?|show|list|get|find).*(?:in|of|from)?\s+(\d)(?:st|nd|rd|th)?\s*(?:year)", message, re.IGNORECASE)
            if year_match:
                year = year_match.group(1).strip()
        
        if year:
            try:
                year_int = int(year)
                students = get_students_by_year(year_int)
                if students:
                    #
                    if len(students) > PDF_THRESHOLD:
                        dispatcher.utter_message(text=f"Found {len(students)} students in year {year}.")
                        
                        
                        pdf_url = self._generate_pdf_for_results(students, "year", str(year_int))
                        if pdf_url:
                            dispatcher.utter_message(text=f"I've prepared a PDF report with all the results. [Download PDF]({pdf_url})")
                        else:
                           
                            dispatcher.utter_message(text="Here are the first few results:")
                            for student in students[:PDF_THRESHOLD]:
                                dispatcher.utter_message(text=format_student_details(student))
                            dispatcher.utter_message(text=f"... and {len(students) - PDF_THRESHOLD} more students.")
                    else:
                        
                        dispatcher.utter_message(text=f"Found {len(students)} students in year {year}:")
                        for student in students:
                            dispatcher.utter_message(text=format_student_details(student))
                    
                    return [SlotSet("year", year_int)]
                else:
                    dispatcher.utter_message(text=f"No students found in year {year}.")
            except ValueError:
                dispatcher.utter_message(text=f"Invalid year value: {year}. Please provide a number between 1 and 4.")
        else:
            dispatcher.utter_message(text="I couldn't identify a year in your query. Please specify which year you're interested in.")
        
        return []
    
    def _handle_students_by_semester(self, dispatcher: CollectingDispatcher, entity_dict: Dict[str, Any], message: str) -> List[Dict[Text, Any]]:
        """Handle queries for students by semester"""
        semester = entity_dict.get('semester')
        
        if not semester:
            
            semester_match = re.search(r"(?:students?|show|list|get|find).*(?:in|of|from)?\s+(\d)(?:st|nd|rd|th)?\s*(?:semester|sem)", message, re.IGNORECASE)
            if semester_match:
                semester = semester_match.group(1).strip()
        
        if semester:
            try:
                semester_int = int(semester)
                students = get_students_by_semester(semester_int)
                if students:
                   
                    if len(students) > PDF_THRESHOLD:
                        dispatcher.utter_message(text=f"Found {len(students)} students in semester {semester}.")
                        
                        
                        pdf_url = self._generate_pdf_for_results(students, "semester", str(semester_int))
                        if pdf_url:
                            dispatcher.utter_message(text=f"I've prepared a PDF report with all the results. [Download PDF]({pdf_url})")
                        else:
                           
                            dispatcher.utter_message(text="Here are the first few results:")
                            for student in students[:PDF_THRESHOLD]:
                                dispatcher.utter_message(text=format_student_details(student))
                            dispatcher.utter_message(text=f"... and {len(students) - PDF_THRESHOLD} more students.")
                    else:
                        
                        dispatcher.utter_message(text=f"Found {len(students)} students in semester {semester}:")
                        for student in students:
                            dispatcher.utter_message(text=format_student_details(student))
                    
                    return [SlotSet("semester", semester_int)]
                else:
                    dispatcher.utter_message(text=f"No students found in semester {semester}.")
            except ValueError:
                dispatcher.utter_message(text=f"Invalid semester value: {semester}. Please provide a number between 1 and 8.")
        else:
            dispatcher.utter_message(text="I couldn't identify a semester in your query. Please specify which semester you're interested in.")
        
        return []
    
    def _handle_students_by_section(self, dispatcher: CollectingDispatcher, entity_dict: Dict[str, Any], message: str) -> List[Dict[Text, Any]]:
        """Handle queries for students by section"""
        section = entity_dict.get('section')
        
        if not section:
            
            section_match = re.search(r"(?:students?|show|list|get|find).*(?:in|of|from)?\s+(?:section\s+)?([A-Za-z])\b", message, re.IGNORECASE)
            if section_match:
                section = section_match.group(1).strip().upper()
        
        if section:
            students = get_students_by_section(section)
            if students:
                
                if len(students) > PDF_THRESHOLD:
                    dispatcher.utter_message(text=f"Found {len(students)} students in section {section}.")
                    
                   
                    pdf_url = self._generate_pdf_for_results(students, "section", section)
                    if pdf_url:
                        dispatcher.utter_message(text=f"I've prepared a PDF report with all the results. [Download PDF]({pdf_url})")
                    else:
                       
                        dispatcher.utter_message(text="Here are the first few results:")
                        for student in students[:PDF_THRESHOLD]:
                            dispatcher.utter_message(text=format_student_details(student))
                        dispatcher.utter_message(text=f"... and {len(students) - PDF_THRESHOLD} more students.")
                else:
                    
                    dispatcher.utter_message(text=f"Found {len(students)} students in section {section}:")
                    for student in students:
                        dispatcher.utter_message(text=format_student_details(student))
                
                return [SlotSet("section", section)]
            else:
                dispatcher.utter_message(text=f"No students found in section {section}.")
        else:
            dispatcher.utter_message(text="I couldn't identify a section in your query. Please specify which section (e.g., A, B, C) you're interested in.")
        
        return []
    
    def _handle_students_by_batch(self, dispatcher: CollectingDispatcher, entity_dict: Dict[str, Any], message: str) -> List[Dict[Text, Any]]:
        """Handle queries for students by batch"""
        batch = entity_dict.get('batch')
        
        if not batch:
           
            batch_match = re.search(r"(?:students?|show|list|get|find).*(?:in|of|from)?\s+(?:batch\s+)?(\d{4}-\d{4})", message, re.IGNORECASE)
            if batch_match:
                batch = batch_match.group(1).strip()
        
        if batch:
            students = get_students_by_batch(batch)
            if students:
                
                if len(students) > PDF_THRESHOLD:
                    dispatcher.utter_message(text=f"Found {len(students)} students in batch {batch}.")
                    
                   
                    pdf_url = self._generate_pdf_for_results(students, "batch", batch)
                    if pdf_url:
                        dispatcher.utter_message(text=f"I've prepared a PDF report with all the results. [Download PDF]({pdf_url})")
                    else:
                       
                        dispatcher.utter_message(text="Here are the first few results:")
                        for student in students[:PDF_THRESHOLD]:
                            dispatcher.utter_message(text=format_student_details(student))
                        dispatcher.utter_message(text=f"... and {len(students) - PDF_THRESHOLD} more students.")
                else:
                    
                    dispatcher.utter_message(text=f"Found {len(students)} students in batch {batch}:")
                    for student in students:
                        dispatcher.utter_message(text=format_student_details(student))
                
                return [SlotSet("batch", batch)]
            else:
                dispatcher.utter_message(text=f"No students found in batch {batch}.")
        else:
            dispatcher.utter_message(text="I couldn't identify a batch in your query. Please specify which batch (e.g., 2021-2025) you're interested in.")
        
        return []
    
    def _handle_students_by_type(self, dispatcher: CollectingDispatcher, entity_dict: Dict[str, Any], message: str) -> List[Dict[Text, Any]]:
        """Handle queries for students by type (B.Tech, M.Tech, PhD)"""
        
        student_type = entity_dict.get('type')
        
        if not student_type:
           
            student_type = extract_type(message)
        
        if student_type:
            
            normalized_type = student_type.lower()
            
            
            is_mtech_is = bool(re.search(r'm\.?tech\s+is|m\s*tech\s+is', message, re.IGNORECASE))
            is_mtech_ds = bool(re.search(r'm\.?tech\s+ds|m\s*tech\s+ds', message, re.IGNORECASE))
            
            
            if normalized_type == "btech":
                db_type = "B.Tech"
            elif normalized_type == "mtech":
               
                if is_mtech_is:
                    db_type = "M.Tech IS"  
                    logger.info(f"Detected M.Tech IS specialization in message: {message}")
                elif is_mtech_ds:
                    db_type = "M.Tech DS"  
                    logger.info(f"Detected M.Tech DS specialization in message: {message}")
                else:
                    
                    db_type = "M.Tech%"
                    logger.info(f"Using general M.Tech% pattern for query")
            elif normalized_type == "mca":
                db_type = "MCA"  
            else:
                db_type = student_type  
            
            logger.info(f"Looking up students with type: {db_type} (normalized from {student_type})")
            
           
            if "%" in db_type:
                logger.info(f"SQL Query will be: SELECT * FROM student WHERE type LIKE '{db_type}'")
            else:
                logger.info(f"SQL Query will be: SELECT * FROM student WHERE type = '{db_type}'")
            
            students = get_students_by_type(db_type)
            
           
            display_type = student_type
            if is_mtech_is:
                display_type = "M.Tech IS"
            elif is_mtech_ds:
                display_type = "M.Tech DS"
            elif normalized_type == "btech":
                display_type = "B.Tech"
            elif normalized_type == "mtech":
                display_type = "M.Tech"
            elif normalized_type == "mca":
                display_type = "MCA"
            
            if students:
                
                if len(students) > PDF_THRESHOLD:
                    dispatcher.utter_message(text=f"Found {len(students)} {display_type} students.")
                    
                    
                    pdf_url = self._generate_pdf_for_results(students, "type", display_type)
                    if pdf_url:
                        dispatcher.utter_message(text=f"I've prepared a PDF report with all the results. [Download PDF]({pdf_url})")
                    else:
                       
                        dispatcher.utter_message(text="Here are the first few results:")
                        for student in students[:PDF_THRESHOLD]:
                            dispatcher.utter_message(text=format_student_details(student))
                        dispatcher.utter_message(text=f"... and {len(students) - PDF_THRESHOLD} more students.")
                else:
                
                    dispatcher.utter_message(text=f"Found {len(students)} {display_type} students:")
                    for student in students:
                        dispatcher.utter_message(text=format_student_details(student))
                
                return [SlotSet("student_type", student_type)]
            else:
                dispatcher.utter_message(text=f"No students found of type {display_type}.")
        else:
            dispatcher.utter_message(text="I couldn't identify the student type in your query. Please specify B.Tech, M.Tech IS, M.Tech DS, or MCA.")
        
        return []
    
    def _handle_generic_student_query(self, dispatcher: CollectingDispatcher, message: str) -> List[Dict[Text, Any]]:
        """Handle generic student queries by trying to extract information from the message"""
        
        if "student" in message.lower() or "students" in message.lower():
          
            if re.search(r'm\.?tech\s+is|m\s*tech\s+is', message, re.IGNORECASE):
                logger.info(f"Generic handler detected M.Tech IS student query: {message}")
               
                return self._handle_students_by_type(dispatcher, {'type': 'mtech'}, message)
            elif re.search(r'm\.?tech\s+ds|m\s*tech\s+ds', message, re.IGNORECASE):
                logger.info(f"Generic handler detected M.Tech DS student query: {message}")
                
                return self._handle_students_by_type(dispatcher, {'type': 'mtech'}, message)
            
           
            if "btech" in message.lower() or "b.tech" in message.lower() or "b tech" in message.lower():
                return self._handle_students_by_type(dispatcher, {'type': 'btech'}, message)
            elif "mtech" in message.lower() or "m.tech" in message.lower() or "m tech" in message.lower():
                return self._handle_students_by_type(dispatcher, {'type': 'mtech'}, message)
            elif "mca" in message.lower():
                return self._handle_students_by_type(dispatcher, {'type': 'mca'}, message)
            elif "phd" in message.lower():
                return self._handle_students_by_type(dispatcher, {'type': 'phd'}, message)
        
        
        reg_no = extract_register_number(message)
        if reg_no:
            return self._handle_student_info(dispatcher, {'register_no': reg_no}, message)
        
        student_type = extract_type(message)
        if student_type:
            return self._handle_students_by_type(dispatcher, {'type': student_type}, message)
        
        year = re.search(r'\b[1-4]\b', message)
        if year:
            return self._handle_students_by_year(dispatcher, {'year': year.group()}, message)
        
        semester = re.search(r'\b[1-8]\b', message)
        if semester:
            return self._handle_students_by_semester(dispatcher, {'semester': semester.group()}, message)
        
        section = re.search(r'\b[A-C]\b', message, re.IGNORECASE)
        if section:
            return self._handle_students_by_section(dispatcher, {'section': section.group().upper()}, message)
        
        batch_match = re.search(r'(\d{4}-\d{4})', message)
        if batch_match:
            return self._handle_students_by_batch(dispatcher, {'batch': batch_match.group()}, message)
        
        
        name = extract_student_name(message)
        if name:
            return self._handle_student_by_name(dispatcher, {'student_name': name}, message)
        
      
        dispatcher.utter_message(text="I couldn't understand what student information you're looking for. Please try being more specific.")
        return [] 