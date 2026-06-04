# 🏭 Gelişmiş Fabrika Üretim Hattı, Darboğaz ve Bakım Koordinasyon Simülatörü

Bu proje, çok aşamalı ve ardışık operasyonlara sahip endüstriyel bir üretim hattını **Ayrık Olay Simülasyonu (Discrete Event Simulation - DES)** kurallarına göre modelleyen gelişmiş bir benzetim uygulamasıdır. Python'ın **SimPy** kütüphanesi üzerine kurulan simülasyon motoru; stokastik (rassal) sipariş akışını, makine aşınma dinamiklerini, kısıtlı ortak bakım teknisyeni kaynağını, ara stok kısıtlarını ve finansal kârlılık dengelerini gerçekçi bir şekilde taklit eder.

---

## 🚀 Öne Çıkan Gelişmiş Özellikler

### 1. Ara Stok (WIP) Kısıtlamaları ve Makine Bloklanması (Blocking)
* **Sınırlı Tampon Alanları:** İstasyonlar arasındaki ara stok (buffer) kapasiteleri fiziksel kısıtları yansıtacak şekilde sınırlıdır (örn: maksimum 5 adet).
* **Bloklanma (Blocking):** Sonraki istasyonun önündeki buffer alanı dolduğunda, önceki istasyondaki makine işlemini bitirse dahi parçasını teslim edemez. Makine **bloklanır (blocked)** ve yeni iş kabul edemez hale gelir. Bu durum, hat dengeleme çalışmalarındaki darboğazların ana sebebidir.

### 2. Finansal & Ekonomik Analiz Katmanı (P&L ve SLA Maliyetleri)
Üretim başarısı sadece üretim adetleriyle değil, mali performansla ölçülür:
* **Brüt Gelir:** Tamamlanan her ürün başına sisteme gelir yansıtılır.
* **Operasyonel Giderler:** Aktif makinelerin saatlik işletme maliyetleri ve teknisyenlerin saatlik ücretleri gider olarak yazılır.
* **Gecikme Cezaları (SLA):** Siparişlerin fabrikada geçirdiği toplam süre belirlenen teslimat eşiğini aşarsa, aşan her dakika için sisteme gecikme cezası yansıtılarak kârlılık düşürülür.
* **Net Kâr/Zarar:** Tüm bu kalemler birleştirilerek sistemin net kârlılığı hesaplanır ve anlık olarak arayüzde gösterilir.

### 3. Makine Yaşlanması ve Önleyici Bakım (Preventive Maintenance - PM)
* **Dinamik Arıza Olasılığı (Aşınma):** Makinelerin arıza olasılıkları sabit değildir. Makine çalıştıkça biriken aktif süreye bağlı olarak arıza ihtimali doğrusal olarak artar.
* **Bakım Stratejileri:** Kullanıcı "Yalnızca Arıza Durumunda Bakım (Reactive)" ile "Planlı Periyodik Bakım (Preventive)" stratejilerini kıyaslayabilir. Önleyici bakım, arıza frekansını düşürerek plansız duruşları azaltır.

### 4. 4 Durumlu OEE ve Kuyruk Analizi Grafikeri (Plotly)
* **Makine OEE Grafik:** Makinelerin zaman kullanımları; **Üretim (Aktif)**, **Bloklu (Ara Stok Dolu)**, **Arıza/PM Duruşu** ve **Atıl (Boşta/İş Bekleme)** olarak 4 duruma ayrılarak stacked bar chart ile çizilir.
* **Bekleme Süresi Dağılımı:** İstasyonlar bazında siparişlerin bekleme sürelerinin değişkenliği ve uç değerleri (outliers) kutu grafiği (box plot) ile gösterilir.
* **Zaman Yoğunluk Haritası:** Saatlik sipariş geliş sıklığı ısı haritasıyla görselleştirilir.

### 5. Karar Destek Sistemi
Simülasyon sonunda çalışan kural tabanlı motor; teknisyen doluluk oranlarını, makine atıl kapasitelerini ve ara stok kısıtlarını inceleyerek hat verimini ve **kârlılığı artıracak somut iyileştirme önerileri** sunar.

---

## 🛠️ Kullanılan Teknolojiler
* **Python 3.11+**
* **SimPy**: Ayrık olay simülasyon motoru
* **Streamlit**: Web tabanlı kontrol paneli ve kullanıcı arayüzü
* **Plotly**: Etkileşimli analitik grafikler
* **Pandas & NumPy**: Veri manipülasyonu ve istatistiksel işlemler

---

## 📂 Proje Yapısı
```text
├── app.py                     # Ana Streamlit arayüzü ve KPI gösterge paneli
├── requirements.txt           # Gerekli Python kütüphaneleri
├── config/
│   └── default_config.py      # Varsayılan simülasyon, arıza ve maliyet parametreleri
├── simulation/
│   ├── engine.py              # SimPy Environment kurulumu ve kaynak yönetimi
│   ├── entities.py            # İş (Job) nesnesi ve zaman damgaları
│   ├── processes.py           # Bloklanma, aşınma ve PM süreç kuralları
│   ├── metrics.py             # Metrik toplama ve veri yapısı
│   └── decision_support.py    # Finansal analiz ve karar destek optimizasyon motoru
└── ui/
    └── charts.py              # OEE stacked bar, box plot ve heatmap çizicileri
```

---

## ⚙️ Kurulum ve Çalıştırma

1. Proje dizininde bir sanal ortam oluşturun ve aktif edin:
   ```bash
   python -m venv venv
   
   # Windows için:
   .\venv\Scripts\activate
   
   # macOS/Linux için:
   source venv/bin/activate
   ```

2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

3. Simülasyon uygulamasını başlatın:
   ```bash
   streamlit run app.py
   ```

---

## 📊 Örnek Simülasyon Senaryoları ve Deneyler

Uygulamayı başlattıktan sonra yan paneldeki parametrelerle şu deneyleri gerçekleştirebilirsiniz:

1. **Önleyici Bakım Optimizasyonu:**
   Bakım politikasını "Yalnızca Arıza" modundan "Önleyici Bakım" moduna geçirin. Bakım aralığı (`pm_interval`) ve bakım süresi değişkenlerini değiştirerek plansız duruşları azaltıp net kârı nasıl maksimize edebileceğinizi inceleyin.

2. **Kapasite ve Hat Dengeleme:**
   OEE durum tablosuna bakarak atıl kalma oranı %80'in üzerinde olan makineleri hattan çıkartın (makine sayısını azaltın) ve işletme maliyetlerindeki düşüşün net kâr üzerindeki etkisini gözlemleyin.

3. **Ara Stok (Buffer) Sınır Analizi:**
   Ara stok limitlerini minimuma (örn: 1) indirdiğinizde Kesim makinelerinde oluşan bloklanma (blocking) sürelerinin OEE grafiğindeki sarı alanları nasıl artırdığını gözlemleyin.
