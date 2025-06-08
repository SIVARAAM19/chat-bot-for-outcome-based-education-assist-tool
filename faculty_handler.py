from typing import List, Dict, Any, Optional, Text
import logging
import re
import requests
import json
from actions.utils.database import get_db_connection, normalize_faculty_name
from actions.utils.database import extract_subject_name, extract_faculty_name

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


PDF_THRESHOLD = 5

def get_faculty_for_subject(subject_name: str) -> List[Dict[str, Any]]:
    """
    Get faculty members teaching a specific subject
    
    Args:
        subject_name: The name of the subject (partial match)
        
    Returns:
        List of dictionaries with faculty details
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        
        subject_pattern = f"%{subject_name}%"
        
        
        if re.search(r'computer\s+networks?', subject_name, re.IGNORECASE):
            subject_pattern = "%Computer Network%"
        
        query = """
        SELECT f.name, c.code as subject_code, c.name as subject_name
        FROM faculty f
        JOIN faculty_course fc ON f.id = fc.faculty_id
        JOIN course c ON fc.course_id = c.code
        WHERE c.name LIKE %s
        """
        
        cursor.execute(query, (subject_pattern,))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return results
    except Exception as e:
        logger.error(f"Error fetching faculty for subject: {e}")
        return []

def get_subjects_for_faculty(faculty_name: str) -> List[Dict[str, Any]]:
    """
    Get subjects taught by a specific faculty member
    
    Args:
        faculty_name: The name of the faculty member (partial match)
        
    Returns:
        List of dictionaries with subject details
    """
    try:
        
        normalized_name = normalize_faculty_name(faculty_name)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT f.name, c.code as subject_code, c.name as subject_name
        FROM faculty f
        JOIN faculty_course fc ON f.id = fc.faculty_id
        JOIN course c ON fc.course_id = c.code
        WHERE f.name LIKE %s
        """
        
        cursor.execute(query, (f"%{normalized_name}%",))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return results
    except Exception as e:
        logger.error(f"Error fetching subjects for faculty: {e}")
        return []

def handle_faculty_query(text: str) -> Dict[str, Any]:
    """
    Main function to handle faculty-related queries
    
    Args:
        text: The user's query text
        
    Returns:
        Dictionary with response data and success status
    """
    logger.info(f"Handling faculty query: {text}")
    
    
    subject_name = extract_subject_name(text)
    if subject_name:
        faculty_list = get_faculty_for_subject(subject_name)
        if faculty_list:
            response = f"Faculty teaching {subject_name}:\n\n"
            for i, faculty in enumerate(faculty_list, 1):
                response += f"{i}. {faculty['name']} - {faculty['subject_code']}: {faculty['subject_name']}\n"
            
            return {
                "success": True,
                "query_type": "faculty_for_subject",
                "data": faculty_list,
                "message": response
            }
        else:
            return {
                "success": False,
                "query_type": "faculty_for_subject",
                "message": f"No faculty found teaching '{subject_name}'. Please check the subject name."
            }
    
   
    faculty_name = extract_faculty_name(text)
    if faculty_name:
        subjects = get_subjects_for_faculty(faculty_name)
        if subjects:
            # Group by faculty name
            faculty_subjects = {}
            for subject in subjects:
                if subject['name'] not in faculty_subjects:
                    faculty_subjects[subject['name']] = []
                faculty_subjects[subject['name']].append(f"{subject['subject_code']}: {subject['subject_name']}")
            
            response = ""
            for faculty, subject_list in faculty_subjects.items():
                response += f"Subjects taught by {faculty}:\n"
                for subject in subject_list:
                    response += f"{subject}\n"
                response += "\n"
            
            return {
                "success": True,
                "query_type": "subjects_for_faculty",
                "data": subjects,
                "message": response.strip()
            }
        else:
            return {
                "success": False,
                "query_type": "subjects_for_faculty",
                "message": f"No subjects found for faculty '{faculty_name}'. Please check the faculty name."
            }
    
    
    return {
        "success": False,
        "query_type": "unknown",
        "message": "I couldn't understand your faculty query. Please try rephrasing it."
    }

class ActionFacultyQuery(Action):
    """Handle all faculty-related queries"""

    def name(self) -> Text:
        return "action_faculty_query"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Process faculty-related queries based on intent and entities"""
        
       
        intent = tracker.latest_message.get('intent', {}).get('name')
        message = tracker.latest_message.get('text', '')
        
        logger.info(f"Processing faculty query with intent: {intent}, message: {message}")
        
       
        entities = tracker.latest_message.get('entities', [])
        entity_dict = {e['entity']: e['value'] for e in entities if 'entity' in e and 'value' in e}
        
        
        if intent == "faculty_by_subject":
            return self._handle_faculty_by_subject(dispatcher, entity_dict, message)
        elif intent == "subjects_by_faculty":
            return self._handle_subjects_by_faculty(dispatcher, entity_dict, message)
        else:
            
            return self._handle_generic_faculty_query(dispatcher, message)
    
    def _generate_pdf_for_results(self, data: List[Dict[str, Any]], query_type: str, query_value: str) -> Optional[str]:
        """Generate a PDF for large result sets and return the download URL"""
        try:
           
            from actions.utils.pdf_generator import PDFGenerator
            pdf_generator = PDFGenerator()
            pdf_url = pdf_generator.generate_faculty_report(data, query_type, query_value)
            return pdf_url
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return None
    
    def _handle_faculty_by_subject(self, dispatcher: CollectingDispatcher, entity_dict: Dict[str, Any], message: str) -> List[Dict[Text, Any]]:
        """Handle queries for faculty by subject"""
        subject = entity_dict.get('subject')
        
        if not subject:
         
            subject_name = extract_subject_name(message)
            if subject_name:
                subject = subject_name
        
        if subject:
            faculty_list = get_faculty_for_subject(subject)
            if faculty_list:
                
                if len(faculty_list) > PDF_THRESHOLD:
                    dispatcher.utter_message(text=f"Found {len(faculty_list)} faculty members teaching {subject}.")
                    
                    
                    pdf_url = self._generate_pdf_for_results(faculty_list, "subject", subject)
                    if pdf_url:
                        dispatcher.utter_message(text=f"I've prepared a PDF report with all the results. [Download PDF]({pdf_url})")
                    else:
                       
                        dispatcher.utter_message(text="Here are the first few results:")
                        for faculty in faculty_list[:PDF_THRESHOLD]:
                            dispatcher.utter_message(text=f"- {faculty.get('name')} teaches {faculty.get('subject_name')} ({faculty.get('subject_code')})")
                        dispatcher.utter_message(text=f"... and {len(faculty_list) - PDF_THRESHOLD} more faculty members.")
                else:
                   
                    if len(faculty_list) == 1:
                        dispatcher.utter_message(text=f"{subject} is taught by:")
                    else:
                        dispatcher.utter_message(text=f"{subject} is taught by multiple faculty members:")
                    
                    for faculty in faculty_list:
                        dispatcher.utter_message(text=f"- {faculty.get('name')} teaches {faculty.get('subject_name')} ({faculty.get('subject_code')})")
                
                return [SlotSet("subject_name", subject)]
            else:
                dispatcher.utter_message(text=f"No faculty found teaching '{subject}'. Please check the subject name.")
        else:
            dispatcher.utter_message(text="I couldn't identify a subject in your query. Please provide a subject name.")
        
        return []
    
    def _handle_subjects_by_faculty(self, dispatcher: CollectingDispatcher, entity_dict: Dict[str, Any], message: str) -> List[Dict[Text, Any]]:
        """Handle queries for subjects by faculty"""
        faculty_name = entity_dict.get('faculty_name')
        
        if not faculty_name:
            
            extracted_name = extract_faculty_name(message)
            if extracted_name:
                faculty_name = extracted_name
        
        if faculty_name:
           
            faculty_name = normalize_faculty_name(faculty_name)
            
            subjects = get_subjects_for_faculty(faculty_name)
            if subjects:
                
                if len(subjects) > PDF_THRESHOLD:
                    dispatcher.utter_message(text=f"Found {len(subjects)} subjects taught by {faculty_name}.")
                    
                
                    pdf_url = self._generate_pdf_for_results(subjects, "faculty", faculty_name)
                    if pdf_url:
                        dispatcher.utter_message(text=f"I've prepared a PDF report with all the results. [Download PDF]({pdf_url})")
                    else:
                        # Fallback to displaying limited results
                        dispatcher.utter_message(text="Here are the first few results:")
                        for subject in subjects[:PDF_THRESHOLD]:
                            dispatcher.utter_message(text=f"- {subject.get('subject_name')} ({subject.get('subject_code')})")
                        dispatcher.utter_message(text=f"... and {len(subjects) - PDF_THRESHOLD} more subjects.")
                else:
                    
                    if len(subjects) == 1:
                        dispatcher.utter_message(text=f"{faculty_name} teaches:")
                    else:
                        dispatcher.utter_message(text=f"{faculty_name} teaches multiple subjects:")
                    
                    for subject in subjects:
                        dispatcher.utter_message(text=f"- {subject.get('subject_name')} ({subject.get('subject_code')})")
                
                return [SlotSet("faculty_name", faculty_name)]
            else:
                dispatcher.utter_message(text=f"No subjects found for faculty '{faculty_name}'. Please check the faculty name.")
        else:
            dispatcher.utter_message(text="I couldn't identify a faculty name in your query. Please provide a faculty name.")
        
        return []
    
    def _handle_generic_faculty_query(self, dispatcher: CollectingDispatcher, message: str) -> List[Dict[Text, Any]]:
        """Handle generic faculty queries using regex patterns"""
        
      
        subject_name = extract_subject_name(message)
        if subject_name:
            return self._handle_faculty_by_subject(dispatcher, {"subject": subject_name}, message)
        
        
        faculty_name = extract_faculty_name(message)
        if faculty_name:
            return self._handle_subjects_by_faculty(dispatcher, {"faculty_name": faculty_name}, message)
        
        
        dispatcher.utter_message(text="I couldn't understand your faculty query. Please try again with more specific information.")
        return []

    def _handle_faculty_for_subject(self, dispatcher: CollectingDispatcher, entity_dict: Dict[str, Any], message: str) -> List[Dict[Text, Any]]:
        """Handle queries for faculty teaching a specific subject"""
        subject_name = entity_dict.get('subject_name')
        
        if not subject_name:
           
            subject_match = re.search(r"(?:who|which faculty|faculty).*(?:teaches?|teaching|for)\s+([^?]+?)(?:\?)?$", message, re.IGNORECASE)
            if subject_match:
                subject_name = subject_match.group(1).strip()
        
        if subject_name:
            faculty = get_faculty_for_subject(subject_name)
            if faculty:
                for f in faculty:
                    dispatcher.utter_message(text=format_faculty_details(f))
                return [SlotSet("subject_name", subject_name)]
            else:
                dispatcher.utter_message(text=f"No faculty found teaching '{subject_name}'. Please check the subject name.")
        else:
            dispatcher.utter_message(text="I couldn't identify a subject name in your query. Please specify which subject you're interested in.")
        
        return [] 