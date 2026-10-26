const notesEl = document.getElementById("notes");
const questionEl = document.getElementById("question");
const resultEl = document.getElementById("result");
const modeEl = document.getElementById("mode");
const actionButtons = [...document.querySelectorAll("[data-action]")];

function showText(text) {
  resultEl.textContent = text;
}

function showQuiz(quiz) {
  resultEl.replaceChildren();
  if (typeof quiz === "string") {
    resultEl.textContent = quiz;
    return;
  }
  quiz.forEach((item) => {
    const card = document.createElement("div");
    card.className = "quiz-question";
    const title = document.createElement("strong");
    title.textContent = item.question;
    card.appendChild(title);
    item.options.forEach((option) => {
      const line = document.createElement("div");
      line.textContent = "• " + option;
      card.appendChild(line);
    });
    const answer = document.createElement("div");
    answer.textContent = "Answer: " + item.answer;
    answer.style.marginTop = "8px";
    answer.style.fontWeight = "700";
    card.appendChild(answer);
    resultEl.appendChild(card);
  });
}

async function runAction(action, button) {
  const notes = notesEl.value.trim();
  if (!notes) {
    showText("Pehle notes ya topic enter karo.");
    notesEl.focus();
    return;
  }
  actionButtons.forEach((b) => b.disabled = true);
  button.textContent = "Working...";
  modeEl.textContent = "Processing";
  showText("Please wait...");

  try {
    const response = await fetch("/api/study", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        notes,
        question: questionEl.value.trim()
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Something went wrong.");
    modeEl.textContent = data.mode || "Done";
    if (action === "quiz" && data.quiz) showQuiz(data.quiz);
    else showText(data.result || "No result returned.");
  } catch (error) {
    modeEl.textContent = "Error";
    showText(error.message);
  } finally {
    actionButtons.forEach((b) => b.disabled = false);
    button.textContent = ({
      summary: "Summarize notes",
      quiz: "Generate quiz",
      ask: "Ask question"
    })[action];
  }
}

actionButtons.forEach((button) => {
  button.addEventListener("click", () => runAction(button.dataset.action, button));
});

document.getElementById("clear").addEventListener("click", () => {
  showText("Your summary, quiz, or answer will appear here.");
  modeEl.textContent = "Ready";
});

// Simple local demo chat
const chatUserEl = document.getElementById("chatUser");
const chatWithEl = document.getElementById("chatWith");
const chatMessageEl = document.getElementById("chatMessage");
const chatMessagesEl = document.getElementById("chatMessages");
async function refreshChat() {
  const user1 = chatUserEl.value.trim(), user2 = chatWithEl.value.trim();
  if (!user1 || !user2) { chatMessagesEl.textContent = "Please enter both names."; return; }
  try {
    const res = await fetch(`/api/chat?user1=${encodeURIComponent(user1)}&user2=${encodeURIComponent(user2)}`);
    const data = await res.json(); chatMessagesEl.replaceChildren();
    if (!data.messages.length) { chatMessagesEl.textContent = "No messages yet. Start the conversation!"; return; }
    data.messages.forEach(m => {
      const line = document.createElement("div"); line.className = "chat-line";
      const strong = document.createElement("strong"); strong.textContent = `${m.sender} → ${m.recipient}`;
      const body = document.createElement("div"); body.textContent = m.message;
      const time = document.createElement("small"); time.textContent = m.created_at;
      line.append(strong, body, time); chatMessagesEl.appendChild(line);
    });
    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
  } catch { chatMessagesEl.textContent = "Could not load messages. Check that the Flask app is running."; }
}
document.getElementById("refreshChat").addEventListener("click", refreshChat);
document.getElementById("sendChat").addEventListener("click", async () => {
  const sender = chatUserEl.value.trim(), recipient = chatWithEl.value.trim(), message = chatMessageEl.value.trim();
  if (!sender || !recipient || !message) { alert("Your name, other user's name aur message bharo."); return; }
  try {
    const res = await fetch("/api/chat", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({sender, recipient, message}) });
    const data = await res.json(); if (!res.ok) throw new Error(data.error || "Message send nahi hua.");
    chatMessageEl.value = ""; await refreshChat();
  } catch (e) { alert(e.message); }
});

// Resume preview: user's supplied details only; print dialog can save as PDF.
const resumeFields = ["resumeName", "resumeEmail", "resumePhone", "resumeLocation", "resumeEducation", "resumeSkills", "resumeProjects", "resumeObjective"];
const getVal = id => document.getElementById(id).value.trim();
function addResumeSection(parent, heading, text) {
  if (!text) return;
  const h = document.createElement("h3"); h.textContent = heading; parent.appendChild(h);
  const p = document.createElement("p"); p.textContent = text; parent.appendChild(p);
}
document.getElementById("makeResume").addEventListener("click", () => {
  if (!getVal("resumeName") || !getVal("resumeEducation") || !getVal("resumeSkills")) { alert("Full name, education aur skills zaroor bharo."); return; }
  const preview = document.getElementById("resumePreview"); preview.replaceChildren();
  const h = document.createElement("h2"); h.textContent = getVal("resumeName"); preview.appendChild(h);
  const contact = [getVal("resumeEmail"), getVal("resumePhone"), getVal("resumeLocation")].filter(Boolean).join(" | ");
  if (contact) { const p = document.createElement("p"); p.textContent = contact; preview.appendChild(p); }
  addResumeSection(preview, "CAREER OBJECTIVE", getVal("resumeObjective"));
  addResumeSection(preview, "EDUCATION", getVal("resumeEducation"));
  addResumeSection(preview, "TECHNICAL SKILLS", getVal("resumeSkills"));
  addResumeSection(preview, "PROJECTS", getVal("resumeProjects"));
  document.getElementById("printResume").disabled = false;
});
document.getElementById("printResume").addEventListener("click", () => window.print());
