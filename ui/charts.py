"""
Arayüz için gerekli Plotly grafiklerini oluşturur.
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def plot_machine_utilization(metrics_df, total_time):
    """Makinelerin çalışma, bloklanma, duruş ve atıl kalma oranlarını gösterir."""
    if metrics_df.empty:
        return go.Figure()
        
    fig = go.Figure(data=[
        go.Bar(name='Üretim (Aktif)', x=metrics_df['Makine'], y=metrics_df['Aktif Çalışma (%)'], marker_color='#2ca02c'),
        go.Bar(name='Bloklu (Ara Stok Dolu)', x=metrics_df['Makine'], y=metrics_df['Bloklanma (%)'], marker_color='#ff7f0e'),
        go.Bar(name='Arıza / PM Duruş', x=metrics_df['Makine'], y=metrics_df['Duruş/Bakım (%)'], marker_color='#d62728'),
        go.Bar(name='Atıl (Boşta)', x=metrics_df['Makine'], y=metrics_df['Atıl Kapasite (%)'], marker_color='#7f7f7f'),
    ])
    
    # Y-Ekseni %100'ü geçmesin
    fig.update_layout(
        barmode='stack', 
        title="Makine Zaman Dağılımı ve Duruş Oranları",
        yaxis=dict(title='Yüzde (%)', range=[0, 105])
    )
    return fig

def plot_wait_times(jobs_df):
    """Her aşamadaki bekleme sürelerinin dağılımını Kutu Grafiği (Box Plot) ile gösterir."""
    if jobs_df.empty:
        return go.Figure()
        
    # Geniş formattaki DataFrame'i uzun (melted) formata dönüştür
    # Sütun isimleri app.py'de tanımlanacak olanlarla eşleşmeli
    melted_df = pd.melt(
        jobs_df, 
        id_vars=['İş ID'], 
        value_vars=['Kesim Bekleme (dk)', 'Montaj Bekleme (dk)', 'Paketleme Bekleme (dk)'],
        var_name='Aşama', 
        value_name='Bekleme Süresi (dk)'
    )
    
    # Kutu Grafiği çiz
    fig = px.box(
        melted_df, 
        x='Aşama', 
        y='Bekleme Süresi (dk)', 
        color='Aşama',
        title='İstasyon Bazlı Kuyrukta Bekleme Süresi Dağılımı',
        color_discrete_map={
            'Kesim Bekleme (dk)': '#1f77b4',
            'Montaj Bekleme (dk)': '#ff7f0e',
            'Paketleme Bekleme (dk)': '#2ca02c'
        },
        labels={'Bekleme Süresi (dk)': 'Bekleme Süresi (Dakika)', 'Aşama': 'Üretim İstasyonu'}
    )
    
    fig.update_layout(showlegend=False)
    return fig

def plot_hourly_heatmap(jobs_df):
    """Zamana (Örn: Saat dilimine) yayılan iş geliş yoğunluğunu ısı haritası olarak gösterir."""
    if jobs_df.empty:
        return go.Figure()
        
    # Geliş zamanını 60 dakikalık (saatlik) dilimlere grupla
    jobs_df['Saat Dilimi'] = (jobs_df['Geliş Zamanı'] // 60).astype(int) + 1
    
    # Her saat başı gelen işlerin toplam sayısını al
    heatmap_data = jobs_df.groupby('Saat Dilimi').size().reset_index(name='Gelen İş Sayısı')
    
    # Sadece görselleştirmek için Y eksenine statik bir değer atayalım ('Hat Yoğunluğu' vb.)
    heatmap_data['Metrik'] = 'Geliş Sıklığı'
    
    fig = px.density_heatmap(
        heatmap_data, 
        x="Saat Dilimi", 
        y="Metrik", 
        z="Gelen İş Sayısı", 
        color_continuous_scale="YlOrRd", 
        title="Zamana Göre Üretim Hattı Yoğunluğu (Isı Haritası)"
    )
    return fig
