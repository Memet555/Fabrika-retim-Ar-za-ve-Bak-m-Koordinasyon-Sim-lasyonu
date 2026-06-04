import streamlit as st
import pandas as pd
from config.default_config import DEFAULT_CONFIG
from simulation.engine import FactorySimulation
from simulation.decision_support import generate_recommendations, calculate_financial_metrics
from ui.charts import plot_machine_utilization, plot_wait_times, plot_hourly_heatmap

# Sayfa yapılandırması
st.set_page_config(page_title="Fabrika Simülasyonu", layout="wide", page_icon="🏭")

st.title("🏭 Fabrika Üretim, Arıza ve Bakım Koordinasyon Simülasyonu")
st.markdown("""
> **Gelişmiş Fabrika Simülasyonu (Final Sürümü):** Bu sürüm; ara stok limitlerini (WIP), makine bloklanma (blocking) durumlarını, ekonomik kârlılık analizini, makine yaşlanmasını ve önleyici bakım politikalarını modellemektedir.
""")

# ---- YAN MENÜ (SIDEBAR) KONTROLLERİ ----
st.sidebar.header("⚙️ Simülasyon Parametreleri")

# 1. Genel Sipariş & Teknisyen Ayarları
with st.sidebar.expander("🛒 Sipariş ve Bakım Kaynakları", expanded=True):
    arrival_rate_level = st.selectbox(
        "İş/Sipariş Geliş Yoğunluğu",
        options=["düşük", "normal", "yoğun", "çok yoğun"],
        index=1
    )
    num_techs = st.slider("Teknisyen Sayısı", min_value=0, max_value=10, value=DEFAULT_CONFIG["num_technicians"])
    mean_repair = st.number_input("Ort. Tamir Süresi (dk)", min_value=1.0, max_value=100.0, value=float(DEFAULT_CONFIG["mean_repair_time"]))

# 2. Ara Stok (Buffer) Kapasiteleri
with st.sidebar.expander("🗄️ Ara Stok (Buffer) Kapasiteleri", expanded=True):
    buffer_kesim_montaj = st.slider("Kesim - Montaj Ara Stok Sınırı", min_value=1, max_value=20, value=DEFAULT_CONFIG["buffer_limit_kesim_montaj"])
    buffer_montaj_paketleme = st.slider("Montaj - Paketleme Ara Stok Sınırı", min_value=1, max_value=20, value=DEFAULT_CONFIG["buffer_limit_montaj_paketleme"])

# 3. Bakım Stratejileri (Önleyici Bakım)
with st.sidebar.expander("🔧 Bakım & Yaşlanma Stratejisi", expanded=False):
    maintenance_policy = st.radio("Bakım Politikası", options=["Yalnızca Arıza (Reactive)", "Önleyici Bakım (Preventive)"], index=0)
    pm_policy_val = "reactive" if "Reactive" in maintenance_policy else "preventive"
    pm_interval = st.number_input("Önleyici Bakım Sıklığı (Çalışma dk)", min_value=10.0, max_value=1000.0, value=float(DEFAULT_CONFIG["pm_interval"]))
    mean_pm_time = st.number_input("Ort. Bakım Süresi (PM dk)", min_value=1.0, max_value=100.0, value=float(DEFAULT_CONFIG["mean_pm_time"]))
    aging_factor = st.slider("Aşınma (Yaşlanma) Katsayısı", min_value=0.1, max_value=5.0, value=float(DEFAULT_CONFIG["aging_factor"]), step=0.1)

# 4. Gelir ve Maliyet Faktörleri (₺)
with st.sidebar.expander("💰 Gelir ve Maliyet Faktörleri (₺)", expanded=False):
    revenue_per_job = st.number_input("Ürün Başı Brüt Gelir (₺)", min_value=10.0, max_value=10000.0, value=float(DEFAULT_CONFIG["revenue_per_job"]))
    machine_cost_hourly = st.number_input("Makine Saatlik Maliyeti (₺/saat)", min_value=1.0, max_value=1000.0, value=float(DEFAULT_CONFIG["machine_cost_hourly"]))
    tech_cost_hourly = st.number_input("Teknisyen Saatlik Ücreti (₺/saat)", min_value=1.0, max_value=2000.0, value=float(DEFAULT_CONFIG["tech_cost_hourly"]))
    delay_penalty_threshold = st.number_input("Gecikme Limiti (dk)", min_value=5.0, max_value=1000.0, value=float(DEFAULT_CONFIG["delay_penalty_threshold"]))
    delay_penalty_per_minute = st.number_input("Dakika Başı Gecikme Cezası (₺/dk)", min_value=0.1, max_value=500.0, value=float(DEFAULT_CONFIG["delay_penalty_per_minute"]))

# 5. Aşama 1: Kesim İstasyonu
with st.sidebar.expander("🪵 1. Aşama: Kesim İstasyonu", expanded=False):
    num_machines_kesim = st.slider("Kesim Makine Sayısı", min_value=1, max_value=10, value=DEFAULT_CONFIG["num_machines_kesim"])
    mean_process_kesim = st.number_input("Kesim Süresi (dk)", min_value=1.0, max_value=100.0, value=float(DEFAULT_CONFIG["mean_process_kesim"]))
    breakdown_prob_kesim = st.slider("Kesim Arıza Oranı (%)", min_value=0.0, max_value=0.8, value=DEFAULT_CONFIG["breakdown_prob_kesim"], step=0.01)

# 6. Aşama 2: Montaj İstasyonu
with st.sidebar.expander("⚙️ 2. Aşama: Montaj İstasyonu", expanded=False):
    num_machines_montaj = st.slider("Montaj Makine Sayısı", min_value=1, max_value=10, value=DEFAULT_CONFIG["num_machines_montaj"])
    mean_process_montaj = st.number_input("Montaj Süresi (dk)", min_value=1.0, max_value=100.0, value=float(DEFAULT_CONFIG["mean_process_montaj"]))
    breakdown_prob_montaj = st.slider("Montaj Arıza Oranı (%)", min_value=0.0, max_value=0.8, value=DEFAULT_CONFIG["breakdown_prob_montaj"], step=0.01)

# 7. Aşama 3: Paketleme İstasyonu
with st.sidebar.expander("📦 3. Aşama: Paketleme İstasyonu", expanded=False):
    num_machines_paketleme = st.slider("Paketleme Makine Sayısı", min_value=1, max_value=10, value=DEFAULT_CONFIG["num_machines_paketleme"])
    mean_process_paketleme = st.number_input("Paketleme Süresi (dk)", min_value=1.0, max_value=100.0, value=float(DEFAULT_CONFIG["mean_process_paketleme"]))
    breakdown_prob_paketleme = st.slider("Paketleme Arıza Oranı (%)", min_value=0.0, max_value=0.8, value=DEFAULT_CONFIG["breakdown_prob_paketleme"], step=0.01)

# 8. Genel Zaman & Tohum Ayarları
with st.sidebar.expander("🕒 Zaman ve Güvenilirlik", expanded=False):
    sim_time = st.number_input("Simülasyon Süresi (dk)", min_value=60, max_value=14400, value=DEFAULT_CONFIG["simulation_time"], step=60)
    random_seed = st.number_input("Rastgelelik Tohumu (Seed)", value=DEFAULT_CONFIG["random_seed"])

run_btn = st.sidebar.button("🚀 Simülasyonu Başlat", use_container_width=True, type="primary")

# ---- SİMÜLASYONU VE ARAYÜZÜ YÜKLE ----
if run_btn:
    # Kullanıcıdan alınan parametreleri config dictionary'sine yükle
    config = {
        "arrival_rate_level": arrival_rate_level,
        "num_machines_kesim": num_machines_kesim,
        "num_machines_montaj": num_machines_montaj,
        "num_machines_paketleme": num_machines_paketleme,
        
        "mean_process_kesim": mean_process_kesim,
        "mean_process_montaj": mean_process_montaj,
        "mean_process_paketleme": mean_process_paketleme,
        
        "breakdown_prob_kesim": breakdown_prob_kesim,
        "breakdown_prob_montaj": breakdown_prob_montaj,
        "breakdown_prob_paketleme": breakdown_prob_paketleme,
        
        "num_technicians": num_techs,
        "mean_repair_time": mean_repair,
        "simulation_time": sim_time,
        "random_seed": random_seed,
        
        # Gelişmiş Parametreler
        "buffer_limit_kesim_montaj": buffer_kesim_montaj,
        "buffer_limit_montaj_paketleme": buffer_montaj_paketleme,
        "maintenance_policy": pm_policy_val,
        "pm_interval": pm_interval,
        "mean_pm_time": mean_pm_time,
        "aging_factor": aging_factor,
        "revenue_per_job": revenue_per_job,
        "machine_cost_hourly": machine_cost_hourly,
        "tech_cost_hourly": tech_cost_hourly,
        "delay_penalty_threshold": delay_penalty_threshold,
        "delay_penalty_per_minute": delay_penalty_per_minute
    }
    
    with st.spinner('Simülasyon çalışıyor ve veriler işleniyor...'):
        # Simülasyon motorunu başlat ve çalıştır
        sim = FactorySimulation(config)
        metrics = sim.run()
        
    st.success("✅ Simülasyon başarıyla tamamlandı!")
    
    # Metrikleri hesaplamak için varsayılan zamanlar
    total_time = config["simulation_time"]
    
    # Finansal Hesaplamalar
    fin = calculate_financial_metrics(metrics, config)
    
    # KPI Hesaplamaları
    completed_jobs = metrics.total_completed_jobs
    started_jobs = [j for j in metrics.jobs if j.start_time_s1 >= 0]
    
    # Ortalama bekleme süreleri
    avg_wait = sum(j.total_wait_time for j in started_jobs) / len(started_jobs) if started_jobs else 0.0
    throughput = completed_jobs / (total_time / 60) if total_time > 0 else 0
    
    # Teknisyen kullanım oranı
    if num_techs > 0:
        tech_util = (metrics.technician_busy_time / (total_time * num_techs)) * 100
    else:
        has_breakdowns = (breakdown_prob_kesim > 0 or breakdown_prob_montaj > 0 or breakdown_prob_paketleme > 0 or pm_policy_val == "preventive")
        tech_util = 100.0 if has_breakdowns else 0.0
        
    # --- ÜST KPI KARTLARI ---
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("📦 Tamamlanan Sipariş", f"{completed_jobs}")
    col2.metric("⏱️ Ort. Toplam Bekleme", f"{avg_wait:.1f} dk")
    col3.metric("🔧 Arıza (Planlı PM)", f"{metrics.total_breakdowns} ({metrics.total_pm_count})")
    col4.metric("📈 Throughput (/Saat)", f"{throughput:.1f}")
    col5.metric("👷 Teknisyen Kullanımı", f"%{tech_util:.1f}")
    
    net_profit_val = fin["net_profit"]
    if net_profit_val >= 0:
        col6.metric("💰 Net Kâr (₺)", f"{net_profit_val:.1f} ₺", delta=f"+{net_profit_val:.1f} ₺")
    else:
        col6.metric("💰 Net Kâr (₺)", f"{net_profit_val:.1f} ₺", delta=f"{net_profit_val:.1f} ₺", delta_color="inverse")
        
    st.markdown("---")
    
    # --- FİNANSAL TABLO VE DETAYLAR ---
    st.markdown("### 📊 Finansal Durum Analizi")
    col_fin1, col_fin2, col_fin3, col_fin4 = st.columns(4)
    col_fin1.info(f"💵 **Toplam Brüt Gelir:**  \n{fin['revenue']:.2f} ₺")
    col_fin2.warning(f"🏭 **Makine İşletme Gideri:**  \n{fin['machine_cost']:.2f} ₺")
    col_fin3.warning(f"👷 **Teknisyen Gideri:**  \n{fin['tech_cost']:.2f} ₺")
    col_fin4.error(f"⚠️ **Gecikme Cezaları (SLA):**  \n{fin['delay_penalty']:.2f} ₺")
    
    st.markdown("---")
    
    # --- VERİ HAZIRLAMA (DATAFRAMELER) ---
    machine_data = []
    
    # Helper to calculate and append machine metrics
    def add_machine_metrics(num_machines, stage_name, display_name):
        for i in range(num_machines):
            m_name = f"{stage_name}-{i+1}"
            busy = metrics.machine_busy_time.get(m_name, 0.0)
            down = metrics.machine_downtime.get(m_name, 0.0)
            blocked = metrics.machine_blocked_time.get(m_name, 0.0)
            pm = metrics.machine_pm_time.get(m_name, 0.0)
            
            downtime_total = down + pm
            idle = max(0.0, total_time - busy - downtime_total - blocked)
            
            busy_pct = min((busy / total_time) * 100, 100.0)
            blocked_pct = min((blocked / total_time) * 100, 100.0)
            down_pct = min((downtime_total / total_time) * 100, 100.0)
            idle_pct = min((idle / total_time) * 100, 100.0)
            
            machine_data.append({
                "İstasyon": display_name,
                "Makine": m_name,
                "Aktif Çalışma (%)": busy_pct,
                "Bloklanma (%)": blocked_pct,
                "Duruş/Bakım (%)": down_pct,
                "Atıl Kapasite (%)": idle_pct
            })

    add_machine_metrics(num_machines_kesim, "Kesim", "Kesim")
    add_machine_metrics(num_machines_montaj, "Montaj", "Montaj")
    add_machine_metrics(num_machines_paketleme, "Paketleme", "Paketleme")
        
    df_machines = pd.DataFrame(machine_data)
    
    jobs_data = [{
        "İş ID": j.job_id,
        "Geliş Zamanı": j.arrival_time,
        "Kesim Bekleme (dk)": j.wait_time_s1,
        "Montaj Bekleme (dk)": j.wait_time_s2,
        "Paketleme Bekleme (dk)": j.wait_time_s3,
        "Toplam Bekleme (dk)": j.total_wait_time,
        "Sistemde Kalma Süresi (dk)": j.time_in_system
    } for j in started_jobs]
    df_jobs = pd.DataFrame(jobs_data)
    
    # --- GRAFİKLER ---
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.plotly_chart(plot_machine_utilization(df_machines, total_time), use_container_width=True)
        
    with col_chart2:
        st.plotly_chart(plot_wait_times(df_jobs), use_container_width=True)
        
    col_heat, col_decision = st.columns(2)
    with col_heat:
        st.plotly_chart(plot_hourly_heatmap(df_jobs), use_container_width=True)
        
    with col_decision:
        st.subheader("💡 Karar Destek Sistemi Önerileri")
        st.markdown("Mevcut simülasyon sonuçlarına ve maliyet kısıtlarına göre üretilen optimizasyon önerileri:")
        recommendations = generate_recommendations(metrics, config)
        for rec in recommendations:
             # Eğer "darboğaz" / "Zarar" / "Risk" geçiyorsa kırmızı / uyarı (warning veya error)
             if "Zarar" in rec or "Risk" in rec or "Alarm" in rec:
                 st.error(rec)
             elif "Darboğaz" in rec or "Uyarısı" in rec or "Kısıtı" in rec:
                 st.warning(rec)
             elif "Atıl" in rec or "öneri" in rec:
                 st.info(rec)
             else:
                 st.success(rec)
                 
    # --- SENTETİK VERİ İNDİRME ALANI ---
    st.markdown("---")
    st.subheader("📥 Sentetik Simülasyon Verilerini Dışa Aktar")
    st.markdown("Veri analizi, optimizasyon veya makine öğrenmesi modelleri eğitmek için simülasyon çıktılarını indirebilirsiniz:")
    
    csv_jobs = df_jobs.to_csv(index=False).encode('utf-8')
    csv_machines = df_machines.to_csv(index=False).encode('utf-8')
    
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="📄 Sipariş Geliş ve Bekleme Verilerini İndir (CSV)",
            data=csv_jobs,
            file_name="sentetik_siparis_verileri.csv",
            mime="text/csv",
            key="download_jobs_csv",
            use_container_width=True
        )
    with col_dl2:
        st.download_button(
            label="⚙️ Makine Performans ve Bloklanma Verilerini İndir (CSV)",
            data=csv_machines,
            file_name="sentetik_makine_verileri.csv",
            mime="text/csv",
            key="download_machines_csv",
            use_container_width=True
        )
            
    # --- DETAYLI TABLO ---
    with st.expander("📊 Makine Bazlı Detaylı OEE Durum Tablosunu Göster"):
        st.dataframe(df_machines.style.format({
            "Aktif Çalışma (%)": "{:.2f}%", 
            "Bloklanma (%)": "{:.2f}%",
            "Duruş/Bakım (%)": "{:.2f}%",
            "Atıl Kapasite (%)": "{:.2f}%"
        }), use_container_width=True)
        
else:
    st.info("👈 Tüm parametreleri sol panelden ayarlayıp, simülasyonu başlatmak için 'Simülasyonu Başlat' butonuna tıklayınız.")
