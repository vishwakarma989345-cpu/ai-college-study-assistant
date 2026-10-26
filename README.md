# AI College Study Assistant (with Student Chat + Resume Builder)

Beginner-friendly Flask project featuring:
- Study notes summary, quiz and question-answer demo
- Student-to-student demo chat saved in a local SQLite database
- Resume builder based on the details the user enters, with Print / Save as PDF
- Optional OpenAI API integration for study features

## Requirements
- Python 3.10+
- VS Code (recommended)

## Run on Windows PowerShell
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000 in your browser.

## Resume to PDF
Fill the required fields, click Generate resume, then Print / Save as PDF. In the print dialog choose "Save as PDF".

## Chat notes
This is a local demonstration, not production-ready messaging. Messages are stored in `chat.db` on the computer running the app. It has no user accounts, authentication, or encryption. Do not use private or sensitive information. To let people chat across different devices, deploy the app online and add secure accounts and authentication first.

## Optional real AI
Set `OPENAI_API_KEY` in your environment before starting the app. Never share or commit API keys to GitHub. Without a key, study features use simple local demo logic.
