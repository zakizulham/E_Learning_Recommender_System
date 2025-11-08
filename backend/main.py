import pandas as pd
import joblib
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware  # <--- INI PERBAIKANNYA

# Inisialisasi Aplikasi FastAPI
app = FastAPI(
    title="API Gaya Belajar Siswa",
    description="API untuk memprediksi dan mengambil persona gaya belajar siswa.",
    version="1.0"
)

# Konfigurasi CORS
# Izinkan frontend React kita (localhost:5173) untuk "berbicara" dengan backend ini.
origins = [
    "http://localhost:5173",  # Port default Vite/React
    "http://localhost:3000",  # Port React (jaga-jaga)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kamus Definisi Persona
# Menerjemahkan cluster_id (int) -> info persona (string)
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

# Pemuatan Artefak (Model & Data) saat Startup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '../data/user_features_with_clusters.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'kmeans_model.joblib')
SCALER_PATH = os.path.join(BASE_DIR, 'scaler.joblib')

try:
    # Data CSV adalah yang utama untuk V1 (mengambil cluster yang sudah ada)
    df_clustered = pd.read_csv(DATA_PATH, index_col='user_id')
    print(f"Berhasil memuat data cluster: {DATA_PATH}")

    # Model & scaler dimuat untuk V2 (prediksi real-time)
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print(f"Berhasil memuat model dan scaler.")

except FileNotFoundError as e:
    print(f"Error: File tidak ditemukan. Pastikan file ada di path yang benar.")
    print(e)
    df_clustered = None
except Exception as e:
    print(f"Error saat memuat artefak: {e}")
    df_clustered = None


# Model Data Pydantic (Validasi Respons)
class LearningStyleResponse(BaseModel):
    user_id: int
    cluster: int
    persona_name: str
    persona_description: str

# Endpoint API
@app.get("/api/v1/learning-style/{user_id}", response_model=LearningStyleResponse)
async def get_learning_style(user_id: int):
    """
    Mengambil persona gaya belajar untuk user_id yang sudah ada (di-cluster).
    """
    if df_clustered is None:
        raise HTTPException(status_code=500, detail="Data cluster tidak dimuat di server.")

    try:
        # 1. Cari user_id di DataFrame
        user_data = df_clustered.loc[user_id]
        
        # 2. Ambil label clusternya
        cluster_label = int(user_data['cluster'])
        
        # 3. Cari persona di kamus
        persona_info = PERSONA_MAP.get(cluster_label)
        
        if persona_info is None:
            raise HTTPException(status_code=500, detail=f"Cluster {cluster_label} tidak memiliki definisi persona.")

        # 4. Kembalikan respons JSON yang rapi
        return LearningStyleResponse(
            user_id=user_id,
            cluster=cluster_label,
            persona_name=persona_info['name'],
            persona_description=persona_info['description']
        )

    except KeyError:
        # Jika .loc[user_id] gagal (KeyError), berarti user_id tidak ada
        raise HTTPException(
            status_code=404, 
            detail=f"User ID {user_id} tidak ditemukan. User ini mungkin tidak aktif (kurang dari 5 interaksi)."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal: {str(e)}")