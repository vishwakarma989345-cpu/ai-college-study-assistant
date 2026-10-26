import os
import re
from collections import Counter

from flask import Flask, render_template, request, jsonify
import sqlite3
from pathlib import Path

app = Flask(__name__)
DB_PATH = Path(__file__).with_name("chat.db")

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT NOT NULL, recipient TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")

init_db()

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
def home():
    return render_template("index.html")

@app.route("/api/study", methods=["POST"])
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
