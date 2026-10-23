import os, json, sqlite3
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, g
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-development-key")
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024
DB_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "study_buddy.db"))

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS documents (
      id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL,
      subject TEXT DEFAULT 'General', content TEXT DEFAULT '', created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS quiz_results (
      id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT NOT NULL,
      topic TEXT NOT NULL, score INTEGER NOT NULL, total INTEGER NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS study_tasks (
      id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
      subject TEXT DEFAULT 'General', due_date TEXT, done INTEGER DEFAULT 0
    );
    """)
    count = conn.execute("SELECT COUNT(*) FROM study_tasks").fetchone()[0]
    if count == 0:
        conn.executemany("INSERT INTO study_tasks(title,subject,due_date,done) VALUES(?,?,?,?)", [
            ("Revise RSA algorithm", "Cyber Security", date.today().isoformat(), 0),
            ("Practice 10 AI questions", "Artificial Intelligence", date.today().isoformat(), 0),
            ("Review OS process scheduling", "Operating Systems", date.today().isoformat(), 1),
        ])
    conn.commit()
    conn.close()

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stats")
def stats():
    conn = db()
    docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    results = conn.execute("SELECT score,total FROM quiz_results").fetchall()
    avg = round(sum((r["score"] / r["total"] * 100) for r in results) / len(results)) if results else 72
    tasks = conn.execute("SELECT COUNT(*) FROM study_tasks WHERE done=0").fetchone()[0]
    return jsonify({"documents": docs, "average": avg, "tasks": tasks, "streak": 4})

@app.route("/api/documents", methods=["GET", "POST"])
def documents():
    conn = db()
    if request.method == "GET":
        rows = conn.execute("SELECT id,filename,subject,created_at FROM documents ORDER BY id DESC").fetchall()
        return jsonify([dict(r) for r in rows])
    data = request.get_json(force=True)
    cur = conn.execute("INSERT INTO documents(filename,subject,content,created_at) VALUES(?,?,?,?)",
        (data.get("filename","Study notes.txt"), data.get("subject","General"), data.get("content",""), datetime.now().isoformat(timespec="minutes")))
    conn.commit()
    return jsonify({"id": cur.lastrowid, "ok": True})

@app.route("/api/tasks", methods=["GET", "POST"])
def tasks():
    conn = db()
    if request.method == "GET":
        rows = conn.execute("SELECT * FROM study_tasks ORDER BY done,due_date,id").fetchall()
        return jsonify([dict(r) for r in rows])
    data = request.get_json(force=True)
    cur = conn.execute("INSERT INTO study_tasks(title,subject,due_date,done) VALUES(?,?,?,0)",
        (data.get("title","Study session"), data.get("subject","General"), data.get("due_date","")))
    conn.commit()
    return jsonify({"id":cur.lastrowid,"ok":True})

@app.route("/api/tasks/<int:task_id>", methods=["PATCH", "DELETE"])
def task_detail(task_id):
    conn = db()
    if request.method == "DELETE":
        conn.execute("DELETE FROM study_tasks WHERE id=?", (task_id,))
        conn.commit()
        return jsonify({"ok":True})
    data = request.get_json(force=True)
    conn.execute("UPDATE study_tasks SET done=? WHERE id=?", (1 if data.get("done") else 0, task_id))
    conn.commit()
    return jsonify({"ok":True})

@app.route("/api/quiz-results", methods=["GET", "POST"])
def quiz_results():
    conn = db()
    if request.method == "GET":
        return jsonify([dict(r) for r in conn.execute("SELECT * FROM quiz_results ORDER BY id DESC LIMIT 12").fetchall()])
    data = request.get_json(force=True)
    conn.execute("INSERT INTO quiz_results(subject,topic,score,total,created_at) VALUES(?,?,?,?,?)",
      (data.get("subject","General"),data.get("topic","Mixed practice"),int(data.get("score",0)),int(data.get("total",1)),datetime.now().isoformat(timespec="minutes")))
    conn.commit()
    return jsonify({"ok":True})

@app.route("/api/ai", methods=["POST"])
def ai():
    data = request.get_json(force=True)
    prompt = (data.get("prompt") or "").strip()
    context = (data.get("context") or "").strip()
    language = data.get("language","Simple English")
    if not prompt:
        return jsonify({"error":"Please enter a question first."}), 400
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            instructions = f"""You are AI Study Buddy, a careful tutor for college students.
Answer in {language}. Explain clearly with headings and examples.
Use the student's provided notes when relevant. If the notes do not contain the answer, say so and clearly distinguish general knowledge from the notes. Never invent page references.
Keep the answer useful for exam revision.
Student notes:
{context[:18000] if context else '(No notes supplied)'}
Question: {prompt}"""
            response = client.models.generate_content(model=model, contents=instructions)
            return jsonify({"answer": response.text or "I couldn't generate an answer. Please try again."})
        except Exception as e:
            app.logger.exception("Gemini request failed")
            return jsonify({"error":"AI request failed. Check your API key, model access, and internet connection. You can still explore demo mode."}), 502
    return jsonify({"answer": demo_answer(prompt, context, language), "demo": True})

def demo_answer(prompt, context, language):
    q = prompt.lower()
    if "rsa" in q:
        answer = """## RSA algorithm (demo explanation)

RSA is an asymmetric cryptographic algorithm. It uses a **public key** to encrypt or verify, and a **private key** to decrypt or sign.

**Basic steps**
1. Choose two prime numbers, p and q.
2. Calculate n = p × q and φ(n) = (p−1)(q−1).
3. Choose public exponent e that is coprime with φ(n).
4. Find private exponent d, where (e × d) mod φ(n) = 1.
5. Public key is (e, n); private key is (d, n).

**Remember:** Real RSA uses very large primes and secure padding. Tiny classroom examples are only for understanding."""
    elif "digital signature" in q:
        answer = """## Digital signature

A digital signature helps verify **authenticity**, **integrity**, and **non-repudiation**.

1. The sender hashes the message.
2. The sender signs the hash using their private key.
3. The receiver verifies the signature using the sender's public key.
4. The receiver also hashes the received message and compares the results.

If the message changes, the hash comparison should fail. A digital signature does not automatically encrypt the message."""
    elif "mcq" in q or "quiz" in q or "question" in q:
        answer = """## Practice questions

**1. Which key is kept secret in asymmetric cryptography?**
- A. Public key
- B. Private key
- C. Session label
- D. Hash output

**Correct answer:** B — the private key must remain secret.

**2. What does a cryptographic hash primarily provide?**
- A. Data integrity checking
- B. Faster internet
- C. Screen encryption
- D. User authentication by itself

**Correct answer:** A — a hash can help detect changes to data."""
    elif "summary" in q or "notes" in q:
        source = context.strip() or "No document text has been uploaded in this demo yet."
        answer = "## Quick study summary\n\n" + source[:1800] + ("\n\n*Demo mode: add a Gemini API key for AI-generated summaries of your own notes.*" if not context else "")
    else:
        answer = f"""## Let's understand this

**Your question:** {prompt}

Start by identifying the key definition, then learn the steps or components, and finish with one example. For exam preparation, write:
1. Definition
2. Main points or working
3. A small example or diagram
4. One-line conclusion

*This is a local demo response, not a live AI answer. Add your Gemini API key in the `.env` file to enable Gemini-powered explanations.*"""
    if "marathi" in language.lower() or "hindi" in language.lower():
        answer += "\n\n**Language note:** Demo mode may respond mainly in English. Configure a Gemini API key for more reliable Marathi/Hindi or mixed-language explanations."
    return answer

@app.route("/api/upload-text", methods=["POST"])
def upload_text():
    data = request.get_json(force=True)
    filename = data.get("filename","Pasted notes.txt")
    content = data.get("content","")
    subject = data.get("subject","General")
    if not content.strip():
        return jsonify({"error":"No readable text was found. Paste text, or use a text-based PDF."}), 400
    conn = db()
    cur = conn.execute("INSERT INTO documents(filename,subject,content,created_at) VALUES(?,?,?,?)",
        (filename,subject,content,datetime.now().isoformat(timespec="minutes")))
    conn.commit()
    return jsonify({"id":cur.lastrowid,"filename":filename,"subject":subject,"content":content,"ok":True})

@app.route("/api/document/<int:doc_id>", methods=["GET", "DELETE"])
def document_detail(doc_id):
    conn = db()
    row = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
    if request.method == "DELETE":
        if not row:
            return jsonify({"error":"Document not found"}), 404
        conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
        conn.commit()
        return jsonify({"ok": True})
    if not row:
        return jsonify({"error":"Document not found"}), 404
    return jsonify(dict(row))

# Initialize tables when the module is imported by a production server (e.g. Gunicorn).
# This also keeps `python app.py` working for local development.
init_db()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
            host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
