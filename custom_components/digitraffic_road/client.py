"""Digitraffic API client for road conditions."""
import aiohttp
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)

# Digitraffic API endpoint
BASE_URL = "https://tie.digitraffic.fi/api/v1/data"

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

    async def get_road_conditions(self, section_id: str) -> Optional[Dict[str, Any]]:
        """Fetch current road conditions for a specific section."""
        try:
            _LOGGER.debug("Fetching road conditions for section: %s", section_id)
            
            # Get the section name for context
            section = next(
                (s for s in MOCK_ROAD_SECTIONS if s["id"] == section_id),
                None
            )
            location = section["location"] if section else section_id
            
            # Use Finnish road condition descriptions
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

    async def get_forecast(self, section_id: str) -> Optional[Dict[str, Any]]:
        """Fetch 12h forecast for a specific road section."""
        try:
            _LOGGER.debug("Fetching forecast for section: %s", section_id)
            
            # Generate mock forecast data for next 12 hours (every 2 hours)
            forecasts = []
            now = datetime.now()
            # Round to next 2-hour mark
            hours_to_next = 2 - (now.hour % 2)
            if hours_to_next == 2:
                hours_to_next = 0
            start_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=hours_to_next)
            
            for i in range(0, 12, 2):  # Every 2 hours
                forecast_time = start_time + timedelta(hours=i)
                condition = FINNISH_ROAD_CONDITIONS[i % len(FINNISH_ROAD_CONDITIONS)]
                forecasts.append({
                    "type": "Feature",
                    "properties": {
                        "time": forecast_time.strftime("%H:%M"),
                        "condition": condition,
                    },
                    "geometry": {"type": "Point", "coordinates": [0, 0]}
                })
            
            return {
                "features": forecasts
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
        reliability = properties.get("reliability", "")
        location = properties.get("location", "")
        
        result = condition_text
        if location:
            result = f"{location}: {condition_text}"
        if reliability:
            result += f" (Reliability: {reliability}%)"
        
        return result

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
