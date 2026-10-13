"""
Region Presets and Geocoding Search Router
"""

from typing import List
import httpx
from fastapi import APIRouter, Query
from backend.app.schemas import RegionPreset

router = APIRouter(tags=["Regions"])

PRESET_REGIONS: List[RegionPreset] = [
    RegionPreset(
        id="phoenix",
        name="Phoenix",
        country="United States",
        latitude=33.4484,
        longitude=-112.0740,
        description="Sonoran desert basin with intense summer diurnal maximums and extended urban heat island."
    ),
    RegionPreset(
        id="paris",
        name="Paris",
        country="France",
        latitude=48.8566,
        longitude=2.3522,
        description="Western European temperate climate characterized by pronounced summer heat domes and seasonal droughts."
    ),
    RegionPreset(
        id="madrid",
        name="Madrid",
        country="Spain",
        latitude=40.4168,
        longitude=-3.7038,
        description="Inland Iberian Mediterranean continental climate subject to Saharan air advection and persistent droughts."
    ),
    RegionPreset(
        id="new_delhi",
        name="New Delhi",
        country="India",
        latitude=28.6139,
        longitude=77.2090,
        description="Indo-Gangetic plain with severe pre-monsoon heatwaves and extreme monsoon precipitation events."
    ),
    RegionPreset(
        id="tokyo",
        name="Tokyo",
        country="Japan",
        latitude=35.6762,
        longitude=139.6503,
        description="Humid subtropical coastal megacity subject to intense typhoon rainfall and summer heatwaves."
    ),
    RegionPreset(
        id="sydney",
        name="Sydney",
        country="Australia",
        latitude=-33.8688,
        longitude=151.2093,
        description="Southern hemisphere temperate coastal zone experiencing continental foehn heat bursts and East Coast Low storms."
    ),
    RegionPreset(
        id="cairo",
        name="Cairo",
        country="Egypt",
        latitude=30.0444,
        longitude=31.2357,
        description="Nile Delta arid subtropical climate with persistent high-temperature anomalies and severe drought exposure."
    ),
    RegionPreset(
        id="london",
        name="London",
        country="United Kingdom",
        latitude=51.5074,
        longitude=-0.1278,
        description="Maritime temperate zone experiencing sharp historical shifts in summer maximums and intense convective downpours."
    ),
    RegionPreset(
        id="sao_paulo",
        name="São Paulo",
        country="Brazil",
        latitude=-23.5505,
        longitude=-46.6333,
        description="Subtropical highland zone with acute multi-year meteorological droughts (e.g. 2014-2015 Cantareira crisis) and intense storm bursts."
    ),
    RegionPreset(
        id="nairobi",
        name="Nairobi",
        country="Kenya",
        latitude=-1.2921,
        longitude=36.8219,
        description="East African equatorial highland influenced by bimodal rainy seasons, prolonged droughts, and dipole flood anomalies."
    )
]


@router.get("/regions", response_model=List[RegionPreset])
def list_preset_regions():
    return PRESET_REGIONS


@router.get("/regions/search", response_model=List[RegionPreset])
def search_regions(q: str = Query(..., min_length=2, description="Search query string (city name)")):
    """
    Searches locations using Open-Meteo Geocoding API with fallback to preset matches.
    """
    clean_q = q.strip().lower()

    # Check presets first
    preset_matches = [
        r for r in PRESET_REGIONS
        if clean_q in r.name.lower() or clean_q in r.country.lower()
    ]

    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": q, "count": 5, "language": "en", "format": "json"}
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                api_regions: List[RegionPreset] = []
                for item in results:
                    r_id = f"{item.get('name', '').lower().replace(' ', '_')}_{item.get('country_code', '').lower()}"
                    api_regions.append(
                        RegionPreset(
                            id=r_id,
                            name=item.get("name", ""),
                            country=item.get("country", "") or item.get("admin1", ""),
                            latitude=round(float(item.get("latitude")), 4),
                            longitude=round(float(item.get("longitude")), 4),
                            description=f"Coordinates: {item.get('latitude')}°, {item.get('longitude')}°. Elevation: {item.get('elevation', 'N/A')} m."
                        )
                    )
                if api_regions:
                    return api_regions
    except Exception:
        pass

    return preset_matches if preset_matches else PRESET_REGIONS[:3]
