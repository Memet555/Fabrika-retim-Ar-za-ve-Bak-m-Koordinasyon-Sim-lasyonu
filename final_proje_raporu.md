# Fabrika Üretim Hattı Simülasyonu Projesi - Final Raporu

**Ders:** Benzetim Programları / Simülasyon  
**Konu:** Gelişmiş Ayrık Olay Simülasyonu (Vize Sürümünden Gelişmiş Final Sürümüne Geçiş ve Modelleme Raporu)  

---

## 1. Proje Özeti ve Amacı
Bu çalışma, bir imalat fabrikasındaki üretim hattını **Ayrık Olay Simülasyonu (Discrete Event Simulation)** prensipleri doğrultusunda modellemektedir. Simülasyon motoru olarak Python'ın **SimPy** kütüphanesi kullanılmıştır. 

Geliştirilen uygulama; üretim sürecindeki dinamikleri (siparişlerin gelişi, makinelerde işlenmesi, makine arızaları, teknisyen bakım müdahaleleri, ara stok limitleri ve makine bloklanmaları) taklit ederek sistemdeki verim kayıplarını, darboğazları ve ekonomik kârlılığı analiz etmeyi amaçlar.

---

## 2. Vize Sürümü ile Gelişmiş Final Sürümü Karşılaştırması

Projenin **Vize** çalışması aşamasındaki kısıtlı yapısı, **Final** projesinde endüstri mühendisliği, bakım teorisi ve simülasyon metodolojisine uygun şekilde son derece gelişmiş bir mimariye dönüştürülmüştür. Yapılan geliştirmeler aşağıdaki tabloda özetlenmiştir:

| Özellik / Metrik | Vize Sürümü (Mid-term) | İlk Final Taslağı | Gelişmiş Final Sürümü (Son Hali) |
| :--- | :--- | :--- | :--- |
| **Hat Mimarisi** | Tek Aşamalı (Tüm makineler tek bir havuzdaydı). | Ardışık 3 Aşamalı Üretim Hattı (Kesim $\rightarrow$ Montaj $\rightarrow$ Paketleme). | **Ardışık 3 Aşamalı Üretim Hattı** (Ara stok kısıtlamaları entegreli). |
| **Ara Stok & Kuyruklar** | Sınırsız kuyruk kapasitesi. | Sınırsız kuyruk kapasitesi. | **Ara Stok (Buffer/WIP) Sınırları ve Bloklanma (Blocking):** İstasyonlar arasındaki ara stoklar sınırlıdır. Sonraki istasyon dolduğunda önceki makine işini bitirse bile bloklanır ve çalışmayı durdurur. |
| **Arıza ve Bakım Modeli** | Tek bir genel arıza olasılığı. | Aşama bazlı arıza olasılığı ve ortak teknisyen havuzu. | **Makine Aşınması (Aging) & Önleyici Bakım (PM):** Makineler çalıştıkça arıza olasılıkları dinamik olarak artar (Aşınma). Kullanıcı "Yalnızca Arıza Durumunda Tamir" ile "Periyodik Önleyici Bakım" stratejilerini kıyaslayabilir. |
| **Ekonomik / Finansal Katman** | Yok. | Yok. | **Finansal Analiz (P&L):** Üretilen ürünlerden elde edilen gelir, makine işletme maliyetleri, teknisyen ücretleri ve müşteri gecikme cezaları (SLA) hesaplanarak sistemin net kârlılığı hesaplanır. |
| **Veri Analitiği Grafikleri** | Basit bekleme süresi histogramı. | Makine verimliliği (stacked) ve bekleme süresi kutu grafiği. | **4 Durumlu OEE Grafiği:** Makinelerin zaman kullanımı; "Aktif Üretim", "Bloklanma", "Arıza/Bakım Duruşu" ve "Atıl Kalma (Boşta)" olarak 4 duruma ayrılarak Plotly ile görselleştirilir. |
| **Karar Destek Sistemi** | Sadece kuyruk süresi tespiti. | Teknik bekleme sürelerine göre makine artırma önerileri. | **Ekonomik ve Teknik Karar Desteği:** Ara stok bloklanma analizleri, önleyici bakım verimliliği ve kârlılığı maksimize edecek makine/teknisyen sayısı optimizasyon önerileri. |

---

## 3. Teorik Alt Yapı ve Matematiksel Dağılımlar

Simülasyonda kullanılan olaylar ve süreler olasılıksal (stokastik) olarak modellenmiştir:
- **İşlerin Geliş Süreçleri:** Siparişlerin fabrikaya geliş zamanları arasındaki süreler **Eksponansiyel (Üstel) Dağılım** ile modellenmiştir ($f(t) = \lambda e^{-\lambda t}$).
- **Makine İşlem Süreleri (Processing Times):** Kesim, montaj ve paketleme aşamalarındaki işlem süreleri her makine grubu için ayrı ayrı belirlenmiş ortalamalara sahip **Eksponansiyel Dağılım** ile çalışmaktadır.
- **Dinamik Arıza ve Yaşlanma Modellemesi:** Her istasyonda tamamlanan her işin ardından, makinenin son bakımdan/arızadan bu yana yaptığı toplam çalışma süresi ($t$) takip edilir. Anlık arıza olasılığı sabit kalmayıp zamanla artar:
  $$P(\text{Arıza}) = \min\left(P_{\text{baz}} \times \left(1 + \alpha \times \frac{t}{60.0}\right), 0.90\right)$$
  Burada $\alpha$ aşınma katsayısını, $t$ ise son bakımdan sonra geçen aktif çalışma süresini (dakika) temsil eder.
- **Bakım ve Onarım Süreleri (Repair & PM Times):** Arıza durumunda teknisyenin makineyi tamir etme süresi ile planlı önleyici bakım (PM) süreleri yine üstel dağılımla simüle edilir.

---

## 4. Gelişmiş Özelliklerin Matematiksel Modellemesi

### A. Ara Stok (WIP) ve Bloklanma (Blocking)
Gerçek hayatta üretim hatlarında makineler arasındaki stok alanları sınırlıdır. Bu durum simülasyonda şu şekilde modellenmiştir:
1. Makine işini bitirdiğinde, sonraki istasyonun önündeki buffer slotundan (`simpy.Resource`) yer talep eder:
   `buffer_req = buffer_slots.request()`
2. Eğer buffer doluysa, makine bu istek tamamlanana kadar **bloklanır**. Bloklu kaldığı süre boyunca makine havuzuna geri dönemez, yeni iş kabul edemez ve elektrik/işletme maliyeti yazmaya devam eder.
3. Sonraki istasyondaki bir makine iş kabul ettiğinde buffer slotunu serbest bırakır:
   `buffer_slots.release(buffer_req)`

### B. Finansal Maliyet Modeli
Sistemin başarısı sadece üretim adetiyle değil, toplam kârlılıkla ölçülür:
- **Net Kâr** = Toplam Gelir - (Makine Maliyeti + Teknisyen Maliyeti + Gecikme Cezası)
- **Gecikme Cezası:** Siparişin fabrikada geçirdiği toplam süre (Sistemde Kalma Süresi) belirlenen gecikme limiti eşiğini ($T_{\text{eşik}}$) aşarsa, aşan her dakika için sisteme gecikme cezası yansıtılır.

---

## 5. Gelişmiş Yazılım Mimarisi ve Kod Yapısı

Sistem nesne yönelimli ve modüler bir yapıda tasarlanmıştır:
1. **`app.py`**: Streamlit tabanlı kullanıcı arayüzüdür. Kullanıcının tüm ara stok kısıtlarını, önleyici bakım parametrelerini, finansal katsayıları ve istasyon özelliklerini yönetmesini sağlar. Net kâr kartını ve finansal P&L tablosunu basar.
2. **`simulation/entities.py`**: İş (`Job`) varlığını tanımlar. Zaman damgalarını tutar.
3. **`simulation/engine.py`**: SimPy ortamını hazırlar. Ara stok kısıtları için kapasiteli kaynakları tanımlar.
4. **`simulation/processes.py`**: Bloklanma, aşınma (yaşlanma) ve önleyici bakım (PM) mantığını yürüten ana SimPy süreçlerini içerir.
5. **`simulation/decision_support.py`**: Simülasyon bittiğinde toplanan metrikleri finansal ve teknik açıdan analiz ederek darboğazları saptar ve kural tabanlı öneriler sunar.
6. **`ui/charts.py`**: Plotly grafik kütüphanesini kullanarak makine verimlilik yığılı çubuk grafiklerini (Aktif, Bloklu, Duruş, Atıl) ve bekleme dağılımlarını hazırlar.

---

## 6. Kullanıcı Arayüzü Tasarımı ve Görselleştirme

Geliştirilen dinamik Streamlit web arayüzü, kullanıcının parametrelerin sistem üzerindeki etkisini anlık olarak görselleştirmesine imkan tanır. Aşağıda iki farklı simülasyon senaryosunun ekran görüntüleri analiz edilmiştir:

### A. Reaktif (Arıza Sonrası) Bakım ve Darboğaz Senaryosu
*Açıklama: Bu senaryoda ara stok limitlerinin yetersiz olması nedeniyle makinelerde yüksek oranda bloklanma (sarı alanlar) yaşanmış ve plansız arızalar nedeniyle net kâr düşmüştür.*

![Reaktif Senaryo Görünümü](images/bulanık%20mantık1.PNG)
*Şekil 1: Reaktif Bakım ve Düşük Ara Stok Limitli Simülasyon Çıktıları*

### B. Önleyici Bakım ve Optimize Edilmiş Ara Stok Senaryosu
*Açıklama: Önleyici bakım politikasının aktif edilmesiyle plansız arızalar en aza indirilmiş, ara stok sınırlarının yükseltilmesiyle bloklanmalar çözülmüş ve sistem yüksek kârlılığa ulaştırılmıştır.*

![Önleyici Bakım ve Optimize Senaryo Görünümü](images/bulanık%20mantık2.PNG)
*Şekil 2: Önleyici Bakım ve Optimize Parametrelerle Maksimum Kârlılık Çıktıları*

### C. Yoğunluk Haritası, Karar Destek Önerileri ve OEE Durum Tablosu
*Açıklama: Simülasyon sonrasında üretilen zamana yayılmış yoğunluk haritası, kural tabanlı karar destek sistemi önerileri ve her makineye ait ayrıntılı OEE durum tablosu.*

![Karar Destek ve Veri Tablosu Görünümü](images/bulanık%20mantık3.PNG)
*Şekil 3: Karar Destek Önerileri ve Detaylı OEE Performans Tablosu*

---

## 7. Üretilen Sentetik Veri Setleri

Geliştirilen simülasyon motoru, gelecekte makine öğrenmesi modelleri veya ileri seviye veri analitiği (Kuyruk Teorisi, OEE iyileştirme vb.) çalışmalarında kullanılmak üzere iki adet CSV formatında sentetik veri seti ihraç edebilmektedir. Bu veri setlerinin yapıları ve öznitelikleri şunlardır:

### A. Sipariş Bekleme ve Çevrim Süresi Veri Seti (`sentetik_siparis_verileri.csv`)
Bu veri seti, fabrikaya giren ve üretim hattını tamamlayan her bir siparişin zaman damgalarını ve kuyrukta bekleme sürelerini saniye hassasiyetinde tutar:
- **İş ID:** Siparişe atanan benzersiz kimlik numarası (Sıralı tam sayı).
- **Geliş Zamanı:** Siparişin fabrikaya giriş yaptığı zaman damgası (Simülasyon dakikası).
- **Kesim Bekleme (dk):** Siparişin Kesim istasyonu önündeki kuyrukta boş makine beklediği süre.
- **Montaj Bekleme (dk):** Siparişin Kesim'den çıkıp Montaj istasyonu önündeki kuyrukta beklediği süre.
- **Paketleme Bekleme (dk):** Siparişin Montaj'dan çıkıp Paketleme önünde beklediği süre.
- **Toplam Bekleme (dk):** Siparişin üretim hattı boyunca kuyruklarda geçirdiği toplam süre (Kesim + Montaj + Paketleme).
- **Sistemde Kalma Süresi (dk):** Siparişin fabrikada geçirdiği toplam çevrim süresi (Cycle Time - Girişten çıkışa kadar geçen süre).

### B. Makine Performans ve Duruş Veri Seti (`sentetik_makine_verileri.csv`)
Bu veri seti, üretim hattında bulunan her bir makinenin zaman kullanım oranlarını ve OEE (Toplam Ekipman Etkinliği) durum kırılımlarını yüzde (%) olarak saklar:
- **İstasyon:** Makinenin ait olduğu operasyonel aşama (Kesim, Montaj veya Paketleme).
- **Makine:** Makinenin benzersiz adı (örn: Kesim-1, Montaj-2).
- **Aktif Çalışma (%):** Makinenin katma değerli üretim yaptığı zamanın toplam simülasyon süresine oranı.
- **Bloklanma (%):** Makinenin işini bitirmesine rağmen, sonraki istasyonun ara stok (buffer) alanı dolu olduğu için bloke olarak durduğu süre oranı.
- **Duruş/Bakım (%):** Makinenin plansız arızalar veya planlı önleyici bakımlar (PM) sebebiyle üretim yapamadığı süre oranı.
- **Atıl Kapasite (%):** İstasyonda iş kuyruğu olmaması nedeniyle makinenin boşta (idle) beklediği süre oranı.

---

## 8. Sonuç ve Optimizasyon Çıktıları

Geliştirilen bu sistem sayesinde öğrenciler ve endüstri mühendisleri şu analizleri yapabilirler:
1. **Ara Stok Optimizasyonu:** Ara stok limitinin çok küçük tutulması durumunda bloklanma sürelerinin arttığını, çok büyük tutulduğunda ise ara stok maliyetlerinin ve gecikmelerin nasıl değiştiğini gözlemleyebilirler.
2. **Bakım Stratejisi Analizi:** "Yalnızca Arıza" modunda yüksek plansız duruşların kârlılığı nasıl düşürdüğünü; "Önleyici Bakım" açıldığında ise planlı duruşların arıza frekansını düşürerek net kârı nasıl artırdığını deneyimleyebilirler.
3. **Finansal Hat Dengeleme:** Makinelerin atıl kalma süreleri ile gecikme cezaları arasındaki finansal dengeyi (Trade-off) kurarak, toplam kârı maksimize eden en optimum makine ve teknisyen kadrosunu bulabilirler.
