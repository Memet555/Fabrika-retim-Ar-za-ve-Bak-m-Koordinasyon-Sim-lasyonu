"""
Varsayılan yapılandırma ayarlarını içerir.
"""

# Yoğunluk seviyelerine göre geliş aralıkları (interarrival times) dakika cinsinden
ARRIVAL_RATES = {
    "düşük": 15,
    "normal": 10,
    "yoğun": 5,
    "çok yoğun": 2
}

DEFAULT_CONFIG = {
    "arrival_rate_level": "normal", # düşük, normal, yoğun, çok yoğun
    
    # Makine Sayıları
    "num_machines_kesim": 3,
    "num_machines_montaj": 2,
    "num_machines_paketleme": 2,
    
    # Ortalama İşlem Süreleri (dakika)
    "mean_process_kesim": 6.0,
    "mean_process_montaj": 10.0,
    "mean_process_paketleme": 5.0,
    
    # Arıza Olasılıkları (% olarak iş başına)
    "breakdown_prob_kesim": 0.05,
    "breakdown_prob_montaj": 0.10,
    "breakdown_prob_paketleme": 0.03,
    
    # Ortak Kaynaklar
    "num_technicians": 1,
    "mean_repair_time": 15.0, # Ortak teknisyenlerin ortalama tamir süresi
    
    # Yeni Parametreler: Ara Stok (Buffer) Limitleri
    "buffer_limit_kesim_montaj": 5,
    "buffer_limit_montaj_paketleme": 5,

    # Yeni Parametreler: Maliyet ve Finansal Analiz (₺)
    "revenue_per_job": 250.0,            # Ürün başı brüt gelir
    "machine_cost_hourly": 30.0,         # Makine başı saatlik işletme maliyeti
    "tech_cost_hourly": 75.0,            # Teknisyen başı saatlik ücret
    "delay_penalty_threshold": 45.0,     # Maksimum gecikme süresi eşiği (dakika)
    "delay_penalty_per_minute": 3.0,     # Gecikilen dakika başına ceza

    # Yeni Parametreler: Önleyici Bakım (PM) ve Yaşlanma
    "maintenance_policy": "reactive",    # "reactive" (sadece arıza durumunda) veya "preventive" (önleyici bakım)
    "pm_interval": 120.0,                # PM yapılma sıklığı (aktif çalışma dakikası)
    "mean_pm_time": 8.0,                 # Ortalama önleyici bakım süresi (dakika)
    "aging_factor": 1.5,                 # Yaşlandıkça arıza olasılığı artış çarpanı
    
    "simulation_time": 480, # 8 saatlik bir vardiya (dakika cinsinden)
    "random_seed": 42
}
