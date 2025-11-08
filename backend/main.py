import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

# --- 1. INISIALISASI APLIKASI ---
# Ini adalah "server" FastAPI kita
app = FastAPI(
    title="API Gaya Belajar Siswa",
    description="API untuk memprediksi dan mengambil persona gaya belajar siswa.",
    version="1.0"
)

# --- 2. KAMUS PERSONA ---
# Di sinilah kita "menerjemahkan" output cluster (0, 1, 2, 3)
# menjadi sesuatu yang bisa dibaca manusia.
# PENTING: Sesuaikan ini dengan analisis kita di Notebook 03!
PERSONA_MAP = {
    0: {
        "name": "Si Penyelesai Efisien",
        "description": "Fokus, suka tutorial singkat, dan hampir selalu menyelesaikan apa yang dimulai."
    },
    1: {
        "name": "Si Penjelajah Ahli",
        "description": "Sangat aktif, menjelajahi banyak topik, dan tetap menyelesaikan video."
    },
    2: {
        "name": "Si 'Drop-off'",
        "description": "Cenderung tidak puas, memiliki tingkat penyelesaian terendah dan berisiko churn."
    },
    3: {
        "name": "Si Pelajar Mendalam",
        "description": "Suka konten yang panjang dan mendalam (webcast) dan sangat berkomitmen."
    }
}

# --- 3. MEMUAT ARTEFAK (MODEL & DATA) ---
# Kita muat semua file yang kita butuhkan saat server pertama kali menyala.

# Tentukan path relatif dari file main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '../data/user_features_with_clusters.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'kmeans_model.joblib')
SCALER_PATH = os.path.join(BASE_DIR, 'scaler.joblib')

try:
    # Muat data CSV yang berisi user_id dan cluster_id mereka
    df_clustered = pd.read_csv(DATA_PATH, index_col='user_id')
    print(f"Berhasil memuat data cluster: {DATA_PATH}")

    # Muat model dan scaler (kita akan pakai ini di V2, tapi muat sekarang)
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print(f"Berhasil memuat model dan scaler: {MODEL_PATH}, {SCALER_PATH}")

except FileNotFoundError as e:
    print(f"Error: File tidak ditemukan. Pastikan file ada di path yang benar.")
    print(e)
    # Jika file tidak ada, kita tidak bisa menjalankan server.
    # Untuk V1, kita hanya butuh CSV, jadi kita bisa beri 'pass' jika model/scaler belum ada
    # tapi untuk sekarang, kita asumsikan semua ada.
    df_clustered = None # Gagal memuat


# --- 4. TENTUKAN MODEL DATA (UNTUK RESPONSE) ---
# Ini memberi tahu FastAPI format JSON seperti apa yang akan kita kirim kembali
class LearningStyleResponse(BaseModel):
    user_id: int
    cluster: int
    persona_name: str
    persona_description: str

# --- 5. BUAT ENDPOINT API KITA ---

@app.get("/api/v1/learning-style/{user_id}", response_model=LearningStyleResponse)
async def get_learning_style(user_id: int):
    """
    Mengambil persona gaya belajar untuk user_id yang sudah ada (di-cluster).
    """
    if df_clustered is None:
        raise HTTPException(status_code=500, detail="Data cluster tidak dimuat di server.")

    try:
        # 1. Cari user_id di DataFrame kita
        user_data = df_clustered.loc[user_id]
        
        # 2. Ambil label clusternya
        cluster_label = int(user_data['cluster']) # pyright: ignore[reportArgumentType]
        
        # 3. Cari persona di kamus kita
        persona_info = PERSONA_MAP.get(cluster_label)
        
        if persona_info is None:
            # Ini seharusnya tidak terjadi jika data kita konsisten
            raise HTTPException(status_code=500, detail=f"Cluster {cluster_label} tidak memiliki definisi persona.")

        # 4. Kembalikan respons JSON yang rapi
        return LearningStyleResponse(
            user_id=user_id,
            cluster=cluster_label,
            persona_name=persona_info['name'],
            persona_description=persona_info['description']
        )

    except KeyError:
        # Jika .loc[user_id] gagal, berarti user_id tidak ada di data kita
        raise HTTPException(
            status_code=404, 
            detail=f"User ID {user_id} tidak ditemukan. User ini mungkin tidak aktif (kurang dari 5 interaksi)."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal: {str(e)}")