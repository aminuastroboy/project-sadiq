# 📚 Lecture Attendance Checker

A Streamlit-based webapp for biometric lecture attendance tracking.

## 🚀 Features
- Student registration with face capture
- Secure login with hashed passwords
- Face-based lecture check-in (DeepFace + Facenet)
- Attendance dashboard per lecture
- SQLite database storage

## 🛠️ Setup (Local)

1. Clone or unzip the project:
   ```bash
   git clone <repo-url>
   cd lecture-attendance-app
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   streamlit run app.py
   ```

4. Open the app in your browser at `http://localhost:8501`.

## 🌐 Deployment (Streamlit Cloud)

1. Push the project to a GitHub repository.

2. Go to [Streamlit Cloud](https://share.streamlit.io).

3. Connect your GitHub account and select the repository.

4. In the deployment settings:
   - **Main file path**: `app.py`
   - **Python version**: 3.11+
   - **Dependencies file**: `requirements.txt`

5. Deploy 🚀

## 📂 Project Structure
```
lecture-attendance-app/
│── app.py              # Main Streamlit app
│── requirements.txt    # Dependencies
│── README.md           # Deployment guide
│── data/               # Face images (auto-created)
│── attendance.db       # SQLite database (auto-created)
```

---

Made with ❤️ using Streamlit + DeepFace.
