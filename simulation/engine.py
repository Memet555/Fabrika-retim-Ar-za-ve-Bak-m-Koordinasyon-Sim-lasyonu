"""
Ana simülasyon orkestrasyon sınıfı.
"""
import simpy
import random
from simulation.metrics import MetricsCollector
from simulation.processes import job_generator

class FactorySimulation:
    """SimPy Environment kurulumu ve kaynakların yönetimi (3 Aşamalı Hat)."""
    def __init__(self, config):
        self.config = config
        self.env = simpy.Environment()
        self.metrics = MetricsCollector()
        
        # Tekrar edilebilirlik için
        random.seed(self.config.get("random_seed", 42))
        
        # Ortak Bakım teknisyenleri kaynağı
        self.tech_resource = simpy.Resource(self.env, capacity=self.config.get("num_technicians", 1))
        
        # 1. Aşama Kesim Makineleri Havuzu
        self.pool_kesim = simpy.Store(self.env, capacity=self.config.get("num_machines_kesim", 3))
        for i in range(self.config.get("num_machines_kesim", 3)):
            self.pool_kesim.put(f"Kesim-{i+1}")
            
        # 2. Aşama Montaj Makineleri Havuzu
        self.pool_montaj = simpy.Store(self.env, capacity=self.config.get("num_machines_montaj", 2))
        for i in range(self.config.get("num_machines_montaj", 2)):
            self.pool_montaj.put(f"Montaj-{i+1}")
            
        # 3. Aşama Paketleme Makineleri Havuzu
        self.pool_paketleme = simpy.Store(self.env, capacity=self.config.get("num_machines_paketleme", 2))
        for i in range(self.config.get("num_machines_paketleme", 2)):
            self.pool_paketleme.put(f"Paketleme-{i+1}")
            
        # Ara stok (buffer) kapasite limitleri
        buffer_km_cap = self.config.get("buffer_limit_kesim_montaj", 5)
        buffer_mp_cap = self.config.get("buffer_limit_montaj_paketleme", 5)
        
        # Sınırsız durumda SimPy Resource kapasitesini çok büyük bir sayı yapıyoruz
        self.buffer_slots_kesim_montaj = simpy.Resource(self.env, capacity=buffer_km_cap if buffer_km_cap > 0 else 999999)
        self.buffer_slots_montaj_paketleme = simpy.Resource(self.env, capacity=buffer_mp_cap if buffer_mp_cap > 0 else 999999)
            
    def run(self):
        """Simülasyon sürecini başlatır ve belirtilen süre kadar işletir."""
        # İş üreten süreci ekle
        self.env.process(job_generator(
            self.env, 
            self.config, 
            self.pool_kesim,
            self.pool_montaj,
            self.pool_paketleme,
            self.tech_resource, 
            self.metrics,
            self.buffer_slots_kesim_montaj,
            self.buffer_slots_montaj_paketleme
        ))
        
        # Motoru çalıştır
        self.env.run(until=self.config.get("simulation_time", 480))
        
        return self.metrics
