import re
import logging
from typing import Dict, Any, Tuple


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def classify_query(text: str) -> Tuple[str, float]:
    """
    Classify a query as student-related, faculty-related, or unknown
    
    Args:
        text: The user's query text
        
    Returns:
        Tuple of (query_type, confidence)
    """
  
    student_keywords = [
        "student", "students", "year", "semester", "section", "batch",
        "register", "registration", "reg no", "who is", "tell me about"
    ]
    

    faculty_keywords = [
        "faculty", "teacher", "professor", "lecturer", "instructor",
        "subject", "course", "teach", "teaches", "teaching", "taught",
        "handle", "handles", "handling", "handled", "take", "takes", "taking"
    ]
    
    # Count matches 
    student_count = sum(1 for keyword in student_keywords if keyword.lower() in text.lower())
    faculty_count = sum(1 for keyword in faculty_keywords if keyword.lower() in text.lower())
    
    # Calculate confidence based on keyword matches
    total_count = student_count + faculty_count
    if total_count == 0:
        return "unknown", 0.0
    
    if student_count > faculty_count:
        return "student", student_count / total_count
    elif faculty_count > student_count:
        return "faculty", faculty_count / total_count
    else:
        return "unknown", 0.0

def is_student_query(text: str) -> bool:
    """Check if a query is student-related using regex patterns"""
    student_patterns = [
        r"(?:who|tell me about|about)\s+(?:is|are)?\s*([A-Za-z\s]+)(?:\?)?$",  # Who is Aamir Khan?
        r"(?:about|tell me about|find|get)\s+(?:student|register number|reg no)?\s*([0-9]{2}[A-Za-z]{2}[0-9]{4})(?:\?)?",  # Tell me about 21CS1001
        r"(?:students|student|show|list|get|find).*(?:in|of|from)?\s+(?:year)?\s*([1-4])(?:\?)?",  # Show students in year 3
        r"(?:students|student|show|list|get|find).*(?:in|of|from)?\s+(?:semester|sem)?\s*([1-8])(?:\?)?",  # List students in semester 6
        r"(?:students|student|show|list|get|find).*(?:in|of|from)?\s+(?:section)?\s*([A-C])(?:\?)?",  # Show students in section A
        r"(?:students|student|show|list|get|find).*(?:in|of|from)?\s+(?:batch)?\s*(20\d{2}-20\d{2})(?:\?)?",  # List students in batch 2021-2025
    ]
    
    for pattern in student_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def is_faculty_query(text: str) -> bool:
    """Check if a query is faculty-related using regex patterns"""
    faculty_patterns = [
        r"(?:what|which)\s+(?:subject|subjects)(?:\s+does)?\s+([A-Za-z\s\.]+)(?:\s+(?:teach|teaches|take|takes|handle|handles))?",  # What subjects does Dr. Sreenath teach?
        r"(?:who|which faculty)(?:\s+(?:is|are))?\s+(?:teaching|teaches|taking|takes|handling|handles)\s+([A-Za-z\s]+)",  # Who teaches Computer Networks?
        r"(?:faculty|teacher|professor)(?:\s+(?:for|of))\s+([A-Za-z\s]+)",  # Faculty for Computer Networks
    ]
    
    for pattern in faculty_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def route_query(text: str) -> Dict[str, Any]:
    """
    Route a query to the appropriate handler based on classification
    
    Args:
        text: The user's query text
        
    Returns:
        Dictionary with response data and success status
    """
    logger.info(f"Routing query: {text}")
    
   
    greeting_keywords = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]
    if any(keyword in text.lower() for keyword in greeting_keywords) or text.lower() in greeting_keywords:
        return handle_greeting()
    
    goodbye_keywords = ["bye", "goodbye", "see you", "farewell", "thanks", "thank you"]
    if any(keyword in text.lower() for keyword in goodbye_keywords) or text.lower() in goodbye_keywords:
        return handle_goodbye()
    
    help_keywords = ["help", "assist", "support", "guide", "what can you do", "how to use"]
    if any(keyword in text.lower() for keyword in help_keywords) or text.lower() in help_keywords:
        return handle_help()
    
   
    query_type, confidence = classify_query(text)
    logger.info(f"Query classified as {query_type} with confidence {confidence}")
    
    # Route to the appropriate handler
    if query_type == "student":
        return handle_student_query(text)
    elif query_type == "faculty":
        return handle_faculty_query(text)
    else:
        
        student_result = handle_student_query(text)
        if student_result["success"]:
            return student_result
        
        faculty_result = handle_faculty_query(text)
        if faculty_result["success"]:
            return faculty_result
        
        # If both handlers fail, return a generic fallback response
        return handle_fallback(text) 