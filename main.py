import streamlit as st
import pandas as pd
import numpy as np
from aco import AntColonyOptimizer
from data import LOCATIONS
from math import radians, cos, sin, asin, sqrt
import folium
from streamlit_folium import st_folium

# Sayfa Ayarları
st.set_page_config(page_title="İstanbul Tur Rotası (ACO)", layout="wide")

st.title("🐜 Karınca Kolonisi ile İstanbul Gezi Rotası Optimizasyonu")
st.markdown("**Senaryo 6:** 1 Günde 15 Tarihi Mekan için En Kısa Rota")

# --- YARDIMCI FONKSİYONLAR ---
def haversine(lon1, lat1, lon2, lat2):
    """
    İki koordinat arası kuş uçuşu mesafeyi (km) hesaplar.
    API Anahtarı yoksa bu kullanılır.
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Dünya yarıçapı (km)
    return c * r

def get_distance_matrix(locations):
    """
    Mesafe matrisini oluşturur. 
    Not: Gerçek projede burada Google Maps API kullanılır.
    Ancak API anahtarı olmayanlar için Haversine (kuş uçuşu) formülü ile
    yedekli çalışır.
    """
    places = list(locations.keys())
    size = len(places)
    matrix = np.zeros((size, size))

    for i in range(size):
        for j in range(size):
            if i == j:
                matrix[i][j] = np.inf # Kendine olan mesafe sonsuz (gitmesin diye)
            else:
                loc1 = locations[places[i]]
                loc2 = locations[places[j]]
                # Normalde API çağrısı yapılır
                # Şimdilik matematiksel hesaplanır
                dist = haversine(loc1['lon'], loc1['lat'], loc2['lon'], loc2['lat'])
                matrix[i][j] = dist
    return matrix, places

# --- SIDEBAR (PARAMETRELER) ---
st.sidebar.header("Algoritma Ayarları")
st.sidebar.info("Simülasyon parametrelerini buradan yapılandırabilirsiniz.")

n_ants = st.sidebar.slider("Karınca Sayısı", 10, 100, 30)
n_iterations = st.sidebar.slider("İterasyon Sayısı", 10, 200, 50)
decay = st.sidebar.slider("Buharlaşma Oranı (Decay)", 0.1, 0.9, 0.5)
alpha = st.sidebar.slider("Feromon Önemi (Alpha)", 0.1, 5.0, 1.0)
beta = st.sidebar.slider("Mesafe Önemi (Beta)", 0.1, 5.0, 2.0)

# --- UYGULAMA MANTIĞI ---
if st.button("Rotayı Hesapla 🚀"):
    with st.spinner('Karıncalar yola çıktı... En kısa yol aranıyor...'):
        
        # 1. Mesafe Matrisini Hazırla
        distance_matrix, place_names = get_distance_matrix(LOCATIONS)
        
        # 2. Algoritmayı Çalıştır
        optimizer = AntColonyOptimizer(
            distances=distance_matrix,
            n_ants=n_ants,
            n_best=int(n_ants / 5), # En iyi %20
            n_iterations=n_iterations,
            decay=decay,
            alpha=alpha,
            beta=beta
        )
        
        best_path, history = optimizer.run()
        
        # 3. Sonuçları Göster
        st.success(f"Optimizasyon Tamamlandı! Toplam Mesafe: {best_path[1]:.2f} km")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📍 Harita Üzerinde Rota")
            # Harita Merkezi (İstanbul)
            m = folium.Map(location=[41.01521152533961, 28.979540496313042], zoom_start=13)
            
            path_indices = best_path[0]
            route_coords = []
            
            # Noktaları ve Çizgileri Ekle
            for i, (start_idx, end_idx) in enumerate(path_indices):
                start_name = place_names[start_idx]
                end_name = place_names[end_idx]
                
                start_loc = [LOCATIONS[start_name]['lat'], LOCATIONS[start_name]['lon']]
                end_loc = [LOCATIONS[end_name]['lat'], LOCATIONS[end_name]['lon']]
                
                # Marker ekle
                folium.Marker(start_loc, tooltip=f"{i+1}. {start_name}").add_to(m)
                
                # Çizgi ekle
                folium.PolyLine([start_loc, end_loc], color="red", weight=2.5, opacity=1).add_to(m)
            
            st_folium(m, width=700)
            
        with col2:
            st.subheader("📈 İterasyon Grafiği")
            st.line_chart(history)
            st.write("Grafik, karıncaların her iterasyonda daha kısa bir yol bulduğunu gösterir (Yakınsama).")
            
            st.subheader("📝 Rota Adımları")
            rota_text = ""
            for i, (start_idx, end_idx) in enumerate(path_indices):
                rota_text += f"{i+1}. {place_names[start_idx]} ➡️ {place_names[end_idx]}\n"
            st.text(rota_text)

else:
    st.write("Ayarları yapın ve 'Rotayı Hesapla' butonuna basın.")