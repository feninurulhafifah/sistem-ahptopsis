import numpy as np

# ============================================================
# DATA KRITERIA DAN ALTERNATIF
# ============================================================

KRITERIA = [
    {"kode": "C1", "nama": "Minat"},
    {"kode": "C2", "nama": "Kemampuan Pemrograman"},
    {"kode": "C3", "nama": "Problem Solving"},
    {"kode": "C4", "nama": "Ketertarikan Teknologi"},
    {"kode": "C5", "nama": "Pengalaman/Project"},
    {"kode": "C6", "nama": "Orientasi Karier"},
]

ALTERNATIF = [
    {"kode": "A1", "nama": "Artificial Intelligence"},
    {"kode": "A2", "nama": "Software Development"},
    {"kode": "A3", "nama": "Computer Network"},
]

# Matriks perbandingan berpasangan AHP (dari penilaian pakar/dosen)
# Skala Saaty 1-9
MATRIKS_AHP = np.array([
    [1,   2,   3,   4,   3,   2],   # C1 Minat
    [0.5, 1,   2,   3,   2,   1],   # C2 Kemampuan Pemrograman
    [0.33,0.5, 1,   2,   1,   0.5], # C3 Problem Solving
    [0.25,0.33,0.5, 1,   0.5, 0.33],# C4 Ketertarikan Teknologi
    [0.33,0.5, 1,   2,   1,   0.5], # C5 Pengalaman/Project
    [0.5, 1,   2,   3,   2,   1],   # C6 Orientasi Karier
])

RI = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12,
      6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}


# ============================================================
# AHP — MENGHITUNG BOBOT KRITERIA
# ============================================================

def hitung_ahp(matriks):
    """
    Menghitung bobot kriteria menggunakan AHP.
    Returns: bobot (array), CR (float)
    """
    n = len(matriks)

    # 1. Normalisasi: bagi setiap elemen dengan jumlah kolomnya
    jumlah_kolom = matriks.sum(axis=0)
    normalisasi = matriks / jumlah_kolom

    # 2. Bobot = rata-rata baris dari matriks ternormalisasi
    bobot = normalisasi.mean(axis=1)

    # 3. Uji konsistensi
    # Hitung lambda max
    lambda_max = np.sum(matriks.dot(bobot) / bobot) / n

    # Consistency Index
    CI = (lambda_max - n) / (n - 1)

    # Consistency Ratio
    CR = CI / RI[n] if RI[n] != 0 else 0

    return bobot, CR


# ============================================================
# TOPSIS — MENGHITUNG PERINGKAT ALTERNATIF
# ============================================================

def hitung_topsis(jawaban_mahasiswa, bobot_kriteria):
    """
    Menghitung peringkat alternatif menggunakan TOPSIS.
    
    jawaban_mahasiswa: array 2D (3 alternatif x 6 kriteria)
    bobot_kriteria: array 1D (6 kriteria)
    
    Returns: nilai_preferensi (array), peringkat (list of dict)
    """
    matriks = np.array(jawaban_mahasiswa, dtype=float)

    # 1. Normalisasi matriks keputusan
    pembagi = np.sqrt((matriks ** 2).sum(axis=0))
    normalisasi = matriks / pembagi

    # 2. Pembobotan ternormalisasi
    terbobot = normalisasi * bobot_kriteria

    # 3. Solusi ideal positif dan negatif
    A_positif = terbobot.max(axis=0)
    A_negatif = terbobot.min(axis=0)

    # 4. Jarak ke solusi ideal
    D_positif = np.sqrt(((terbobot - A_positif) ** 2).sum(axis=1))
    D_negatif = np.sqrt(((terbobot - A_negatif) ** 2).sum(axis=1))

    # 5. Nilai preferensi
    V = D_negatif / (D_positif + D_negatif + 1e-9)

    # 6. Peringkat
    urutan = np.argsort(V)[::-1]
    peringkat = []
    for i, idx in enumerate(urutan):
        peringkat.append({
            "peringkat": i + 1,
            "kode": ALTERNATIF[idx]["kode"],
            "nama": ALTERNATIF[idx]["nama"],
            "nilai": round(float(V[idx]) * 100, 2)
        })

    return V, peringkat


# ============================================================
# FUNGSI UTAMA — DIPANGGIL DARI FLASK
# ============================================================

def proses_rekomendasi(jawaban_kuesioner):
    """
    jawaban_kuesioner: list berisi 15 nilai (skala 1-5)
    
    Returns: dict berisi hasil lengkap
    """
    # 1. Hitung bobot AHP
    bobot, CR = hitung_ahp(MATRIKS_AHP)

    # 2. Konversi jawaban kuesioner (15 item) menjadi matriks 3x6
    # Item 1-5   → C1 (Minat) untuk A1, A2, A3
    # Item 6-10  → C2 (Kemampuan) untuk A1, A2, A3
    # Item 11-15 → C3 (Problem Solving) untuk A1, A2, A3
    # (Dalam implementasi nyata, pemetaan disesuaikan dengan desain kuesioner)
    
    # Contoh pemetaan sederhana: 15 item dibagi rata ke 6 kriteria
    # Setiap kriteria diwakili oleh 2-3 item, dirata-rata
    j = jawaban_kuesioner
    
    # Pemetaan: setiap kriteria diwakili oleh 2-3 item
    # C1: item 1,2,3 | C2: item 4,5,6 | C3: item 7,8
    # C4: item 9,10 | C5: item 11,12 | C6: item 13,14,15
    skor_kriteria = np.array([
        np.mean([j[0], j[1], j[2]]),   # C1
        np.mean([j[3], j[4], j[5]]),   # C2
        np.mean([j[6], j[7]]),         # C3
        np.mean([j[8], j[9]]),         # C4
        np.mean([j[10], j[11]]),       # C5
        np.mean([j[12], j[13], j[14]]) # C6
    ])

    # 3. Buat matriks keputusan 3 alternatif x 6 kriteria
    # Setiap alternatif diberi skor berdasarkan kedekatan dengan profil
    # (Dalam implementasi nyata, ini bisa dari pembobotan berbeda per alternatif)
    
    # Contoh: matriks keputusan berdasarkan skor kriteria mahasiswa
    # dan karakteristik setiap alternatif
    matriks_keputusan = np.array([
        # AI: butuh C1 tinggi, C2 tinggi, C3 tinggi, C4 tinggi, C5 sedang, C6 tinggi
        [skor_kriteria[0]*0.9, skor_kriteria[1]*1.0, skor_kriteria[2]*1.0,
         skor_kriteria[3]*1.0, skor_kriteria[4]*0.8, skor_kriteria[5]*0.9],
        # Software Dev: butuh C1 tinggi, C2 tinggi, C3 tinggi, C4 sedang, C5 tinggi, C6 tinggi
        [skor_kriteria[0]*1.0, skor_kriteria[1]*1.0, skor_kriteria[2]*0.9,
         skor_kriteria[3]*0.8, skor_kriteria[4]*1.0, skor_kriteria[5]*1.0],
        # Network: butuh C1 sedang, C2 sedang, C3 tinggi, C4 tinggi, C5 sedang, C6 sedang
        [skor_kriteria[0]*0.7, skor_kriteria[1]*0.7, skor_kriteria[2]*1.0,
         skor_kriteria[3]*1.0, skor_kriteria[4]*0.7, skor_kriteria[5]*0.7],
    ])

    # 4. Hitung TOPSIS
    V, peringkat = hitung_topsis(matriks_keputusan, bobot)

    # 5. Saran karier
    karier = {
        "Artificial Intelligence": [
            "Machine Learning Engineer", "Data Scientist",
            "AI Research Scientist", "Computer Vision Engineer"
        ],
        "Software Development": [
            "Web Developer", "Mobile Application Developer",
            "System Analyst", "Backend Engineer"
        ],
        "Computer Network": [
            "Network Engineer", "Network Administrator",
            "Cybersecurity Analyst", "Cloud Engineer"
        ]
    }

    konsentrasi_utama = peringkat[0]["nama"]

    return {
        "bobot_kriteria": [
            {"kode": KRITERIA[i]["kode"], "nama": KRITERIA[i]["nama"],
             "bobot": round(float(bobot[i]), 4)}
            for i in range(len(KRITERIA))
        ],
        "CR": round(float(CR), 4),
        "peringkat": peringkat,
        "konsentrasi_utama": konsentrasi_utama,
        "saran_karier": karier.get(konsentrasi_utama, [])
    }