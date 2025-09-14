import streamlit as st
import sqlite3, os
from datetime import datetime
from PIL import Image
from deepface import DeepFace
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = "attendance.db"
DATA_DIR = "data"

# --- Ensure data directory exists ---
os.makedirs(DATA_DIR, exist_ok=True)

# --- Database helpers ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE,
        name TEXT,
        email TEXT UNIQUE,
        password_hash TEXT,
        face_path TEXT,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS lectures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lecture_code TEXT,
        lecture_title TEXT,
        date TEXT
    );
    CREATE TABLE IF NOT EXISTS attendances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        lecture_id INTEGER,
        timestamp TEXT,
        FOREIGN KEY (lecture_id) REFERENCES lectures(id)
    );
    """)
    conn.commit()
    conn.close()

# --- Save uploaded face image ---
def save_face(student_id, image):
    img = Image.open(image).convert("RGB")
    path = os.path.join(DATA_DIR, f"{student_id}.jpg")
    img.save(path)
    return path

# --- Verify faces with DeepFace ---
def verify_faces(registered_img, new_img):
    try:
        result = DeepFace.verify(img1_path=registered_img, img2_path=new_img, model_name="Facenet")
        return result["verified"], result["distance"]
    except Exception:
        return False, 1.0

# --- Session state ---
if "user" not in st.session_state:
    st.session_state.user = None

# --- UI ---
st.set_page_config(page_title="Lecture Attendance Checker", page_icon="📚", layout="centered")
st.title("📚 Lecture Attendance Checker")

init_db()

menu = ["Home", "Register", "Login", "Check-in", "Dashboard"]
choice = st.sidebar.radio("Menu", menu)

# --- Registration ---
if choice == "Register":
    st.header("📝 Student Registration")
    sid = st.text_input("Student ID")
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    pw = st.text_input("Password", type="password")
    photo = st.camera_input("Capture face")
    if st.button("Register"):
        if not (sid and email and pw and photo):
            st.error("All fields and a face capture are required.")
        else:
            face_path = save_face(sid, photo)
            conn = get_db()
            try:
                conn.execute(
                    "INSERT INTO students(student_id,name,email,password_hash,face_path,created_at) VALUES(?,?,?,?,?,?)",
                    (sid, name, email, generate_password_hash(pw), face_path, datetime.utcnow().isoformat())
                )
                conn.commit()
                st.success("✅ Registered successfully! You can now login.")
            except sqlite3.IntegrityError:
                st.error("Student ID or Email already exists.")
            conn.close()

# --- Login ---
elif choice == "Login":
    st.header("🔑 Login")
    email = st.text_input("Email")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        conn = get_db()
        row = conn.execute("SELECT * FROM students WHERE email=?", (email,)).fetchone()
        conn.close()
        if row and check_password_hash(row["password_hash"], pw):
            st.session_state.user = dict(row)
            st.success(f"Welcome {row['name'] or row['student_id']}!")
        else:
            st.error("Invalid credentials")

# --- Check-in ---
elif choice == "Check-in":
    if not st.session_state.user:
        st.warning("Please login first.")
    else:
        st.header("📸 Lecture Check-in")
        lec_code = st.text_input("Lecture Code (e.g. CS101-2025-09-05)")
        lec_title = st.text_input("Lecture Title")
        photo = st.camera_input("Capture face to verify")
        if st.button("Check-in"):
            if not lec_code or not photo:
                st.error("Lecture code and face capture required.")
            else:
                user = st.session_state.user
                probe_path = save_face(f"{user['student_id']}_probe", photo)

                ok, dist = verify_faces(user["face_path"], probe_path)

                if not ok:
                    st.error(f"❌ Face mismatch (distance={dist:.3f})")
                else:
                    conn = get_db()
                    lec = conn.execute("SELECT id FROM lectures WHERE lecture_code=?", (lec_code,)).fetchone()
                    if not lec:
                        conn.execute(
                            "INSERT INTO lectures(lecture_code,lecture_title,date) VALUES(?,?,?)",
                            (lec_code, lec_title, datetime.utcnow().date().isoformat())
                        )
                        conn.commit()
                        lec_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    else:
                        lec_id = lec["id"]

                    dup = conn.execute("SELECT id FROM attendances WHERE student_id=? AND lecture_id=?",
                                       (user["student_id"], lec_id)).fetchone()
                    if dup:
                        st.info("Already checked in for this lecture.")
                    else:
                        conn.execute("INSERT INTO attendances(student_id,lecture_id,timestamp) VALUES(?,?,?)",
                                     (user["student_id"], lec_id, datetime.utcnow().isoformat()))
                        conn.commit()
                        st.success("✅ Check-in successful!")
                    conn.close()

# --- Dashboard ---
elif choice == "Dashboard":
    st.header("📊 Attendance Dashboard")
    conn = get_db()
    lecs = conn.execute("SELECT * FROM lectures ORDER BY date DESC").fetchall()
    lec_map = {f"{l['lecture_code']} - {l['date']}": l["id"] for l in lecs}
    if lec_map:
        lec_choice = st.selectbox("Select lecture", list(lec_map.keys()))
        if lec_choice:
            lec_id = lec_map[lec_choice]
            rows = conn.execute("""
                SELECT a.timestamp,s.student_id,s.name
                FROM attendances a
                JOIN students s ON s.student_id=a.student_id
                WHERE lecture_id=?
                ORDER BY a.timestamp
            """,(lec_id,)).fetchall()
            st.write(f"Attendance for {lec_choice}:")
            st.table(rows)
    else:
        st.info("No lectures yet.")
    conn.close()

# --- Home ---
else:
    st.subheader("👋 Welcome")
    if st.session_state.user:
        st.success(f"Logged in as {st.session_state.user['email']}")
    else:
        st.info("Use the sidebar to register, login, and check in.")

    st.markdown("---")
    st.markdown("### 📌 Project Details")
    st.markdown("""
    **Project Owner**: Abubakar Sadiq Sani  
    **School ID**: CSC/22D/4441 | CSC?21D/3172  
    **School Year**: 2024/2025  
    """)
