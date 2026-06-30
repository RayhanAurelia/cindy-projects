"""
Generator diagram alur penggunaan aplikasi (Usage Flow) -> docs/alur-penggunaan.png
Dirender lokal dengan matplotlib (tanpa dependensi eksternal selain matplotlib).
Jalankan:  python docs/generate_flowchart.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon

# ---- Palet warna (selaras tema monokrom aplikasi) ----
NAVY   = "#0f172a"
SLATE  = "#64748b"
LIGHT  = "#e2e8f0"
PAPER  = "#f8fafc"
WHITE  = "#ffffff"

fig, ax = plt.subplots(figsize=(12, 17))
ax.set_xlim(0, 100)
ax.set_ylim(0, 144)
ax.axis("off")
fig.patch.set_facecolor(WHITE)

def box(x, y, w, h, text, fill=WHITE, edge=NAVY, fc=NAVY, fontsize=10, weight="normal", rounded=True):
    style = "round,pad=0.3,rounding_size=2" if rounded else "square,pad=0.3"
    p = FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=style,
                       linewidth=1.6, edgecolor=edge, facecolor=fill, mutation_scale=1)
    ax.add_patch(p)
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
            color=fc, weight=weight, wrap=True)
    return (x, y, w, h)

def diamond(x, y, w, h, text, fill=LIGHT, edge=NAVY, fc=NAVY, fontsize=9.5, weight="bold"):
    pts = [(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)]
    ax.add_patch(Polygon(pts, closed=True, linewidth=1.6, edgecolor=edge, facecolor=fill))
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize, color=fc, weight=weight)
    return (x, y, w, h)

def arrow(p1, p2, color=NAVY, label=None, lx=0, ly=0, style="-|>", rad=0.0):
    a = FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=16,
                        linewidth=1.4, color=color,
                        connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)
    if label:
        mx, my = (p1[0] + p2[0]) / 2 + lx, (p1[1] + p2[1]) / 2 + ly
        ax.text(mx, my, label, ha="center", va="center", fontsize=8.5,
                color=SLATE, weight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc=WHITE, ec="none"))

# ====== TITLE ======
ax.text(50, 141, "Diagram Alur Penggunaan Aplikasi",
        ha="center", va="center", fontsize=17, weight="bold", color=NAVY)
ax.text(50, 137.5, "Simulator Sistem Kontrol — Pencampuran Susu & Pewarna (DCS Siemens PCS 7)",
        ha="center", va="center", fontsize=10.5, color=SLATE)

# ====== START ======
start = box(50, 131, 26, 6, "Buka Aplikasi", fill=NAVY, fc=WHITE, weight="bold")

# ====== MENU DIAMOND ======
menu = diamond(50, 121, 30, 9, "Pilih Menu\ndi Sidebar")
arrow((50, 128), (50, 125.6))

# ====== MENU BAND (5 halaman) ======
y_menu = 110
m_ratio   = box(12, y_menu, 17, 7, "Sistem\nKontrol Rasio", fill=LIGHT, fontsize=9, weight="bold")
m_cascade = box(31, y_menu, 17, 7, "Sistem Kontrol\nBertingkat", fill=LIGHT, fontsize=9, weight="bold")
m_scl     = box(50, y_menu, 17, 7, "Template\nKode SCL", fill=LIGHT, fontsize=9, weight="bold")
m_hb      = box(69, y_menu, 17, 7, "Panduan\nSistem Kontrol", fill=LIGHT, fontsize=9, weight="bold")
m_hist    = box(88, y_menu, 17, 7, "Riwayat\nPengujian", fill=LIGHT, fontsize=9, weight="bold")

for mx in [12, 31, 50, 69, 88]:
    arrow((50, 116.5), (mx, y_menu + 3.6), color=SLATE, rad=0.0)

# ====== SIMULATION FLOW (dari Ratio & Cascade) ======
cfg = diamond(31, 97, 26, 9, "Atur\nSkenario")
arrow((12, y_menu - 3.6), (31, 101.5), color=NAVY, rad=-0.1)
arrow((31, y_menu - 3.6), (31, 101.5), color=NAVY)

preset = box(14, 85, 22, 7, "Klik PRESET\n(1-4 skenario siap pakai)", fontsize=9)
param  = box(48, 85, 26, 8, "Atur Parameter manual:\nFlow Susu, Target Rasio/Warna,\nPID (Kp/Ki/Kd), Gangguan", fontsize=8.3)
arrow((24, 95), (16, 88.5), color=SLATE, label="cepat", ly=1)
arrow((38, 95), (46, 89), color=SLATE, label="manual", ly=1)

run = box(31, 74, 20, 6, "Tekan  START", fill=NAVY, fc=WHITE, weight="bold")
arrow((14, 81.5), (28, 77), color=NAVY)
arrow((48, 81), (34, 77), color=NAVY)

live = box(31, 64, 30, 8, "Simulasi REAL-TIME:\nkartu metrik • visualisasi tangki\n• grafik flow / rasio / warna", fontsize=8.6)
arrow((31, 71), (31, 68), color=NAVY)

dec1 = diamond(31, 52, 24, 9, "Hasil\nsesuai?")
arrow((31, 60), (31, 56.5), color=NAVY)

tune = box(72, 52, 24, 8, "PAUSE  →  ubah PID /\naktifkan gangguan\n(uji respons sistem)", fontsize=8.6)
arrow((43, 52), (60, 52), color=SLATE, label="belum", ly=1.6)
arrow((72, 56), (40, 64), color=SLATE, rad=-0.25)  # loop balik ke simulasi

dec2 = diamond(31, 40, 22, 8, "Aksi")
arrow((31, 47.5), (31, 44), color=NAVY, label="ya / cukup", lx=-9)

reset = box(72, 40, 24, 7, "RESET JALUR\n(bersihkan data,\nmulai ulang)", fontsize=8.6)
arrow((42, 40), (60, 40), color=SLATE, label="reset", ly=1.4)
arrow((72, 43.5), (31, 93), color=SLATE, rad=0.35)  # loop balik ke Atur Skenario

save = box(31, 29, 26, 7, "END & SIMPAN\n(rekam ke Riwayat)", fill=NAVY, fc=WHITE, fontsize=9, weight="bold")
arrow((31, 36), (31, 32.5), color=NAVY, label="simpan", lx=-10)

# ====== HALAMAN PENDUKUNG (aksi akhir) ======
# Riwayat (penyimpanan + analisis)
hist_act = box(88, 22, 20, 9, "RIWAYAT:\nbandingkan pengujian,\ndetail grafik,\nUnduh CSV", fill=PAPER, fontsize=8.4)
arrow((88, y_menu - 3.6), (88, 26.5), color=SLATE)              # dari menu Riwayat
arrow((44, 29), (78, 23.5), color=NAVY, rad=-0.15, label="data tersimpan", ly=2.5)  # dari Save

# SCL
scl_act = box(50, 96, 20, 7, "Salin Function Block\nSCL → TIA Portal /\nSTEP 7", fill=PAPER, fontsize=8.4)
arrow((50, y_menu - 3.6), (50, 99.5), color=SLATE)

# Handbook
hb_act = box(69, 96, 19, 7, "Pelajari konsep\nRatio / Cascade / PID", fill=PAPER, fontsize=8.6)
arrow((69, y_menu - 3.6), (69, 99.5), color=SLATE)

# ====== LEGEND ======
ax.text(6, 12, "Keterangan:", fontsize=9, weight="bold", color=NAVY)
box(11, 8, 12, 4, "Mulai/Aksi inti", fill=NAVY, fc=WHITE, fontsize=8)
box(30, 8, 12, 4, "Proses", fill=WHITE, fontsize=8)
diamond(48, 8, 13, 5, "Keputusan", fontsize=8, weight="normal")
box(67, 8, 12, 4, "Menu sidebar", fill=LIGHT, fontsize=8)
box(86, 8, 13, 4, "Halaman hasil", fill=PAPER, fontsize=8)

plt.tight_layout()
out = "docs/alur-penggunaan.png"
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=WHITE)
print("Saved:", out)
