import math
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def bounding_box(lat, lon, radius_km):
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * math.cos(math.radians(lat)))
    return lat-dlat, lat+dlat, lon-dlon, lon+dlon


def _corpus(users):
    docs = []
    for u in users:
        tags = " ".join(u.get("interests", []) * 3)
        bio  = u.get("bio", "")
        docs.append(f"{bio} {tags}".strip().lower() or "open conversation")
    return docs


def compute_compatibility(current: Dict, candidates: List[Dict]) -> List[float]:
    if not candidates: return []
    corpus = _corpus([current] + candidates)
    try:
        mat  = TfidfVectorizer(stop_words="english", ngram_range=(1,2),
                               min_df=1, max_features=500).fit_transform(corpus)
        sims = cosine_similarity(mat[0], mat[1:]).flatten()
        return sims.tolist()
    except ValueError:
        return [0.5] * len(candidates)


def rank_nearby_users(current, nearby, cur_lat, cur_lon,
                      max_km=2.0, dw=0.4, iw=0.6):
    candidates = []
    for u in nearby:
        d = haversine_km(cur_lat, cur_lon, u["latitude"], u["longitude"])
        if d <= max_km:
            u["distance_km"] = round(d, 3)
            candidates.append(u)
    if not candidates: return []

    sims = compute_compatibility(current, candidates)
    for i, c in enumerate(candidates):
        ds = 1.0 - (c["distance_km"] / max_km)
        c["compatibility"] = round(float(sims[i]), 4)
        c["match_score"]   = round(dw * ds + iw * float(sims[i]), 4)
    return sorted(candidates, key=lambda x: x["match_score"], reverse=True)