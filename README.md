# AspirasiKita — Sistem Pengaduan dan Aspirasi Masyarakat

Aplikasi contoh berbasis Python Flask, HTML/CSS, dan MySQL. Fitur: registrasi/login, dashboard, pengiriman laporan dengan foto opsional, riwayat dan status laporan, serta panel admin.

## 1. Prasyarat
- Python 3.10 atau lebih baru
- MySQL aktif (dapat dijalankan melalui Laragon)
- VS Code

## 2. Siapkan database
1. Buka Laragon dan klik **Start All** (atau jalankan layanan MySQL saja).
2. Buka HeidiSQL/phpMyAdmin/MySQL client yang tersedia.
3. Jalankan seluruh isi `database.sql`.
4. Konfigurasi bawaan mengasumsikan MySQL di `127.0.0.1:3306`, user `root`, password kosong. Jika berbeda, atur environment variables `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.

## 3. Pasang dependensi dan jalankan
Buka folder proyek di VS Code, kemudian buka Terminal.

Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Jika PowerShell memblokir aktivasi virtual environment, gunakan Command Prompt:
```bat
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python app.py
```

Buka alamat `http://127.0.0.1:5000` di browser. Biarkan terminal tetap terbuka selama aplikasi dipakai.

## 4. Jadikan akun sebagai admin
1. Daftar akun biasa melalui halaman **Daftar**.
2. Di MySQL, jalankan perintah berikut dengan email akun yang kamu daftarkan:
```sql
USE pengaduan_masyarakat;
UPDATE users SET role = 'admin' WHERE email = 'emailkamu@example.com';
```
3. Logout lalu login kembali. Akun tersebut akan diarahkan ke Panel Admin.

## Catatan keamanan
- Kata sandi disimpan menggunakan hash Werkzeug, bukan teks biasa.
- Query database menggunakan parameter.
- Aplikasi ini merupakan starter project untuk pembelajaran. Sebelum dipasang ke internet/produksi, tambahkan perlindungan CSRF, konfigurasi secret key yang kuat, HTTPS, pembatasan percobaan login, dan penyajian file bukti melalui endpoint yang mengautentikasi akses. Jangan gunakan mode debug di server publik.
