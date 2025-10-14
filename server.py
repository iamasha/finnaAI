import http.server, json, sqlite3, smtplib, uuid, random
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from email.message import EmailMessage

DB_FILE = "users.db"
OTP_EXPIRY_MINUTES = 5

# --- SMTP EMAIL ---
def send_email(to_email, subject, body):
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "hwakaasha@gmail.com"
    SMTP_PASS = 'your_app_password'

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

# --- DB setup ---
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    phone TEXT,
    password TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS otp_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    code TEXT,
    expires_at TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER
)
""")
conn.commit()
conn.close()

# --- Request Handler ---
class RequestHandler(http.server.SimpleHTTPRequestHandler):

    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw)
        except:
            return self._send_json(400, {"detail":"Invalid JSON"})

        # --- REGISTER ---
        if self.path == "/register":
            name, email, phone, password = data.get("name",""), data.get("email",""), data.get("phone",""), data.get("password","")
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (name,email,phone,password) VALUES (?,?,?,?)",
                               (name,email,phone,password))
                conn.commit()
                conn.close()
                return self._send_json(200, {"status":"success"})
            except sqlite3.IntegrityError:
                return self._send_json(400, {"detail":"Email already registered"})

        # --- LOGIN (Generate OTP) ---
        elif self.path == "/login":
            email, password = data.get("email"), data.get("password")
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM users WHERE email=? AND password=?", (email,password))
            row = cursor.fetchone()
            conn.close()
            if not row:
                return self._send_json(401, {"detail":"Invalid credentials"})

            user_id, name = row
            otp_code = f"{random.randint(100000,999999)}"
            expires_at = (datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM otp_codes WHERE user_id=?", (user_id,))
            cursor.execute("INSERT INTO otp_codes (user_id, code, expires_at) VALUES (?,?,?)",
                           (user_id, otp_code, expires_at))
            conn.commit()
            conn.close()

            try:
                send_email(email, "Your OTP Code", f"Hello {name}, your OTP is: {otp_code}")
            except Exception as e:
                print("Email send failed:", e)

            return self._send_json(200, {"user_id":user_id})

        # --- VERIFY OTP ---
        # elif self.path == "/verify-otp":
        #     user_id, otp = data.get("user_id"), data.get("otp")
        #     if not user_id or not otp:
        #         return self._send_json(400, {"detail":"user_id and otp required"})

        #     conn = sqlite3.connect(DB_FILE)
        #     cursor = conn.cursor()
        #     cursor.execute("SELECT code, expires_at FROM otp_codes WHERE user_id=?", (user_id,))
        #     row = cursor.fetchone()
        #     conn.close()
        #     if not row:
        #         return self._send_json(400, {"detail":"OTP not found"})

        #     saved_otp, expires_at = row
        #     if datetime.now() > datetime.fromisoformat(expires_at):
        #         return self._send_json(400, {"detail":"OTP expired"})
        #     if otp != saved_otp:
        #         return self._send_json(400, {"detail":"Incorrect OTP"})

        #     # OTP valid → create session
        #     session_id = str(uuid.uuid4())
        #     conn = sqlite3.connect(DB_FILE)
        #     cursor = conn.cursor()
        #     cursor.execute("INSERT INTO sessions (session_id,user_id) VALUES (?,?)", (session_id,user_id))
        #     cursor.execute("DELETE FROM otp_codes WHERE user_id=?", (user_id,))
        #     conn.commit()
        #     conn.close()
        #     return self._send_json(200, {"status":"success", "session_id":session_id})

        # --- LOGOUT ---
        elif self.path == "/logout":
            session_id = data.get("session_id")
            if session_id:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
                conn.commit()
                conn.close()
                return self._send_json(200, {"status":"logged out"})
            return self._send_json(400, {"detail":"Session ID required"})

        else:
            return self._send_json(404, {"detail":"Not found"})

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path == "/user":
            user_id = qs.get("user_id",[None])[0]
            if user_id:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT name,email FROM users WHERE id=?", (user_id,))
                row = cursor.fetchone()
                conn.close()
                if row:
                    name,email = row
                    return self._send_json(200, {"name":name,"email":email})
            return self._send_json(404, {"detail":"User not found"})

        # Serve static files
        if self.path in ["/","/login.html","/register.html","/dashboard.html"]:
            self.path = self.path if self.path != "/" else "/login.html"
        return http.server.SimpleHTTPRequestHandler.do_GET(self)


if __name__ == "__main__":
    PORT = 8000
    print(f"Server running on port {PORT}...")
    http.server.HTTPServer(("", PORT), RequestHandler).serve_forever()
