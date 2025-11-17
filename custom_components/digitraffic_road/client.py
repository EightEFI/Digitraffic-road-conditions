"""Digitraffic API client for road conditions."""
import aiohttp
import logging
import re
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone

_LOGGER = logging.getLogger(__name__)

# Digitraffic API endpoints
BASE_URL = "https://tie.digitraffic.fi/api/v1/data"
FORECAST_SECTIONS_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections/forecasts"
FORECAST_SECTIONS_METADATA_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections"
TMS_STATIONS_URL = "https://tie.digitraffic.fi/api/tms/v1/stations"
TMS_STATION_URL = "https://tie.digitraffic.fi/api/tms/v1/stations/{id}"
TMS_SENSOR_CONSTANTS_URL = "https://tie.digitraffic.fi/api/tms/v1/stations/{id}/sensor-constants"
TMS_STATION_DATA_URL = "https://tie.digitraffic.fi/api/tms/v1/stations/{id}/data"
WEATHER_STATIONS_URL = "https://tie.digitraffic.fi/api/weather/v1/stations"
WEATHER_STATION_URL = "https://tie.digitraffic.fi/api/weather/v1/stations/{id}"
WEATHER_STATION_DATA_URL = "https://tie.digitraffic.fi/api/weather/v1/stations/{id}/data"

# Finnish road condition descriptions
FINNISH_ROAD_CONDITIONS = [
    "Tienpinta on kuiva",
    "Tien pinta on märkä",
    "Tienpinnassa on paikoin jäätä",
    "Tienpinnassa on mahdollisesti kuuraa",
    "Liukasta, tienpinnassa on jäätä tai lunta",
    "Lumisade tai rankka vesisade",
    "Raskas lumisade",
    "Hyvä ajokeli",
    "Huono ajokeli",
]

ENGLISH_ROAD_CONDITIONS = [
    "Road surface is dry",
    "Road surface is wet",
    "Patches of ice on the road",
    "Possible hoarfrost on the road",
    "Slippery, ice or snow on the road",
    "Snow or heavy rain",
    "Heavy snow",
    "Good driving conditions",
    "Poor driving conditions",
]

# Maps from API roadCondition / overallRoadCondition values to human text
# Includes values returned by the actual Digitraffic forecast-sections API
ROAD_CONDITION_MAP = {
    # Actual forecast-sections API roadCondition values
    "DRY": {"fi": "Kuiva", "en": "Dry"},
    "WET": {"fi": "Märkä", "en": "Wet"},
    "FROST": {"fi": "Kuuraa", "en": "Frost"},
    "ICE": {"fi": "Jäätä", "en": "Ice"},
    "MOIST": {"fi": "Kostea", "en": "Damp"},
    "PARTLY_ICY": {"fi": "Osittain jäätä", "en": "Partly icy"},
    "SLUSH": {"fi": "Loskaa", "en": "Slush"},
    "SNOW": {"fi": "Lunta", "en": "Snow"},
    # Actual forecast-sections API overallRoadCondition values
    "NORMAL_CONDITION": {"fi": "Hyvä ajokeli", "en": "Good driving conditions"},
    "POOR_CONDITION": {"fi": "Huono ajokeli", "en": "Poor driving conditions"},
    "EXTREMELY_POOR_CONDITION": {"fi": "Erittäin huono ajokeli", "en": "Extremely poor driving conditions"},
    # Legacy values (kept for compatibility)
    "ICY": {"fi": "Jäätä", "en": "Icy"},
    "POSSIBLE_RIME": {"fi": "Kuuraa", "en": "Possible frost"},
    "SLIPPERY": {"fi": "Loskaa", "en": "Slippery"},
    "HEAVY_SNOW": {"fi": "Lunta", "en": "Heavy snow"},
    "GOOD": {"fi": "Hyvä ajokeli", "en": "Good driving conditions"},
    "POOR": {"fi": "Huono ajokeli", "en": "Poor driving conditions"},
    "SLEET": {"fi": "Loskaa", "en": "Sleet"},
}

# Precise mock road sections based on Finnish road structure
# Format: "Road Type + Number: Location + KM marker"
MOCK_ROAD_SECTIONS = [
    # E-roads (European highways)
    {
        "id": "E18_0_50",
        "name": "E18: Tietokatu",
        "road": "E18",
        "location": "Tietokatu",
        "km": "0.0-50.0",
        "description": "Helsinki - Kilo area"
    },
    {
        "id": "E18_50_100",
        "name": "E18: Kehä III - Espoo boundary",
        "road": "E18",
        "location": "Kehä III - Espoo boundary",
        "km": "50.0-100.0",
        "description": "Espoo area"
    },
    {
        "id": "E75_0_40",
        "name": "E75: Hakamäentie",
        "road": "E75",
        "location": "Hakamäentie",
        "km": "0.0-40.0",
        "description": "Helsinki - Turku road start"
    },
    {
        "id": "E75_40_100",
        "name": "E75: Lohja area",
        "road": "E75",
        "location": "Lohja",
        "km": "40.0-100.0",
        "description": "Lohja - Turku area"
    },
    # National roads (Valtatie)
    {
        "id": "VT1_0_50",
        "name": "VT1: Hämeentie",
        "road": "VT1",
        "location": "Hämeentie",
        "km": "0.0-50.0",
        "description": "Helsinki - Tampere start"
    },
    {
        "id": "VT1_50_120",
        "name": "VT1: Karviainen area",
        "road": "VT1",
        "location": "Karviainen",
        "km": "50.0-120.0",
        "description": "Inland towards Tampere"
    },
    {
        "id": "VT3_0_45",
        "name": "VT3: Länsimetro area",
        "road": "VT3",
        "location": "Länsimetro",
        "km": "0.0-45.0",
        "description": "Helsinki - Turku alternative route start"
    },
    {
        "id": "VT4_0_50",
        "name": "VT4: Tuusula area",
        "road": "VT4",
        "location": "Tuusula",
        "km": "0.0-50.0",
        "description": "Helsinki - Oulu start"
    },
    {
        "id": "VT4_50_130",
        "name": "VT4: Perämerentie",
        "road": "VT4",
        "location": "Perämerentie",
        "km": "50.0-130.0",
        "description": "Oulu direction - central area"
    },
    {
        "id": "VT4_130_200",
        "name": "VT4: Oulu area",
        "road": "VT4",
        "location": "Oulu",
        "km": "130.0-200.0",
        "description": "Oulu region"
    },
    {
        "id": "VT22_0_80",
        "name": "VT22: Kemintie",
        "road": "VT22",
        "location": "Kemintie",
        "km": "0.0-80.0",
        "description": "Kemi - Oulu road"
    },
    # Regional roads (Seututie)
    {
        "id": "ST101_0_30",
        "name": "ST101: Itäväylä",
        "road": "ST101",
        "location": "Itäväylä",
        "km": "0.0-30.0",
        "description": "Helsinki east ring road"
    },
    {
        "id": "ST105_0_25",
        "name": "ST105: Westbound area",
        "road": "ST105",
        "location": "Westbound",
        "km": "0.0-25.0",
        "description": "Helsinki west area"
    },
]


class DigitraficClient:
    """Client to interact with Digitraffic API."""

    def __init__(self, session: aiohttp.ClientSession):
        """Initialize the client."""
        self.session = session

    @staticmethod
    def _normalize_string(s: str) -> str:
        """Normalize string for comparison: lowercase, remove punctuation, collapse spaces."""
        s = s.lower()
        s = re.sub(r"[^a-z0-9åäöÅÄÖ ]+", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    async def resolve_section_id(self, user_input: str) -> Optional[str]:
        """Resolve a user-entered road section title to an API section ID.
        
        Searches the forecast-sections metadata endpoint to find matching section IDs.
        Returns the best match or None if no match found.
        
        Args:
            user_input: User-entered section title (e.g., "Tie 3: Valtatie 3 3.250")
        
        Returns:
            Best matching section ID (e.g., "00003_250_00000_1_0") or None
        """
        try:
            _LOGGER.debug("Attempting to resolve section ID for: %s", user_input)

            # Check for user overrides first (persistent mapping from query -> section id)
            try:
                overrides_path = Path(__file__).parent / "overrides.json"
                if overrides_path.exists():
                    with overrides_path.open("r", encoding="utf-8") as fh:
                        overrides = json.load(fh)
                    # use normalized key to match stored overrides
                    norm_key = self._normalize_string(user_input)
                    mapped = overrides.get(norm_key)
                    if mapped:
                        _LOGGER.debug("Found override for '%s' -> %s", user_input, mapped)
                        return mapped
            except Exception as e:
                _LOGGER.debug("Failed to read overrides: %s", e)
            
            # If input looks like an ID (numeric pattern), return as-is
            if re.match(r"^[0-9]{5}_\d+", user_input):
                return user_input

            # Prefer numeric parsing: if the user entered a road + km marker (e.g. "Valtatie 3 3.250")
            # then try to find metadata entries that match roadNumber and roadSectionNumber
            try:
                candidates = await self.resolve_section_candidates(user_input, max_candidates=8)
                if candidates:
                    # If resolve_section_candidates returned exact numeric matches, they will be first.
                    # Choose the best candidate deterministically (first in list).
                    first = candidates[0]
                    cid = first.get('id')
                    if cid:
                        _LOGGER.debug("Resolved '%s' to section %s via numeric/metadata match", user_input, cid)
                        return cid
            except Exception as e:
                _LOGGER.debug("Numeric candidate resolution failed: %s", e)

            # Fallback: original text token overlap approach (if numeric/match not found)
            async with self.session.get(FORECAST_SECTIONS_METADATA_URL) as resp:
                if resp.status != 200:
                    _LOGGER.debug("Metadata endpoint returned %d", resp.status)
                    return None
                
                data = await resp.json()
                features = data.get("features", [])
                
            norm_user = self._normalize_string(user_input)
            user_tokens = set(norm_user.split())
            
            candidates = []
            for feat in features:
                props = feat.get("properties", {})
                desc = props.get("description", "")
                if desc:
                    norm_desc = self._normalize_string(desc)
                    desc_tokens = set(norm_desc.split())
                    common = user_tokens & desc_tokens
                    if len(common) > 0:
                        score = len(common)
                        section_id = props.get("id")
                        candidates.append((score, section_id, desc))

            if candidates:
                # Sort by text match score (descending)
                candidates.sort(reverse=True, key=lambda x: x[0])
                best_score = candidates[0][0]
                # Gather all top-scoring candidates
                top_candidates = [c for c in candidates if c[0] == best_score]

                # If only one top candidate, return it
                if len(top_candidates) == 1:
                    _, best_id, best_desc = top_candidates[0]
                    _LOGGER.debug("Resolved '%s' to section %s (score %d, desc: %s)", 
                                 user_input, best_id, best_score, best_desc)
                    return best_id

                # Tie-breaker: fetch forecast feed and score candidates by forecast content
                try:
                    async with self.session.get(FORECAST_SECTIONS_URL) as fresp:
                        if fresp.status == 200:
                            fdata = await fresp.json()
                            fs_map = {fs.get('id'): fs for fs in fdata.get('forecastSections', [])}
                            best_candidate = None
                            best_tie_score = -1
                            for _, cid, cdesc in top_candidates:
                                fs = fs_map.get(cid)
                                if not fs:
                                    continue
                                tie_score = 0
                                # Score based on forecasts: prefer NORMAL_CONDITION and MOIST
                                for f in fs.get('forecasts', []):
                                    if f.get('type') != 'FORECAST':
                                        continue
                                    if f.get('overallRoadCondition') == 'NORMAL_CONDITION':
                                        tie_score += 2
                                    if f.get('forecastConditionReason', {}).get('roadCondition') == 'MOIST':
                                        tie_score += 1
                                if tie_score > best_tie_score:
                                    best_tie_score = tie_score
                                    best_candidate = cid
                            if best_candidate:
                                _LOGGER.debug("Resolved '%s' to section %s by forecast tie-breaker (text score %d, tie score %d)",
                                             user_input, best_candidate, best_score, best_tie_score)
                                return best_candidate
                except Exception as e:
                    _LOGGER.debug("Tie-breaker forecast check failed: %s", e)

                # Fallback: return first top candidate
                _, best_id, best_desc = top_candidates[0]
                _LOGGER.debug("Resolved '%s' to section %s (score %d, desc: %s) [fallback]", 
                             user_input, best_id, best_score, best_desc)
                return best_id
        
        except Exception as err:
            _LOGGER.warning("Error resolving section ID: %s", err)
            return None

    async def resolve_section_candidates(self, user_input: str, max_candidates: int = 8) -> List[Dict[str, Any]]:
        """Return candidate metadata entries for a user-entered section title.

        This method first attempts to parse explicit road and km markers from the
        user input (e.g. "Valtatie 3 3.250" -> roadNumber=3, roadSectionNumber=250)
        and returns exact metadata matches. If no explicit numeric match is found,
        it falls back to token-overlap scoring and returns the top-scoring
        metadata entries.

        Returns a list of property dictionaries (as returned by the metadata
        endpoint) ordered by relevance.
        """
        try:
            async with self.session.get(FORECAST_SECTIONS_METADATA_URL) as resp:
                if resp.status != 200:
                    _LOGGER.debug("Metadata endpoint returned %d", resp.status)
                    return []
                data = await resp.json()
                features = data.get("features", [])

            norm = self._normalize_string(user_input)

            # First: exact-match against the `description` field (normalized).
            # This allows the config flow to compare the user's typed label directly
            # to the authoritative metadata `description` and present exact matches
            # for the user to pick from if there are multiple identical descriptions.
            exact_matches: List[Dict[str, Any]] = []
            for feat in features:
                props = feat.get("properties", {})
                desc = props.get("description", "") or props.get("name", "")
                if desc and self._normalize_string(desc) == norm:
                    exact_matches.append(props)
            if exact_matches:
                return exact_matches[:max_candidates]

            # If user input contains a ':' it's likely in the form "Tie 717: Vähäkyröntie 717.6".
            # In that case, try to parse road number from the left side and exact description
            # from the right side and return all metadata entries that match both.
            if ':' in user_input:
                try:
                    left, right = user_input.split(':', 1)
                    left = left.strip()
                    right = right.strip()
                    # Try to extract road number from left part
                    mroad = re.search(r"(?:tie|vt|valtatie|st)?\s*(\d{1,4})\b", left, flags=re.IGNORECASE)
                    if mroad:
                        road_num = int(mroad.group(1))
                        norm_right = self._normalize_string(right)
                        matched: List[Dict[str, Any]] = []
                        for feat in features:
                            props = feat.get("properties", {})
                            if props.get("roadNumber") != road_num:
                                continue
                            desc = props.get("description", "") or props.get("name", "")
                            if desc and self._normalize_string(desc) == norm_right:
                                matched.append(props)
                        if matched:
                            return matched[:max_candidates]
                except Exception:
                    pass

            # Try to extract patterns like '3 3.250' or 'valtatie 3 3.250' or 'vt3 3.250'
            # Look for the first occurrence of a road number and a km marker
            road_num = None
            section_num = None
            m = re.search(r"(?:vt|valtatie|tie)?\s*(\d{1,3})[^0-9]{0,3}(\d+\.\d+)", user_input, flags=re.IGNORECASE)
            if m:
                try:
                    road_num = int(m.group(1))
                    km = float(m.group(2))
                    # roadSectionNumber in metadata appears to be the decimal part * 1000
                    frac = km - int(km)
                    section_num = int(round(frac * 1000))
                except Exception:
                    road_num = None
                    section_num = None

            candidates: List[Dict[str, Any]] = []

            # If we parsed numeric road + section, prefer exact matches
            if road_num is not None and section_num is not None:
                for feat in features:
                    props = feat.get("properties", {})
                    if props.get("roadNumber") == road_num and props.get("roadSectionNumber") == section_num:
                        candidates.append(props)
                if candidates:
                    return candidates[:max_candidates]

            # Fallback: token-overlap scoring (as before)
            user_tokens = set(norm.split())
            scored = []
            for feat in features:
                props = feat.get("properties", {})
                desc = props.get("description", "") or props.get("name", "")
                if not desc:
                    continue
                norm_desc = self._normalize_string(desc)
                desc_tokens = set(norm_desc.split())
                score = len(user_tokens & desc_tokens)
                if score > 0:
                    scored.append((score, props))
            scored.sort(key=lambda x: (-x[0], x[1].get("id", "")))
            return [p for _, p in scored[:max_candidates]]
        except Exception as err:
            _LOGGER.warning("Error resolving candidates: %s", err)
            return []

    async def async_search_tms_stations(self, query: str, max_results: int = 12) -> List[Dict[str, Any]]:
        """Search TMS stations by name.

        Matches against `properties.names` (fi/sv/en) and `properties.name`.
        Returns a list of `properties` dicts for matching stations.
        """
        try:
            async with self.session.get(TMS_STATIONS_URL, headers={"Accept": "application/json"}) as resp:
                if resp.status != 200:
                    _LOGGER.debug("TMS stations endpoint returned %d", resp.status)
                    return []
                # API requires gzip; aiohttp handles compression automatically
                data = await resp.json()
                features = data.get("features", [])

            norm = self._normalize_string(query)
            tokens = set(norm.split())

            matches: List[Tuple[int, Dict[str, Any]]] = []
            for feat in features:
                props = feat.get("properties", {})
                # Look into names dict first
                names = props.get("names", {}) or {}
                candidates = [names.get(k, "") for k in ("fi", "sv", "en")] + [props.get("name", "")]
                for cand in candidates:
                    if not cand:
                        continue
                    norm_cand = self._normalize_string(cand)
                    # exact normalized match gets highest priority
                    if norm_cand == norm:
                        matches.append((100, props))
                        break
                    # token overlap scoring
                    common = tokens & set(norm_cand.split())
                    if common:
                        matches.append((len(common), props))
                        break

            # Deduplicate by id keeping highest score
            best: Dict[Any, Tuple[int, Dict[str, Any]]] = {}
            for score, p in matches:
                pid = p.get("id")
                if pid not in best or score > best[pid][0]:
                    best[pid] = (score, p)

            # Sort by score (descending) without attempting to compare dicts.
            # Using a key avoids TypeError when scores tie and dicts would be compared.
            scored = sorted(best.values(), key=lambda x: -x[0])
            return [p for _, p in scored[:max_results]]
        except Exception as err:
            _LOGGER.debug("Error searching TMS stations: %s", err)
            return []

    async def async_get_tms_station(self, station_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single TMS station feature by id."""
        try:
            url = TMS_STATION_URL.format(id=station_id)
            async with self.session.get(url, headers={"Accept": "application/json"}) as resp:
                if resp.status != 200:
                    _LOGGER.debug("TMS station %s returned %d", station_id, resp.status)
                    return None
                return await resp.json()
        except Exception as err:
            _LOGGER.debug("Error fetching TMS station %s: %s", station_id, err)
            return None

    async def async_get_tms_sensor_constants(self, station_id: int) -> Optional[Dict[str, Any]]:
        """Fetch sensor constant values for a station by id.

        Returns JSON structure containing sensor constant definitions/values.
        """
        try:
            url = TMS_SENSOR_CONSTANTS_URL.format(id=station_id)
            async with self.session.get(url, headers={"Accept": "application/json"}) as resp:
                if resp.status != 200:
                    _LOGGER.debug("TMS sensor-constants %s returned %d", station_id, resp.status)
                    return None
                return await resp.json()
        except Exception as err:
            _LOGGER.debug("Error fetching TMS sensor constants %s: %s", station_id, err)
            return None

    async def async_get_tms_station_data(self, station_id: int) -> Optional[Dict[str, Any]]:
        """Fetch station measurement data (sensorValues) for a TMS station.

        Returns the JSON payload which contains `sensorValues` list.
        """
        try:
            url = TMS_STATION_DATA_URL.format(id=station_id)
            async with self.session.get(url, headers={"Accept": "application/json"}) as resp:
                if resp.status != 200:
                    _LOGGER.debug("TMS station data %s returned %d", station_id, resp.status)
                    return None
                return await resp.json()
        except Exception as err:
            _LOGGER.debug("Error fetching TMS station data %s: %s", station_id, err)
            return None

    async def async_search_weather_stations(self, query: str, max_results: int = 12) -> List[Dict[str, Any]]:
        """Search weather stations by name or id."""
        if not query:
            return []

        try:
            async with self.session.get(WEATHER_STATIONS_URL, headers={"Accept": "application/json"}) as resp:
                if resp.status != 200:
                    _LOGGER.debug("Weather stations endpoint returned %d", resp.status)
                    return []
                payload = await resp.json()
        except Exception as err:
            _LOGGER.debug("Error fetching weather stations: %s", err)
            return []

        features = payload.get("features", [])
        norm_query = self._normalize_string(query)
        tokens = set(norm_query.split())

        matches: List[Tuple[int, Dict[str, Any]]] = []
        for feat in features:
            props = feat.get("properties", {})
            name = props.get("name") or feat.get("name") or ""
            if not name:
                continue

            # Allow direct id match
            if str(props.get("id")) == query.strip():
                matches.append((200, props))
                continue

            norm_name = self._normalize_string(name)
            if norm_name == norm_query:
                matches.append((100, props))
                continue

            common = tokens & set(norm_name.split())
            if common:
                matches.append((len(common), props))

        if not matches:
            return []

        best: Dict[Any, Tuple[int, Dict[str, Any]]] = {}
        for score, props in matches:
            sid = props.get("id")
            if sid not in best or score > best[sid][0]:
                best[sid] = (score, props)

        scored = sorted(best.values(), key=lambda item: -item[0])
        results: List[Dict[str, Any]] = []
        for _, props in scored[:max_results]:
            results.append(
                {
                    "id": props.get("id"),
                    "name": props.get("name"),
                    "collectionStatus": props.get("collectionStatus"),
                    "state": props.get("state"),
                    "dataUpdatedTime": props.get("dataUpdatedTime"),
                }
            )
        return results

    async def async_get_weather_station(self, station_id: int) -> Optional[Dict[str, Any]]:
        """Fetch metadata for a single weather station."""
        try:
            url = WEATHER_STATION_URL.format(id=station_id)
            async with self.session.get(url, headers={"Accept": "application/json"}) as resp:
                if resp.status != 200:
                    _LOGGER.debug("Weather station %s returned %d", station_id, resp.status)
                    return None
                return await resp.json()
        except Exception as err:
            _LOGGER.debug("Error fetching weather station %s: %s", station_id, err)
            return None

    async def async_get_weather_station_data(self, station_id: int) -> Optional[Dict[str, Any]]:
        """Fetch measurement data for a weather station."""
        try:
            url = WEATHER_STATION_DATA_URL.format(id=station_id)
            async with self.session.get(url, headers={"Accept": "application/json"}) as resp:
                if resp.status != 200:
                    _LOGGER.debug("Weather station data %s returned %d", station_id, resp.status)
                    return None
                return await resp.json()
        except Exception as err:
            _LOGGER.debug("Error fetching weather station data %s: %s", station_id, err)
            return None

    def save_override(self, user_input: str, section_id: str) -> bool:
        """Persist a user override mapping from the normalized user_input to section_id.

        Returns True on success.
        """
        try:
            overrides_path = Path(__file__).parent / "overrides.json"
            overrides = {}
            if overrides_path.exists():
                with overrides_path.open("r", encoding="utf-8") as fh:
                    try:
                        overrides = json.load(fh)
                    except Exception:
                        overrides = {}

            key = self._normalize_string(user_input)
            overrides[key] = section_id
            with overrides_path.open("w", encoding="utf-8") as fh:
                json.dump(overrides, fh, ensure_ascii=False, indent=2)
            _LOGGER.debug("Saved override: %s -> %s", key, section_id)
            return True
        except Exception as err:
            _LOGGER.warning("Failed to save override: %s", err)
            return False

    async def search_road_sections(self, query: str) -> List[Dict[str, Any]]:
        """Search for road sections by name, road number, or location.
        
        Args:
            query: Search string (e.g., "E18", "Perämerentie", "VT4")
        
        Returns:
            List of matching road sections
        """
        query_lower = query.lower().strip()
        
        if not query_lower:
            return []
        
        matching = []
        for section in MOCK_ROAD_SECTIONS:
            # Search in road, location, name, and description
            if (query_lower in section.get("road", "").lower() or
                query_lower in section.get("location", "").lower() or
                query_lower in section.get("name", "").lower() or
                query_lower in section.get("description", "").lower()):
                matching.append(section)
        
        return matching

    async def get_road_sections(self) -> List[Dict[str, Any]]:
        """Fetch available road sections."""
        try:
            _LOGGER.debug("Fetching road sections")
            # Return mock data in GeoJSON format
            return [
                {
                    "properties": {
                        "id": section["id"],
                        "name": section["name"],
                        "road": section["road"],
                        "location": section["location"],
                        "km": section["km"],
                        "description": section["description"]
                    }
                }
                for section in MOCK_ROAD_SECTIONS
            ]
        except Exception as err:
            _LOGGER.error("Error fetching road sections: %s", err)
            return []

    async def get_road_conditions(self, section_id: str, language: str = "fi") -> Optional[Dict[str, Any]]:
        """Fetch current road conditions for a specific section.
        
        Args:
            section_id: Either an API section ID or a user-entered road title (will be resolved)
            language: Language for condition text ("fi" or "en")
        """
        try:
            _LOGGER.debug("Fetching road conditions for section: %s", section_id)

            # Attempt to resolve user input to API section ID
            resolved_id = section_id
            if not re.match(r"^[0-9]{5}_\d+", section_id):
                # Doesn't look like an API ID, try to resolve
                resolved = await self.resolve_section_id(section_id)
                if resolved:
                    resolved_id = resolved
                else:
                    _LOGGER.warning("Could not resolve section title: %s", section_id)
            
            # If session looks like an aiohttp session, attempt to fetch real data
            if hasattr(self.session, "get"):
                try:
                    async with self.session.get(FORECAST_SECTIONS_URL) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            # Find matching forecast section by resolved ID
                            for fs in data.get("forecastSections", []):
                                if fs.get("id") == resolved_id:
                                    # Find observation
                                    obs = next((f for f in fs.get("forecasts", []) if f.get("type") == "OBSERVATION"), None)
                                    if obs:
                                        rc = obs.get("overallRoadCondition") or obs.get("forecastConditionReason", {}).get("roadCondition")
                                        condition_text = ROAD_CONDITION_MAP.get(rc, {}).get(language, rc or "Unknown")
                                        return {
                                            "features": [
                                                {
                                                    "type": "Feature",
                                                    "properties": {
                                                        "id": fs.get("id"),
                                                        "location": section_id,
                                                        "condition": condition_text,
                                                        "reliability": obs.get("reliability"),
                                                        "last_updated": data.get("dataUpdatedTime"),
                                                    },
                                                    "geometry": {"type": "Point", "coordinates": [0, 0]}
                                                }
                                            ]
                                        }
                except Exception as err:
                    _LOGGER.debug("Failed to fetch real road conditions, falling back to mock: %s", err)

            # Fallback to mock data if network unavailable or no match
            section = next(
                (s for s in MOCK_ROAD_SECTIONS if s["id"] == section_id),
                None
            )
            location = section["location"] if section else section_id

            # Choose language for condition descriptions
            if language == "en":
                condition = ENGLISH_ROAD_CONDITIONS[hash(section_id) % len(ENGLISH_ROAD_CONDITIONS)]
            else:
                condition = FINNISH_ROAD_CONDITIONS[hash(section_id) % len(FINNISH_ROAD_CONDITIONS)]

            return {
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": section_id,
                            "location": location,
                            "condition": condition,
                            "reliability": 90 + (hash(section_id) % 10),
                            "last_updated": datetime.now().isoformat(),
                        },
                        "geometry": {"type": "Point", "coordinates": [0, 0]}
                    }
                ]
            }
        except Exception as err:
            _LOGGER.error("Error fetching road conditions for %s: %s", section_id, err)
            return None

    async def get_forecast(self, section_id: str, language: str = "fi") -> Optional[Dict[str, Any]]:
        """Fetch forecast for a specific road section.
        
        Args:
            section_id: Either an API section ID or a user-entered road title (will be resolved)
            language: Language for condition text ("fi" or "en")
        """
        try:
            _LOGGER.debug("Fetching forecast for section: %s", section_id)
            
            # Attempt to resolve user input to API section ID
            resolved_id = section_id
            if not re.match(r"^[0-9]{5}_\d+", section_id):
                # Doesn't look like an API ID, try to resolve
                resolved = await self.resolve_section_id(section_id)
                if resolved:
                    resolved_id = resolved
                else:
                    _LOGGER.warning("Could not resolve section title: %s", section_id)
            
            # Try to use real API if session supports network calls
            if hasattr(self.session, "get"):
                try:
                    async with self.session.get(FORECAST_SECTIONS_URL) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            # Find matching forecast section by resolved ID
                            for fs in data.get("forecastSections", []):
                                if fs.get("id") == resolved_id:
                                    # Build forecasts from API
                                    forecasts = []
                                    for f in fs.get("forecasts", []):
                                        if f.get("type") == "FORECAST":
                                            time_iso = f.get("time")
                                            try:
                                                # Parse UTC time and convert to EET (UTC+2)
                                                dt_utc = datetime.fromisoformat(time_iso.replace("Z", "+00:00"))
                                                # Convert to EET (UTC+2)
                                                eet = timezone(timedelta(hours=2))
                                                dt_eet = dt_utc.astimezone(eet)
                                                time_str = dt_eet.strftime("%H:%M")
                                            except Exception:
                                                time_str = time_iso
                                            
                                            # Get overall road condition
                                            overall_rc = f.get("overallRoadCondition")
                                            overall_text = ROAD_CONDITION_MAP.get(overall_rc, {}).get(language, overall_rc or "")
                                            
                                            # Get specific road condition
                                            road_rc = f.get("forecastConditionReason", {}).get("roadCondition")
                                            road_text = ROAD_CONDITION_MAP.get(road_rc, {}).get(language, road_rc or "")
                                            # Make specific condition lowercase
                                            if road_text:
                                                road_text = road_text[0].lower() + road_text[1:] if len(road_text) > 0 else road_text
                                            
                                            # Combine both conditions
                                            if overall_text and road_text:
                                                condition_text = f"{overall_text}, {road_text}"
                                            elif overall_text:
                                                condition_text = overall_text
                                            elif road_text:
                                                condition_text = road_text
                                            else:
                                                condition_text = "Unavailable"
                                            
                                            forecasts.append({
                                                "type": "Feature",
                                                "properties": {
                                                    "time": time_str,
                                                    "condition": condition_text,
                                                },
                                                "geometry": {"type": "Point", "coordinates": [0, 0]}
                                            })
                                    if forecasts:
                                        return {"features": forecasts}
                except Exception as err:
                    _LOGGER.debug("Failed to fetch real forecast: %s", err)

            # No real data available - return unavailable instead of mock
            unavailable_text = "Tiedot eivät saatavilla" if language == "fi" else "Data unavailable"
            return {
                "features": [{
                    "type": "Feature",
                    "properties": {
                        "time": "N/A",
                        "condition": unavailable_text,
                    },
                    "geometry": {"type": "Point", "coordinates": [0, 0]}
                }]
            }
        except Exception as err:
            _LOGGER.error("Error fetching forecast for %s: %s", section_id, err)
            return None

    def parse_conditions(self, data: Dict[str, Any]) -> str:
        """Parse road conditions data into human-readable text."""
        if not data:
            return "Unknown"
        
        conditions = data.get("features", [])
        if not conditions:
            return "No data available"
        
        feature = conditions[0]
        properties = feature.get("properties", {})
        
        condition_text = properties.get("condition", "Unknown")
        # Return only the plain condition text for the sensor state.
        # Additional details (reliability, last_updated) are exposed
        # as entity attributes by the sensor implementation.
        return condition_text

    def parse_forecast(self, data: Dict[str, Any]) -> str:
        """Parse forecast data into human-readable text."""
        if not data:
            return "No forecast data available"
        
        forecasts = data.get("features", [])
        if not forecasts:
            return "No forecast data available"
        
        forecast_lines = []
        for forecast in forecasts:
            properties = forecast.get("properties", {})
            time_str = properties.get("time", "Unknown")
            condition = properties.get("condition", "Unknown")
            
            # Time is already in HH:MM format
            line = f"{time_str} {condition}"
            forecast_lines.append(line)
        
        return "\n".join(forecast_lines) if forecast_lines else "No forecast data"
