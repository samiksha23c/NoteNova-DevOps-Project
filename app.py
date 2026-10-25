
from flask import Flask, render_template, request
from collections import Counter
from datetime import datetime
import sqlite3
import re


# ---------------------------------
# Flask Application
# ---------------------------------

app = Flask(__name__)

DATABASE = "notenova.db"

app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


# ---------------------------------
# Stop Words
# ---------------------------------

STOP_WORDS = {
    "the", "is", "a", "an", "and", "or", "of", "to",
    "in", "on", "for", "with", "are", "was", "were",
    "it", "this", "that", "from", "by", "as", "at",
    "be", "can", "has", "have", "their", "its", "into",
    "without", "main", "three"
}


# ---------------------------------
# Database Initialization
# ---------------------------------

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT NOT NULL,
                word_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


# ---------------------------------
# Save Study Session
# ---------------------------------

def save_session(notes, summary):
    title = " ".join(notes.split()[:6])
    word_count = len(notes.split())

    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            INSERT INTO study_sessions
            (title, content, summary, word_count, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            title,
            notes,
            summary,
            word_count,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))


# Create database tables
init_db()


# ---------------------------------
# Keyword Extraction
# ---------------------------------

def extract_keywords(text, limit=8):
    words = re.findall(
        r"\b[a-zA-Z]{3,}\b",
        text.lower()
    )

    filtered = [
        word for word in words
        if word not in STOP_WORDS
    ]

    counts = Counter(filtered)

    return [
        word for word, count
        in counts.most_common(limit)
    ]


# ---------------------------------
# Automatic Text Summarization
# ---------------------------------

def generate_summary(text, max_sentences=3):
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text.strip()
    )

    sentences = [
        sentence for sentence in sentences
        if sentence.strip()
    ]

    if len(sentences) <= max_sentences:
        return text.strip()

    keywords = set(extract_keywords(text, 15))

    scored = []

    for index, sentence in enumerate(sentences):
        words = re.findall(
            r"\b[a-zA-Z]+\b",
            sentence.lower()
        )

        score = sum(
            1 for word in words
            if word in keywords
        )

        scored.append((score, index, sentence))

    selected = sorted(
        sorted(
            scored,
            reverse=True
        )[:max_sentences],
        key=lambda item: item[1]
    )

    return " ".join(
        item[2] for item in selected
    )


# ---------------------------------
# Automatic Quiz Generator
# ---------------------------------

def generate_quiz(text, max_questions=5):
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text.strip()
    )

    keywords = extract_keywords(text, 15)

    questions = []
    used_answers = set()

    for sentence in sentences:
        words = re.findall(
            r"\b[a-zA-Z]{3,}\b",
            sentence
        )

        for word in words:
            if (
                word.lower() in keywords
                and word.lower() not in used_answers
            ):
                question = re.sub(
                    r"\b" + re.escape(word) + r"\b",
                    "________",
                    sentence,
                    count=1,
                    flags=re.IGNORECASE
                )

                questions.append({
                    "question": question,
                    "answer": word.lower()
                })

                used_answers.add(word.lower())
                break

        if len(questions) >= max_questions:
            break

    return questions


# ---------------------------------
# Homepage Route
# ---------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------------------------
# Study Material Analyzer Route
# ---------------------------------

@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    result = None
    error = None
    notes = ""
    summary = None
    keywords = []
    quiz = []

    if request.method == "POST":
        notes = request.form.get("notes", "").strip()
        uploaded_file = request.files.get("file")

        if uploaded_file and uploaded_file.filename:
            if not uploaded_file.filename.lower().endswith(".txt"):
                error = "Please upload a .txt file only."
            else:
                try:
                    notes = uploaded_file.read().decode("utf-8")
                except UnicodeDecodeError:
                    error = "Please upload a UTF-8 text file."

        if not error:
            if not notes.strip():
                error = "Please enter notes or upload a file."
            else:
                result = notes[:2000]

                summary = generate_summary(notes)
                keywords = extract_keywords(notes)
                quiz = generate_quiz(notes)

                # Save analysis to database
                save_session(notes, summary)

    return render_template(
        "analyze.html",
        result=result,
        error=error,
        notes=notes,
        summary=summary,
        keywords=keywords,
        quiz=quiz
    )


# ---------------------------------
# Study Dashboard Route
# ---------------------------------

@app.route("/dashboard")
def dashboard():
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row

        sessions = conn.execute("""
            SELECT id, title, summary,
                   word_count, created_at
            FROM study_sessions
            ORDER BY id DESC
        """).fetchall()

    total_sessions = len(sessions)

    total_words = sum(
        session["word_count"]
        for session in sessions
    )

    return render_template(
        "dashboard.html",
        sessions=sessions,
        total_sessions=total_sessions,
        total_words=total_words
    )


# ---------------------------------
# Run Flask Application
# ---------------------------------

if __name__ == "__main__":
    app.run(debug=True)
