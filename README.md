# Mediagnotek API - Dokumentasi untuk Frontend

## Base URL
```
https://mediagnotek-backend.vercel.app
```

## Swagger (Interactive Docs)
Buka link berikut untuk mencoba semua endpoint langsung dari browser:
```
https://mediagnotek-backend.vercel.app/docs
```

---

## Daftar Endpoint

### 1. Penyakit

**GET /api/v1/diseases** — List semua penyakit (dengan pagination & search)

| Parameter | Tipe   | Wajib | Keterangan                    |
|-----------|--------|-------|-------------------------------|
| page      | number | tidak | Halaman ke-n (default: 1)     |
| size      | number | tidak | Jumlah per halaman (default: 20, max: 100) |
| search    | string | tidak | Cari berdasarkan nama penyakit |

Contoh request:
```
GET /api/v1/diseases?page=1&size=5&search=diabetes
```

Contoh response:
```json
{
  "total": 3,
  "page": 1,
  "size": 5,
  "items": [
    {
      "id": 245,
      "nama": "Diabetes Melitus Tipe 1",
      "deskripsi": "Diabetes melitus tipe 1 adalah..."
    }
  ]
}
```

---

**GET /api/v1/diseases/{id}** — Detail penyakit (termasuk gejala & obat terkait)

Contoh request:
```
GET /api/v1/diseases/245
```

Contoh response:
```json
{
  "id": 245,
  "nama": "Diabetes Melitus Tipe 1",
  "deskripsi": "...",
  "penyebab": "...",
  "gejala_teks": "...",
  "symptoms": [
    {"id": 12, "nama": "sering buang air kecil"},
    {"id": 34, "nama": "penurunan berat badan"}
  ],
  "drugs": [
    {"id": 100, "nama": "Insulin Glargine", "deskripsi": "...", "merek_dagang": "Lantus"}
  ]
}
```

---

### 2. Obat

**GET /api/v1/drugs** — List semua obat (dengan pagination & search)

| Parameter | Tipe   | Wajib | Keterangan                |
|-----------|--------|-------|---------------------------|
| page      | number | tidak | Halaman ke-n (default: 1) |
| size      | number | tidak | Jumlah per halaman (default: 20, max: 100) |
| search    | string | tidak | Cari berdasarkan nama obat |

Contoh request:
```
GET /api/v1/drugs?search=paracetamol
```

Contoh response:
```json
{
  "total": 2,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": 150,
      "nama": "Paracetamol",
      "deskripsi": "Paracetamol adalah obat untuk...",
      "merek_dagang": "Panadol, Sanmol, Tempra"
    }
  ]
}
```

---

**GET /api/v1/drugs/{id}** — Detail obat (termasuk penyakit terkait)

Contoh response:
```json
{
  "id": 150,
  "nama": "Paracetamol",
  "deskripsi": "...",
  "peringatan": "...",
  "dosis": "Dewasa: 500 mg tiap 4-6 jam...",
  "efek_samping": "...",
  "merek_dagang": "Panadol, Sanmol, Tempra",
  "rxcui": null,
  "diseases": [
    {"id": 300, "nama": "Demam", "deskripsi": "..."}
  ]
}
```

---

### 3. Diagnosis (Prediksi Penyakit)

**POST /api/v1/diagnosis** — Input gejala, dapatkan prediksi penyakit + obat

Request body (JSON):
```json
{
  "gejala": ["demam", "sakit kepala", "mual"]
}
```

Response:
```json
{
  "predictions": [
    {
      "penyakit": "Demam Berdarah",
      "confidence": 0.67,
      "deskripsi": "..."
    },
    {
      "penyakit": "Tifus",
      "confidence": 0.33,
      "deskripsi": "..."
    }
  ],
  "obat_terkait": [
    {"id": 150, "nama": "Paracetamol", "deskripsi": "...", "merek_dagang": "Panadol"}
  ]
}
```

---

### 4. Interaksi Obat

**GET /api/v1/drugs/{id}/interactions** — Lihat interaksi obat tertentu

**POST /api/v1/interactions/check** — Cek interaksi antar beberapa obat

Request body (JSON):
```json
{
  "drug_ids": [150, 200, 310]
}
```

Response:
```json
{
  "has_interactions": true,
  "interactions": [
    {
      "drug1_nama": "Paracetamol",
      "drug2_nama": "Warfarin",
      "severity": "moderate",
      "deskripsi": "Meningkatkan risiko pendarahan..."
    }
  ]
}
```

---

### 5. Prediksi Stok

**POST /api/v1/stock/predict** — Prediksi kebutuhan stok obat

Request body (JSON):
```json
{
  "drug_id": 150,
  "period_days": 30
}
```

---

## Catatan untuk Frontend

1. **Content-Type**: Semua request POST menggunakan `Content-Type: application/json`
2. **CORS**: API sudah mengizinkan akses dari domain manapun
3. **Error format**: Jika terjadi error, response berformat:
   ```json
   {"detail": "Pesan error"}
   ```
   dengan HTTP status code 4xx atau 5xx
4. **Pagination**: Semua endpoint list mengembalikan objek dengan `total`, `page`, `size`, dan `items`
5. **Cold start**: Request pertama mungkin lambat (10-30 detik) karena Vercel serverless. Request selanjutnya cepat.
