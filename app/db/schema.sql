-- ==============================================================================
-- MEDIAGNOTEK PHARMACY & CLINICAL AI PLATFORM - SQL DATABASE SCHEMA (PostgreSQL)
-- ==============================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. FACILITIES (Multi-tenant Apotek / Klinik)
CREATE TABLE IF NOT EXISTS facilities (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(255) NOT NULL,
    kode_faskes VARCHAR(50) UNIQUE,
    alamat TEXT NOT NULL,
    no_telp VARCHAR(50),
    email VARCHAR(100),
    nomor_sia VARCHAR(100),        -- Surat Izin Apotek
    nomor_sipa VARCHAR(100),       -- SIPA Apoteker Pengelola (APA)
    nama_apa VARCHAR(200),         -- Nama Apoteker Pengelola Apotek
    logo_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. USERS (Staf & Autentikasi RBAC)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    facility_id INT NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nama_lengkap VARCHAR(200) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('ADMIN', 'APOTEKER', 'KASIR', 'KEUANGAN')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_facility_role ON users(facility_id, role);

-- 4. SUPPLIERS (Pedagang Besar Farmasi / PBF)
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    facility_id INT NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    nama_pbf VARCHAR(255) NOT NULL,
    no_izin_pbf VARCHAR(100),
    nama_kontak VARCHAR(150),
    no_telp VARCHAR(50),
    alamat TEXT,
    nomor_rekening VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. DISEASES & SYMPTOMS (Knowledge Base)
CREATE TABLE IF NOT EXISTS diseases (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(500) NOT NULL,
    deskripsi TEXT,
    penyebab TEXT,
    gejala_teks TEXT
);
CREATE INDEX IF NOT EXISTS idx_diseases_nama ON diseases(nama);

CREATE TABLE IF NOT EXISTS symptoms (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(300) NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_symptoms_nama ON symptoms(nama);

CREATE TABLE IF NOT EXISTS disease_symptom (
    disease_id INT NOT NULL REFERENCES diseases(id) ON DELETE CASCADE,
    symptom_id INT NOT NULL REFERENCES symptoms(id) ON DELETE CASCADE,
    PRIMARY KEY (disease_id, symptom_id)
);

-- 6. MASTER DRUGS (Katalog Farmasi)
CREATE TABLE IF NOT EXISTS drugs (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(500) NOT NULL,
    deskripsi TEXT,
    peringatan TEXT,
    dosis TEXT,
    efek_samping TEXT,
    merek_dagang VARCHAR(1000),
    rxcui VARCHAR(50),
    barcode VARCHAR(100) UNIQUE,
    satuan_terkecil VARCHAR(50) NOT NULL DEFAULT 'Tablet', -- Tablet, Strip, Botol, Ampul
    golongan VARCHAR(50) NOT NULL DEFAULT 'Bebas',          -- Bebas, Bebas Terbatas, Keras, Narkotika, Psikotropika
    stok_minimum INT NOT NULL DEFAULT 10,
    harga_jual_default NUMERIC(12, 2) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_drugs_nama ON drugs(nama);
CREATE INDEX IF NOT EXISTS idx_drugs_barcode ON drugs(barcode);

CREATE TABLE IF NOT EXISTS disease_drug (
    disease_id INT NOT NULL REFERENCES diseases(id) ON DELETE CASCADE,
    drug_id INT NOT NULL REFERENCES drugs(id) ON DELETE CASCADE,
    PRIMARY KEY (disease_id, drug_id)
);

CREATE TABLE IF NOT EXISTS drug_interactions (
    id SERIAL PRIMARY KEY,
    drug_id_1 INT NOT NULL REFERENCES drugs(id) ON DELETE CASCADE,
    drug_id_2 INT NOT NULL REFERENCES drugs(id) ON DELETE CASCADE,
    severity VARCHAR(50), -- low, moderate, high
    deskripsi TEXT
);

-- 7. DRUG BATCHES (Inventori Fisik, FEFO Engine & HPP Modal)
CREATE TABLE IF NOT EXISTS drug_batches (
    id SERIAL PRIMARY KEY,
    facility_id INT NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    drug_id INT NOT NULL REFERENCES drugs(id) ON DELETE RESTRICT,
    supplier_id INT REFERENCES suppliers(id) ON DELETE SET NULL,
    batch_number VARCHAR(100) NOT NULL,
    expired_date DATE NOT NULL,                  -- Dasar pengurutan FEFO
    stok_awal INT NOT NULL CHECK (stok_awal >= 0),
    stok_sisa INT NOT NULL CHECK (stok_sisa >= 0),
    harga_beli_hpp NUMERIC(12, 2) NOT NULL,      -- HPP Modal Bersih per satuan
    harga_jual NUMERIC(12, 2) NOT NULL,          -- Harga jual ke konsumen
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_batches_fefo ON drug_batches(drug_id, is_active, expired_date ASC) WHERE stok_sisa > 0;
CREATE INDEX IF NOT EXISTS idx_batches_expiry ON drug_batches(expired_date);

-- 8. PURCHASE INVOICES (Faktur Pembelian PBF)
CREATE TABLE IF NOT EXISTS purchase_invoices (
    id SERIAL PRIMARY KEY,
    facility_id INT NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    supplier_id INT NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    nomor_faktur VARCHAR(100) NOT NULL,
    tanggal_faktur DATE NOT NULL,
    jatuh_tempo DATE,
    total_bruto NUMERIC(14, 2) NOT NULL DEFAULT 0,
    diskon_nominal NUMERIC(14, 2) NOT NULL DEFAULT 0,
    ppn_nominal NUMERIC(14, 2) NOT NULL DEFAULT 0,
    total_neto NUMERIC(14, 2) NOT NULL DEFAULT 0,
    status_pembayaran VARCHAR(50) NOT NULL DEFAULT 'LUNAS' CHECK (status_pembayaran IN ('LUNAS', 'HUTANG', 'KONSINYASI')),
    bukti_faktur_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS purchase_invoice_items (
    id SERIAL PRIMARY KEY,
    invoice_id INT NOT NULL REFERENCES purchase_invoices(id) ON DELETE CASCADE,
    drug_id INT NOT NULL REFERENCES drugs(id) ON DELETE RESTRICT,
    batch_id INT REFERENCES drug_batches(id) ON DELETE SET NULL,
    jumlah INT NOT NULL CHECK (jumlah > 0),
    harga_satuan_hpp NUMERIC(12, 2) NOT NULL,
    diskon_persen NUMERIC(5, 2) DEFAULT 0,
    subtotal NUMERIC(14, 2) NOT NULL
);

-- 9. PATIENTS (Buku Rekam Data Pasien)
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    facility_id INT NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    nomor_rm VARCHAR(50) NOT NULL,              -- RM-YYYYMM-XXXX
    nama_lengkap VARCHAR(200) NOT NULL,
    nik VARCHAR(20),
    tanggal_lahir DATE,
    jenis_kelamin VARCHAR(10) CHECK (jenis_kelamin IN ('L', 'P')),
    no_hp VARCHAR(30) NOT NULL,
    alamat TEXT,
    riwayat_alergi TEXT,                        -- Alergi Penisilin, Asam Mefenamat, dll
    riwayat_komorbid TEXT,                      -- Hipertensi, DM, Gagal Ginjal
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_patients_search ON patients(facility_id, nama_lengkap, no_hp);

-- 10. TRANSACTIONS (Kasir POS & Laba Kotor HPP)
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    facility_id INT NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    nomor_struk VARCHAR(100) NOT NULL UNIQUE,   -- TRX-YYYYMMDD-XXXX
    user_id INT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    patient_id INT REFERENCES patients(id) ON DELETE SET NULL,
    tanggal_transaksi TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    jenis_transaksi VARCHAR(50) NOT NULL DEFAULT 'BEBAS' CHECK (jenis_transaksi IN ('BEBAS', 'RESEP_PATEN', 'RESEP_RACIKAN')),
    total_omzet NUMERIC(14, 2) NOT NULL DEFAULT 0,        -- Total dibayar pasien
    total_hpp NUMERIC(14, 2) NOT NULL DEFAULT 0,          -- Total modal HPP batch
    laba_kotor NUMERIC(14, 2) NOT NULL DEFAULT 0,         -- total_omzet - total_hpp
    margin_persen NUMERIC(6, 2) NOT NULL DEFAULT 0,       -- (laba_kotor / total_omzet) * 100
    metode_bayar VARCHAR(50) NOT NULL DEFAULT 'TUNAI' CHECK (metode_bayar IN ('TUNAI', 'QRIS', 'DEBIT', 'TRANSFER')),
    nominal_tunai NUMERIC(14, 2),
    nominal_kembalian NUMERIC(14, 2),
    catatan TEXT
);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(facility_id, tanggal_transaksi DESC);

CREATE TABLE IF NOT EXISTS transaction_items (
    id SERIAL PRIMARY KEY,
    transaction_id INT NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    drug_id INT NOT NULL REFERENCES drugs(id) ON DELETE RESTRICT,
    batch_id INT NOT NULL REFERENCES drug_batches(id) ON DELETE RESTRICT,
    jumlah INT NOT NULL CHECK (jumlah > 0),
    harga_jual_satuan NUMERIC(12, 2) NOT NULL,  -- Snapshot harga saat transaksi
    hpp_satuan NUMERIC(12, 2) NOT NULL,         -- Snapshot modal batch saat transaksi
    subtotal_omzet NUMERIC(14, 2) NOT NULL,     -- jumlah * harga_jual_satuan
    subtotal_hpp NUMERIC(14, 2) NOT NULL,       -- jumlah * hpp_satuan
    laba_item NUMERIC(14, 2) NOT NULL,          -- subtotal_omzet - subtotal_hpp
    aturan_pakai VARCHAR(200)                   -- 3x1 sesudah makan
);
CREATE INDEX IF NOT EXISTS idx_trx_items_batch ON transaction_items(batch_id);

-- 11. STOCK MUTATIONS (Audit Log Mutasi Barang)
CREATE TABLE IF NOT EXISTS stock_mutations (
    id SERIAL PRIMARY KEY,
    facility_id INT NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    drug_id INT NOT NULL REFERENCES drugs(id) ON DELETE CASCADE,
    batch_id INT NOT NULL REFERENCES drug_batches(id) ON DELETE CASCADE,
    tipe_mutasi VARCHAR(50) NOT NULL CHECK (tipe_mutasi IN ('MASUK_FAKTUR', 'KELUAR_PENJUALAN', 'PENYESUAIAN_OPNAME', 'RETUR_PBF', 'RUSAK_KEDALUWARSA')),
    jumlah INT NOT NULL,
    stok_sebelum INT NOT NULL,
    stok_sesudah INT NOT NULL,
    referensi_id VARCHAR(100),
    keterangan TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_stock_mutations ON stock_mutations(drug_id, batch_id, created_at DESC);

-- 12. CASH FLOWS (Buku Kas & Arus Keuangan)
CREATE TABLE IF NOT EXISTS cash_flows (
    id SERIAL PRIMARY KEY,
    facility_id INT NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    tanggal DATE NOT NULL,
    tipe VARCHAR(20) NOT NULL CHECK (tipe IN ('MASUK', 'KELUAR')),
    kategori VARCHAR(100) NOT NULL,
    nominal NUMERIC(14, 2) NOT NULL,
    deskripsi TEXT,
    referensi_transaksi_id INT REFERENCES transactions(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 13. AI CLINICAL CONSULTATION (Audit Log Sesi AI)
CREATE TABLE IF NOT EXISTS ai_consultation_sessions (
    id VARCHAR(100) PRIMARY KEY,
    facility_id INT NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    patient_id INT REFERENCES patients(id) ON DELETE SET NULL,
    judul_konsultasi VARCHAR(255) DEFAULT 'Konsultasi Telaah Resep & Diagnosa',
    mode_tampilan VARCHAR(50) DEFAULT 'STANDARD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_consultation_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL REFERENCES ai_consultation_sessions(id) ON DELETE CASCADE,
    sender VARCHAR(20) NOT NULL CHECK (sender IN ('USER', 'AI', 'SYSTEM')),
    content TEXT NOT NULL,
    lampiran_resep_url TEXT,
    detected_icd10_code VARCHAR(20),
    detected_icd10_desc VARCHAR(255),
    interaksi_ditemukan JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 14. STOCK PREDICTIONS (Machine Learning / Heuristic)
CREATE TABLE IF NOT EXISTS stock_predictions (
    id SERIAL PRIMARY KEY,
    drug_id INT NOT NULL REFERENCES drugs(id) ON DELETE CASCADE,
    tanggal VARCHAR(10) NOT NULL,
    stok_masuk INT DEFAULT 0,
    stok_keluar INT DEFAULT 0,
    sisa INT DEFAULT 0
);
