
from flask import Flask, render_template, request
from collections import Counter
import re

app = Flask(__name__)

STOP_WORDS = {
    "the", "is", "a", "an", "and", "or", "of", "to",
    "in", "on", "for", "with", "are", "was", "were",
    "it", "this", "that", "from", "by", "as", "at",
    "be", "can", "has", "have", "their", "its", "into",
    "without", "main", "three"
}


def extract_keywords(text, limit=8):
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    filtered = [word for word in words if word not in STOP_WORDS]
    counts = Counter(filtered)
    return [word for word, count in counts.most_common(limit)]


def generate_summary(text, max_sentences=3):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s for s in sentences if s.strip()]

    if len(sentences) <= max_sentences:
        return text.strip()

    keywords = set(extract_keywords(text, 15))

    scored = []
    for index, sentence in enumerate(sentences):
        words = re.findall(r"\b[a-zA-Z]+\b", sentence.lower())
        score = sum(1 for word in words if word in keywords)
        scored.append((score, index, sentence))

    selected = sorted(
        sorted(scored, reverse=True)[:max_sentences],
        key=lambda item: item[1]
    )

    return " ".join(item[2] for item in selected)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    result = None
    error = None
    notes = ""
    summary = None
    keywords = []

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

    return render_template(
        "analyze.html",
        result=result,
        error=error,
        notes=notes,
        summary=summary,
        keywords=keywords
    )


if __name__ == "__main__":
    app.run(debug=True)
