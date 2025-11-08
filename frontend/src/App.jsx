// frontend/src/App.jsx

import React, { useState } from 'react';
import './App.css';

function App() {
  // State untuk menyimpan input dari user
  const [userId, setUserId] = useState('');
  
  // State untuk menyimpan hasil dari API
  const [persona, setPersona] = useState(null);
  
  // State untuk menyimpan pesan error
  const [error, setError] = useState(null);
  
  // State untuk tahu kapan harus menampilkan loading
  const [isLoading, setIsLoading] = useState(false);

  // Fungsi yang dipanggil saat tombol di-klik
  const handleSubmit = async (e) => {
    e.preventDefault(); // Mencegah form refresh halaman
    
    // 1. Reset state
    setPersona(null);
    setError(null);
    setIsLoading(true);

    try {
      // 2. Panggil API FastAPI kita!
      // sudah perbaiki CORS di backend
      const response = await fetch(`http://127.0.0.1:8000/api/v1/learning-style/${userId}`);

      // 3. Ubah respons menjadi JSON
      const data = await response.json();

      // 4. Cek apakah API mengembalikan error (seperti 404 atau 500)
      if (!response.ok) {
        // 'data.detail' adalah format error default dari FastAPI
        throw new Error(data.detail || 'Terjadi kesalahan');
      }

      // 5. SUKSES! Simpan data persona ke state
      setPersona(data);

    } catch (err) {
      // 6. GAGAL! Simpan pesan error ke state
      setError(err.message);
    } finally {
      // 7. Selesai (sukses atau gagal), berhenti loading
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🔍 Cek Gaya Belajar Siswa</h1>
        
        {/* Form Input */}
        <form onSubmit={handleSubmit} className="search-form">
          <input
            type="number"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="Masukkan User ID (cth: 72, 30, 114)"
            className="search-input"
          />
          <button type="submit" disabled={isLoading} className="search-button">
            {isLoading ? 'Mencari...' : 'Cari'}
          </button>
        </form>

        {/* --- Area Hasil --- */}
        <div className="result-container">
          {/* 1. Jika sedang loading */}
          {isLoading && <p>Loading...</p>}

          {/* 2. Jika ada error */}
          {error && (
            <div className="result-card error-card">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* 3. Jika sukses dan ada data persona */}
          {persona && (
            <div className="result-card persona-card">
              <h2>{persona.persona_name}</h2>
              <p><strong>User ID:</strong> {persona.user_id}</p>
              <p><strong>Cluster:</strong> {persona.cluster}</p>
              <p><strong>Deskripsi:</strong> {persona.persona_description}</p>
            </div>
          )}
        </div>

      </header>
    </div>
  );
}

export default App;