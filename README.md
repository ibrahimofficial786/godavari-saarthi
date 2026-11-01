# GODAVARI SAARTHI (PS-04) - full stack
Run: python server.py (Windows: run.bat, Termux: sh run.sh). Open http://localhost:8000
Stack: vanilla JS PWA front end, Python standard-library HTTP server, SQLite (saarthi.db).
Accounts: sign up in the app. The account whose email equals ADMIN_EMAIL (default admin@saarthi.local) becomes administrator. Set ADMIN_EMAIL to your own email before first run.
Passwords are salted PBKDF2 hashes. Saved journeys sync to the signed-in account. Guests can use everything except sync and admin.
Optional AI assistant: install Ollama, `ollama pull llama3.2`.
Before deployment: official data, HTTPS, your own ADMIN_EMAIL.

Groq AI assistant (optional): get a free key at console.groq.com, then set GROQ_API_KEY before running (Windows: set GROQ_API_KEY=gsk_...  Termux: export GROQ_API_KEY=gsk_...). Change model with GROQ_MODEL if needed. Without a key it uses Ollama, then keyword answers.

## API keys
Open the env folder, edit the file named .env, paste your key after GROQ_API_KEY= and save. Restart the server. The console prints "Groq AI: key loaded". Never share the env folder or upload it to GitHub.
