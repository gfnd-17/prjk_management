# Project Management - Odoo Module

## 📌 Pendahuluan
Modul ini merupakan sistem manajemen proyek yang dikembangkan untuk Odoo 16 CE. 
Fitur utama dalam modul ini termasuk:
- CRUD proyek dengan informasi detail
- Perhitungan durasi proyek otomatis
- Integrasi dengan Trello untuk sinkronisasi proyek
- Notifikasi email saat status proyek berubah

## 🛠 Instalasi

### 1. Salin Modul ke Direktori Odoo
Pindahkan modul ini ke dalam direktori `addons` Odoo:

```bash
cp -r project_management /opt/odoo/custom_addons/
```

### 2. Restart Odoo Server
```bash
sudo systemctl restart odoo
```

### 3. Aktifkan Modul di Odoo
- Buka **Apps** di Odoo
- Klik **Update Apps List**
- Cari **Project Management**
- Klik **Install**

## 🔗 Konfigurasi Trello API

### 1. Dapatkan API Key dan Token
- **API Key**: [https://trello.com/app-key](https://trello.com/app-key)
- **Token**: 
```bash
https://trello.com/1/authorize?key=YOUR_API_KEY&name=OdooProjectManagement&expiration=never&response_type=token&scope=read,write
```

Gantilah `YOUR_API_KEY` dengan API Key Anda, lalu salin token yang muncul.

### 2. Masukkan API Key & Token ke Odoo
- Buka **Settings → Technical → System Parameters**
- Tambahkan parameter berikut:
  - `trello.api_key`: API Key Trello Anda
  - `trello.token`: Token Trello Anda

## 🕒 Cron Jobs (Scheduled Actions)
Modul ini memiliki 2 cron job untuk otomatisasi:

| Nama Cron Job                     | Interval | Fungsi |
|------------------------------------|---------|--------------------------------|
| Update Status Proyek Otomatis      | 1 hari  | update_project_status()        |
| Sinkronisasi Status dari Trello    | 1 jam   | sync_status_from_trello()      |

Untuk menjalankan cron job secara manual:
1. Masuk ke **Settings → Technical → Automation → Scheduled Actions**
2. Pilih cron job yang ingin dijalankan
3. Klik **Run Manually**

## 🧪 Menjalankan Unit Test
Unit test memastikan semua fitur berjalan dengan baik. Untuk menjalankan unit test, gunakan perintah berikut:

```bash
odoo-bin --test-enable -i project_management
```

Jika menggunakan Odoo sebagai service:
```bash
sudo service odoo restart --test-enable -i project_management
```

Pastikan unit test berada di dalam direktori `tests/` dengan struktur berikut:
```
project_management/
│── models/
│── views/
│── data/
│── tests/
│   ├── test_project_management.py
│   ├── __init__.py
│── __init__.py
│── __manifest__.py
```

## 🚀 Troubleshooting
Jika ada kendala dalam menjalankan modul, coba solusi berikut:

- **Modul tidak muncul di Apps?**  
  ✔ Pastikan direktori modul sudah benar dan jalankan **Update Apps List**.

- **Proyek tidak sinkron dengan Trello?**  
  ✔ Periksa **System Parameters** dan pastikan API Key & Token benar.  
  ✔ Jalankan cron job secara manual.

- **Notifikasi email tidak terkirim?**  
  ✔ Pastikan server email sudah dikonfigurasi di **Settings → Outgoing Mail Servers**.

## 📌 Kesimpulan
Modul ini memungkinkan manajemen proyek dalam Odoo dengan fitur lengkap, termasuk integrasi dengan Trello dan notifikasi otomatis. Jika ada kendala atau perbaikan yang dibutuhkan, silakan menghubungi tim pengembang.

---
✍ **Developer**: Gofindo.17
📅 **Versi**: 1.0  
📧 **Kontak**: govindo1706@gmail.com
