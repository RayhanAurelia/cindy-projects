import streamlit as st
import time
import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import textwrap
from simulation.ratio_control import RatioControlSimulation
from simulation.cascade_control import CascadeControlSimulation
import scl_generator

# Page Config
st.set_page_config(
    page_title="Industrial Control System Simulator",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* Hilangkan tombol collapse sidebar */
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# Load CSS
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# JS to intercept Streamlit's 'c' key shortcut (Clear Caches) and 'r' (Rerun) so they don't block Ctrl+C/copying
st.components.v1.html(
    """
    <script>
    const parentDoc = window.parent.document;
    parentDoc.addEventListener("keydown", function(e) {
        const k = e.key.toLowerCase();
        const active = parentDoc.activeElement;
        const inField = active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable);
        if (inField) return;

        // Ctrl/Cmd + C : izinkan salin native, tapi cegah shortcut Streamlit (Clear Caches)
        if ((e.ctrlKey || e.metaKey) && k === 'c') {
            e.stopImmediatePropagation();   // hentikan ke handler Streamlit
            return;                         // TANPA preventDefault -> copy tetap berjalan
        }

        // Tombol 'c' atau 'r' polos : blokir shortcut Clear Caches / Rerun
        if ((k === 'c' || k === 'r') && !e.ctrlKey && !e.metaKey && !e.altKey) {
            e.stopImmediatePropagation();
            e.preventDefault();
        }
    }, true);
    </script>
    """,
    height=0,
    width=0
)

# Initialize simulations in session state
if "ratio_sim" not in st.session_state:
    st.session_state.ratio_sim = RatioControlSimulation()
if "cascade_sim" not in st.session_state:
    st.session_state.cascade_sim = CascadeControlSimulation()
if "sim_running" not in st.session_state:
    st.session_state.sim_running = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "ratio"
if "test_history" not in st.session_state:
    st.session_state.test_history = []   # Riwayat hasil pengujian yang disimpan

# Initialize session state variables for Ratio Control sliders
if "ratio_milk_input" not in st.session_state:
    st.session_state.ratio_milk_input = 50.0
if "ratio_target_ratio" not in st.session_state:
    st.session_state.ratio_target_ratio = 0.10
if "ratio_mode" not in st.session_state:
    st.session_state.ratio_mode = "Auto (PID)"
if "ratio_kp" not in st.session_state:
    st.session_state.ratio_kp = 2.5
if "ratio_ki" not in st.session_state:
    st.session_state.ratio_ki = 1.5
if "ratio_kd" not in st.session_state:
    st.session_state.ratio_kd = 0.10
if "ratio_dist_milk" not in st.session_state:
    st.session_state.ratio_dist_milk = False
if "ratio_dist_clog" not in st.session_state:
    st.session_state.ratio_dist_clog = False

# Initialize session state variables for Cascade Control sliders
if "cascade_target_color" not in st.session_state:
    st.session_state.cascade_target_color = 100.0
if "cascade_mode" not in st.session_state:
    st.session_state.cascade_mode = "Auto (Cascade PID)"
if "cas_kp_out" not in st.session_state:
    st.session_state.cas_kp_out = 0.15
if "cas_ki_out" not in st.session_state:
    st.session_state.cas_ki_out = 0.03
if "cas_kd_out" not in st.session_state:
    st.session_state.cas_kd_out = 0.01
if "cas_kp_in" not in st.session_state:
    st.session_state.cas_kp_in = 2.5
if "cas_ki_in" not in st.session_state:
    st.session_state.cas_ki_in = 1.5
if "cas_kd_in" not in st.session_state:
    st.session_state.cas_kd_in = 0.10
if "cascade_dist_milk" not in st.session_state:
    st.session_state.cascade_dist_milk = False
if "cascade_dist_pressure" not in st.session_state:
    st.session_state.cascade_dist_pressure = False

# Sidebar Navigation
st.sidebar.markdown("<h2 style='text-align: center; color: #0f172a; font-weight: 700; letter-spacing: 2px; margin-bottom: 20px;'>CONTROLLER</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Custom Sidebar Buttons (Monochrome Navigation)
btn_ratio_type = "primary" if st.session_state.current_page == "ratio" else "secondary"
btn_cascade_type = "primary" if st.session_state.current_page == "cascade" else "secondary"
btn_scl_type = "primary" if st.session_state.current_page == "scl" else "secondary"
btn_handbook_type = "primary" if st.session_state.current_page == "handbook" else "secondary"
btn_history_type = "primary" if st.session_state.current_page == "history" else "secondary"

if st.sidebar.button("Sistem Kontrol Rasio", type=btn_ratio_type, icon=":material/monitoring:", use_container_width=True):
    st.session_state.current_page = "ratio"
    st.rerun()

if st.sidebar.button("Sistem Kontrol Bertingkat", type=btn_cascade_type, icon=":material/schema:", use_container_width=True):
    st.session_state.current_page = "cascade"
    st.rerun()

if st.sidebar.button("Template Kode SCL PCS 7", type=btn_scl_type, icon=":material/code:", use_container_width=True):
    st.session_state.current_page = "scl"
    st.rerun()

if st.sidebar.button("Panduan Sistem Kontrol", type=btn_handbook_type, icon=":material/menu_book:", use_container_width=True):
    st.session_state.current_page = "handbook"
    st.rerun()

if st.sidebar.button("Riwayat Pengujian", type=btn_history_type, icon=":material/history:", use_container_width=True):
    st.session_state.current_page = "history"
    st.rerun()

st.sidebar.markdown("---")
# Manual Clear Caches button inside sidebar as requested
if st.sidebar.button("Hapus Cache", icon=":material/restart_alt:", use_container_width=True):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.toast("Cache berhasil dibersihkan!")

# Helper function to apply Ratio presets
def apply_ratio_preset(ratio, kp, ki, kd, dist_milk, dist_clog):
    st.session_state.ratio_target_ratio = ratio
    st.session_state.ratio_kp = kp
    st.session_state.ratio_ki = ki
    st.session_state.ratio_kd = kd
    st.session_state.ratio_dist_milk = dist_milk
    st.session_state.ratio_dist_clog = dist_clog
    st.session_state.ratio_mode = "Auto (PID)"
    st.session_state.sim_running = True

# Helper function to apply Cascade presets
def apply_cascade_preset(color, kp_out, ki_out, kd_out, kp_in, ki_in, kd_in, dist_milk, dist_press):
    st.session_state.cascade_target_color = color
    st.session_state.cas_kp_out = kp_out
    st.session_state.cas_ki_out = ki_out
    st.session_state.cas_kd_out = kd_out
    st.session_state.cas_kp_in = kp_in
    st.session_state.cas_ki_in = ki_in
    st.session_state.cas_kd_in = kd_in
    st.session_state.cascade_dist_milk = dist_milk
    st.session_state.cascade_dist_pressure = dist_press
    st.session_state.cascade_mode = "Auto (Cascade PID)"
    st.session_state.sim_running = True

# ----------------------------------------------------
# Helper: simpan hasil pengujian ke Riwayat (dipanggil tombol "End & Simpan")
# ----------------------------------------------------
def save_test_result(sim, control_type, params, param_str):
    """Ambil snapshot data simulasi + hitung metrik performa, lalu simpan ke riwayat."""
    hist = sim.history
    n = len(hist["time"])
    if n == 0:
        return False  # Tidak ada data untuk disimpan

    data = {k: list(v) for k, v in hist.items()}  # Salin agar tidak terhapus saat reset

    # Hitung metrik performa untuk analisis kestabilan
    val_pct = 100.0 * (sum(data["validation_ok"]) / n)
    if control_type == "Ratio":
        # Mean Absolute Error antara aliran pewarna aktual dan setpoint-nya
        err = np.abs(np.array(data["colorant_flow"]) - np.array(data["colorant_flow_sp"]))
        mae_label = "MAE Aliran (L/min)"
    else:
        # Mean Absolute Error antara warna terukur dan target warna
        err = np.abs(np.array(data["sensor_color"]) - np.array(data["target_color"]))
        mae_label = "MAE Warna"
    mae = float(np.mean(err))

    record = {
        "id": st.session_state.get("history_counter", 0) + 1,
        "timestamp": datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S"),
        "type": control_type,
        "params": params,
        "param_str": param_str,
        "data": data,
        "summary": {
            "durasi": round(data["time"][-1], 1),
            "mae": round(mae, 3),
            "mae_label": mae_label,
            "val_pct": round(val_pct, 1),
            "n": n,
        },
    }
    st.session_state.history_counter = record["id"]
    st.session_state.test_history.append(record)
    return True

# ----------------------------------------------------
# PAGE: RATIO CONTROL
# ----------------------------------------------------
if st.session_state.current_page == "ratio":
    st.markdown("<h1 style='color: #0f172a; font-weight: 700;'>Sistem Kontrol Rasio (Ratio Control)</h1>", unsafe_allow_html=True)
    st.markdown(
        "Sistem Kontrol Rasio menjaga perbandingan tetap antara laju aliran **Susu (Wild Flow)** "
        "dan laju aliran **Pewarna (Slave Flow)**. Logika ini secara otomatis menyesuaikan laju aliran pewarna "
        "mengikuti fluktuasi laju susu agar kualitas pencampuran tetap konsisten"
    )
    st.markdown("---")
    
    col1, col2 = st.columns([1, 3])
    sim = st.session_state.ratio_sim
    
    # Left Column: Control Panel
    with col1:
        # Template Preset Buttons for Fast Demo
        with st.container(border=True):
            st.markdown("<h4 style='margin-top:0; font-weight: 600;'>Presets & Skenario Simulasi</h4>", unsafe_allow_html=True)
            st.markdown("<small style='color: #64748b;'>Pilih template skenario dibawah ini : </small>", unsafe_allow_html=True)
            
            if st.button("1. Rasio Ringan (Rasio 5%)", use_container_width=True):
                apply_ratio_preset(0.05, 2.5, 1.5, 0.1, False, False)
                st.rerun()
                
            if st.button("2. Rasio Pekat (Rasio 15%)", use_container_width=True):
                apply_ratio_preset(0.15, 2.5, 1.5, 0.1, False, False)
                st.rerun()
                
            if st.button("3. Tes Gangguan Laju Susu", use_container_width=True):
                apply_ratio_preset(0.10, 2.5, 1.5, 0.1, True, False)
                st.rerun()
                
            if st.button("4. Tes Gangguan Valve Tersumbat", use_container_width=True):
                apply_ratio_preset(0.10, 3.5, 2.0, 0.15, False, True)
                st.rerun()
        
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        
        # Manual Adjustments
        with st.container(border=True):
            st.markdown("<h4 style='margin-top:0; font-weight: 600;'>Parameter Kontrol</h4>", unsafe_allow_html=True)
            
            milk_input = st.slider(
                "Flow Susu Input (Nominal) [L/min]", 20.0, 90.0, key="ratio_milk_input", step=1.0,
                help="Flow_Susu_Input — laju aliran susu nominal (Wild Flow / PV). "
                     "Setpoint pewarna mengikuti nilai ini: SP = K_ratio × laju susu. "
                     "Saat 'Fluktuasi Laju Susu Ekstrem' aktif, nilai ini di-override oleh step disturbance."
            )
            st.caption("Laju susu masuk (Wild Flow). **↑** → setpoint & aliran pewarna ikut naik proporsional; **↓** → ikut turun.")
            sim.nominal_milk_flow = milk_input

            target_ratio = st.slider(
                "Target Rasio (Pewarna : Susu)", 0.02, 0.20, key="ratio_target_ratio",
                help="K_ratio = perbandingan laju Pewarna terhadap Susu. "
                     "Setpoint aliran pewarna dihitung otomatis: SP = K_ratio × laju susu. "
                     "Mis. 0.10 berarti pewarna = 10% dari laju susu."
            )
            st.caption("Perbandingan pewarna : susu (setpoint utama). **↑ rasio** → warna campuran makin pekat; **↓** → makin terang.")
            sim.target_ratio = target_ratio

            auto_mode = st.radio(
                "Mode Operasi:", ["Auto (PID)", "Manual"], key="ratio_mode",
                help="Auto = PID otomatis mengatur bukaan katup agar rasio sesuai target. "
                     "Manual = bukaan katup diatur sendiri (untuk uji open-loop)."
            ) == "Auto (PID)"
            st.caption("**Auto**: PID mengatur katup otomatis. **Manual**: katup diatur sendiri (uji tanpa kendali).")

            manual_valve = 0.0
            if not auto_mode:
                manual_valve = st.slider(
                    "Bukaan Katup Manual (%)", 0.0, 100.0, float(sim.valve_output), 1.0,
                    help="Posisi katup pewarna yang dipaksa secara manual (0% tertutup, 100% terbuka penuh)."
                )
                st.caption("Paksa bukaan katup pewarna. **↑ %** → aliran pewarna bertambah; **0%** → katup tertutup.")

            st.markdown("---")
            st.markdown("<h5 style='font-weight: 600; margin-bottom: 5px;'>Tuning PID (Slave Flow)</h5>", unsafe_allow_html=True)
            st.caption("Mengatur seberapa agresif katup pewarna mengejar setpoint aliran.")
            kp = st.slider(
                "Kp (Proportional)", 0.1, 10.0, key="ratio_kp",
                help="Proportional Gain — penguatan sebanding besar error (setpoint − aliran aktual). "
                     "Makin besar: respons makin cepat/agresif, tapi rawan overshoot & osilasi."
            )
            st.caption("Penguatan sebanding error. **↑ Kp** → koreksi lebih cepat tapi rawan *overshoot*/osilasi; **↓** → lambat tapi halus.")
            ki = st.slider(
                "Ki (Integral)", 0.0, 5.0, key="ratio_ki",
                help="Integral Gain — mengakumulasi error dari waktu ke waktu untuk menghapus "
                     "sisa error permanen (steady-state error/offset). Terlalu besar memperlambat & bikin osilasi."
            )
            st.caption("Menghapus sisa error tetap (*offset*). **↑ Ki** → offset cepat hilang tapi rawan osilasi; **↓** → bisa tersisa error permanen.")
            kd = st.slider(
                "Kd (Derivative)", 0.0, 2.0, key="ratio_kd",
                help="Derivative Gain — bereaksi pada laju perubahan pengukuran (derivative-on-measurement) "
                     "untuk meredam overshoot. Terlalu besar memperkuat noise sensor."
            )
            st.caption("Meredam berdasarkan laju perubahan. **↑ Kd** → *overshoot* teredam tapi noise menguat; **↓** → kurang redaman.")
            sim.set_pid_params(kp, ki, kd)
            
            st.markdown("---")
            st.markdown("<h5 style='font-weight: 600; margin-bottom: 5px;'>Aktifkan Gangguan Manual</h5>", unsafe_allow_html=True)
            dist_milk = st.checkbox("Fluktuasi Laju Susu Ekstrem", key="ratio_dist_milk")
            sim.milk_disturbance_active = dist_milk
            
            dist_clog = st.checkbox("Simulasi Katup Tersumbat", key="ratio_dist_clog")
            sim.clogging_factor = 0.4 if dist_clog else 1.0
            
            st.markdown("---")
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("Start", icon=":material/play_arrow:", type="primary", use_container_width=True):
                    st.session_state.sim_running = True
                    st.rerun()
            with btn_col2:
                if st.button("Pause", icon=":material/pause:", use_container_width=True):
                    st.session_state.sim_running = False
                    st.rerun()

            ctrl_col1, ctrl_col2 = st.columns(2)
            with ctrl_col1:
                if st.button("End & Simpan", icon=":material/stop_circle:", use_container_width=True):
                    param_str = f"Rasio={target_ratio:.2f}, Kp={kp}, Ki={ki}, Kd={kd}"
                    saved = save_test_result(
                        sim, "Ratio",
                        {"Target Rasio": target_ratio, "Kp": kp, "Ki": ki, "Kd": kd,
                         "Gangguan Susu": dist_milk, "Katup Tersumbat": dist_clog},
                        param_str
                    )
                    st.session_state.sim_running = False
                    st.toast("Hasil pengujian disimpan ke Riwayat." if saved
                             else "Belum ada data simulasi untuk disimpan.")
                    st.rerun()
            with ctrl_col2:
                if st.button("Reset Jalur", icon=":material/restart_alt:", use_container_width=True):
                    sim.reset()
                    st.session_state.sim_running = False
                    st.rerun()

    # Advance simulation if active
    if st.session_state.sim_running:
        for _ in range(5):
            sim.step(dt=0.1, auto_mode=auto_mode, manual_valve_input=manual_valve)

    # Right Column: Visuals & Charts
    with col2:
        curr_milk = sim.milk_flow
        curr_colorant = sim.colorant_flow
        curr_sp = sim.colorant_flow_sp
        curr_color = sim.sensor_color_reading
        curr_valv = sim.valve_position

        target_color = (target_ratio / (1.0 + target_ratio)) * 1000.0
        diff = abs(curr_color - target_color)
        is_ok = diff <= (target_color * 0.10)
        
        # Display Metrics Cards
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        
        with m_col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Aliran Susu (Wild)</div>
                <div class='metric-value'>{curr_milk:.1f}</div>
                <div class='metric-unit'>L / min</div>
            </div>
            """, unsafe_allow_html=True)
            
        with m_col2:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Aliran Pewarna (Slave)</div>
                <div class='metric-value'>{curr_colorant:.1f} <span style='font-size:0.9rem; color:#64748b;'>/ {curr_sp:.1f} SP</span></div>
                <div class='metric-unit'>L / min</div>
            </div>
            """, unsafe_allow_html=True)
            
        with m_col3:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Bukaan Katup</div>
                <div class='metric-value'>{curr_valv:.1f}%</div>
                <div class='metric-unit'>Posisi Katup Pewarna</div>
            </div>
            """, unsafe_allow_html=True)
            
        with m_col4:
            val_text = "<span class='status-badge status-ok'>SESUAI</span>" if is_ok else "<span class='status-badge status-error'>DEVIASI</span>"
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Sensor TCS3200</div>
                <div class='metric-value'>{curr_color:.1f}</div>
                <div class='metric-unit'>Intensitas Campuran : {val_text}</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Draw physical mixing visualization
        act_ratio = curr_colorant / (curr_milk + curr_colorant) if (curr_milk + curr_colorant) > 0.1 else 0.0
        
        # Dynamically calculate mixing color (white mixed with black ink)
        color_val = int(max(0, min(255, 255 - act_ratio * 1200.0)))
        liq_color = f"rgb({color_val}, {color_val}, {color_val})"
        
        colorant_opacity = min(1.0, curr_colorant / 10.0) if curr_colorant > 0.05 else 0.0
        
        st.markdown("<h3 style='margin-top:10px; font-weight: 600;'>Visualisasi Proses Pencampuran</h3>", unsafe_allow_html=True)
        st.markdown(
            "<small style='color: #64748b; display:block; margin-bottom:15px;'>"
            "Visualisasi di bawah menyimulasikan aliran susu putih bersih (kiri) bertemu cairan pewarna hitam pekat (kanan) "
            "masuk ke dalam tangki pencampuran. <b>Warna cairan di dalam tangki akan berubah warna secara dinamis "
            "mengikuti perbandingan aktual kedua bahan</b></small>", unsafe_allow_html=True
        )
        
        viz_html = f"""
        <div style="background-color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-end; height: 100px; margin-bottom: 0;">
                <!-- Pipa Susu (White Flow) -->
                <div style="width: 40%; text-align: left;">
                    <div style="font-weight:500; color:#475569; font-size:0.8rem; margin-bottom: 5px;">Pipa Susu (Wild Flow)</div>
                    <div class="pipe-horizontal">
                        <div class="pipe-liquid-flow" style="background: linear-gradient(90deg, transparent, rgba(255,255,255,0.9), transparent); background-size: 40px 100%;"></div>
                    </div>
                </div>
                
                <!-- Pipa Pewarna (Dark Flow) -->
                <div style="width: 40%; text-align: right;">
                    <div style="font-weight:500; color:#475569; font-size:0.8rem; margin-bottom: 5px;">Pipa Pewarna - Valve: {curr_valv:.1f}%</div>
                    <div class="pipe-horizontal">
                        <div class="pipe-liquid-flow" style="background: linear-gradient(270deg, transparent, rgba(15,23,42,{colorant_opacity:.2f}), transparent); background-size: 40px 100%;"></div>
                    </div>
                </div>
            </div>
            
            <div style="display: flex; justify-content: center; margin-top: 15px;">
                <div style="width: 50%;">
                    <div style="text-align: center; color: #475569; font-weight:600; font-size: 0.8rem; margin-bottom:5px;">TANGKI PENCAMPURAN</div>
                    <div class="tank-container">
                        <div class="tank-grid"></div>
                        <div class="tank-liquid" style="height: 70%; background: linear-gradient(180deg, {liq_color} 0%, rgba(0, 0, 0, 0.15) 100%);"></div>
                    </div>
                    <!-- Sensor TCS3200 -->
                    <div style="display: flex; justify-content: center; margin-top: -10px; position: relative; z-index: 10;">
                        <div style="background-color: #0f172a; color: #ffffff; padding: 4px 12px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; border: 1px solid #0f172a;">
                            SENSOR WARNA TCS3200 (Downstream)
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
        st.html(textwrap.dedent(viz_html))
        
        # Charts
        st.markdown("<h3 style='font-weight: 600;'>Grafik Analisa Sistem</h3>", unsafe_allow_html=True)
        
        if len(sim.history["time"]) > 0:
            df = pd.DataFrame(sim.history)
            df = df.tail(150)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["time"], y=df["milk_flow"], mode='lines', name='Aliran Susu (L/min)', line=dict(color='#0f172a', width=2)))
            fig.add_trace(go.Scatter(x=df["time"], y=df["colorant_flow"], mode='lines', name='Aliran Pewarna (L/min)', line=dict(color='#64748b', width=2.5)))
            fig.add_trace(go.Scatter(x=df["time"], y=df["colorant_flow_sp"], mode='lines', name='Setpoint Pewarna (SP)', line=dict(color='#94a3b8', width=1.5, dash='dash')))
            
            fig.update_layout(
                title="Laju Aliran Bahan Pencampur",
                xaxis_title="Waktu (detik)",
                yaxis_title="Laju Aliran (L/min)",
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=40, r=40, t=45, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df["time"], y=df["valve_position"], mode='lines', name='Bukaan Katup (%)', line=dict(color='#0f172a', width=2)))
            fig2.add_trace(go.Scatter(x=df["time"], y=df["actual_ratio"]*100, mode='lines', name='Rasio Aktual (%)', line=dict(color='#64748b', width=2)))
            fig2.add_trace(go.Scatter(x=df["time"], y=df["target_ratio"]*100, mode='lines', name='Target Rasio (%)', line=dict(color='#94a3b8', width=1.5, dash='dash')))
            
            fig2.update_layout(
                title="Respons Bukaan Katup vs Deviasi Rasio",
                xaxis_title="Waktu (detik)",
                yaxis_title="Persen (%)",
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=40, r=40, t=45, b=40)
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Tekan tombol **Start** atau klik salah satu Preset di panel kiri untuk menjalankan simulasi.", icon=":material/info:")

# ----------------------------------------------------
# PAGE: CASCADE CONTROL
# ----------------------------------------------------
elif st.session_state.current_page == "cascade":
    st.markdown("<h1 style='color: #0f172a; font-weight: 700;'>Sistem Kontrol Bertingkat (Cascade Control)</h1>", unsafe_allow_html=True)
    st.markdown(
        "Sistem Kontrol Bertingkat menghubungkan dua loop PID secara seri. **Loop Luar (Primary)** mengontrol "
        "warna produk akhir berdasarkan data sensor TCS3200 dengan mengeluarkan nilai Target Aliran. **Loop Dalam (Secondary)** "
        "mengendalikan katup aliran pewarna agar secepat mungkin menyamai target aliran tersebut untuk meredam gangguan jalur"
    )
    st.markdown("---")
    
    col1, col2 = st.columns([1, 3])
    sim = st.session_state.cascade_sim
    
    # Left Column: Control Panel
    with col1:
        # Template Preset Buttons for Fast Demo
        with st.container(border=True):
            st.markdown("<h4 style='margin-top:0; font-weight: 600;'>Presets & Skenario Simulasi</h4>", unsafe_allow_html=True)
            st.markdown("<small style='color: #64748b;'>Pilih template skenario dibawah ini :</small>", unsafe_allow_html=True)
            
            if st.button("1. Target Warna Ringan (50)", use_container_width=True):
                apply_cascade_preset(50.0, 0.10, 0.02, 0.0, 2.0, 1.2, 0.05, False, False)
                st.rerun()
                
            if st.button("2. Target Warna Gelap (120)", use_container_width=True):
                apply_cascade_preset(120.0, 0.18, 0.04, 0.01, 2.8, 1.8, 0.10, False, False)
                st.rerun()
                
            if st.button("3. Tes Redam Tekanan Drop", use_container_width=True):
                apply_cascade_preset(100.0, 0.15, 0.03, 0.01, 2.5, 1.5, 0.10, False, True)
                st.rerun()
                
            if st.button("4. Gangguan Aliran & Susu", use_container_width=True):
                apply_cascade_preset(100.0, 0.20, 0.04, 0.01, 3.0, 2.0, 0.10, True, True)
                st.rerun()
        
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        
        # Manual Adjustments
        with st.container(border=True):
            st.markdown("<h4 style='margin-top:0; font-weight: 600;'>Parameter Kontrol</h4>", unsafe_allow_html=True)
            
            target_color = st.slider(
                "Target Intensitas Warna (0-200)", 20.0, 200.0, key="cascade_target_color",
                help="Setpoint utama (SP) sistem: nilai intensitas warna produk akhir yang dibaca "
                     "sensor TCS3200. Loop luar berusaha menjaga warna campuran sama dengan nilai ini."
            )
            st.caption("Setpoint warna produk akhir (dibaca TCS3200). **↑ nilai** → produk makin gelap; **↓** → makin terang.")
            sim.target_color = target_color

            auto_mode = st.radio(
                "Mode Operasi:", ["Auto (Cascade PID)", "Manual"], key="cascade_mode",
                help="Auto = dua loop PID (warna→aliran) bekerja bertingkat otomatis. "
                     "Manual = bukaan katup diatur sendiri."
            ) == "Auto (Cascade PID)"
            st.caption("**Auto**: dua loop PID (warna → aliran) bekerja bertingkat. **Manual**: katup diatur sendiri.")

            manual_valve = 0.0
            if not auto_mode:
                manual_valve = st.slider(
                    "Bukaan Katup Manual (%)", 0.0, 100.0, float(sim.valve_output), 1.0,
                    help="Posisi katup pewarna yang dipaksa manual (0% tertutup, 100% terbuka penuh)."
                )
                st.caption("Paksa bukaan katup pewarna. **↑ %** → aliran pewarna bertambah; **0%** → katup tertutup.")

            st.markdown("---")
            st.markdown("<h5 style='font-weight: 600; margin-bottom: 5px;'>Loop Luar (Primary - Color)</h5>", unsafe_allow_html=True)
            st.caption("Loop lambat: membaca warna TCS3200 (PV) → menghasilkan setpoint laju pewarna untuk loop dalam.")
            kp_out = st.slider(
                "Kp (Outer)", 0.01, 1.0, key="cas_kp_out",
                help="Proportional Gain Loop Luar — penguatan error warna (target − warna terukur). "
                     "Outputnya menjadi target laju aliran pewarna. Dibuat kecil karena ada transport delay."
            )
            st.caption("Penguatan error warna. **↑ Kp** → loop warna agresif tapi rawan osilasi (ada *dead time*); **↓** → lambat tapi stabil.")
            ki_out = st.slider(
                "Ki (Outer)", 0.0, 0.5, key="cas_ki_out",
                help="Integral Gain Loop Luar — menghapus offset warna akhir agar benar-benar mencapai target."
            )
            st.caption("Menghapus *offset* warna akhir. **↑ Ki** → target warna cepat tercapai tapi rawan osilasi lambat; **↓** → bisa sisa selisih warna.")
            kd_out = st.slider(
                "Kd (Outer)", 0.0, 0.2, key="cas_kd_out",
                help="Derivative Gain Loop Luar — meredam osilasi warna akibat keterlambatan (dead time) sensor."
            )
            st.caption("Meredam osilasi warna. **↑ Kd** → ayunan warna lebih kalem; terlalu besar → noise sensor menguat.")

            st.markdown("<h5 style='font-weight: 600; margin-bottom: 5px;'>Loop Dalam (Secondary - Flow)</h5>", unsafe_allow_html=True)
            st.caption("Loop cepat: membaca laju pewarna (PV) → mengatur katup mengejar setpoint dari loop luar.")
            kp_in = st.slider(
                "Kp (Inner)", 0.1, 10.0, key="cas_kp_in",
                help="Proportional Gain Loop Dalam — penguatan error aliran (setpoint loop luar − laju aktual). "
                     "Dibuat besar/agresif agar cepat meredam gangguan tekanan sebelum mempengaruhi warna."
            )
            st.caption("Penguatan error aliran. **↑ Kp** → aliran cepat ikut target & gangguan tekanan teredam, tapi rawan osilasi; **↓** → lambat.")
            ki_in = st.slider(
                "Ki (Inner)", 0.0, 5.0, key="cas_ki_in",
                help="Integral Gain Loop Dalam — menghapus sisa error laju aliran pewarna."
            )
            st.caption("Menghapus sisa error laju aliran. **↑ Ki** → laju tepat ke setpoint tapi rawan osilasi; **↓** → bisa tersisa selisih.")
            kd_in = st.slider(
                "Kd (Inner)", 0.0, 2.0, key="cas_kd_in",
                help="Derivative Gain Loop Dalam — meredam lonjakan aliran (derivative-on-measurement)."
            )
            st.caption("Meredam lonjakan aliran. **↑ Kd** → respons lebih halus; terlalu besar → memperkuat noise pengukuran.")

            sim.set_pid_params(kp_out, ki_out, kd_out, kp_in, ki_in, kd_in)
            
            st.markdown("---")
            st.markdown("<h5 style='font-weight: 600; margin-bottom: 5px;'>Aktifkan Gangguan Manual</h5>", unsafe_allow_html=True)
            dist_milk = st.checkbox("Fluktuasi Laju Susu Ekstrem", key="cascade_dist_milk")
            sim.milk_disturbance_active = dist_milk
            
            dist_pressure = st.checkbox("Tekanan Pewarna Drop 50%", key="cascade_dist_pressure")
            sim.pressure_disturbance_active = dist_pressure
            
            st.markdown("---")
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("Start", icon=":material/play_arrow:", type="primary", use_container_width=True):
                    st.session_state.sim_running = True
                    st.rerun()
            with btn_col2:
                if st.button("Pause", icon=":material/pause:", use_container_width=True):
                    st.session_state.sim_running = False
                    st.rerun()

            ctrl_col1, ctrl_col2 = st.columns(2)
            with ctrl_col1:
                if st.button("End & Simpan", icon=":material/stop_circle:", use_container_width=True):
                    param_str = (f"Warna={target_color:.0f}, Kp_o={kp_out}, Ki_o={ki_out}, "
                                 f"Kd_o={kd_out}, Kp_i={kp_in}, Ki_i={ki_in}, Kd_i={kd_in}")
                    saved = save_test_result(
                        sim, "Cascade",
                        {"Target Warna": target_color,
                         "Kp Outer": kp_out, "Ki Outer": ki_out, "Kd Outer": kd_out,
                         "Kp Inner": kp_in, "Ki Inner": ki_in, "Kd Inner": kd_in,
                         "Gangguan Susu": dist_milk, "Tekanan Drop": dist_pressure},
                        param_str
                    )
                    st.session_state.sim_running = False
                    st.toast("Hasil pengujian disimpan ke Riwayat." if saved
                             else "Belum ada data simulasi untuk disimpan.")
                    st.rerun()
            with ctrl_col2:
                if st.button("Reset Jalur", icon=":material/restart_alt:", use_container_width=True):
                    sim.reset()
                    st.session_state.sim_running = False
                    st.rerun()

    # Advance simulation if active
    if st.session_state.sim_running:
        for _ in range(5):
            sim.step(dt=0.1, auto_mode=auto_mode, manual_valve_input=manual_valve)

    # Right Column: Visuals & Charts
    with col2:
        curr_milk = sim.milk_flow
        curr_colorant = sim.colorant_flow
        curr_sp = sim.colorant_flow_sp
        curr_color = sim.sensor_color_reading
        curr_valv = sim.valve_position

        is_ok = abs(curr_color - target_color) <= max(3.0, target_color * 0.05)
        
        # Display Metrics Cards
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        
        with m_col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Aliran Susu (Wild)</div>
                <div class='metric-value'>{curr_milk:.1f}</div>
                <div class='metric-unit'>L / min</div>
            </div>
            """, unsafe_allow_html=True)
            
        with m_col2:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Aliran Pewarna (Slave)</div>
                <div class='metric-value'>{curr_colorant:.1f} <span style='font-size:0.9rem; color:#64748b;'>/ {curr_sp:.1f} SP</span></div>
                <div class='metric-unit'>L / min (Target Loop Luar)</div>
            </div>
            """, unsafe_allow_html=True)
            
        with m_col3:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Bukaan Katup</div>
                <div class='metric-value'>{curr_valv:.1f}%</div>
                <div class='metric-unit'>Posisi Katup Pewarna</div>
            </div>
            """, unsafe_allow_html=True)
            
        with m_col4:
            val_text = "<span class='status-badge status-ok'>STABIL</span>" if is_ok else "<span class='status-badge status-error'>DEVIASI</span>"
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Sensor TCS3200</div>
                <div class='metric-value'>{curr_color:.1f} <span style='font-size:0.9rem; color:#64748b;'>/ {target_color:.1f} SP</span></div>
                <div class='metric-unit'>Warna Umpan Balik | {val_text}</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Draw physical mixing visualization
        act_ratio = curr_colorant / (curr_milk + curr_colorant) if (curr_milk + curr_colorant) > 0.1 else 0.0
        
        # Dynamically calculate mixing color (white mixed with black ink)
        color_val = int(max(0, min(255, 255 - act_ratio * 1200.0)))
        liq_color = f"rgb({color_val}, {color_val}, {color_val})"
        
        colorant_opacity = min(1.0, curr_colorant / 10.0) if curr_colorant > 0.05 else 0.0
        
        st.markdown("<h3 style='margin-top:10px; font-weight: 600;'>Visualisasi Proses Pencampuran</h3>", unsafe_allow_html=True)
        st.markdown(
            "<small style='color: #64748b; display:block; margin-bottom:15px;'>"
            "Pada mode Bertingkat (Cascade), loop PID luar membaca sensor TCS3200 downstream untuk terus menghitung "
            "laju aliran pewarna baru yang ideal. <b>Warna cairan di dalam tangki berubah warna secara dinamis "
            "mengikuti pencampuran susu (putih) dan pewarna (hitam) secara real-time</b></small>", unsafe_allow_html=True
        )
        
        viz_html = f"""
        <div style="background-color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-end; height: 100px; margin-bottom: 0;">
                <!-- Pipa Susu (White Flow) -->
                <div style="width: 40%; text-align: left;">
                    <div style="font-weight:500; color:#475569; font-size:0.8rem; margin-bottom: 5px;">Pipa Susu (Wild Flow)</div>
                    <div class="pipe-horizontal">
                        <div class="pipe-liquid-flow" style="background: linear-gradient(90deg, transparent, rgba(255,255,255,0.9), transparent); background-size: 40px 100%;"></div>
                    </div>
                </div>
                
                <!-- Pipa Pewarna (Dark Flow) -->
                <div style="width: 40%; text-align: right;">
                    <div style="font-weight:500; color:#475569; font-size:0.8rem; margin-bottom: 5px;">Pipa Pewarna - Valve: {curr_valv:.1f}%</div>
                    <div class="pipe-horizontal">
                        <div class="pipe-liquid-flow" style="background: linear-gradient(270deg, transparent, rgba(15,23,42,{colorant_opacity:.2f}), transparent); background-size: 40px 100%;"></div>
                    </div>
                </div>
            </div>
            
            <div style="display: flex; justify-content: center; margin-top: 15px;">
                <div style="width: 50%;">
                    <div style="text-align: center; color: #475569; font-weight:600; font-size: 0.8rem; margin-bottom:5px;">TANGKI PENCAMPURAN</div>
                    <div class="tank-container">
                        <div class="tank-grid"></div>
                        <div class="tank-liquid" style="height: 70%; background: linear-gradient(180deg, {liq_color} 0%, rgba(0, 0, 0, 0.15) 100%);"></div>
                    </div>
                    <!-- Sensor TCS3200 -->
                    <div style="display: flex; justify-content: center; margin-top: -10px; position: relative; z-index: 10;">
                        <div style="background-color: #0f172a; color: #ffffff; padding: 4px 12px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; border: 1px solid #0f172a;">
                            SENSOR WARNA TCS3200 (Downstream)
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
        st.html(textwrap.dedent(viz_html))
        
        # Charts
        st.markdown("<h3 style='font-weight: 600;'>Grafik Analisa Sistem Bertingkat</h3>", unsafe_allow_html=True)
        
        if len(sim.history["time"]) > 0:
            df = pd.DataFrame(sim.history)
            df = df.tail(150)
            
            # Flow rates chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["time"], y=df["milk_flow"], mode='lines', name='Aliran Susu (L/min)', line=dict(color='#0f172a', width=2)))
            fig.add_trace(go.Scatter(x=df["time"], y=df["colorant_flow"], mode='lines', name='Aliran Pewarna (L/min)', line=dict(color='#64748b', width=2.5)))
            fig.add_trace(go.Scatter(x=df["time"], y=df["colorant_flow_sp"], mode='lines', name='Setpoint Aliran (Flow SP)', line=dict(color='#94a3b8', width=1.5, dash='dash')))
            
            fig.update_layout(
                title="Laju Aliran (Secondary Loop)",
                xaxis_title="Waktu (detik)",
                yaxis_title="Laju Aliran (L/min)",
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=40, r=40, t=45, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Color measurement chart
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df["time"], y=df["sensor_color"], mode='lines', name='Warna Sensor TCS3200', line=dict(color='#0f172a', width=2.5)))
            fig2.add_trace(go.Scatter(x=df["time"], y=df["target_color"], mode='lines', name='Target Warna SP', line=dict(color='#94a3b8', width=1.5, dash='dash')))
            
            fig2.update_layout(
                title="Kontrol Kualitas Warna Akhir (Primary Loop)",
                xaxis_title="Waktu (detik)",
                yaxis_title="Nilai Warna Sensor (0-200)",
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=40, r=40, t=45, b=40)
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            # Valve position
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df["time"], y=df["valve_position"], mode='lines', name='Bukaan Katup (%)', line=dict(color='#0f172a', width=2)))
            
            fig3.update_layout(
                title="Bukaan Katup Kendali (Manipulated Variable)",
                xaxis_title="Waktu (detik)",
                yaxis_title="Bukaan Katup (%)",
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=40, r=40, t=45, b=40)
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Tekan tombol **Start** atau klik salah satu Preset di panel kiri untuk menjalankan simulasi.", icon=":material/info:")


elif st.session_state.current_page == "scl":
    st.markdown("<h1 style='color: #0f172a; font-weight: 700;'>Template Kode SCL Siemens PCS 7</h1>", unsafe_allow_html=True)
    st.markdown(
        "Berikut adalah kode program SCL (Structured Control Language) terstruktur untuk Siemens PCS 7 "
        "(atau STEP 7 / TIA Portal) yang mengimplementasikan logika kontrol yang sama dengan simulator"
    )
    st.markdown("---")
    
    tab_code1, tab_code2 = st.tabs(["Sistem Kontrol Rasio (Ratio Control)", "Sistem Kontrol Bertingkat (Cascade Control)"])
    
    with tab_code1:
        st.markdown("### Kode SCL: FB_RatioControl")
        st.code(scl_generator.get_ratio_control_scl(), language="pascal")
        st.info(
            "**Cara Integrasi di Siemens PCS 7:**\n"
            "1. Buat source file SCL baru di TIA Portal / STEP 7.\n"
            "2. Tempel kode di atas ke dalamnya.\n"
            "3. Lakukan kompilasi untuk menghasilkan Function Block (FB).\n"
            "4. Masukkan FB tersebut ke dalam program CFC (Continuous Function Chart) Anda."
        )
        
    with tab_code2:
        st.markdown("### Kode SCL: FB_CascadeControl")
        st.code(scl_generator.get_cascade_control_scl(), language="pascal")
        st.info(
            "**Mengapa menggunakan Blok Tunggal untuk Cascade?**\n"
            "Menggabungkannya dalam satu FB SCL sangat baik untuk menghemat memori program (work memory PLC), "
            "menyederhanakan penanganan Anti-Windup antar-loop, serta memastikan propagasi mode Manual/Auto "
            "antara loop luar dan dalam berjalan sinkron."
        )


elif st.session_state.current_page == "handbook":
    st.markdown("<h1 style='color: #0f172a; font-weight: 700;'>Panduan & Konsep Sistem Kontrol</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("""
    ### 1. Sistem Kontrol Rasio (Ratio Control)
    
    Ratio Control digunakan saat kita ingin mempertahankan perbandingan konstan antara dua aliran:
    - **Wild Flow (Aliran Bebas/Liar)**: Laju pasokan susu dari tangki hulu yang berubah secara acak (tidak dapat diubah oleh sistem kontrol).
    - **Controlled Flow (Aliran Terkendali)**: Laju aliran pewarna yang diatur bukaan katupnya secara otomatis agar rasionya tetap terhadap aliran susu.
    
    **Diagram Logika:**
    ```
    Aliran Susu (Wild) ─────────► [ × Rasio ] ──► Setpoint Aliran Pewarna ──► [ PID Controller ] ──► Katup Pewarna ──► Aliran Pewarna (PV)
    ```
    
    - **Kelebihan**: Sangat cepat bereaksi terhadap perubahan mendadak pada laju aliran susu.
    - **Kekurangan**: Tidak mendeteksi jika konsentrasi pewarna itu sendiri berubah (misal tangki pewarna mulai encer).
    
    ---
    
    ### 2. Sistem Kontrol Bertingkat (Cascade Control)
    
    Menggabungkan dua loop kontrol PID untuk mengatasi keterlambatan deteksi warna (transport delay) dan menstabilkan gangguan aliran dengan cepat:
    - **Loop Luar (Primary/Outer Loop)**: Membaca sensor warna TCS3200 di bagian hilir (downstream). PID akan menghitung target laju aliran pewarna agar warna akhir sesuai.
    - **Loop Dalam (Secondary/Inner Loop)**: Membaca laju aliran pewarna (flow transmitter) dan mengendalikan katup bukaan pewarna secara cepat agar langsung mencapai target aliran dari loop luar.
      
    **Diagram Logika:**
    ```
    Target Warna (SP) ──► [ PID Luar ] ──► Flow SP ──► [ PID Dalam ] ──► Katup ──► Laju Aliran ──► Tangki ──► (Waktu Tunda) ──► Sensor TCS3200 (PV) 
    ```
    
    - **Mengapa ini lebih baik?**
      Jika tekanan pasokan pewarna tiba-tiba turun, loop dalam (aliran) akan langsung mendeteksi penurunan laju aliran pewarna dan langsung membuka katup lebih lebar. Loop luar tidak perlu menunggu warna campuran yang salah sampai ke sensor warna downstream untuk melakukan koreksi.

    ---

    ### 3. Implementasi Algoritma PID (sesuai kode simulator)

    Setiap loop memakai PID diskret dengan periode cuplik (sample time) **Cycle = 0.1 s**:

    ```
    Error   = Setpoint − PV
    P       = Kp × Error
    Integral = Integral + Error × Cycle ;  I = Ki × Integral
    D       = −Kd × (PV − PV_sebelumnya) / Cycle      (Derivative on Measurement)
    Output  = P + I + D   (dibatasi/clamp 0–100% untuk katup)
    ```

    - **Kp (Proportional)** — penguatan sebanding besar error. Cepat tapi rawan overshoot.
    - **Ki (Integral)** — menghapus *offset*/steady-state error dengan mengakumulasi error.
    - **Kd (Derivative)** — meredam dengan melihat laju perubahan. Memakai **Derivative on Measurement** (turunan dari PV, bukan error) agar tidak terjadi *derivative kick* saat setpoint berubah dan tidak memperkuat noise.
    - **Anti-Windup** — saat output katup tersaturasi (0% atau 100%), akumulasi integral di-*clamp* (dikembalikan) agar tidak menumpuk dan memperlambat pemulihan.

    > Catatan: template kode SCL Siemens PCS 7 pada halaman *Template Kode* menggunakan algoritma yang sama persis, sehingga simulator dan PLC konsisten.
    """)

# ----------------------------------------------------
# PAGE: HISTORY (Riwayat Pengujian)
# ----------------------------------------------------
elif st.session_state.current_page == "history":
    st.markdown("<h1 style='color: #0f172a; font-weight: 700;'>Riwayat Pengujian</h1>", unsafe_allow_html=True)
    st.markdown(
        "Kumpulan hasil simulasi yang disimpan via tombol **End & Simpan**. "
        "Setiap entri menyimpan parameter, metrik performa, tabel data lengkap, dan grafiknya untuk dianalisis."
    )
    st.markdown("---")

    history = st.session_state.test_history

    if not history:
        st.info(
            "Belum ada hasil pengujian tersimpan. Jalankan simulasi pada halaman Ratio/Cascade, "
            "lalu tekan tombol **End & Simpan** untuk merekam hasilnya ke sini.",
            icon=":material/history:"
        )
    else:
        # --- Tabel ringkasan seluruh pengujian ---
        st.markdown("<h3 style='font-weight: 600;'>Ringkasan Seluruh Pengujian</h3>", unsafe_allow_html=True)
        rows = []
        for rec in history:
            s = rec["summary"]
            rows.append({
                "ID": rec["id"],
                "Waktu": rec["timestamp"],
                "Jenis": rec["type"],
                "Durasi (s)": s["durasi"],
                "Jumlah Data": s["n"],
                s["mae_label"] if rec["type"] == "Ratio" else "MAE": s["mae"],
                "Validasi OK (%)": s["val_pct"],
                "Parameter": rec["param_str"],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        c_clear, _ = st.columns([1, 3])
        with c_clear:
            if st.button("Hapus Semua Riwayat", icon=":material/delete:", use_container_width=True):
                st.session_state.test_history = []
                st.toast("Seluruh riwayat pengujian dihapus.")
                st.rerun()

        st.markdown("---")

        # --- Detail satu pengujian ---
        st.markdown("<h3 style='font-weight: 600;'>Detail Pengujian</h3>", unsafe_allow_html=True)
        options = {f"#{rec['id']} — {rec['type']} ({rec['timestamp']})": rec["id"] for rec in reversed(history)}
        selected_label = st.selectbox("Pilih pengujian:", list(options.keys()))
        selected_id = options[selected_label]
        rec = next(r for r in history if r["id"] == selected_id)
        data = rec["data"]
        s = rec["summary"]

        # Kartu metrik performa
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Jenis Kontrol</div>"
                        f"<div class='metric-value' style='font-size:1.6rem;'>{rec['type']}</div>"
                        f"<div class='metric-unit'>{s['n']} titik data</div></div>", unsafe_allow_html=True)
        with mc2:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Durasi Uji</div>"
                        f"<div class='metric-value'>{s['durasi']}</div>"
                        f"<div class='metric-unit'>detik simulasi</div></div>", unsafe_allow_html=True)
        with mc3:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>{s['mae_label']}</div>"
                        f"<div class='metric-value'>{s['mae']}</div>"
                        f"<div class='metric-unit'>rata-rata error absolut</div></div>", unsafe_allow_html=True)
        with mc4:
            badge = "status-ok" if s["val_pct"] >= 70 else "status-error"
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Validasi Lolos</div>"
                        f"<div class='metric-value'>{s['val_pct']}%</div>"
                        f"<div class='metric-unit'><span class='status-badge {badge}'>TCS3200</span></div></div>",
                        unsafe_allow_html=True)

        # Parameter yang digunakan
        with st.expander("Parameter yang digunakan", expanded=False):
            st.json(rec["params"])

        df = pd.DataFrame(data)

        # Grafik sesuai jenis kontrol
        st.markdown("<h4 style='font-weight: 600; margin-top:10px;'>Grafik Hasil Pengujian</h4>", unsafe_allow_html=True)
        if rec["type"] == "Ratio":
            figh = go.Figure()
            figh.add_trace(go.Scatter(x=df["time"], y=df["milk_flow"], mode='lines', name='Aliran Susu (L/min)', line=dict(color='#0f172a', width=2)))
            figh.add_trace(go.Scatter(x=df["time"], y=df["colorant_flow"], mode='lines', name='Aliran Pewarna (L/min)', line=dict(color='#64748b', width=2.5)))
            figh.add_trace(go.Scatter(x=df["time"], y=df["colorant_flow_sp"], mode='lines', name='Setpoint Pewarna', line=dict(color='#94a3b8', width=1.5, dash='dash')))
            figh.update_layout(title="Laju Aliran Bahan", xaxis_title="Waktu (detik)", yaxis_title="L/min",
                               template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=40, t=45, b=40))
            st.plotly_chart(figh, use_container_width=True)

            figh2 = go.Figure()
            figh2.add_trace(go.Scatter(x=df["time"], y=df["actual_ratio"]*100, mode='lines', name='Rasio Aktual (%)', line=dict(color='#0f172a', width=2)))
            figh2.add_trace(go.Scatter(x=df["time"], y=df["target_ratio"]*100, mode='lines', name='Target Rasio (%)', line=dict(color='#94a3b8', width=1.5, dash='dash')))
            figh2.update_layout(title="Rasio Aktual vs Target", xaxis_title="Waktu (detik)", yaxis_title="Rasio (%)",
                                template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=40, t=45, b=40))
            st.plotly_chart(figh2, use_container_width=True)
        else:
            figh = go.Figure()
            figh.add_trace(go.Scatter(x=df["time"], y=df["sensor_color"], mode='lines', name='Warna Sensor TCS3200', line=dict(color='#0f172a', width=2.5)))
            figh.add_trace(go.Scatter(x=df["time"], y=df["target_color"], mode='lines', name='Target Warna', line=dict(color='#94a3b8', width=1.5, dash='dash')))
            figh.update_layout(title="Kontrol Kualitas Warna", xaxis_title="Waktu (detik)", yaxis_title="Nilai Warna",
                               template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=40, t=45, b=40))
            st.plotly_chart(figh, use_container_width=True)

            figh2 = go.Figure()
            figh2.add_trace(go.Scatter(x=df["time"], y=df["colorant_flow"], mode='lines', name='Aliran Pewarna (L/min)', line=dict(color='#64748b', width=2.5)))
            figh2.add_trace(go.Scatter(x=df["time"], y=df["colorant_flow_sp"], mode='lines', name='Setpoint Aliran', line=dict(color='#94a3b8', width=1.5, dash='dash')))
            figh2.add_trace(go.Scatter(x=df["time"], y=df["valve_position"], mode='lines', name='Bukaan Katup (%)', line=dict(color='#0f172a', width=2)))
            figh2.update_layout(title="Aliran Pewarna & Bukaan Katup", xaxis_title="Waktu (detik)", yaxis_title="Nilai",
                                template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=40, t=45, b=40))
            st.plotly_chart(figh2, use_container_width=True)

        # Tabel data lengkap + unduh CSV
        st.markdown("<h4 style='font-weight: 600;'>Tabel Data Lengkap</h4>", unsafe_allow_html=True)
        df_show = df.round(3)
        st.dataframe(df_show, use_container_width=True, height=300)
        st.download_button(
            "Unduh Data (CSV)",
            data=df_show.to_csv(index=False).encode("utf-8"),
            file_name=f"pengujian_{rec['type']}_{rec['id']}.csv",
            mime="text/csv",
            icon=":material/download:"
        )

# ----------------------------------------------------
# bottom of file rerun trigger for real-time simulation
# ----------------------------------------------------
if st.session_state.sim_running and st.session_state.current_page in ("ratio", "cascade"):
    time.sleep(0.08)
    st.rerun()
