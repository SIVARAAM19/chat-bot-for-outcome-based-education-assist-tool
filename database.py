import mysql.connector
import re
import logging
from typing import List, Dict, Any, Tuple, Optional


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the MySQL database"""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root", 
            password="", 
            database="oat"
        )
        return conn
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
        raise

def normalize_faculty_name(name: str) -> str:
    """Normalize faculty name by handling variations with or without Dr. prefix"""
    
    name = re.sub(r'[.,;:!?]$', '', name).strip()
    
   
    if name.lower().startswith('dr '):
        name = 'Dr. ' + name[3:]
    elif name.lower().startswith('dr. '):
        pass  
    elif name.lower().startswith('dr.'):
        name = 'Dr. ' + name[3:]
    
    return name

def extract_register_number(text: str) -> Optional[str]:
    """Extract register number from text"""
    
    cleaned_text = re.sub(r'^(?:hi|hello|hey|greetings|good\s+(?:morning|afternoon|evening))\s*', '', text.lower())
    
    patterns = [
        # MCA format (e.g., 2401507109, 2301507311)
        r'\b(2[0-9]{9})\b',
        # B.Tech format (e.g., 21CS1001)
        r'\b([0-9]{2}[A-Za-z]{2}[0-9]{4})\b',
        
        r'\b([0-9]{10})\b'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, cleaned_text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def extract_student_name(text: str) -> Optional[str]:
    """Extract student name from text"""
    patterns = [
        r'who\s+is\s+([A-Za-z\s]+)',
        r'tell\s+me\s+about\s+([A-Za-z\s]+)',
        r'find\s+student\s+named\s+([A-Za-z\s]+)',
        r'student\s+([A-Za-z\s]+)',
        r'about\s+([A-Za-z\s]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None

def extract_year(text: str) -> Optional[str]:
    """Extract year from text"""
    patterns = [
        r'(?:show|list|get|who).*(?:students|are).*(?:in|of|from|the).*(?:year|yr).*?([1-4])',
        r'(?:year|yr)\s+([1-4]).*(?:students|are)',
        r'([1-4])(?:st|nd|rd|th)?\s+(?:year|yr).*(?:students|are)',
        r'(?:students|are).*(?:year|yr).*?([1-4])'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def extract_semester(text: str) -> Optional[str]:
    """Extract semester from text"""
    patterns = [
        r'(?:show|list|get|who).*(?:students|are).*(?:in|of|from).*semester.*?([1-8])',
        r'semester\s+([1-8]).*(?:students|are)',
        r'([1-8])(?:st|nd|rd|th)?\s+semester.*(?:students|are)',
        r'(?:students|are).*semester.*?([1-8])'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def extract_section(text: str) -> Optional[str]:
    """Extract section from text"""
    patterns = [
        r'(?:show|list|get|who).*(?:students|are).*(?:in|of|from).*section.*?([A-E])',
        r'section\s+([A-E]).*(?:students|are)',
        r'(?:students|are).*section.*?([A-E])'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return None

def extract_batch(text: str) -> Optional[str]:
    """Extract batch from text"""
    patterns = [
        r'(?:show|list|get|who).*(?:students|are).*(?:in|of|from).*batch.*?(\d{4}-\d{4})',
        r'batch\s+(\d{4}-\d{4}).*(?:students|are)',
        r'(?:students|are).*batch.*?(\d{4}-\d{4})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def extract_subject_name(text: str) -> Optional[str]:
    """Extract subject name from text"""
    patterns = [
        r'who\s+(?:is\s+)?(?:teaching|teaches|taking|takes|handling|handles)\s+([A-Za-z\s]+)',
        r'faculty\s+(?:for|of)\s+([A-Za-z\s]+)',
        r'which\s+faculty\s+(?:teaches|handles|taking|takes)\s+([A-Za-z\s]+)',
        r'who\s+(?:is|are)\s+(?:the)?\s*(?:faculty|teacher|professor)\s+(?:for|of)\s+([A-Za-z\s]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            subject_name = match.group(1).strip()
            
            subject_name = re.sub(r'[.,;:!?]$', '', subject_name)
            return subject_name
    
    
    if len(text.split()) <= 3:
        return text.strip()
    
    return None

def extract_faculty_name(text: str) -> Optional[str]:
    """Extract faculty name from text"""
    patterns = [
        r'what\s+(?:subject|subjects|courses)?\s+(?:does|do|is|are)?\s+([A-Za-z\s\.]+?)(?:\s+(?:teach|handle|take|handles|teaches|taking|taught|handled)s?)?(?:\s*\??)?$',
        r'(?:subject|subjects)\s+(?:taught|handled)\s+by\s+([^?]+?)(?:\s*\??)?$',
        r'what\s+does\s+([A-Za-z\s\.]+?)(?:\s+(?:teach|handle|take|handles|teaches|taking|taught|handled)s?)?(?:\s*\??)?$',
        r'what\s+(?:subject|subjects|courses)?\s+(?:does|do)?\s*([A-Za-z\s\.]+?)(?:\s+(?:teach|handle|take|handles|teaches|taking|taught|handled)s?)?(?:\s*\??)?$',
        r'(?:subject|subjects|courses)\s+(?:of|for|by)\s+([A-Za-z\s\.]+?)(?:\s*\??)?$',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            faculty_name = match.group(1).strip()
            # Remove any trailing punctuation
            faculty_name = re.sub(r'[.,;:!?]$', '', faculty_name)
            logger.info(f"Extracted faculty name: '{faculty_name}' from query: '{text}'")
            return faculty_name
    
    
    words = text.split()
    if 2 <= len(words) <= 4:
        
        for word in words:
            if word[0].isupper() and len(word) > 2 and word.lower() not in ['what', 'who', 'does', 'teach', 'subject', 'subjects', 'take', 'takes', 'handle', 'handles']:
                logger.info(f"Extracted potential faculty name: '{word}' from short query: '{text}'")
                return word
    
    logger.info(f"Could not extract faculty name from: '{text}'")
    return None

def extract_type(text: str) -> Optional[str]:
    """Extract student type from text"""
    text = text.lower()
    
    
    if re.search(r'm\.?tech\s+is|m\s*tech\s+is', text, re.IGNORECASE):
        logger.info(f"Extracted M.Tech IS from: {text}")
        return "mtech"  
    elif re.search(r'm\.?tech\s+ds|m\s*tech\s+ds', text, re.IGNORECASE):
        logger.info(f"Extracted M.Tech DS from: {text}")
        return "mtech"  
    elif re.search(r'm\.?tech|m\s*tech', text, re.IGNORECASE):
        logger.info(f"Extracted general M.Tech from: {text}")
        return "mtech"
    
    
    if "btech" in text or "b.tech" in text or "b tech" in text:
        logger.info(f"Extracted B.Tech from: {text}")
        return "btech"
    elif "mca" in text:
        logger.info(f"Extracted MCA from: {text}")
        return "mca"
    
    return None

def get_students_by_type(type_str: str) -> List[Dict[str, Any]]:
    """Get students by type (B.Tech, M.Tech IS, M.Tech DS, MCA, PhD)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
       
        if "%" in type_str:
            logger.info(f"Using LIKE query for type: {type_str}")
            query = "SELECT * FROM student WHERE type LIKE %s"
        else:
            logger.info(f"Using exact match query for type: {type_str}")
            query = "SELECT * FROM student WHERE type = %s"
        
        
        logger.info("Executing SQL: " + query.replace("%s", f'"{type_str}"'))
        
        cursor.execute(query, (type_str,))
        results = cursor.fetchall()
        
        
        if results:
            logger.info(f"Found {len(results)} students with type: {type_str}")
            
            if len(results) > 0:
                logger.info(f"First result type: {results[0].get('type', 'unknown')}")
        else:
            logger.info(f"No students found with type: {type_str}")
            
            
            if "%" not in type_str:
                try:
                    cursor.execute("SELECT DISTINCT type FROM student")
                    types = cursor.fetchall()
                    type_list = [t.get('type', 'unknown') for t in types]
                    logger.info(f"Available types in database: {type_list}")
                except Exception as e:
                    logger.error(f"Error fetching available types: {e}")
        
        cursor.close()
        conn.close()
        
        return results
    except Exception as e:
        logger.error(f"Error fetching students by type: {e}")
    return []

def is_student_query(text: str) -> bool:
    """Determine if a query is related to students"""
    
    reg_no = extract_register_number(text)
    if reg_no:
        return True
        
   
    cleaned_text = re.sub(r'^(?:hi|hello|hey|greetings|good\s+(?:morning|afternoon|evening))\s*', '', text.lower())
    
    student_keywords = ["student", "students", "register", "reg no", "year", "semester", "section", "batch", "b.tech", "m.tech", "btech", "mtech", "phd", "mca"]
    
    # student keyword
    if any(keyword in cleaned_text.lower() for keyword in student_keywords):
        return True
    
    # student name 
    if extract_student_name(cleaned_text):
        return True
    
    
    if (extract_year(cleaned_text) or extract_semester(cleaned_text) or 
        extract_section(cleaned_text) or extract_batch(cleaned_text) or
        extract_type(cleaned_text)):
        return True
    
    return False

def is_faculty_query(text: str) -> bool:
    """Determine if a query is related to faculty"""
    faculty_keywords = ["faculty", "teacher", "professor", "lecturer", "instructor", "teaches", "teaching", "subject", "course"]
    
    # faculty keywords
    if any(keyword in text.lower() for keyword in faculty_keywords):
        return True
    
    # faculty name patterns
    if extract_faculty_name(text):
        return True
    
    #  subject name patterns
    if extract_subject_name(text):
        return True
    
    return False

def classify_query(text: str) -> Tuple[str, float]:
    """Classify the query type with confidence score"""
  
    if extract_register_number(text):
        return "student", 1.0  
    
   
    cleaned_text = re.sub(r'^(?:hi|hello|hey|greetings|good\s+(?:morning|afternoon|evening))\s*', '', text.lower())
    
   
    student_score = 0.0
    if is_student_query(cleaned_text):
        student_score = 0.8
        
        
        if extract_year(cleaned_text) or extract_semester(cleaned_text) or extract_section(cleaned_text) or extract_batch(cleaned_text):
            student_score = 0.9
        elif extract_type(cleaned_text):
            student_score = 0.9
    
    
    faculty_score = 0.0
    if is_faculty_query(cleaned_text):
        faculty_score = 0.8
        
      
        if extract_subject_name(cleaned_text) and ("who" in cleaned_text.lower() or "faculty" in cleaned_text.lower()):
            faculty_score = 0.9
        elif extract_faculty_name(cleaned_text) and "subject" in cleaned_text.lower():
            faculty_score = 0.9
    
   
    if student_score > faculty_score and student_score > 0.6:
        return "student", student_score
    elif faculty_score > 0.6:
        return "faculty", faculty_score
    else:
        return "unknown", 0.0

class DatabaseConnection:
    """Class to handle database connections and operations"""
    
    def __init__(self, host="127.0.0.1", user="root", password="", database="oat"):
        """Initialize database connection parameters"""
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """Establish connection to the database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.connection.cursor(dictionary=True)
            return True
        except mysql.connector.Error as err:
            logger.error(f"Database connection error: {err}")
            return False
    
    def disconnect(self) -> None:
        """Close the database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        results = []
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
        except mysql.connector.Error as err:
            logger.error(f"Query execution error: {err}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
        
        return results

# Student database operations
def get_student_by_name(name: str) -> List[Dict[str, Any]]:
    """Get student details by name"""
    db = DatabaseConnection()
    if db.connect():
        query = """
        SELECT * FROM student 
        WHERE name LIKE %s
        """
        params = (f"%{name}%",)
        results = db.execute_query(query, params)
        db.disconnect()
        return results
    return []

def get_student_by_register_number(reg_no: str) -> List[Dict[str, Any]]:
    """Get student details by register number"""
    db = DatabaseConnection()
    if db.connect():
        query = "SELECT * FROM student WHERE register_no = %s"
        params = (reg_no,)
        results = db.execute_query(query, params)
        
        
        if not results and reg_no.startswith('0'):
            query = "SELECT * FROM student WHERE register_no = %s"
            params = (reg_no.lstrip('0'),)
            results = db.execute_query(query, params)
        
        db.disconnect()
        return results
    return []

def get_students_by_year(year: int) -> List[Dict[str, Any]]:
    """Get students by year"""
    db = DatabaseConnection()
    if db.connect():
        query = "SELECT * FROM student WHERE year = %s"
        params = (year,)
        results = db.execute_query(query, params)
        db.disconnect()
        return results
    return []

def get_students_by_semester(semester: int) -> List[Dict[str, Any]]:
    """Get students by semester"""
    db = DatabaseConnection()
    if db.connect():
        query = "SELECT * FROM student WHERE semester = %s"
        params = (semester,)
        results = db.execute_query(query, params)
        db.disconnect()
        return results
    return []

def get_students_by_section(section: str) -> List[Dict[str, Any]]:
    """Get students by section"""
    db = DatabaseConnection()
    if db.connect():
        query = "SELECT * FROM student WHERE section = %s"
        params = (section,)
        results = db.execute_query(query, params)
        db.disconnect()
        return results
    return []

def get_students_by_batch(batch: str) -> List[Dict[str, Any]]:
    """Get students by batch"""
    db = DatabaseConnection()
    if db.connect():
        query = "SELECT * FROM student WHERE batch = %s"
        params = (batch,)
        results = db.execute_query(query, params)
        db.disconnect()
        return results
    return []

# Faculty database operations
def get_faculty_by_subject(subject: str) -> List[Dict[str, Any]]:
    """Get faculty details by subject"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        
        subject_pattern = f"%{subject}%"
        
        
        if re.search(r'computer\s+networks?', subject, re.IGNORECASE):
            subject_pattern = "%Computer Network%"
            logger.info(f"Special handling for Computer Networks, using pattern: {subject_pattern}")
        
        logger.info(f"Searching for faculty teaching subject matching: {subject_pattern}")
        
        query = """
        SELECT f.id, f.name, f.email, f.role, c.code as subject_code, c.name as subject_name
        FROM faculty f
        JOIN faculty_course fc ON f.id = fc.faculty_id
        JOIN course c ON fc.course_id = c.code
        WHERE c.name LIKE %s
        """
        
        cursor.execute(query, (subject_pattern,))
        results = cursor.fetchall()
        
        logger.info(f"Found {len(results)} faculty members teaching {subject}")
        
       
        if not results:
           
            flexible_pattern = f"%{' '.join(subject.split()[:2])}%"
            logger.info(f"No results found, trying with more flexible pattern: {flexible_pattern}")
            
            cursor.execute(query, (flexible_pattern,))
            results = cursor.fetchall()
            logger.info(f"Found {len(results)} faculty members with flexible pattern")
        
        cursor.close()
        conn.close()
        
        return results
    except Exception as e:
        logger.error(f"Error fetching faculty for subject: {e}")
        return []

def get_subjects_by_faculty(faculty_name: str) -> List[Dict[str, Any]]:
    """Get subjects taught by a faculty member"""
    try:
        
        normalized_name = normalize_faculty_name(faculty_name)
        logger.info(f"Searching for subjects taught by faculty: {normalized_name}")
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT f.name, c.code as subject_code, c.name as subject_name, fc.section
        FROM faculty f
        JOIN faculty_course fc ON f.id = fc.faculty_id
        JOIN course c ON fc.course_id = c.code
        WHERE f.name LIKE %s
        """
        
        pattern = f"%{normalized_name}%"
        cursor.execute(query, (pattern,))
        results = cursor.fetchall()
        
        logger.info(f"Found {len(results)} subjects taught by faculty matching '{normalized_name}'")
        
      
        if not results and ' ' in normalized_name:
            first_name = normalized_name.split()[0]
            logger.info(f"No results found, trying with just first name: {first_name}")
            
            cursor.execute(query, (f"%{first_name}%",))
            results = cursor.fetchall()
            logger.info(f"Found {len(results)} subjects with first name search")
        
        cursor.close()
        conn.close()
        
        return results
    except Exception as e:
        logger.error(f"Error fetching subjects for faculty: {e}")
        return []

# formatting responses
def format_student_details(student: Dict[str, Any]) -> str:
    """Format student details for display"""
    details = (
        f"Register No: {student.get('register_no')} "
        f"Name: {student.get('name')} "
        f"Year: {student.get('year')} "
        f"Semester: {student.get('semester')} "
        f"Section: {student.get('section')} "
    )
    
    
    if student.get('batch'):
        details += f"Batch: {student.get('batch')} "
    if student.get('type'):
        details += f"Type: {student.get('type')}"
    
    return details.strip()

def format_faculty_details(faculty: Dict[str, Any]) -> str:
    """Format faculty details for display"""
    return (
        f"Name: {faculty.get('name')} "
        f"Email: {faculty.get('email')} "
        f"Subject: {faculty.get('subject_name')} ({faculty.get('subject_code')})"
    )

def format_subject_details(subject: Dict[str, Any]) -> str:
    """Format subject details for display"""
    section_info = f", Section: {subject.get('section')}" if subject.get('section') else ""
    return (
        f"{subject.get('subject_code')}: {subject.get('subject_name')}{section_info}"
    )

# Course database operations
def get_course_by_code(course_code):
    """Get course details by course code"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    
    normalized_code = course_code.replace(" ", "").upper()
    
    cursor.execute("SELECT * FROM course WHERE code = %s", (normalized_code,))
    courses = cursor.fetchall()
    
    conn.close()
    return courses

def get_course_by_name(course_name):
    """Get course details by course name (partial match)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM course WHERE name LIKE %s", (f"%{course_name}%",))
    courses = cursor.fetchall()
    
    conn.close()
    return courses

def get_courses_by_semester(semester):
    """Get courses offered in a specific semester"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM course WHERE semester = %s", (semester,))
    courses = cursor.fetchall()
    
    conn.close()
    return courses

def get_courses_by_credits(credits):
    """Get courses with specific credit value"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM course WHERE credits = %s", (credits,))
    courses = cursor.fetchall()
    
    conn.close()
    return courses

def get_courses_by_type(course_type):
    """Get courses of a specific type (core, elective, etc.)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM course WHERE type = %s", (course_type,))
    courses = cursor.fetchall()
    
    conn.close()
    return courses

def format_course_details(course):
    """Format course details for display"""
    return f"""
Course: {course['code']} - {course['name']}
Credits: {course['credits']}
Type: {course['type']}
Semester: {course['semester']}
Course Outcomes: {course['no_of_co']}
"""


def extract_course_code(message):
    """Extract course code from message using regex"""
    import re
    code_match = re.search(r"\b([A-Z]{2,3}\s*\d{3})\b", message, re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip().replace(" ", "").upper()
    return None

def extract_course_name(message):
    """Extract course name from message using regex"""
    import re
   
    name_match = re.search(r"(?:about|for|is|on|regarding)\s+([A-Za-z\s&]+?)(?:\?|$|\.)", message)
    if name_match:
        return name_match.group(1).strip()
    return None

def extract_semester(message):
    """Extract semester number from message using regex"""
    import re
    semester_match = re.search(r"semester\s+([1-8])", message, re.IGNORECASE)
    if semester_match:
        return semester_match.group(1)
    return None 