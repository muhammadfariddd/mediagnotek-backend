import httpx
from app.config import get_settings

settings = get_settings()


async def check_rxnav_interactions(rxcui_list: list[str]) -> list[dict]:
    """
    Cek interaksi obat via RxNav Interaction API.
    Input: list rxcui (string).
    Output: list dict {drug_id_1, drug_id_2, severity, deskripsi}.
    """
    if len(rxcui_list) < 2:
        return []

    rxcuis_param = "+".join(rxcui_list)
    url = f"{settings.RXNAV_BASE_URL}/interaction/list.json?rxcuis={rxcuis_param}"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return []
        data = resp.json()

    interactions = []
    full_interactions = data.get("fullInteractionTypeGroup", [])

    for group in full_interactions:
        for interaction_type in group.get("fullInteractionType", []):
            pairs = interaction_type.get("interactionPair", [])
            for pair in pairs:
                concepts = pair.get("interactionConcept", [])
                if len(concepts) >= 2:
                    interactions.append({
                        "rxcui_1": concepts[0].get("minConceptItem", {}).get("rxcui"),
                        "rxcui_2": concepts[1].get("minConceptItem", {}).get("rxcui"),
                        "severity": pair.get("severity", "N/A"),
                        "deskripsi": pair.get("description", ""),
                    })

    return interactions


async def get_rxcui_by_name(drug_name: str) -> str | None:
    """
    Cari kode RxCUI berdasarkan nama obat (generik).
    """
    url = f"{settings.RXNAV_BASE_URL}/drugs?name={drug_name}"

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return None
        data = resp.json()

    drug_group = data.get("drugGroup", {})
    concept_groups = drug_group.get("conceptGroup", [])

    for group in concept_groups:
        props = group.get("conceptProperties", [])
        if props:
            return props[0].get("rxcui")

    return None
