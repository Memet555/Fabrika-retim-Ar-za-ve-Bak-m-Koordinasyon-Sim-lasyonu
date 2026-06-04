"""
SimPy süreçlerini (Process) tanımlayan modül.
"""
import simpy
import random
from config.default_config import ARRIVAL_RATES
from simulation.entities import Job

def job_generator(env, config, pool_kesim, pool_montaj, pool_paketleme, tech_resource, metrics_collector, buffer_slots_km, buffer_slots_mp):
    """Belirli aralıklarla yeni iş (sipariş) üretir."""
    job_id = 0
    arrival_rate_level = config.get("arrival_rate_level", "normal")
    interarrival_time = ARRIVAL_RATES.get(arrival_rate_level, 10.0)
    
    while True:
        job_id += 1
        job = Job(job_id=job_id, arrival_time=env.now)
        metrics_collector.add_job(job)
        
        env.process(process_job(env, job, config, pool_kesim, pool_montaj, pool_paketleme, tech_resource, metrics_collector, buffer_slots_km, buffer_slots_mp))
        
        # Sonraki iş için bekle (Eksponansiyel dağılım)
        yield env.timeout(random.expovariate(1.0 / max(interarrival_time, 0.1)))

def run_stage(env, job, stage_name, machine_pool, tech_resource, mean_process_time, breakdown_probability, mean_repair_time, metrics_collector, config, buffer_slots_to_request=None, buffer_req_to_release=None):
    """Bir siparişin tek bir aşamadaki (Kesim/Montaj/Paketleme) tüm sürecini (Kuyruk, Arıza, İşlem) yürütür."""
    # Uygun bir makine talep et, boş makine yoksa bekle (Kuyruk)
    machine_id = yield machine_pool.get()
    
    # Makine alındığına göre, eğer önceki aşamadan bir buffer kilidi varsa onu bırakıyoruz.
    # Böylece önceki istasyonun önündeki bir boşluk serbest kalır.
    if buffer_req_to_release is not None:
        buffer_slots_ref, req_to_free = buffer_req_to_release
        buffer_slots_ref.release(req_to_free)
        
    # Aşamaya giriş zamanını kaydet
    if stage_name == "kesim":
        job.start_time_s1 = env.now
    elif stage_name == "montaj":
        job.start_time_s2 = env.now
    elif stage_name == "paketleme":
        job.start_time_s3 = env.now

    # --- ARIZA VE YAŞLANMA KONTROLÜ ---
    accumulated_time = metrics_collector.machine_accumulated_time.get(machine_id, 0.0)
    
    # Yaşlanmaya bağlı dinamik arıza olasılığı hesapla
    # Her 60 dk çalışma süresi arıza olasılığını katlar (aging_factor oranında artar)
    aging_factor = config.get("aging_factor", 1.5)
    current_prob = min(breakdown_probability * (1.0 + aging_factor * (accumulated_time / 60.0)), 0.90)
    
    if random.random() < current_prob:
        metrics_collector.total_breakdowns += 1
        metrics_collector.machine_breakdowns[machine_id] = metrics_collector.machine_breakdowns.get(machine_id, 0) + 1
        start_downtime = env.now
        
        # Ortak bakım teknisyeni talep et (Teknisyen meşgulse makine bekler)
        with tech_resource.request() as tech_req:
            yield tech_req
            # Tamir süresi (Eksponansiyel dağılım)
            repair_time = random.expovariate(1.0 / max(mean_repair_time, 0.1))
            yield env.timeout(repair_time)
            metrics_collector.technician_busy_time += repair_time
            
        downtime = env.now - start_downtime
        metrics_collector.machine_downtime[machine_id] = metrics_collector.machine_downtime.get(machine_id, 0.0) + downtime
        # Arıza sonrası makine yaşlanması sıfırlanır
        metrics_collector.machine_accumulated_time[machine_id] = 0.0
        accumulated_time = 0.0
        
    # İşi işle (Eksponansiyel dağılım ile işlem süresi)
    process_time = random.expovariate(1.0 / max(mean_process_time, 0.1))
    yield env.timeout(process_time)
    
    # Makinenin aktif çalışma süresini ve yaşlanmasını kaydet
    metrics_collector.machine_busy_time[machine_id] = metrics_collector.machine_busy_time.get(machine_id, 0.0) + process_time
    new_accumulated = accumulated_time + process_time
    metrics_collector.machine_accumulated_time[machine_id] = new_accumulated
    
    # --- ÖNLEYİCİ BAKIM (PM) KONTROLÜ ---
    if config.get("maintenance_policy", "preventive") == "preventive" and new_accumulated >= config.get("pm_interval", 120.0):
        start_pm = env.now
        
        # Bakım için teknisyen talep et
        with tech_resource.request() as tech_req:
            yield tech_req
            # PM süresi
            pm_time = random.expovariate(1.0 / max(config.get("mean_pm_time", 8.0), 0.1))
            yield env.timeout(pm_time)
            metrics_collector.technician_busy_time += pm_time
            
        pm_duration = env.now - start_pm
        metrics_collector.total_pm_count += 1
        metrics_collector.machine_pm_time[machine_id] = metrics_collector.machine_pm_time.get(machine_id, 0.0) + pm_duration
        # PM sonrası yaşlanma sıfırlanır
        metrics_collector.machine_accumulated_time[machine_id] = 0.0
    
    # Aşama bitiş zamanını kaydet
    if stage_name == "kesim":
        job.end_time_s1 = env.now
    elif stage_name == "montaj":
        job.end_time_s2 = env.now
    elif stage_name == "paketleme":
        job.end_time_s3 = env.now
        
    # --- ARA STOK (BUFFER) VE BLOKLANMA KONTROLÜ ---
    buffer_req = None
    if buffer_slots_to_request is not None:
        block_start = env.now
        buffer_req = buffer_slots_to_request.request()
        yield buffer_req  # Buffer'da yer açılana kadar bekle (Makineyi kilitler / Bloklar)
        block_duration = env.now - block_start
        metrics_collector.machine_blocked_time[machine_id] = metrics_collector.machine_blocked_time.get(machine_id, 0.0) + block_duration
        
    # Makineyi havuza geri bırak ki diğer işler alabilsin
    machine_pool.put(machine_id)
    
    return buffer_req

def process_job(env, job, config, pool_kesim, pool_montaj, pool_paketleme, tech_resource, metrics_collector, buffer_slots_km, buffer_slots_mp):
    """Bir siparişin tüm üretim hattı boyunca (Kesim -> Montaj -> Paketleme) sırayla akmasını sağlar."""
    # 1. Aşama: Kesim
    # Kesim sonrasında Montaj buffer'ı (buffer_slots_km) için yer talep edilir
    buffer_req_km = yield env.process(run_stage(
        env, job, "kesim", pool_kesim, tech_resource,
        config.get("mean_process_kesim", 6.0),
        config.get("breakdown_prob_kesim", 0.05),
        config.get("mean_repair_time", 15.0),
        metrics_collector,
        config,
        buffer_slots_to_request=buffer_slots_km,
        buffer_req_to_release=None
    ))
    
    # 2. Aşama: Montaj
    # Montaj başladığında Kesim buffer slotu serbest bırakılır, iş bittiğinde Paketleme buffer'ı (buffer_slots_mp) talep edilir
    buffer_req_mp = yield env.process(run_stage(
        env, job, "montaj", pool_montaj, tech_resource,
        config.get("mean_process_montaj", 10.0),
        config.get("breakdown_prob_montaj", 0.10),
        config.get("mean_repair_time", 15.0),
        metrics_collector,
        config,
        buffer_slots_to_request=buffer_slots_mp,
        buffer_req_to_release=(buffer_slots_km, buffer_req_km)
    ))
    
    # 3. Aşama: Paketleme
    # Paketleme başladığında Montaj buffer slotu serbest bırakılır, paketleme son aşama olduğu için yeni buffer talep edilmez
    yield env.process(run_stage(
        env, job, "paketleme", pool_paketleme, tech_resource,
        config.get("mean_process_paketleme", 5.0),
        config.get("breakdown_prob_paketleme", 0.03),
        config.get("mean_repair_time", 15.0),
        metrics_collector,
        config,
        buffer_slots_to_request=None,
        buffer_req_to_release=(buffer_slots_mp, buffer_req_mp)
    ))
    
    # Tüm aşamalar bittiğinde işi tamamlandı olarak işaretle
    metrics_collector.record_completed_job()
