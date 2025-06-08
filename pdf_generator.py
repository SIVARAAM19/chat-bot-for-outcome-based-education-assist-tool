import os
import logging
import time
from fpdf import FPDF
from typing import List, Dict, Any, Optional


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


PDF_DIR = "pdf_reports"

PDF_WEB_PATH = "/AuraAI/pdf_reports"


os.makedirs(PDF_DIR, exist_ok=True)

class PDFGenerator:
    """
    Class for generating PDF reports from query results
    """
    
    def __init__(self, title: str = "AuraAI Report"):
        """Initialize the PDF generator with a title"""
        self.title = title
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        self.pdf.set_font("Arial", size=12)
        
    def _add_header(self):
        """Add a header to the PDF"""
        self.pdf.add_page()
        self.pdf.set_font("Arial", "B", 16)
        self.pdf.cell(0, 10, self.title, 0, 1, "C")
        self.pdf.ln(10)
        
    def generate_student_report(self, students: List[Dict[str, Any]], query_type: str, query_value: str) -> str:
        """
        Generate a PDF report for student data
        
        Args:
            students: List of student dictionaries
            query_type: Type of query (e.g., "batch", "year", "section")
            query_value: Value of the query
            
        Returns:
            Web URL to the generated PDF file
        """
        
        self.title = f"Student Report - {query_value}"
        
        self._add_header()
        
       
        self.pdf.set_font("Arial", "B", 12)
        self.pdf.cell(0, 10, "Student Report", 0, 1, "C")
        self.pdf.set_font("Arial", "", 10)
        self.pdf.cell(0, 10, f"{query_type}: {query_value}", 0, 1, "L")
        self.pdf.ln(10)
        
        if not students:
            self.pdf.cell(0, 10, "No students found matching the criteria.", 0, 1, "C")
            return self._save_pdf()
        
        
        col_widths = [30, 50, 15, 20, 20, 30, 30] 
        
      
        self.pdf.set_font("Arial", "B", 10)
        headers = ["Reg No", "Name", "Year", "Semester", "Section", "Batch", "Type"]  # Added Type header
        
        for i, header in enumerate(headers):
            self.pdf.cell(col_widths[i], 10, header, 1, 0, "C")
        self.pdf.ln()
        
        
        alternate = False
        for student in students:
            if alternate:
                self.pdf.set_fill_color(240, 240, 240) 
                self.pdf.set_font("Arial", "", 9)
            else:
                self.pdf.set_fill_color(255, 255, 255)  
                self.pdf.set_font("Arial", "", 9)
            
          
            self.pdf.cell(col_widths[0], 10, str(student.get("register_no", "")), 1, 0, "L", alternate)
            
           
            name = str(student.get("name", ""))
            current_x = self.pdf.get_x()
            current_y = self.pdf.get_y()
            self.pdf.cell(col_widths[1], 10, name[:25] + "..." if len(name) > 25 else name, 1, 0, "L", alternate)
            
           
            self.pdf.cell(col_widths[2], 10, str(student.get("year", "")), 1, 0, "C", alternate)
            self.pdf.cell(col_widths[3], 10, str(student.get("semester", "")), 1, 0, "C", alternate)
            self.pdf.cell(col_widths[4], 10, str(student.get("section", "")), 1, 0, "C", alternate)
            self.pdf.cell(col_widths[5], 10, str(student.get("batch", "")), 1, 0, "C", alternate)
            self.pdf.cell(col_widths[6], 10, str(student.get("type", "")), 1, 1, "C", alternate)  # Added type column
            
            alternate = not alternate
        
        
        timestamp = int(time.time())
        filename = f"student_report_{query_type}_{query_value}_{timestamp}.pdf"
        filepath = os.path.join(PDF_DIR, filename)
        
        
        self.pdf.output(filepath)
        
        logger.info(f"Generated PDF report at {filepath}")
        
        
        return f"{PDF_WEB_PATH}/{filename}"
    
    def generate_faculty_report(self, faculty_data: List[Dict[str, Any]], query_type: str, query_value: str) -> str:
        """
        Generate a PDF report for faculty data
        
        Args:
            faculty_data: List of faculty dictionaries
            query_type: Type of query (e.g., "subject", "faculty")
            query_value: Value of the query
            
        Returns:
            Web URL to the generated PDF file
        """
        
        self.title = f"Faculty Report - {query_value}"
        
      
        self._add_header()
        
        
        self.pdf.set_font("Arial", "B", 12)
        self.pdf.cell(0, 10, f"{query_type}: {query_value}", 0, 1)
        self.pdf.cell(0, 10, f"Total Results: {len(faculty_data)}", 0, 1)
        self.pdf.ln(5)
        
        
        self.pdf.set_font("Arial", "B", 10)
        self.pdf.set_fill_color(200, 220, 255)
        
        
        col_widths = [70, 90, 30]  
        
       
        headers = ["Faculty Name", "Subject", "Department"]
        
        
        for i, header in enumerate(headers):
            self.pdf.cell(col_widths[i], 10, header, 1, 0, "C", True)
        self.pdf.ln()
        
        
        self.pdf.set_font("Arial", "", 10)
        
        
        alternate = False
        
        for faculty in faculty_data:
            if alternate:
                self.pdf.set_fill_color(240, 240, 240)
            else:
                self.pdf.set_fill_color(255, 255, 255)
            
            
            self.pdf.cell(col_widths[0], 10, str(faculty.get("name", "")), 1, 0, "L", alternate)
            self.pdf.cell(col_widths[1], 10, str(faculty.get("subject_name", "")), 1, 0, "L", alternate)
            self.pdf.cell(col_widths[2], 10, str(faculty.get("department", "N/A")), 1, 0, "L", alternate)
            self.pdf.ln()
            
         
            alternate = not alternate
        
       
        timestamp = int(time.time())
        filename = f"faculty_report_{query_type}_{query_value}_{timestamp}.pdf"
        filepath = os.path.join(PDF_DIR, filename)
        
      
        self.pdf.output(filepath)
        
        logger.info(f"Generated PDF report at {filepath}")
        
        
        return f"{PDF_WEB_PATH}/{filename}"
    
    def generate_course_report(self, courses: List[Dict[str, Any]], query_type: str, query_value: str) -> str:
        """
        Generate a PDF report for course data
        
        Args:
            courses: List of course dictionaries
            query_type: Type of query (e.g., "semester", "credits", "code")
            query_value: Value of the query
            
        Returns:
            Web URL to the generated PDF file
        """
        
        self.title = f"Course Report - {query_value}"
        
        
        self._add_header()
        
        
        self.pdf.set_font("Arial", "B", 12)
        self.pdf.cell(0, 10, f"{query_type}: {query_value}", 0, 1)
        self.pdf.cell(0, 10, f"Total Results: {len(courses)}", 0, 1)
        self.pdf.ln(5)
        
        
        self.pdf.set_font("Arial", "B", 10)
        self.pdf.set_fill_color(200, 220, 255)
        
        
        col_widths = [30, 90, 20, 25, 25]
        
        
        headers = ["Code", "Course Name", "Credits", "Semester", "No. of COs"]
        
       
        for i, header in enumerate(headers):
            self.pdf.cell(col_widths[i], 10, header, 1, 0, "C", True)
        self.pdf.ln()
        
       
        self.pdf.set_font("Arial", "", 9)
        
        
        alternate = False
        
        for course in courses:
            if alternate:
                self.pdf.set_fill_color(240, 240, 240)
            else:
                self.pdf.set_fill_color(255, 255, 255)
            
          
            if self.pdf.get_y() > 250:  
                self.pdf.add_page()
                
                self.pdf.set_font("Arial", "B", 10)
                self.pdf.set_fill_color(200, 220, 255)
                for i, header in enumerate(headers):
                    self.pdf.cell(col_widths[i], 10, header, 1, 0, "C", True)
                self.pdf.ln()
                self.pdf.set_font("Arial", "", 9)
            
          
            self.pdf.cell(col_widths[0], 10, str(course.get("code", "")), 1, 0, "L", alternate)
            
            
            course_name = str(course.get("name", ""))
            self.pdf.cell(col_widths[1], 10, course_name, 1, 0, "L", alternate)
            
            self.pdf.cell(col_widths[2], 10, str(course.get("credits", "")), 1, 0, "C", alternate)
            self.pdf.cell(col_widths[3], 10, str(course.get("semester", "")), 1, 0, "C", alternate)
            self.pdf.cell(col_widths[4], 10, str(course.get("no_of_co", "")), 1, 0, "C", alternate)
            self.pdf.ln()
            
            
            alternate = not alternate
        
       
        timestamp = int(time.time())
        filename = f"course_report_{query_type}_{query_value}_{timestamp}.pdf"
        filepath = os.path.join(PDF_DIR, filename)
        
        
        self.pdf.output(filepath)
        
        logger.info(f"Generated PDF report at {filepath}")
        
   
        return f"{PDF_WEB_PATH}/{filename}" 