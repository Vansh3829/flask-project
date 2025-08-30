from flask import Flask, render_template, request
import io
import os
import fitz  # PyMuPDF
from docx import Document

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_stream):
    text = ""
    try:
        with fitz.open("pdf", file_stream) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        text = f"Error reading PDF: {e}"
    return text

def extract_text_from_docx(file_stream):
    try:
        doc = Document(file_stream)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        return f"Error reading DOCX: {e}"

def analyze_resume(resume_text, job_description):
    """Keyword matching"""
    required_skills = {skill.strip().lower() for skill in job_description.split()}
    resume_words = {word.lower() for word in resume_text.split()}

    matched_skills = required_skills.intersection(resume_words)
    missing_skills = required_skills - resume_words

    return {
        'matched_skills': list(matched_skills),
        'missing_skills': list(missing_skills),
        'match_score': len(matched_skills) / len(required_skills) if required_skills else 0
    }

@app.route("/", methods=['GET', 'POST'])
def upload_and_process():
    extracted_text = None
    results = None

    if request.method == 'POST':
        resume_file = request.files.get('file')
        job_description = request.form.get('job_description', '')

        if not resume_file or resume_file.filename == '':
            return render_template('index.html', error="No file selected")

        if allowed_file(resume_file.filename):
            file_extension = resume_file.filename.rsplit('.', 1)[1].lower()
            file_stream = io.BytesIO(resume_file.read())

            if file_extension == 'pdf':
                extracted_text = extract_text_from_pdf(file_stream)
            elif file_extension == 'docx':
                extracted_text = extract_text_from_docx(file_stream)
            else:
                extracted_text = "Unsupported file type"

            if extracted_text and job_description:
                results = analyze_resume(extracted_text, job_description)
        else:
            extracted_text = "Invalid file type"

    return render_template('index.html', extracted_text=extracted_text, analysis_results=results)

if __name__ == '__main__':
    app.run(debug=True)
