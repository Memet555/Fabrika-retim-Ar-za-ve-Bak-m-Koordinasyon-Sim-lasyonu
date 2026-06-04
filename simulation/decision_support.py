"""
Gelişmiş kural-tabanlı (rule-based) karar destek ve finansal analiz motoru.
"""

def calculate_financial_metrics(metrics, config):
    """Simülasyon sonuçlarına göre operasyonel gelir, gider, gecikme cezası ve net kâr hesaplar."""
    total_time = config.get("simulation_time", 480)
    completed_jobs = metrics.total_completed_jobs
    
    # 1. Gelir (Ürün Başına Sabit Gelir)
    revenue = completed_jobs * config.get("revenue_per_job", 250.0)
    
    # 2. Makine İşletme Maliyeti
    num_machines = (config.get("num_machines_kesim", 3) + 
                    config.get("num_machines_montaj", 2) + 
                    config.get("num_machines_paketleme", 2))
    machine_cost = num_machines * (total_time / 60.0) * config.get("machine_cost_hourly", 30.0)
    
    # 3. Teknisyen Maliyeti
    num_techs = config.get("num_technicians", 1)
    tech_cost = num_techs * (total_time / 60.0) * config.get("tech_cost_hourly", 75.0)
    
    # 4. Gecikme Cezası (Müşteri Memnuniyeti / SLA Maliyeti)
    started_jobs = [j for j in metrics.jobs if j.start_time_s1 >= 0]
    delay_penalty = 0.0
    delay_threshold = config.get("delay_penalty_threshold", 45.0)
    penalty_per_min = config.get("delay_penalty_per_minute", 3.0)
    
    for j in started_jobs:
        if j.end_time_s3 >= 0:
            sys_time = j.time_in_system
            if sys_time > delay_threshold:
                delay_penalty += (sys_time - delay_threshold) * penalty_per_min
                
    net_profit = revenue - machine_cost - tech_cost - delay_penalty
    
    return {
        "revenue": revenue,
        "machine_cost": machine_cost,
        "tech_cost": tech_cost,
        "delay_penalty": delay_penalty,
        "net_profit": net_profit
    }

def generate_recommendations(metrics, config):
    """Simülasyon sonuçlarına göre finansal ve teknik darboğaz analiz önerileri üretir."""
    recommendations = []
    total_time = config.get("simulation_time", 480)
    
    # Finansal analiz çağrısı
    fin = calculate_financial_metrics(metrics, config)
    
    # Kârlılık Önerisi
    if fin["net_profit"] < 0:
        recommendations.append(f"🔴 **Finansal Alarm:** Sistem bu konfigürasyonda **{fin['net_profit']:.2f} ₺ zarar** etmektedir! Gecikme cezalarını azaltmak için darboğazları çözmeli veya işletme maliyetini kısmak için atıl kapasiteli makineleri azaltmalısınız.")
    else:
        recommendations.append(f"💚 **Kârlı Operasyon:** Sistem **{fin['net_profit']:.2f} ₺ net kâr** üretmektedir. (Brüt Gelir: {fin['revenue']:.0f} ₺, Toplam Gider: {fin['machine_cost'] + fin['tech_cost'] + fin['delay_penalty']:.0f} ₺).")

    # 1. Teknisyen kullanım oranı kontrolü
    num_techs = config.get("num_technicians", 1)
    if num_techs > 0:
        tech_utilization = (metrics.technician_busy_time / (total_time * num_techs)) * 100
        if tech_utilization > 80:
            recommendations.append(f"🔴 **Bakım Darboğazı:** Teknisyen doluluk oranı aşırı yüksek (%{tech_utilization:.1f}). Makineler tamirci veya bakım sırası bekliyor olabilir. Ek teknisyen alınması kârlılığı artırabilir.")
        elif tech_utilization < 20:
             recommendations.append(f"🟢 **Atıl Bakım Kapasitesi:** Teknisyen doluluk oranı düşük (%{tech_utilization:.1f}). Teknisyen sayısını azaltarak giderleri düşürebilirsiniz.")
    else:
        has_breakdowns = (config.get("breakdown_prob_kesim", 0) > 0 or 
                          config.get("breakdown_prob_montaj", 0) > 0 or 
                          config.get("breakdown_prob_paketleme", 0) > 0 or
                          config.get("maintenance_policy", "reactive") == "preventive")
        if has_breakdowns:
            recommendations.append("🔴 **Kritik Risk:** Sistemde teknisyen sayısı 0! Makine arızalandığında veya bakım zamanı geldiğinde hat kalıcı olarak duracaktır.")
    
    # 2. Ara Stok (Buffer) ve Bloklanma Önerileri
    num_m_kesim = config.get("num_machines_kesim", 3)
    num_m_montaj = config.get("num_machines_montaj", 2)
    
    kesim_block_sum = sum(metrics.machine_blocked_time.get(f"Kesim-{i+1}", 0.0) for i in range(num_m_kesim))
    montaj_block_sum = sum(metrics.machine_blocked_time.get(f"Montaj-{i+1}", 0.0) for i in range(num_m_montaj))
    
    if kesim_block_sum > 30.0:
        recommendations.append(f"⚠️ **Ara Stok Kısıtı (Kesim):** Kesim istasyonu makineleri toplam **{kesim_block_sum:.1f} dk** boyunca Montaj buffer'ı dolu olduğu için bloke oldu. 'Kesim-Montaj Ara Stok Sınırı'nı artırmak veya Montaj istasyonunu hızlandırmak tıkanıklığı çözer.")
    if montaj_block_sum > 30.0:
        recommendations.append(f"⚠️ **Ara Stok Kısıtı (Montaj):** Montaj istasyonu makineleri toplam **{montaj_block_sum:.1f} dk** boyunca Paketleme buffer'ı dolu olduğu için bloke oldu. 'Montaj-Paketleme Ara Stok Sınırı'nı artırmak tıkanıklığı azaltacaktır.")

    # 3. Önleyici Bakım Önerileri
    if config.get("maintenance_policy", "reactive") == "reactive" and metrics.total_breakdowns > 5:
        recommendations.append(f"💡 **Bakım Stratejisi Önerisi:** Sistemde çok sayıda arıza ({metrics.total_breakdowns}) oluştu. Önleyici Bakım (PM) politikasını açmak, küçük planlı duruşlarla büyük plansız arızaların önüne geçebilir.")
    elif config.get("maintenance_policy", "preventive") == "preventive":
        recommendations.append(f"🔧 **Planlı Bakım Uygulanıyor:** Toplam **{metrics.total_pm_count} adet** önleyici bakım yapıldı. Bakım sıklığını (PM Interval) arıza sayılarıyla dengeleyerek teknisyen doluluk oranını optimize edebilirsiniz.")

    # 4. İstasyon Bazlı Ortalama Bekleme Süreleri ve Darboğaz Tespiti
    started_jobs = [j for j in metrics.jobs if j.start_time_s1 >= 0]
    if started_jobs:
        avg_wait_s1 = sum(j.wait_time_s1 for j in started_jobs) / len(started_jobs)
        avg_wait_s2 = sum(j.wait_time_s2 for j in started_jobs if j.start_time_s2 >= 0) / len([j for j in started_jobs if j.start_time_s2 >= 0]) if any(j.start_time_s2 >= 0 for j in started_jobs) else 0.0
        avg_wait_s3 = sum(j.wait_time_s3 for j in started_jobs if j.start_time_s3 >= 0) / len([j for j in started_jobs if j.start_time_s3 >= 0]) if any(j.start_time_s3 >= 0 for j in started_jobs) else 0.0
        
        waits = [("Kesim", avg_wait_s1), ("Montaj", avg_wait_s2), ("Paketleme", avg_wait_s3)]
        bottleneck_stage, max_wait = max(waits, key=lambda x: x[1])
        
        if max_wait > 5.0:
            recommendations.append(f"🟠 **Kuyruk / Darboğaz Uyarısı:** En büyük darboğaz **{bottleneck_stage}** aşamasında oluşuyor. Ortalama bekleme süresi **{max_wait:.1f} dk**. Buradaki makine sayısını artırmanız veya işlem süresini kısaltmanız önerilir.")
        else:
            recommendations.append(f"✅ **Kuyruk Durumu:** İstasyon bekleme süreleri dengeli görünüyor (en fazla {max_wait:.1f} dk).")
            
    return recommendations
