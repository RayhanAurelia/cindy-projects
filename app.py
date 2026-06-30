import streamlit as st
import time
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

# Load CSS
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# JS to intercept Streamlit's 'c' key shortcut (Clear Caches) and 'r' (Rerun) so they don't block Ctrl+C/copying
st.components.v1.html(
    """
    <script>
    const parentDoc = window.parent.document;
    parentDoc.addEventListener("keydown", function(e) {
        // Block standalone 'c' or 'r' from reaching Streamlit's key handlers
        if ((e.key.toLowerCase() === 'c' || e.key.toLowerCase() === 'r') && !e.ctrlKey && !e.metaKey && !e.altKey) {
            const active = parentDoc.activeElement;
            if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable)) {
                return;
            }
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

# Initialize session state variables for Ratio Control sliders
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

if st.sidebar.button("📊 Sistem Kontrol Rasio", type=btn_ratio_type, use_container_width=True):
    st.session_state.current_page = "ratio"
    st.rerun()

if st.sidebar.button("🔄 Sistem Kontrol Bertingkat", type=btn_cascade_type, use_container_width=True):
    st.session_state.current_page = "cascade"
    st.rerun()

if st.sidebar.button("📄 Template Kode SCL PCS 7", type=btn_scl_type, use_container_width=True):
    st.session_state.current_page = "scl"
    st.rerun()

if st.sidebar.button("📘 Panduan Sistem Kontrol", type=btn_handbook_type, use_container_width=True):
    st.session_state.current_page = "handbook"
    st.rerun()

st.sidebar.markdown("---")
# Manual Clear Caches button inside sidebar as requested
if st.sidebar.button("🧹 Hapus Cache Fungsi (Clear Cache)", use_container_width=True):
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
# PAGE: RATIO CONTROL
# ----------------------------------------------------
if st.session_state.current_page == "ratio":
    st.markdown("<h1 style='color: #0f172a; font-weight: 700;'>📊 Sistem Kontrol Rasio (Ratio Control)</h1>", unsafe_allow_html=True)
    st.markdown(
        "Sistem Kontrol Rasio menjaga perbandingan tetap antara laju aliran **Susu (Wild Flow)** "
        "dan laju aliran **Pewarna (Slave Flow)**. Logika ini secara otomatis menyesuaikan laju aliran pewarna "
        "mengikuti fluktuasi laju susu agar kualitas pencampuran tetap konsisten."
    )
    st.markdown("---")
    
    col1, col2 = st.columns([1, 3])
    sim = st.session_state.ratio_sim
    
    # Left Column: Control Panel
    with col1:
        # Template Preset Buttons for Fast Demo
        with st.container(border=True):
            st.markdown("<h4 style='margin-top:0; font-weight: 600;'>⚡ Presets & Skenario Cepat</h4>", unsafe_allow_html=True)
            st.markdown("<small style='color: #64748b;'>Pilih template skenario langsung untuk memulai simulasi:</small>", unsafe_allow_html=True)
            
            if st.button("🍼 1. Rasio Ringan (Rasio 5%)", use_container_width=True):
                apply_ratio_preset(0.05, 2.5, 1.5, 0.1, False, False)
                st.rerun()
                
            if st.button("🍓 2. Rasio Pekat (Rasio 15%)", use_container_width=True):
                apply_ratio_preset(0.15, 2.5, 1.5, 0.1, False, False)
                st.rerun()
                
            if st.button("🌊 3. Tes Gangguan Laju Susu", use_container_width=True):
                apply_ratio_preset(0.10, 2.5, 1.5, 0.1, True, False)
                st.rerun()
                
            if st.button("⚠️ 4. Tes Gangguan Valve Tersumbat", use_container_width=True):
                apply_ratio_preset(0.10, 3.5, 2.0, 0.15, False, True)
                st.rerun()
        
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        
        # Manual Adjustments
        with st.container(border=True):
            st.markdown("<h4 style='margin-top:0; font-weight: 600;'>🛠️ Parameter Kontrol</h4>", unsafe_allow_html=True)
            
            target_ratio = st.slider("Target Rasio (Pewarna : Susu)", 0.02, 0.20, key="ratio_target_ratio")
            sim.target_ratio = target_ratio
            
            auto_mode = st.radio("Mode Operasi:", ["Auto (PID)", "Manual"], key="ratio_mode") == "Auto (PID)"
            
            manual_valve = 0.0
            if not auto_mode:
                manual_valve = st.slider("Bukaan Katup Manual (%)", 0.0, 100.0, float(sim.valve_output), 1.0)
                
            st.markdown("---")
            st.markdown("<h5 style='font-weight: 600; margin-bottom: 5px;'>Tuning PID (Slave Flow)</h5>", unsafe_allow_html=True)
            kp = st.slider("Kp (Proportional)", 0.1, 10.0, key="ratio_kp")
            ki = st.slider("Ki (Integral)", 0.0, 5.0, key="ratio_ki")
            kd = st.slider("Kd (Derivative)", 0.0, 2.0, key="ratio_kd")
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
                if st.button("▶ Start", use_container_width=True):
                    st.session_state.sim_running = True
                    st.rerun()
            with btn_col2:
                if st.button("⏸ Pause", use_container_width=True):
                    st.session_state.sim_running = False
                    st.rerun()
                    
            if st.button("🔄 Reset Jalur", use_container_width=True):
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
            val_text = "<span class='status-badge status-ok'>✓ SESUAI</span>" if is_ok else "<span class='status-badge status-error'>✗ DEVIASI</span>"
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Sensor TCS3200</div>
                <div class='metric-value'>{curr_color:.1f}</div>
                <div class='metric-unit'>Intensitas Campuran | {val_text}</div>
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
            "mengikuti perbandingan aktual kedua bahan!</b></small>", unsafe_allow_html=True
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
            st.info("Tekan tombol '▶ Start' atau klik salah satu Preset di kiri untuk menjalankan simulasi.")

# ----------------------------------------------------
# PAGE: CASCADE CONTROL
# ----------------------------------------------------
elif st.session_state.current_page == "cascade":
    st.markdown("<h1 style='color: #0f172a; font-weight: 700;'>🔄 Sistem Kontrol Bertingkat (Cascade Control)</h1>", unsafe_allow_html=True)
    st.markdown(
        "Sistem Kontrol Bertingkat menghubungkan dua loop PID secara seri. **Loop Luar (Primary)** mengontrol "
        "warna produk akhir berdasarkan data sensor TCS3200 dengan mengeluarkan nilai Target Aliran. **Loop Dalam (Secondary)** "
        "mengendalikan katup aliran pewarna agar secepat mungkin menyamai target aliran tersebut untuk meredam gangguan jalur."
    )
    st.markdown("---")
    
    col1, col2 = st.columns([1, 3])
    sim = st.session_state.cascade_sim
    
    # Left Column: Control Panel
    with col1:
        # Template Preset Buttons for Fast Demo
        with st.container(border=True):
            st.markdown("<h4 style='margin-top:0; font-weight: 600;'>⚡ Presets & Skenario Cepat</h4>", unsafe_allow_html=True)
            st.markdown("<small style='color: #64748b;'>Pilih template skenario langsung untuk memulai simulasi:</small>", unsafe_allow_html=True)
            
            if st.button("⚖️ 1. Target Warna Ringan (50)", use_container_width=True):
                apply_cascade_preset(50.0, 0.10, 0.02, 0.0, 2.0, 1.2, 0.05, False, False)
                st.rerun()
                
            if st.button("☕ 2. Target Warna Gelap (120)", use_container_width=True):
                apply_cascade_preset(120.0, 0.18, 0.04, 0.01, 2.8, 1.8, 0.10, False, False)
                st.rerun()
                
            if st.button("🌪️ 3. Tes Redam Tekanan Drop", use_container_width=True):
                apply_cascade_preset(100.0, 0.15, 0.03, 0.01, 2.5, 1.5, 0.10, False, True)
                st.rerun()
                
            if st.button("🥤 4. Gangguan Aliran & Susu", use_container_width=True):
                apply_cascade_preset(100.0, 0.20, 0.04, 0.01, 3.0, 2.0, 0.10, True, True)
                st.rerun()
        
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        
        # Manual Adjustments
        with st.container(border=True):
            st.markdown("<h4 style='margin-top:0; font-weight: 600;'>🛠️ Parameter Kontrol</h4>", unsafe_allow_html=True)
            
            target_color = st.slider("Target Intensitas Warna (0-200)", 20.0, 200.0, key="cascade_target_color")
            sim.target_color = target_color
            
            auto_mode = st.radio("Mode Operasi:", ["Auto (Cascade PID)", "Manual"], key="cascade_mode") == "Auto (Cascade PID)"
            
            manual_valve = 0.0
            if not auto_mode:
                manual_valve = st.slider("Bukaan Katup Manual (%)", 0.0, 100.0, float(sim.valve_output), 1.0)
                
            st.markdown("---")
            st.markdown("<h5 style='font-weight: 600; margin-bottom: 5px;'>Loop Luar (Primary - Color)</h5>", unsafe_allow_html=True)
            kp_out = st.slider("Kp (Outer)", 0.01, 1.0, key="cas_kp_out")
            ki_out = st.slider("Ki (Outer)", 0.0, 0.5, key="cas_ki_out")
            kd_out = st.slider("Kd (Outer)", 0.0, 0.2, key="cas_kd_out")
            
            st.markdown("<h5 style='font-weight: 600; margin-bottom: 5px;'>Loop Dalam (Secondary - Flow)</h5>", unsafe_allow_html=True)
            kp_in = st.slider("Kp (Inner)", 0.1, 10.0, key="cas_kp_in")
            ki_in = st.slider("Ki (Inner)", 0.0, 5.0, key="cas_ki_in")
            kd_in = st.slider("Kd (Inner)", 0.0, 2.0, key="cas_kd_in")
            
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
                if st.button("▶ Start", use_container_width=True):
                    st.session_state.sim_running = True
                    st.rerun()
            with btn_col2:
                if st.button("⏸ Pause", use_container_width=True):
                    st.session_state.sim_running = False
                    st.rerun()
                    
            if st.button("🔄 Reset Jalur", use_container_width=True):
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
            val_text = "<span class='status-badge status-ok'>✓ STABIL</span>" if is_ok else "<span class='status-badge status-error'>✗ DEVIASI</span>"
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
            "mengikuti pencampuran susu (putih) dan pewarna (hitam) secara real-time!</b></small>", unsafe_allow_html=True
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
            st.info("Tekan tombol '▶ Start' atau klik salah satu Preset di kiri untuk menjalankan simulasi.")

# ----------------------------------------------------
# PAGE: CODE SCL GENERATOR
# ----------------------------------------------------
elif st.session_state.current_page == "scl":
    st.markdown("<h1 style='color: #0f172a; font-weight: 700;'>📄 Template Kode SCL Siemens PCS 7</h1>", unsafe_allow_html=True)
    st.markdown(
        "Berikut adalah kode program SCL (Structured Control Language) terstruktur untuk Siemens PCS 7 "
        "(atau STEP 7 / TIA Portal) yang mengimplementasikan logika kontrol yang sama dengan simulator."
    )
    st.markdown("---")
    
    tab_code1, tab_code2 = st.tabs(["Sistem Kontrol Rasio (Ratio Control)", "Sistem Kontrol Bertingkat (Cascade Control)"])
    
    with tab_code1:
        st.markdown("### Kode SCL: FB_RatioControl")
        st.code(scl_generator.get_ratio_control_scl(), language="pascal")
        st.info(
            "💡 **Cara Integrasi di Siemens PCS 7:**\n"
            "1. Buat source file SCL baru di TIA Portal / STEP 7.\n"
            "2. Tempel kode di atas ke dalamnya.\n"
            "3. Lakukan kompilasi untuk menghasilkan Function Block (FB).\n"
            "4. Masukkan FB tersebut ke dalam program CFC (Continuous Function Chart) Anda."
        )
        
    with tab_code2:
        st.markdown("### Kode SCL: FB_CascadeControl")
        st.code(scl_generator.get_cascade_control_scl(), language="pascal")
        st.info(
            "💡 **Mengapa menggunakan Blok Tunggal untuk Cascade?**\n"
            "Menggabungkannya dalam satu FB SCL sangat baik untuk menghemat memori program (work memory PLC), "
            "menyederhanakan penanganan Anti-Windup antar-loop, serta memastikan propagasi mode Manual/Auto "
            "antara loop luar dan dalam berjalan sinkron."
        )

# ----------------------------------------------------
# PAGE: HANDBOOK
# ----------------------------------------------------
elif st.session_state.current_page == "handbook":
    st.markdown("<h1 style='color: #0f172a; font-weight: 700;'>📘 Panduan & Konsep Sistem Kontrol</h1>", unsafe_allow_html=True)
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
    """)

# ----------------------------------------------------
# bottom of file rerun trigger for real-time simulation
# ----------------------------------------------------
if st.session_state.sim_running:
    time.sleep(0.08)
    st.rerun()
