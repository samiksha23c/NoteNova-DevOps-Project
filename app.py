
from flask import Flask, render_template, request

app = Flask(__name__)


# Homepage
@app.route('/')
def home():
    return render_template('index.html')


# Study Material Analyzer
@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    result = None
    error = None
    notes = ""

    if request.method == 'POST':
        notes = request.form.get('notes', '').strip()
        uploaded_file = request.files.get('file')

        if uploaded_file and uploaded_file.filename:
            if not uploaded_file.filename.lower().endswith('.txt'):
                error = "Please upload a .txt file only."
            else:
                try:
                    notes = uploaded_file.read().decode('utf-8')
                except UnicodeDecodeError:
                    error = "Please upload a UTF-8 text file."

        if not error:
            if not notes.strip():
                error = "Please enter notes or upload a file."
            else:
                result = notes[:2000]

    return render_template(
        'analyze.html',
        result=result,
        error=error,
        notes=notes
    )


# Run Flask Application
if __name__ == '__main__':
    app.run(debug=True)
