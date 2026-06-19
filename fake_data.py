import random
from faker import Faker
from database import get_db_connection, init_db

def generate_fake_data():
    """Generates fake records using Faker and populates university.db."""
    # Ensure tables exist
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM Student")
    if cursor.fetchone()[0] > 0:
        print("Database already populated with fake data.")
        conn.close()
        return

    fake = Faker()
    print("Populating database with fake data...")
    
    # 1. Generate Departments (10 departments)
    departments = [
        "Computer Science", "Mathematics", "Physics", "Chemistry", 
        "Biology", "Electrical Engineering", "Mechanical Engineering",
        "Economics", "English Literature", "History"
    ]
    for dept_name in departments:
        cursor.execute("INSERT OR IGNORE INTO Department (name) VALUES (?)", (dept_name,))
    
    # Get all department IDs
    cursor.execute("SELECT id FROM Department")
    dept_ids = [row[0] for row in cursor.fetchall()]
    
    # 2. Generate Teachers (100 teachers)
    # Each teacher assigned to a department
    teacher_ids = []
    for _ in range(100):
        name = fake.name()
        dept_id = random.choice(dept_ids)
        cursor.execute("INSERT INTO Teacher (name, dept_id) VALUES (?, ?)", (name, dept_id))
        teacher_ids.append(cursor.lastrowid)
        
    # 3. Generate Courses (200 courses)
    # Subject prefixes matching departments
    course_subjects = {
        "Computer Science": ["Intro to Programming", "Data Structures", "Algorithms", "Database Systems", "Operating Systems", "Artificial Intelligence", "Machine Learning", "Software Engineering", "Computer Networks", "Cybersecurity"],
        "Mathematics": ["Calculus I", "Calculus II", "Linear Algebra", "Discrete Mathematics", "Probability and Statistics", "Differential Equations", "Number Theory", "Real Analysis", "Abstract Algebra", "Numerical Analysis"],
        "Physics": ["General Physics I", "General Physics II", "Classical Mechanics", "Electromagnetism", "Thermodynamics", "Quantum Mechanics", "Astrophysics", "Solid State Physics", "Optics", "Nuclear Physics"],
        "Chemistry": ["General Chemistry", "Organic Chemistry I", "Organic Chemistry II", "Inorganic Chemistry", "Physical Chemistry", "Analytical Chemistry", "Biochemistry", "Environmental Chemistry", "Polymer Chemistry", "Spectroscopy"],
        "Biology": ["General Biology", "Cell Biology", "Genetics", "Microbiology", "Evolutionary Biology", "Ecology", "Molecular Biology", "Neurobiology", "Immunology", "Marine Biology"],
        "Electrical Engineering": ["Circuit Theory", "Digital Logic", "Signals and Systems", "Microprocessors", "Control Systems", "Power Systems", "Electromagnetics", "Embedded Systems", "Communication Systems", "VLSI Design"],
        "Mechanical Engineering": ["Statics", "Dynamics", "Thermodynamics I", "Fluid Mechanics", "Strength of Materials", "Machine Design", "Heat Transfer", "Manufacturing Processes", "Kinematics", "Robotics"],
        "Economics": ["Microeconomics", "Macroeconomics", "Econometrics", "Game Theory", "International Trade", "Public Finance", "Development Economics", "Labor Economics", "Financial Economics", "Behavioral Economics"],
        "English Literature": ["Introduction to Literature", "Shakespeare", "Creative Writing", "American Literature", "British Literature", "Modern Poetry", "Literary Theory", "World Literature", "Rhetoric", "Contemporary Fiction"],
        "History": ["World History I", "World History II", "American History", "European History", "Ancient Civilizations", "History of Science", "Warfare in History", "Medieval Europe", "Modern Asia", "Historiography"]
    }
    
    # Map department names to their IDs
    cursor.execute("SELECT id, name FROM Department")
    dept_name_to_id = {row[1]: row[0] for row in cursor.fetchall()}
    
    # We will generate 200 courses. Let's iterate and sample randomly or systematically.
    for i in range(200):
        # Pick a random department
        dept_name = random.choice(list(course_subjects.keys()))
        dept_id = dept_name_to_id[dept_name]
        
        # Select a courses list
        course_name = f"{random.choice(course_subjects[dept_name])} {random.randint(100, 499)}"
        
        # Get teachers for this department
        cursor.execute("SELECT id FROM Teacher WHERE dept_id = ?", (dept_id,))
        dept_teachers = [row[0] for row in cursor.fetchall()]
        
        # Fallback to any teacher if none in this department
        teacher_id = random.choice(dept_teachers) if dept_teachers else random.choice(teacher_ids)
        
        cursor.execute("INSERT INTO Course (name, teacher_id) VALUES (?, ?)", (course_name, teacher_id))
        
    # 4. Generate Students (5000 students)
    # Each student assigned to a department, cgpa between 1.5 and 4.0
    students_data = []
    for _ in range(5000):
        name = fake.name()
        dept_id = random.choice(dept_ids)
        cgpa = round(random.uniform(2.0, 4.0), 2)
        students_data.append((name, dept_id, cgpa))
        
    cursor.executemany("INSERT INTO Student (name, dept_id, cgpa) VALUES (?, ?, ?)", students_data)
    
    conn.commit()
    conn.close()
    print("Database population completed successfully!")

if __name__ == "__main__":
    generate_fake_data()
