"""
Seed script: import CSV data ke PostgreSQL.
Jalankan: python -m app.db.seed

Langkah:
1. Import penyakit dari processed_data_penyakit.csv
2. Import obat dari processed_data_obat.csv
3. Parse relasi obat <-> penyakit (fuzzy match)
4. Ekstrak gejala dari teks penyakit -> tabel symptoms + disease_symptom
"""

import asyncio
import csv
import re
from pathlib import Path
from sqlalchemy import select
from app.db.database import engine, async_session, Base
from app.models import Disease, Drug, Symptom, disease_drug, disease_symptom

# Path ke CSV
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
OBAT_CSV = DATA_DIR / "processed_data_obat.csv"
PENYAKIT_CSV = DATA_DIR / "processed_data_penyakit.csv"


def clean_text(text: str) -> str:
    """Bersihkan teks: hapus HTML tags, normalize whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)  # hapus HTML tags
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_gejala(teks_gejala: str) -> list[str]:
    """
    Ekstrak gejala individual dari teks bebas.
    Strategi: split berdasarkan pola umum (koma, titik, kata penghubung).
    """
    if not teks_gejala:
        return []

    teks = clean_text(teks_gejala)

    # Hapus prefix umum yang bukan gejala
    teks = re.sub(r"^(gejala|tanda|ciri)[- ]*(nya|umum|yang muncul|awal)?[:\s]*", "", teks, flags=re.IGNORECASE)

    # Split berdasarkan delimiter
    fragments = re.split(r"[,\n]|(?<=[a-z])\.", teks)

    gejala_list = []
    for frag in fragments:
        frag = frag.strip()
        if len(frag) < 3 or len(frag) > 100:
            continue
        skip_words = [
            "dokter", "pengobatan", "penanganan", "diagnosis", "pemeriksaan",
            "laboratorium", "berikut", "antara lain", "seperti", "yaitu",
            "terapi", "operasi", "komplikasi", "pencegahan",
        ]
        if any(sw in frag.lower() for sw in skip_words):
            continue
        gejala_list.append(frag.strip(". ").lower())

    seen = set()
    result = []
    for g in gejala_list:
        if g not in seen:
            seen.add(g)
            result.append(g)

    return result


def parse_penyakit_obat(teks_penyakit: str) -> list[str]:
    """
    Parse kolom 'Penyakit sesuai dengan obat' menjadi list penyakit.
    Delimiter: dua spasi (  ) digunakan sebagai pemisah di dataset ini.
    """
    if not teks_penyakit:
        return []

    parts = re.split(r"\s{2,}", teks_penyakit.strip())

    result = []
    for part in parts:
        part = part.strip(" ,;.")
        if len(part) >= 2:
            result.append(part.lower())
    return result


def fuzzy_match_disease(nama_penyakit: str, disease_map: dict) -> int | None:
    """
    Cari disease_id berdasarkan nama penyakit (fuzzy).
    """
    nama = nama_penyakit.lower().strip()

    if nama in disease_map:
        return disease_map[nama]

    for disease_nama, disease_id in disease_map.items():
        if nama in disease_nama or disease_nama in nama:
            return disease_id

    words = nama.split()
    if len(words) >= 2:
        key = " ".join(words[:2])
        for disease_nama, disease_id in disease_map.items():
            if key in disease_nama:
                return disease_id

    return None


async def seed():
    print("=== Mediagnotek Database Seeder ===\n")

    # Validasi file
    for f in [OBAT_CSV, PENYAKIT_CSV]:
        if not f.exists():
            print(f"[ERROR] File tidak ditemukan: {f}")
            print(f"        Pastikan file CSV ada di folder: {DATA_DIR}")
            return

    # Buat tabel
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Tabel dibuat\n")

    async with async_session() as session:
        # =====================
        # 1. IMPORT PENYAKIT
        # =====================
        print("[1/4] Import penyakit...")
        disease_map = {}
        symptom_cache = {}
        disease_symptom_pairs = []

        with open(PENYAKIT_CSV, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            diseases = []
            for row in reader:
                d = Disease(
                    nama=row["Nama Penyakit"].strip(),
                    deskripsi=clean_text(row.get("Deskripsi Penyakit", "")),
                    penyebab=clean_text(row.get("Penyebab Penyakit", "")),
                    gejala_teks=clean_text(row.get("Gejala Penyakit", "")),
                )
                diseases.append(d)

            session.add_all(diseases)
            await session.flush()

            for d in diseases:
                disease_map[d.nama.lower()] = d.id

        print(f"      {len(diseases)} penyakit diimport")

        # =====================
        # 2. EKSTRAK GEJALA
        # =====================
        print("[2/4] Ekstrak gejala dari teks...")
        for d in diseases:
            gejala_list = extract_gejala(d.gejala_teks)
            for g in gejala_list:
                if g not in symptom_cache:
                    symptom = Symptom(nama=g)
                    session.add(symptom)
                    await session.flush()
                    symptom_cache[g] = symptom.id

                disease_symptom_pairs.append({
                    "disease_id": d.id,
                    "symptom_id": symptom_cache[g],
                })

        if disease_symptom_pairs:
            unique_pairs = list({(p["disease_id"], p["symptom_id"]): p for p in disease_symptom_pairs}.values())
            await session.execute(disease_symptom.insert(), unique_pairs)

        print(f"      {len(symptom_cache)} gejala unik diekstrak")
        print(f"      {len(unique_pairs) if disease_symptom_pairs else 0} relasi penyakit-gejala")

        # =====================
        # 3. IMPORT OBAT
        # =====================
        print("[3/4] Import obat...")
        drugs = []
        drug_disease_text = []

        with open(OBAT_CSV, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                drug = Drug(
                    nama=row["Nama Obat"].strip(),
                    deskripsi=clean_text(row.get("Deskripsi Obat", "")),
                    peringatan=clean_text(row.get("Peringatan Sebelum Mengonsumsi Obat", "")),
                    dosis=clean_text(row.get("Dosis dan Aturan Pakai Obat", "")),
                    efek_samping=clean_text(row.get("Efek Samping dan Bahaya Obat", "")),
                    merek_dagang=row.get("Merek Dagang", "").strip(),
                )
                drugs.append(drug)
                drug_disease_text.append(
                    row.get("Penyakit sesuai dengan obat", "").strip()
                )

        session.add_all(drugs)
        await session.flush()
        print(f"      {len(drugs)} obat diimport")

        # =====================
        # 4. PARSE RELASI OBAT-PENYAKIT
        # =====================
        print("[4/4] Parse relasi obat-penyakit...")
        disease_drug_pairs = []
        matched = 0
        unmatched_diseases = set()

        for drug, penyakit_teks in zip(drugs, drug_disease_text):
            penyakit_list = parse_penyakit_obat(penyakit_teks)
            for p_nama in penyakit_list:
                disease_id = fuzzy_match_disease(p_nama, disease_map)
                if disease_id:
                    disease_drug_pairs.append({
                        "disease_id": disease_id,
                        "drug_id": drug.id,
                    })
                    matched += 1
                else:
                    unmatched_diseases.add(p_nama)

        if disease_drug_pairs:
            unique_dd = list({(p["disease_id"], p["drug_id"]): p for p in disease_drug_pairs}.values())
            await session.execute(disease_drug.insert(), unique_dd)

        print(f"      {matched} relasi obat-penyakit berhasil di-match")
        print(f"      {len(unmatched_diseases)} nama penyakit dari kolom obat tidak cocok")

        if unmatched_diseases:
            samples = list(unmatched_diseases)[:10]
            print(f"      Contoh unmatched: {samples}")

        await session.commit()

    print("\n=== Seeder selesai ===")

    # Ringkasan
    async with async_session() as session:
        from sqlalchemy import func
        d_count = (await session.execute(select(func.count(Disease.id)))).scalar()
        dr_count = (await session.execute(select(func.count(Drug.id)))).scalar()
        s_count = (await session.execute(select(func.count(Symptom.id)))).scalar()
        dd_count = (await session.execute(select(func.count()).select_from(disease_drug))).scalar()
        ds_count = (await session.execute(select(func.count()).select_from(disease_symptom))).scalar()

        print(f"\nRingkasan database:")
        print(f"  Penyakit              : {d_count}")
        print(f"  Obat                  : {dr_count}")
        print(f"  Gejala unik           : {s_count}")
        print(f"  Relasi obat-penyakit  : {dd_count}")
        print(f"  Relasi penyakit-gejala: {ds_count}")


if __name__ == "__main__":
    asyncio.run(seed())
