
import os
import re
import sqlite3
from collections import Counter
from pathlib import Path
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for, render_template_string
)
from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, render_template, request, jsonify
import sqlite3
from pathlib import Path


app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "local-testing-only-change-before-deployment"
)
DB_PATH = Path(__file__).with_name("chat.db")

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)

init_db()
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("username"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Please login first."}), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or len(password) < 8:
            error = "Username, email bharo. Password 8+ characters ka ho."
        else:
            try:
                with sqlite3.connect(DB_PATH) as con:
                    con.execute(
                        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                        (username, email, generate_password_hash(password))
                    )
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                error = "Username ya email pehle se registered hai."

   
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Register | AI Study Assistant</title>

        <style>
            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                min-height: 100vh;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #101a3a, #4338ca, #06b6d4);
            }

            .register-card {
                width: 100%;
                max-width: 410px;
                padding: 35px;
                background: white;
                border-radius: 22px;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
            }

            .logo {
                width: 65px;
                height: 65px;
                margin: 0 auto 18px;
                border-radius: 18px;
                background: #eef2ff;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 30px;
            }

            h1 {
                text-align: center;
                color: #172033;
                font-size: 26px;
                margin-bottom: 8px;
            }

            .subtitle {
                text-align: center;
                color: #6b7280;
                font-size: 14px;
                margin-bottom: 25px;
            }

            label {
                display: block;
                margin: 17px 0 8px;
                color: #374151;
                font-size: 14px;
                font-weight: bold;
            }

            input {
                width: 100%;
                padding: 13px 14px;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                font-size: 15px;
                outline: none;
            }

            input:focus {
                border-color: #4f46e5;
                box-shadow: 0 0 0 3px #e0e7ff;
            }

            button {
                width: 100%;
                margin-top: 24px;
                padding: 14px;
                border: none;
                border-radius: 10px;
                background: #4338ca;
                color: white;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: background 0.2s, transform 0.2s;
            }

            button:hover {
                background: #3730a3;
                transform: translateY(-2px);
            }

            .error {
                color: #dc2626;
                text-align: center;
                font-size: 14px;
            }

            .signup {
                margin-top: 22px;
                text-align: center;
                color: #6b7280;
                font-size: 14px;
            }

            a {
                color: #4338ca;
                font-weight: bold;
                text-decoration: none;
            }

            a:hover {
                text-decoration: underline;
            }

            @media (max-width: 480px) {
                .register-card {
                    padding: 25px 20px;
                }
            }
        </style>
    </head>

    <body>
        <div class="register-card">
            <div class="logo">🎓</div>

            <h1>Create Account</h1>
            <p class="subtitle">Join your AI College Study Assistant</p>

            {% if error %}
                <p class="error">{{ error }}</p>
            {% endif %}

            <form method="post">
                <label for="username">Username</label>
                <input id="username" name="username"
                       placeholder="Enter your username"
                       maxlength="60" required>

                <label for="email">Email Address</label>
                <input id="email" name="email" type="email"
                       placeholder="Enter your email" required>

                <label for="password">Password</label>
                <input id="password" name="password" type="password"
                       placeholder="At least 8 characters"
                       minlength="8" required>

                <button type="submit">Create Account</button>
            </form>

            <p class="signup">
                Already registered?
                <a href="{{ url_for('login') }}">Login</a>
            </p>
        </div>
    </body>
    </html>
    

    """, error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with sqlite3.connect(DB_PATH) as con:
            con.row_factory = sqlite3.Row
            user = con.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["username"] = user["username"]
            return redirect(url_for("home"))

        error = "Email ya password galat hai."

    return render_template_string("""
    
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login | AI Study Assistant</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #101a3a, #4338ca, #06b6d4);
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .login-card {
            background: white;
            width: 100%;
            max-width: 410px;
            padding: 35px;
            border-radius: 22px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.25);
        }

        .logo {
            width: 65px;
            height: 65px;
            margin: 0 auto 18px;
            border-radius: 18px;
            background: #eef2ff;
            color: #4338ca;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 30px;
        }

        h1 {
            text-align: center;
            color: #172033;
            font-size: 25px;
            margin-bottom: 8px;
        }

        .subtitle {
            text-align: center;
            color: #6b7280;
            font-size: 14px;
            margin-bottom: 28px;
        }

        label {
            display: block;
            margin: 17px 0 8px;
            color: #374151;
            font-size: 14px;
            font-weight: bold;
        }

        input {
            width: 100%;
            padding: 13px 14px;
            border: 1px solid #d1d5db;
            border-radius: 10px;
            font-size: 15px;
            outline: none;
        }

        input:focus {
            border-color: #4f46e5;
            box-shadow: 0 0 0 3px #e0e7ff;
        }

        button {
            width: 100%;
            margin-top: 24px;
            padding: 14px;
            border: none;
            border-radius: 10px;
            background: #4338ca;
            color: white;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
        }

        button:hover {
            background: #3730a3;
        }

        .error {
            color: #dc2626;
            text-align: center;
            font-size: 14px;
        }

        .signup {
            margin-top: 22px;
            text-align: center;
            color: #6b7280;
            font-size: 14px;
        }

        a {
            color: #4338ca;
            font-weight: bold;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }
    </style>
</head>

<body>
    <div class="login-card">
        <div class="logo">🎓</div>

        <h1>Welcome Back!</h1>
        <p class="subtitle">Login to your AI Study Assistant</p>

        <p class="error">{{ error }}</p>

        <form method="post">
            <label for="email">Email Address</label>
            <input id="email" name="email" type="email"
                   placeholder="Enter your email" required>

            <label for="password">Password</label>
            <input id="password" name="password" type="password"
                   placeholder="Enter your password" required>

            <button type="submit">Login to Account</button>
        </form>

        <p class="signup">
            New student?
            <a href="/register">Create an account</a>
        </p>
    </div>
</body>
</html>

    """, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# Optional: real AI mode works when OPENAI_API_KEY is set in your environment.
# Without a key, the project still runs in local demo mode.
def ask_real_ai(prompt):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=prompt
        )
        return response.output_text
    except Exception as exc:
        # Keep the app usable if the API is not configured correctly.
        return f"AI connection error: {exc}. Check your API key/model and try again."

def split_sentences(text):
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]

def local_summary(notes):
    sentences = split_sentences(notes)
    if not sentences:
        return "Please enter some notes first."
    if len(sentences) <= 3:
        return "\n".join("• " + s for s in sentences)
    # Simple beginner-friendly fallback: choose the longest informative sentences.
    selected = sorted(enumerate(sentences), key=lambda x: len(x[1]), reverse=True)[:4]
    selected = sorted(selected, key=lambda x: x[0])
    return "\n".join("• " + sentence for _, sentence in selected)

def local_quiz(notes):
    words = re.findall(r'\b[A-Za-z][A-Za-z-]{4,}\b', notes)
    stopwords = {
        "which", "there", "their", "about", "these", "those", "where", "while",
        "because", "through", "between", "system", "students", "student",
        "using", "used", "also", "often", "every", "first", "other", "should",
        "would", "could", "these", "those", "being", "after", "before"
    }
    counts = Counter(w.lower() for w in words if w.lower() not in stopwords)
    keywords = [w for w, _ in counts.most_common(8)]
    if len(keywords) < 2:
        return "Add a little more text (at least a few sentences) to generate a quiz."
    questions = []
    for i, answer in enumerate(keywords[:3], start=1):
        distractors = [w for w in keywords if w != answer][:3]
        options = [answer] + distractors
        # Deterministic shuffle so the correct answer isn't always first.
        if len(options) > 1:
            options = options[1:] + options[:1]
        questions.append({
            "question": f"{i}. Which term appears in your notes?",
            "options": options,
            "answer": answer
        })
    return questions

def local_answer(notes, question):
    if not notes.strip():
        return "Please paste your notes first so I can answer from them."
    q_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', question.lower()))
    sentences = split_sentences(notes)
    ranked = []
    for sentence in sentences:
        s_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', sentence.lower()))
        score = len(q_words & s_words)
        if score:
            ranked.append((score, sentence))
    if not ranked:
        return "I couldn't find a direct match in these notes. Try asking with keywords used in your notes."
    ranked.sort(key=lambda item: item[0], reverse=True)
    return "Based on your notes:\n" + "\n".join("• " + s for _, s in ranked[:3])

@app.route("/api/chat", methods=["GET", "POST"])
@login_required
def chat():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        sender = (data.get("sender") or "").strip()[:60]
        recipient = (data.get("recipient") or "").strip()[:60]
        message = (data.get("message") or "").strip()[:1000]
        if not sender or not recipient or not message:
            return jsonify({"error": "Sender, recipient aur message tino bharo."}), 400
        if sender.lower() == recipient.lower():
            return jsonify({"error": "Apne aap ko message nahi bhej sakte."}), 400
        with sqlite3.connect(DB_PATH) as con:
            con.execute("INSERT INTO messages (sender, recipient, message) VALUES (?, ?, ?)", (sender, recipient, message))
        return jsonify({"ok": True})
    user1 = (request.args.get("user1") or "").strip()[:60]
    user2 = (request.args.get("user2") or "").strip()[:60]
    if not user1 or not user2:
        return jsonify({"messages": []})
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT sender, recipient, message, created_at FROM messages WHERE (sender=? AND recipient=?) OR (sender=? AND recipient=?) ORDER BY id ASC LIMIT 200", (user1, user2, user2, user1)).fetchall()
    return jsonify({"messages": [dict(row) for row in rows]})




@app.route("/")
@login_required
def home():
    return render_template("index.html")


@app.route("/api/study", methods=["POST"])
@login_required
def study():
    data = request.get_json(silent=True) or {}
    action = data.get("action", "")
    notes = (data.get("notes") or "").strip()
    question = (data.get("question") or "").strip()

    if not notes:
        return jsonify({"error": "Pehle apne notes ya topic enter karo."}), 400

    if action == "summary":
        prompt = "Summarize these college study notes in simple English, using 4-6 clear bullet points. Do not add facts not present in the notes:\n\n" + notes
        ai_result = ask_real_ai(prompt)
        result = ai_result if ai_result is not None else local_summary(notes)
        mode = "AI mode" if ai_result is not None else "Local demo mode"
        return jsonify({"result": result, "mode": mode})

    if action == "quiz":
        prompt = "Create 5 multiple-choice questions from these notes. For each question include 4 options and clearly mark the correct answer. Keep it suitable for a first-year college student:\n\n" + notes
        ai_result = ask_real_ai(prompt)
        if ai_result is not None:
            return jsonify({"result": ai_result, "mode": "AI mode"})
        return jsonify({"quiz": local_quiz(notes), "mode": "Local demo mode"})

    if action == "ask":
        if not question:
            return jsonify({"error": "Apna question bhi likho."}), 400
        prompt = "Answer the student's question in beginner-friendly simple English. Use the notes as the main source and say if the notes do not contain the answer.\n\nNOTES:\n" + notes + "\n\nQUESTION:\n" + question
        ai_result = ask_real_ai(prompt)
        result = ai_result if ai_result is not None else local_answer(notes, question)
        mode = "AI mode" if ai_result is not None else "Local demo mode"
        return jsonify({"result": result, "mode": mode})

    return jsonify({"error": "Unknown action."}), 400

if __name__ == "__main__":
    app.run(debug=True)
