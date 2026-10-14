import os
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, send_from_directory
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'ganti-dengan-secret-key-acak-untuk-produksi')
app.config['UPLOAD_FOLDER'] = str(UPLOAD_DIR)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024


def get_db():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', '3306')),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'pengaduan_masyarakat'),
        ssl_disabled=False,
    )


def query_db(sql, params=(), fetchone=False, commit=False):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        result = cursor.fetchone() if fetchone else cursor.fetchall()
        if commit:
            conn.commit()
        return result
    finally:
        cursor.close()
        conn.close()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return render_template('index.html')
@app.route('/team')
def team():
    members = [
        'Hatman Firdayat',
        'PADIA',
        'SUBUN'
    ]
    return render_template('team.html', members=members)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if not name or not email or not password:
            flash('Semua kolom wajib diisi.', 'danger')
        elif len(password) < 8:
            flash('Kata sandi minimal 8 karakter.', 'danger')
        elif password != confirm:
            flash('Konfirmasi kata sandi tidak sama.', 'danger')
        else:
            try:
                query_db(
    'INSERT INTO users (nama, email, password, role) VALUES (%s, %s, %s, %s)',
    (name, email, generate_password_hash(password), 'masyarakat'),
    commit=True
)
                flash('Registrasi berhasil. Silakan login.', 'success')
                return redirect(url_for('login'))
            except Error as exc:
                if getattr(exc, 'errno', None) == 1062:
                    flash('Email tersebut sudah terdaftar.', 'danger')
                else:
                    app.logger.exception('Gagal mendaftar')
                    flash('Registrasi gagal. Pastikan database sudah disiapkan.', 'danger')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        try:
            user = query_db(
                'SELECT id, nama, email, password, role '
                'FROM users WHERE email = %s',
                (email,),
                fetchone=True
            )
        except Error:
            app.logger.exception('Gagal mengambil data pengguna saat login')
            flash(
                'Terjadi kesalahan saat mengakses database.',
                'danger'
            )
            return render_template('login.html')

        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['name'] = user['nama']
            session['role'] = user['role']

            flash('Berhasil login. Selamat datang!', 'success')

            if user['role'] == 'admin':
                return redirect(url_for('admin'))

            return redirect(url_for('dashboard'))

        flash('Email atau kata sandi salah.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Kamu sudah logout.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('role') == 'admin':
        return redirect(url_for('admin'))
    reports = query_db('SELECT id, title, category, status, created_at FROM reports WHERE user_id = %s ORDER BY created_at DESC LIMIT 5', (session['user_id'],))
    stats = query_db("SELECT COUNT(*) AS total, SUM(status='Menunggu') AS waiting, SUM(status='Diproses') AS processing, SUM(status='Selesai') AS done FROM reports WHERE user_id = %s", (session['user_id'],), fetchone=True)
    return render_template('dashboard.html', reports=reports, stats=stats)


@app.route('/laporan/baru', methods=['GET', 'POST'])
@login_required
def new_report():
    if session.get('role') == 'admin':
        return redirect(url_for('admin'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        if not all([title, category, location, description]):
            flash('Mohon lengkapi semua kolom wajib.', 'danger')
            return render_template('new_report.html')
        filename = None
        uploaded = request.files.get('evidence')
        if uploaded and uploaded.filename:
            if not allowed_file(uploaded.filename):
                flash('Bukti harus berupa PNG, JPG, JPEG, atau WEBP.', 'danger')
                return render_template('new_report.html')
            safe_name = secure_filename(uploaded.filename)
            filename = f"{session['user_id']}_{os.urandom(8).hex()}_{safe_name}"
            uploaded.save(UPLOAD_DIR / filename)
        try:
            query_db('INSERT INTO reports (user_id, title, category, location, description, evidence, status) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                     (session['user_id'], title, category, location, description, filename, 'Menunggu'), commit=True)
            flash('Laporan berhasil dikirim.', 'success')
            return redirect(url_for('my_reports'))
        except Error:
            app.logger.exception('Gagal menyimpan laporan')
            flash('Laporan gagal disimpan. Coba lagi setelah memeriksa database.', 'danger')
    return render_template('new_report.html')


@app.route('/laporan-saya')
@login_required
def my_reports():
    if session.get('role') == 'admin':
        return redirect(url_for('admin'))
    reports = query_db('SELECT id, title, category, location, status, admin_response, created_at FROM reports WHERE user_id = %s ORDER BY created_at DESC', (session['user_id'],))
    return render_template('my_reports.html', reports=reports)


@app.route('/admin')
@admin_required
def admin():
    reports = query_db('SELECT r.*, u.nama AS reporter_name, u.email AS reporter_email FROM reports r JOIN users u ON u.id = r.user_id ORDER BY r.created_at DESC')
    stats = query_db("SELECT COUNT(*) AS total, SUM(status='Menunggu') AS waiting, SUM(status='Diproses') AS processing, SUM(status='Selesai') AS done FROM reports", fetchone=True)
    return render_template('admin.html', reports=reports, stats=stats)


@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    # Evidence is only available to signed-in users; admins can view any report evidence.
    safe = secure_filename(filename)
    if safe != filename:
        abort(404)
    if session.get('role') != 'admin':
        owner = query_db('SELECT id FROM reports WHERE user_id = %s AND evidence = %s', (session['user_id'], filename), fetchone=True)
        if not owner:
            abort(403)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/admin/laporan/<int:report_id>', methods=['POST'])
@admin_required
def update_report(report_id):
    status = request.form.get('status', '')
    response = request.form.get('admin_response', '').strip()
    if status not in {'Menunggu', 'Diproses', 'Selesai', 'Ditolak'}:
        flash('Status tidak valid.', 'danger')
        return redirect(url_for('admin'))
    query_db('UPDATE reports SET status = %s, admin_response = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s',
             (status, response or None, report_id), commit=True)
    flash('Status laporan berhasil diperbarui.', 'success')
    return redirect(url_for('admin'))


@app.errorhandler(403)
def forbidden(_error):
    return render_template('error.html', code=403, message='Halaman ini hanya dapat diakses oleh admin.'), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template('error.html', code=404, message='Halaman yang kamu cari tidak ditemukan.'), 404


@app.errorhandler(413)
def too_large(_error):
    flash('Ukuran file maksimal 5 MB.', 'danger')
    return redirect(url_for('new_report'))


if __name__ == '__main__':
    app.run(debug=True)
