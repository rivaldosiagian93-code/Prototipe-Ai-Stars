# Prototipe-Ai-Stars

AI yang bisa menerima semua curhatan mahasiswa.

Stars adalah asisten AI untuk desktop Windows dan browser. Stars menyediakan chat teks dan input suara, menggunakan API yang kompatibel dengan format OpenAI Chat Completions. Pesan dikirim ke endpoint yang dikonfigurasi. Versi desktop menyimpan percakapan hanya selama aplikasi berjalan; versi web menyimpannya secara lokal di browser.

## Persiapan

1. Pasang Python 3.10 atau lebih baru dan pastikan opsi **Add Python to PATH** aktif.
2. Buka PowerShell di folder proyek dan pasang dependensi:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Siapkan API key dari penyedia AI yang endpoint-nya kompatibel dengan format OpenAI. Agar shortcut bisa menggunakannya, atur variabel pengguna `OPENAI_API_KEY` melalui Windows: cari **Edit environment variables for your account**, pilih **New**, lalu isi nama `OPENAI_API_KEY` dan nilai API key. Tutup dan buka kembali aplikasi setelah mengaturnya.

## Versi desktop

Jalankan aplikasi desktop dengan mikrofon aktif:

```powershell
python .\Stars.py --listen
```

Atau klik dua kali `Jalankan Stars.bat`. Aplikasi juga memiliki tombol **Mulai bicara** untuk menyalakan atau mematikan mikrofon. Beri izin akses mikrofon kepada aplikasi jika Windows memintanya.

Pengenalan suara memakai layanan Google melalui internet. Rekaman ucapan dikirim ke layanan tersebut untuk diubah menjadi teks; pesan teks hasil transkripsi kemudian dikirim ke endpoint AI yang dikonfigurasi. Tkinter biasanya disertakan dalam instalasi Python untuk Windows.

## Versi web

Cara termudah menjalankan server web Stars adalah klik dua kali `Jalankan Stars Web.bat`. Jika `OPENAI_API_KEY` belum tersedia di Windows, server meminta API key di jendela PowerShell dengan input tersembunyi. Key hanya digunakan selama server berjalan dan tidak disimpan ke file proyek atau environment Windows.

Untuk menjalankan server web Stars secara manual:

```powershell
$env:OPENAI_API_KEY = "API-key-anda"
python .\web_app.py --host 127.0.0.1 --port 8000
```

Lalu buka browser ke alamat:

```text
http://127.0.0.1:8000/
```

Versi web mendukung chat teks di browser, dukungan mikrofon bawaan browser jika didukung, dan menggunakan variabel lingkungan yang sama seperti versi desktop.

Tampilan web menyediakan daftar chat, chat baru, dan penghapusan chat. Riwayat disimpan di `localStorage` browser pada perangkat yang digunakan; riwayat tidak disimpan di server dan tidak tersinkron ke perangkat lain. Gunakan browser yang sama untuk membukanya kembali.

Orb bintang pada halaman mengikuti gerakan kursor. Klik **Aktifkan suara** sekali untuk mendengar sapaan Stars dan mengaktifkan pembacaan jawaban. Suara menggunakan fitur text-to-speech bawaan browser/perangkat dengan bahasa Indonesia jika tersedia; karakter suara dan kualitasnya tergantung suara yang terpasang, bukan suara Siri.

## Deploy ke VPS/hosting dengan Docker

Versi web dapat dijalankan dalam container Linux. Pastikan Docker tersedia, lalu siapkan API key dan kata sandi akses yang kuat di PowerShell:

```powershell
$env:OPENAI_API_KEY = "API-key-anda"
$env:STARS_ACCESS_PASSWORD = "kata-sandi-panjang-dan-kuat"
docker build -t stars-web .
docker run -d --name stars-web --restart unless-stopped -p 127.0.0.1:8000:8000 --env OPENAI_API_KEY --env STARS_ACCESS_PASSWORD stars-web
```

Server hanya menerima permintaan dari komputer itu sendiri pada port 8000. Untuk akses publik, pasang reverse proxy seperti Nginx/Caddy di VPS dan aktifkan HTTPS/TLS. Saat dibuka, browser meminta autentikasi dasar; masukkan `stars` sebagai nama pengguna dan nilai `STARS_ACCESS_PASSWORD` sebagai kata sandi. Jangan meneruskan port container langsung ke internet tanpa HTTPS.

Untuk platform hosting yang menetapkan port sendiri, container membaca variabel `PORT`. Atur `OPENAI_API_KEY` dan `STARS_ACCESS_PASSWORD` melalui pengaturan rahasia/environment variables platform, bukan di kode atau repository. Kata sandi akses wajib ada saat container berjalan. Mikrofon browser biasanya hanya tersedia melalui `localhost` atau koneksi HTTPS.

## Konfigurasi opsional

Secara default, Stars menggunakan endpoint OpenAI dan model `gpt-4o-mini`. Untuk mengganti model atau endpoint kompatibel:

```powershell
$env:OPENAI_MODEL = "nama-model"
$env:OPENAI_BASE_URL = "https://alamat-endpoint/v1/chat/completions"
python .\Stars.py
```

Untuk versi web, variabel lingkungan yang sama bisa dipakai sebelum menjalankan server:

```powershell
$env:OPENAI_MODEL = "nama-model"
$env:OPENAI_BASE_URL = "https://alamat-endpoint/v1/chat/completions"
python .\web_app.py --host 127.0.0.1 --port 8000
```

Jangan masukkan API key langsung ke kode atau bagikan key tersebut. Stars mengirim isi percakapan ke endpoint yang dipilih untuk menghasilkan balasan.
