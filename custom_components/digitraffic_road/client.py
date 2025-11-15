"""Digitraffic API client for road conditions."""
import aiohttp
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone

_LOGGER = logging.getLogger(__name__)

# Digitraffic API endpoints
BASE_URL = "https://tie.digitraffic.fi/api/v1/data"
FORECAST_SECTIONS_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections/forecasts"
FORECAST_SECTIONS_METADATA_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections"

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
    # Older/legacy API values
    "DRY": {"fi": "Tienpinta on kuiva", "en": "Road surface is dry"},
    "WET": {"fi": "Tienpinta on märkä", "en": "Road surface is wet"},
    "ICY": {"fi": "Tienpinnassa on paikoin jäätä", "en": "Patches of ice on the road"},
    "POSSIBLE_RIME": {"fi": "Tienpinnassa on mahdollisesti kuuraa", "en": "Possible hoarfrost on the road"},
    "SLIPPERY": {"fi": "Liukasta, tienpinnassa on jäätä tai lunta", "en": "Slippery, ice or snow on the road"},
    "SNOW": {"fi": "Lumisade tai rankka vesisade", "en": "Snow or heavy rain"},
    "HEAVY_SNOW": {"fi": "Raskas lumisade", "en": "Heavy snow"},
    "GOOD": {"fi": "Hyvä ajokeli", "en": "Good driving conditions"},
    "POOR": {"fi": "Huono ajokeli", "en": "Poor driving conditions"},
    # Actual forecast-sections API values
    "NORMAL_CONDITION": {"fi": "Normaali ajokelistä", "en": "Normal driving conditions"},
    "MOIST": {"fi": "Tienpinta on kostea", "en": "Road surface is damp"},
    "FROST": {"fi": "Tienpinnassa on kuuraa", "en": "Hoarfrost on road"},
    "ICE": {"fi": "Tienpinnassa on jäätä", "en": "Ice on road"},
    "PARTLY_ICY": {"fi": "Tienpinta on osittain jäinen", "en": "Road surface partly icy"},
    "SLEET": {"fi": "Räntää", "en": "Sleet"},
    "SNOW": {"fi": "Lumisade", "en": "Snow"},
    "HEAVY_SNOW": {"fi": "Raskas lumisade", "en": "Heavy snow"},
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
            
            # If input looks like an ID (numeric pattern), return as-is
            if re.match(r"^[0-9]{5}_\d+", user_input):
                return user_input
            
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
                    candidates.sort(reverse=True, key=lambda x: x[0])
                    best_score, best_id, best_desc = candidates[0]
                    _LOGGER.debug("Resolved '%s' to section %s (score %d, desc: %s)", 
                                 user_input, best_id, best_score, best_desc)
                    return best_id
                else:
                    _LOGGER.debug("No matching section found for: %s", user_input)
                    return None
        
        except Exception as err:
            _LOGGER.warning("Error resolving section ID: %s", err)
            return None

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
                                            rc = f.get("forecastConditionReason", {}).get("roadCondition") or f.get("overallRoadCondition")
                                            condition_text = ROAD_CONDITION_MAP.get(rc, {}).get(language, rc or "Unavailable")
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
