from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
from hitung_ahp_topsis import proses_rekomendasi, KRITERIA, ALTERNATIF

from functools import wraps
import hashlib
import csv
import io
from flask import send_file
from datetime import datetime
from flask import redirect, url_for

app = Flask(__name__)
app.secret_key = "spk-konsentrasi-secret-key"


# ============================================================
# DECORATOR: Cek apakah admin sudah login
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# ROUTE: Login Admin
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute(
            "SELECT id, nama_lengkap FROM admin WHERE username=? AND password_hash=?",
            (username, password_hash)
        )
        admin = c.fetchone()
        conn.close()

        if admin:
            session["admin_logged_in"] = True
            session["admin_id"] = admin[0]
            session["admin_nama"] = admin[1]
            return redirect(url_for("admin_dashboard"))
        else:
            return render_template("login.html", error="Username atau password salah")

    return render_template("login.html")


# ============================================================
# ROUTE: Logout
# ============================================================

@app.route("/admin")
@login_required
def admin_dashboard():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, nama, jawaban, hasil, created_at FROM assessments ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()

    data = []
    for row in rows:
        try:
            hasil = json.loads(row[3]) if row[3] else {}
        except (json.JSONDecodeError, TypeError):
            hasil = {}

        peringkat = hasil.get("peringkat", [])
        nilai_map = {p["nama"]: p["nilai"] for p in peringkat if "nama" in p and "nilai" in p}

        data.append({
            "id": int(row[0]),
            "nama": str(row[1]) if row[1] else "Anonim",
            "jawaban": json.loads(row[2]) if row[2] else [],
            "konsentrasi_utama": hasil.get("konsentrasi_utama", "-"),
            "peringkat": peringkat,
            "created_at": str(row[4]) if row[4] else "-",
            "nilai_ai": nilai_map.get("Artificial Intelligence", 0),
            "nilai_sd": nilai_map.get("Software Development", 0),
            "nilai_cn": nilai_map.get("Computer Network", 0)
        })

    return render_template("admin.html", data=data, admin_nama=session.get("admin_nama"))

# ============================================================
# ROUTE: Export Excel (CSV)
# ============================================================

@app.route("/admin/export")
@login_required
def export_excel():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, nama, jawaban, hasil, created_at FROM assessments ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()

    # Buat CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "ID", "Nama", "Tanggal",
        "Konsentrasi Utama",
        "Kecocokan AI (%)", "Kecocokan Software Dev (%)", "Kecocokan Network (%)",
        "Peringkat 1", "Peringkat 2", "Peringkat 3"
    ])

    # Data
    for row in rows:
        id_, nama, jawaban, hasil_json, created_at = row
        hasil = json.loads(hasil_json)
        peringkat = hasil.get("peringkat", [])

        # Buat mapping nama → nilai
        nilai_map = {p["nama"]: p["nilai"] for p in peringkat}

        writer.writerow([
            id_,
            nama,
            created_at,
            hasil.get("konsentrasi_utama", "-"),
            nilai_map.get("Artificial Intelligence", 0),
            nilai_map.get("Software Development", 0),
            nilai_map.get("Computer Network", 0),
            peringkat[0]["nama"] if len(peringkat) > 0 else "-",
            peringkat[1]["nama"] if len(peringkat) > 1 else "-",
            peringkat[2]["nama"] if len(peringkat) > 2 else "-",
        ])

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"hasil_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )


# ============================================================
# DATABASE
# ============================================================

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT,
            jawaban TEXT,
            hasil TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Tabel admin (BARU)
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nama_lengkap TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Buat admin default jika belum ada
    c.execute("SELECT COUNT(*) FROM admin")
    if c.fetchone()[0] == 0:
        password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute(
            "INSERT INTO admin (username, password_hash, nama_lengkap) VALUES (?, ?, ?)",
            ("admin", password_hash, "Administrator")
        )
        print(">>> Admin default dibuat: username='admin', password='admin123'")

    conn.commit()
    conn.close()


def simpan_assessment(nama, jawaban, hasil):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO assessments (nama, jawaban, hasil) VALUES (?, ?, ?)",
        (nama, json.dumps(jawaban), json.dumps(hasil))
    )
    conn.commit()
    conn.close()


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def index():
    return render_template("index.html", kriteria=KRITERIA, alternatif=ALTERNATIF)


@app.route("/kuisioner")
def kuesioner():
    return render_template("kuisioner.html")


@app.route("/api/rekomendasi", methods=["POST"])
def api_rekomendasi():
    data = request.get_json()
    nama = data.get("nama", "Anonim")
    jawaban = data.get("jawaban", [])

    # Validasi
    if len(jawaban) != 15:
        return jsonify({"error": "Jumlah jawaban harus 15"}), 400

    # Proses AHP-TOPSIS
    hasil = proses_rekomendasi(jawaban)

    # Simpan ke database
    simpan_assessment(nama, jawaban, hasil)

    return jsonify(hasil)


@app.route("/hasil")
def hasil():
    return render_template("result.html")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)