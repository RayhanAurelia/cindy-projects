# Simulator Sistem Kontrol — Pencampuran Susu & Pewarna (DCS Siemens PCS 7)

Aplikasi simulasi interaktif untuk Tugas Besar **Pengendalian Proses**. Menyimulasikan
**Ratio Control** dan **Cascade Control** pada proses pencampuran susu (*wild flow*) dengan
cairan pewarna (*controlled flow*), lengkap dengan validasi sensor warna **TCS3200** dan
generator template kode **SCL Siemens PCS 7**.

## Fitur

- **Sistem Kontrol Rasio** — laju pewarna (MV) dijaga proporsional terhadap laju susu (PV) via `K_ratio`, dengan loop PID slave.
- **Sistem Kontrol Bertingkat (Cascade)** — loop luar (warna TCS3200) → loop dalam (aliran pewarna).
- **Validasi feedback TCS3200** — koreksi/alarm bila warna campuran menyimpang dari target.
- **Uji gangguan (disturbance)** — fluktuasi laju susu, katup tersumbat, drop tekanan.
- **Generator kode SCL PCS 7** — Function Block siap pakai untuk TIA Portal / STEP 7.
- **Visualisasi real-time** — tangki dinamis + grafik Plotly (flow, rasio, warna, bukaan katup).

## Dokumentasi & Alur Penggunaan

- **[Panduan Lengkap (semua halaman & field)](docs/PANDUAN-LENGKAP.md)** — penjelasan detail tiap halaman, tombol, dan parameter.
- **Diagram alur penggunaan:**

![Diagram Alur Penggunaan](docs/alur-penggunaan.png)

## Struktur Proyek

```
cindy-project/
├── app.py                      # Aplikasi Streamlit (UI utama)
├── scl_generator.py            # Generator template kode SCL Siemens PCS 7
├── simulation/
│   ├── pid.py                  # Algoritma PID + anti-windup
│   ├── ratio_control.py        # Model proses Ratio Control
│   └── cascade_control.py      # Model proses Cascade Control
├── assets/style.css            # Tema monokrom (UI)
├── .streamlit/config.toml      # Konfigurasi tema & server
├── docs/
│   ├── PANDUAN-LENGKAP.md       # Dokumentasi lengkap semua halaman & field
│   ├── alur-penggunaan.png      # Diagram alur penggunaan (gambar)
│   └── generate_flowchart.py    # Skrip pembuat diagram (matplotlib)
└── requirements.txt            # Dependensi Python
```

## Menjalankan Secara Lokal

Butuh **Python 3.11+**.

```bash
# 1. (opsional) buat virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 2. install dependensi
pip install -r requirements.txt

# 3. jalankan aplikasi
streamlit run app.py
```

Aplikasi terbuka otomatis di `http://localhost:8501`.

## Deployment

### Opsi 1 — Streamlit Community Cloud (gratis, paling mudah)

1. Push proyek ini ke repository GitHub publik.
2. Buka <https://share.streamlit.io> dan login dengan akun GitHub.
3. Klik **New app**, pilih repository, branch `main`, dan main file `app.py`.
4. Klik **Deploy**. Streamlit Cloud otomatis membaca `requirements.txt`.

> Aplikasi sudah dikonfigurasi `headless = true` di `.streamlit/config.toml`, jadi siap deploy tanpa perubahan tambahan.

### Opsi 2 — Hugging Face Spaces

1. Buat Space baru bertipe **Streamlit**.
2. Upload seluruh isi proyek (atau hubungkan repo GitHub).
3. Space otomatis menginstall `requirements.txt` dan menjalankan `app.py`.

### Opsi 3 — Docker (server sendiri / VPS)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t ratio-control-sim .
docker run -p 8501:8501 ratio-control-sim
```

## Tim

Dibuat untuk Tugas Besar Pengendalian Proses — bagian *software/coding* (Cindy & Terran).
