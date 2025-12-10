import streamlit as st
import pandas as pd
import numpy as np
from aco import AntColonyOptimizer
from data import LOCATIONS
from math import radians, cos, sin, asin, sqrt
import folium
from streamlit_folium import st_folium

# Sayfa Ayarları
st.set_page_config(page_title="İstanbul Tur Rotası", layout="wide")

st.title("🐜 İstanbul Tarihi Mekanlar - Rota Optimizasyonu")
st.markdown("**Senaryo 6:** 1 Günde 15 Tarihi Mekan için En Kısa Rota")

# --- SESSION STATE (HAFIZA) AYARLARI ---
# Sonuçların ekranda kalması için hafızayı başlatıyoruz
if 'best_path' not in st.session_state:
    st.session_state.best_path = None
if 'history' not in st.session_state:
    st.session_state.history = None
if 'total_dist' not in st.session_state:
    st.session_state.total_dist = 0

# --- YARDIMCI FONKSİYONLAR ---
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 
    return c * r

def get_distance_matrix(locations):
    places = list(locations.keys())
    size = len(places)
    matrix = np.zeros((size, size))

    for i in range(size):
        for j in range(size):
            if i == j:
                matrix[i][j] = np.inf
            else:
                loc1 = locations[places[i]]
                loc2 = locations[places[j]]
                # API Anahtarı kontrolü
                # Eğer secrets dosyasında API key varsa onu kullanabilirsin
                # Şimdilik güvenli mod (Haversine) ile devam ediyoruz.
                dist = haversine(loc1['lon'], loc1['lat'], loc2['lon'], loc2['lat'])
                matrix[i][j] = dist
    return matrix, places

# --- SIDEBAR (AYARLAR) ---
st.sidebar.header("⚙️ Algoritma Ayarları")
st.sidebar.info("Simülasyon parametrelerini buradan yapılandırabilirsiniz.")

n_ants = st.sidebar.slider("Karınca Sayısı", 10, 100, 30)
n_iterations = st.sidebar.slider("İterasyon Sayısı", 10, 200, 50)
decay = st.sidebar.slider("Buharlaşma Oranı (Decay)", 0.1, 0.9, 0.5)
alpha = st.sidebar.slider("Feromon Önemi (Alpha)", 0.1, 5.0, 1.0)
beta = st.sidebar.slider("Mesafe Önemi (Beta)", 0.1, 5.0, 2.0)

# --- HESAPLAMA BUTONU ---
if st.button("Rotayı Hesapla 🚀"):
    with st.spinner('Karıncalar yola çıktı... En kısa yol aranıyor...'):
        # 1. Mesafe Matrisini Hazırla
        distance_matrix, place_names = get_distance_matrix(LOCATIONS)
        
        # 2. Algoritmayı Çalıştır
        optimizer = AntColonyOptimizer(
            distances=distance_matrix,
            n_ants=n_ants,
            n_best=int(n_ants / 5),
            n_iterations=n_iterations,
            decay=decay,
            alpha=alpha,
            beta=beta
        )
        
        best_path, history = optimizer.run()
        
        # 3. Sonuçları HAFIZAYA (Session State) Kaydet
        st.session_state.best_path = best_path
        st.session_state.history = history
        st.session_state.total_dist = best_path[1]
        st.session_state.place_names = place_names # İsimleri de kaydedelim

# --- SONUÇLARI GÖSTERME (Eğer hafızada sonuç varsa ekrana bas) ---
if st.session_state.best_path is not None:
    
    st.success(f"Optimizasyon Tamamlandı! Toplam Mesafe: {st.session_state.total_dist:.2f} km")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📍 Harita Üzerinde Rota")
        # Harita Merkezi
        m = folium.Map(location=[41.015137, 28.979530], zoom_start=13)
        
        path_indices = st.session_state.best_path[0]
        place_names = st.session_state.place_names
        
        # Noktaları ve Çizgileri Ekle
        for i, (start_idx, end_idx) in enumerate(path_indices):
            start_name = place_names[start_idx]
            end_name = place_names[end_idx]
            
            start_loc = [LOCATIONS[start_name]['lat'], LOCATIONS[start_name]['lon']]
            end_loc = [LOCATIONS[end_name]['lat'], LOCATIONS[end_name]['lon']]
            
            # Marker ekle
            folium.Marker(start_loc, tooltip=f"{i+1}. {start_name}", icon=folium.Icon(color='blue', icon='info-sign')).add_to(m)
            
            # Çizgi ekle
            folium.PolyLine([start_loc, end_loc], color="red", weight=3, opacity=0.8).add_to(m)
        
        st_folium(m, width=700)
        
    with col2:
        st.subheader("📈 İterasyon Grafiği")
        st.line_chart(st.session_state.history)
        st.caption("Grafik, karıncaların her iterasyonda bulduğu en kısa mesafeyi gösterir.")
        
        st.subheader("📝 Rota Adımları")
        rota_text = ""
        path_indices = st.session_state.best_path[0]
        for i, (start_idx, end_idx) in enumerate(path_indices):
            rota_text += f"{i+1}. {place_names[start_idx]} ➡️ {place_names[end_idx]}\n"
        st.text(rota_text)

else:
    st.info("Ayarları yapın ve 'Rotayı Hesapla' butonuna basın.")