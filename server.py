"""Godavari Saarthi full-stack server (no installs): python server.py"""
import hashlib, hmac, json, mimetypes, os, re, secrets, socket, sqlite3, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")
ENV_DIR = os.path.join(BASE, "env")
for _f in ([os.path.join(ENV_DIR, n) for n in sorted(os.listdir(ENV_DIR))] if os.path.isdir(ENV_DIR) else []) + [os.path.join(BASE, ".env")]:
    if os.path.isfile(_f):
        for _l in open(_f, encoding="utf-8-sig", errors="ignore"):
            _m = re.match(r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$", _l)
            if _m and _m.group(2).strip("\"'"):
                os.environ.setdefault(_m.group(1), _m.group(2).strip("\"'"))
DB = os.path.join(BASE, "saarthi.db")
PORT = int(os.environ.get("PORT", "8000"))
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@saarthi.local").lower()
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
SECRET_FILE = os.path.join(BASE, ".secret")
if not os.path.exists(SECRET_FILE):
    open(SECRET_FILE, "w").write(secrets.token_hex(32))
SECRET = (os.environ.get("SECRET_KEY") or open(SECRET_FILE).read()).encode()
LAST, FAILS = {}, {}

def db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS kv(k TEXT PRIMARY KEY, v TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY, ts REAL, data TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, pw TEXT, role TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS journeys(uid INTEGER PRIMARY KEY, data TEXT)")
    return c

def sign(m):
    return hmac.new(SECRET, m.encode(), hashlib.sha256).hexdigest()

def hashpw(pw, salt=None):
    salt = salt or secrets.token_hex(8)
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 100000).hex()

def token(uid):
    m = "%d.%d" % (uid, time.time() + 7 * 86400)
    return m + "." + sign(m)

def user_of(auth):
    try:
        uid, exp, sig = auth.replace("Bearer ", "").split(".")
        if not hmac.compare_digest(sig, sign(uid + "." + exp)) or int(exp) < time.time():
            return None
        with db() as c:
            r = c.execute("SELECT id,name,email,role FROM users WHERE id=?", (int(uid),)).fetchone()
        return dict(zip(("id", "name", "email", "role"), r)) if r else None
    except Exception:
        return None

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

def ask_llm(prompt):
    """Groq if GROQ_API_KEY is set, else local Ollama, else None (app falls back to keyword answers)."""
    if GROQ_KEY:
        try:
            body = json.dumps({"model": GROQ_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2, "max_tokens": 200}).encode()
            req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", body, {"Content-Type": "application/json", "Authorization": "Bearer " + GROQ_KEY, "User-Agent": "godavari-saarthi/1.0"})
            return json.loads(urllib.request.urlopen(req, timeout=25).read())["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print("Groq error:", e)
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate", json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}).encode(), {"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=40).read())["response"].strip()
    except Exception:
        return None

class H(BaseHTTPRequestHandler):
    def reply(self, code, body, ctype="application/json"):
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        try:
            return json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except Exception:
            return {}

    def me(self):
        return user_of(self.headers.get("Authorization", ""))

    def need(self, admin=False):
        u = self.me()
        if not u or (admin and u["role"] != "admin"):
            self.reply(403 if u else 401, {"error": "Admin access only" if u else "Please sign in"})
            return None
        return u

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/state":
            with db() as c:
                r = dict(c.execute("SELECT k,v FROM kv").fetchall())
            return self.reply(200, {k: json.loads(r[k]) if k in r else None for k in ("anns", "facs")})
        if path == "/api/me":
            u = self.need()
            return u and self.reply(200, {"user": u})
        if path == "/api/journeys":
            u = self.need()
            if u:
                with db() as c:
                    r = c.execute("SELECT data FROM journeys WHERE uid=?", (u["id"],)).fetchone()
                self.reply(200, {"journeys": json.loads(r[0]) if r else []})
            return
        if path == "/api/admin/reports":
            if self.need(True):
                with db() as c:
                    rows = c.execute("SELECT ts,data FROM reports ORDER BY id DESC LIMIT 100").fetchall()
                self.reply(200, [dict(json.loads(d), ts=time.strftime("%d %b %H:%M", time.localtime(t))) for t, d in rows])
            return
        rel = path.lstrip("/") or "index.html"
        for root in (STATIC, BASE):
            f = os.path.realpath(os.path.join(root, rel))
            parts = os.path.relpath(f, BASE).split(os.sep)
            if f.startswith(root) and not any(x.startswith(".") or x == "env" for x in parts) and os.path.isfile(f) and not f.endswith((".py", ".db", ".secret")):
                return self.reply(200, open(f, "rb").read(), mimetypes.guess_type(f)[0] or "application/octet-stream")
        self.reply(404, ("Not found: %s. Looked in %s" % (path, STATIC)).encode(), "text/plain")

    def do_POST(self):
        path, d, ip = urlparse(self.path).path, self.body(), self.client_address[0]
        if path in ("/api/signup", "/api/signin"):
            FAILS[ip] = [t for t in FAILS.get(ip, []) if t > time.time() - 60]
            if len(FAILS[ip]) >= 8:
                return self.reply(429, {"error": "Too many attempts. Wait a minute."})
            email, pw = str(d.get("email", "")).strip().lower(), str(d.get("password", ""))
            if path == "/api/signup":
                name = str(d.get("name", "")).strip()[:60]
                if not name or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) or len(pw) < 6:
                    return self.reply(400, {"error": "Enter your name, a valid email and a password of 6+ characters"})
                try:
                    with db() as c:
                        cur = c.execute("INSERT INTO users(name,email,pw,role) VALUES(?,?,?,?)", (name, email, hashpw(pw), "admin" if email == ADMIN_EMAIL else "pilgrim"))
                        uid = cur.lastrowid
                except sqlite3.IntegrityError:
                    return self.reply(409, {"error": "This email is already registered. Please sign in."})
            else:
                with db() as c:
                    r = c.execute("SELECT id,pw FROM users WHERE email=?", (email,)).fetchone()
                if not r or not hmac.compare_digest(hashpw(pw, r[1].split("$")[0]), r[1]):
                    FAILS[ip].append(time.time())
                    return self.reply(401, {"error": "Wrong email or password"})
                uid = r[0]
            return self.reply(200, {"token": token(uid), "user": user_of("Bearer " + token(uid))})
        if path == "/api/report":
            if time.time() - LAST.get(ip, 0) < 5:
                return self.reply(429, {"error": "Too fast"})
            LAST[ip] = time.time()
            rec = {k: str(d.get(k, ""))[:300] for k in ("type", "ghat", "details", "phone")}
            with db() as c:
                c.execute("INSERT INTO reports(ts,data) VALUES(?,?)", (time.time(), json.dumps(rec)))
            return self.reply(200, {"ok": True})
        if path == "/api/ask":
            lang = {"te": "Telugu", "hi": "Hindi"}.get(d.get("lang"), "English")
            prompt = ("You are a help assistant for Godavari Pushkaralu pilgrims. Answer ONLY using the facts below. If the answer is not in the facts, say you have no verified information and suggest a help desk or calling 112. Max 60 words. Reply in %s.\nFACTS:\n%s\nQUESTION: %s" % (lang, str(d.get("context", ""))[:4000], str(d.get("q", ""))[:300]))
            ans = ask_llm(prompt)
            return self.reply(200, {"answer": ans})
        self.reply(404, {"error": "no such endpoint"})

    def do_PUT(self):
        path, d = urlparse(self.path).path, self.body()
        if path == "/api/admin/state" and self.need(True):
            with db() as c:
                for k in ("anns", "facs"):
                    if isinstance(d.get(k), list):
                        c.execute("REPLACE INTO kv VALUES(?,?)", (k, json.dumps(d[k])))
            return self.reply(200, {"ok": True})
        if path == "/api/journeys":
            u = self.need()
            if u and isinstance(d.get("journeys"), list):
                with db() as c:
                    c.execute("REPLACE INTO journeys VALUES(?,?)", (u["id"], json.dumps(d["journeys"][:50])))
                return self.reply(200, {"ok": True})

    def log_message(self, *a):
        pass

def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "your-ip"

if __name__ == "__main__":
    print("Groq AI:", "key loaded" if GROQ_KEY else "no key (keyword answers / Ollama only)")
    print("Godavari Saarthi running.\n  This device: http://localhost:%d\n  Other devices on Wi-Fi: http://%s:%d\n  Admin account: sign up with email %s" % (PORT, lan_ip(), PORT, ADMIN_EMAIL))
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
