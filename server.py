# from flask import Flask, request, jsonify, send_from_directory
# import os
# import sqlite3
# import smtplib
# import uuid
# import random
# from datetime import datetime, timedelta
# from email.message import EmailMessage

# DB_FILE = "users.db"
# OTP_EXPIRY_MINUTES = 5

# app = Flask(__name__, static_folder='.', static_url_path='')


# def send_email(to_email, subject, body):
#     SMTP_HOST = "smtp.gmail.com"
#     SMTP_PORT = 587
#     SMTP_USER = os.environ.get("SMTP_USER", "hwakaasha@gmail.com")
#     SMTP_PASS = os.environ.get("SMTP_PASS", "your_app_password")

#     msg = EmailMessage()
#     msg.set_content(body)
#     msg["Subject"] = subject
#     msg["From"] = SMTP_USER
#     msg["To"] = to_email

#     with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
#         server.starttls()
#         server.login(SMTP_USER, SMTP_PASS)
#         server.send_message(msg)


# def init_db():
#     conn = sqlite3.connect(DB_FILE)
#     cursor = conn.cursor()
#     cursor.execute("""
#     CREATE TABLE IF NOT EXISTS users (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         name TEXT,
#         email TEXT UNIQUE,
#         phone TEXT,
#         password TEXT
#     )
#     """)
#     cursor.execute("""
#     CREATE TABLE IF NOT EXISTS otp_codes (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         user_id INTEGER,
#         code TEXT,
#         expires_at TEXT
#     )
#     """)
#     cursor.execute("""
#     CREATE TABLE IF NOT EXISTS sessions (
#         session_id TEXT PRIMARY KEY,
#         user_id INTEGER
#     )
#     """)
#     conn.commit()
#     conn.close()


# def get_db_connection():
#     conn = sqlite3.connect(DB_FILE)
#     return conn


# @app.route('/register', methods=['POST'])
# def register():
#     data = request.get_json(silent=True)
#     if not data:
#         return jsonify({'detail': 'Invalid JSON'}), 400

#     name = data.get('name', '')
#     email = data.get('email', '')
#     phone = data.get('phone', '')
#     password = data.get('password', '')

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("INSERT INTO users (name,email,phone,password) VALUES (?,?,?,?)",
#                        (name, email, phone, password))
#         conn.commit()
#         conn.close()
#         return jsonify({'status': 'success'})
#     except sqlite3.IntegrityError:
#         return jsonify({'detail': 'Email already registered'}), 400


# @app.route('/login', methods=['POST'])
# def login():
#     data = request.get_json(silent=True)
#     if not data:
#         return jsonify({'detail': 'Invalid JSON'}), 400
#     email = data.get('email')
#     password = data.get('password')
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT id, name FROM users WHERE email=? AND password=?", (email, password))
#     row = cursor.fetchone()
#     conn.close()
#     if not row:
#         return jsonify({'detail': 'Invalid credentials'}), 401

#     user_id, name = row
#     otp_code = f"{random.randint(100000,999999)}"
#     expires_at = (datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()

#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("DELETE FROM otp_codes WHERE user_id=?", (user_id,))
#     cursor.execute("INSERT INTO otp_codes (user_id, code, expires_at) VALUES (?,?,?)",
#                    (user_id, otp_code, expires_at))
#     conn.commit()
#     conn.close()

#     try:
#         send_email(email, "Your OTP Code", f"Hello {name}, your OTP is: {otp_code}")
#     except Exception as e:
#         app.logger.warning("Email send failed: %s", e)

#     return jsonify({'user_id': user_id})


# @app.route('/verify-otp', methods=['POST'])
# def verify_otp():
#     data = request.get_json(silent=True)
#     if not data:
#         return jsonify({'detail': 'Invalid JSON'}), 400
#     user_id = data.get('user_id')
#     otp = data.get('otp')
#     if not user_id or not otp:
#         return jsonify({'detail': 'user_id and otp required'}), 400

#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT code, expires_at FROM otp_codes WHERE user_id=?", (user_id,))
#     row = cursor.fetchone()
#     if not row:
#         conn.close()
#         return jsonify({'detail': 'OTP not found'}), 400

#     saved_otp, expires_at = row
#     try:
#         if datetime.now() > datetime.fromisoformat(expires_at):
#             conn.close()
#             return jsonify({'detail': 'OTP expired'}), 400
#     except Exception:
#         pass

#     if otp != saved_otp:
#         conn.close()
#         return jsonify({'detail': 'Incorrect OTP'}), 400

#     session_id = str(uuid.uuid4())
#     cursor.execute("INSERT INTO sessions (session_id,user_id) VALUES (?,?)", (session_id, user_id))
#     cursor.execute("DELETE FROM otp_codes WHERE user_id=?", (user_id,))
#     conn.commit()
#     conn.close()
#     return jsonify({'status': 'success', 'session_id': session_id})


# @app.route('/logout', methods=['POST'])
# def logout():
#     data = request.get_json(silent=True)
#     if not data:
#         return jsonify({'detail': 'Invalid JSON'}), 400
#     session_id = data.get('session_id')
#     if session_id:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
#         conn.commit()
#         conn.close()
#         return jsonify({'status': 'logged out'})
#     return jsonify({'detail': 'Session ID required'}), 400


# def load_dashboard_data():
#     sample_data = []
#     try:
#         import csv
#         with open('dummy.csv', 'r', encoding='utf-8') as f:
#             reader = csv.DictReader(f)
#             for row in reader:
#                 raw_date = row.get('date', '')
#                 try:
#                     dt = datetime.strptime(raw_date, '%m/%d/%Y')
#                     formatted_date = dt.strftime('%d/%m/%Y')
#                 except ValueError:
#                     formatted_date = raw_date

#                 savings = float(row.get('savings_balance', 0) or 0)
#                 loans = float(row.get('repayment_amount', 0) or 0) + float(row.get('next_loan_due_amount', 0) or 0)
#                 balance = float(row.get('account_balance', 0) or 0)

#                 financial_score = 100
#                 insight = 'Great financial health.'
#                 label = 'healthy'

#                 if savings == 0:
#                     financial_score -= 20
#                     insight = 'No active savings detected. Consider creating a savings plan.'
#                     label = 'neutral'

#                 if loans > (savings + balance) * 0.5:
#                     financial_score -= 40
#                     insight = 'High debt-to-assets ratio. Focus on clearing active loans.'
#                     label = 'at_risk'

#                 if row.get('repayment_status') == 'missed':
#                     financial_score -= 30
#                     insight = 'Missed loan repayment detected. Immediate action required!'
#                     label = 'at_risk'

#                 if financial_score < 0:
#                     financial_score = 0

#                 sample_data.append({
#                     'id': row.get('customer_id', ''),
#                     'Name': f"{row.get('first_name','')} {row.get('last_name','')}",
#                     'Email': f"{row.get('first_name','').lower()}@example.com",
#                     'financial_score': financial_score,
#                     'Savings': savings,
#                     'Loans': loans,
#                     'Balance': balance,
#                     'label': label,
#                     'insight': insight,
#                     'Consent': row.get('marketing_consent', 'N'),
#                     'Date': formatted_date
#                 })
#     except Exception as e:
#         app.logger.warning('Error loading CSV: %s', e)
#         sample_data = []
#     return sample_data


# @app.route('/dashboard_data.json', methods=['GET'])
# def dashboard_data():
#     return jsonify(load_dashboard_data())


# @app.route('/user', methods=['GET'])
# def get_user():
#     user_id = request.args.get('user_id')
#     if user_id:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("SELECT name,email FROM users WHERE id=?", (user_id,))
#         row = cursor.fetchone()
#         conn.close()
#         if row:
#             name, email = row
#             return jsonify({'name': name, 'email': email})
#     return jsonify({'detail': 'User not found'}), 404


# @app.route('/')
# def root():
#     return send_from_directory('.', 'login.html')


# @app.route('/<path:filename>')
# def static_files(filename):
#     # Serve root-level HTML files (login.html, register.html, dashboard.html) and assets
#     return send_from_directory('.', filename)


# if __name__ == '__main__':
#     init_db()
#     PORT = int(os.environ.get('PORT', 8000))
#     app.run(host='0.0.0.0', port=PORT)


from flask import Flask, request, jsonify, send_from_directory
import os
import sqlite3
import smtplib
import uuid
import random
import csv
from datetime import datetime, timedelta
from email.message import EmailMessage

# Setup absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "users.db")
CSV_FILE = os.path.join(BASE_DIR, "dummy.csv")

OTP_EXPIRY_MINUTES = 5

app = Flask(__name__, static_folder='.', static_url_path='')

# --- HELPER FUNCTIONS ---
def send_email(to_email, subject, body):
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = os.environ.get("SMTP_USER", "hwakaasha@gmail.com")
    SMTP_PASS = os.environ.get("SMTP_PASS", "your_app_password")

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, phone TEXT, password TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS otp_codes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, code TEXT, expires_at TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, user_id INTEGER)")
    conn.commit()
    conn.close()

# Initialize DB on load
init_db()

def get_db_connection():
    return sqlite3.connect(DB_FILE)

# --- ROUTES ---
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)
    if not data: return jsonify({'detail': 'Invalid JSON'}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name,email,phone,password) VALUES (?,?,?,?)",
                       (data.get('name'), data.get('email'), data.get('phone'), data.get('password')))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    except sqlite3.IntegrityError:
        return jsonify({'detail': 'Email already registered'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not data: return jsonify({'detail': 'Invalid JSON'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM users WHERE email=? AND password=?", (data.get('email'), data.get('password')))
    row = cursor.fetchone()
    conn.close()
    if not row: return jsonify({'detail': 'Invalid credentials'}), 401

    user_id, name = row
    otp_code = f"{random.randint(100000,999999)}"
    expires_at = (datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM otp_codes WHERE user_id=?", (user_id,))
    cursor.execute("INSERT INTO otp_codes (user_id, code, expires_at) VALUES (?,?,?)", (user_id, otp_code, expires_at))
    conn.commit()
    conn.close()

    try:
        send_email(data.get('email'), "Your OTP Code", f"Hello {name}, your OTP is: {otp_code}")
    except Exception as e:
        app.logger.warning("Email send failed: %s", e)

    return jsonify({'user_id': user_id})

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json(silent=True)
    if not data: return jsonify({'detail': 'Invalid JSON'}), 400
    user_id, otp = data.get('user_id'), data.get('otp')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT code, expires_at FROM otp_codes WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'detail': 'OTP not found'}), 400
    
    saved_otp, expires_at = row
    if datetime.now() > datetime.fromisoformat(expires_at):
        conn.close()
        return jsonify({'detail': 'OTP expired'}), 400
    
    if otp != saved_otp:
        conn.close()
        return jsonify({'detail': 'Incorrect OTP'}), 400

    session_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO sessions (session_id,user_id) VALUES (?,?)", (session_id, user_id))
    cursor.execute("DELETE FROM otp_codes WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'session_id': session_id})

@app.route('/dashboard_data.json', methods=['GET'])
def dashboard_data():
    sample_data = []
    if os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Defensive programming: ensure these are never undefined
                    savings = float(row.get('savings_balance') or 0)
                    loans = float(row.get('repayment_amount') or 0) + float(row.get('next_loan_due_amount') or 0)
                    balance = float(row.get('account_balance') or 0)
                    
                    sample_data.append({
                        'Date': row.get('date', 'N/A'),
                        'Name': f"{row.get('first_name','')} {row.get('last_name','')}".strip(),
                        'Email': row.get('email', 'N/A'),
                        'Savings': savings,
                        'Loans': loans,
                        'Balance': balance,
                        'label': row.get('label', 'neutral'),
                        'financial_score': int(row.get('financial_score', 0)),
                        'insight': row.get('insight', 'No data')
                    })
            print(f"DEBUG: Successfully loaded {len(sample_data)} rows.")
        except Exception as e:
            print(f"DEBUG: ERROR reading CSV: {e}")
    else:
        print(f"DEBUG: CSV_FILE not found at {CSV_FILE}")
    return jsonify(sample_data)

@app.route('/debug/users', methods=['GET'])
def debug_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users")
    users = cursor.fetchall()
    conn.close()
    return jsonify([{'id': u[0], 'name': u[1], 'email': u[2]} for u in users])

@app.route('/user', methods=['GET'])
def get_user():
    user_id = request.args.get('user_id')
    print(f"DEBUG: Fetching user_id: {user_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, email FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({'name': row[0], 'email': row[1]})
    print(f"DEBUG: User {user_id} not found in DB.")
    return jsonify({'detail': 'User not found'}), 404

@app.route('/')
def root():
    return send_from_directory(BASE_DIR, 'login.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(BASE_DIR, filename)