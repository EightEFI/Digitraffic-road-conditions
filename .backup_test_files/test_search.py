#!/usr/bin/env python3
"""Test forecast search for 'Tie 3: Valtatie 3 3.250'."""

import asyncio
import aiohttp
from datetime import datetime, timezone, timedelta
import re

FORECAST_SECTIONS_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections/forecasts"
FORECAST_SECTIONS_METADATA_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections"

ROAD_CONDITION_MAP = {
    "DRY": {"fi": "Kuiva", "en": "Dry"},
    "WET": {"fi": "Märkä", "en": "Wet"},
    "FROST": {"fi": "Kuuraa", "en": "Frost"},
    "ICE": {"fi": "Jäätä", "en": "Ice"},
    "MOIST": {"fi": "Kostea", "en": "Damp"},
    "PARTLY_ICY": {"fi": "Osittain jäätä", "en": "Partly icy"},
    "SLUSH": {"fi": "Loskaa", "en": "Slush"},
    "SNOW": {"fi": "Lunta", "en": "Snow"},
    "NORMAL_CONDITION": {"fi": "Hyvä ajokeli", "en": "Good driving conditions"},
    "POOR_CONDITION": {"fi": "Huono ajokeli", "en": "Poor driving conditions"},
    "EXTREMELY_POOR_CONDITION": {"fi": "Erittäin huono ajokeli", "en": "Extremely poor driving conditions"},
}

def _normalize_string(s: str) -> str:
    """Normalize string for comparison."""
    s = s.lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

async def resolve_section_id(session, user_input: str):
    """Resolve user input to section ID."""
    if re.match(r"^[0-9]{5}_\d+", user_input):
        return user_input
    
    try:
        async with session.get(FORECAST_SECTIONS_METADATA_URL) as resp:
            if resp.status != 200:
                return None
            
            data = await resp.json()
            features = data.get("features", [])
            
            normalized_input = _normalize_string(user_input)
            input_tokens = set(normalized_input.split())
            
            best_match = None
            best_score = 0
            
            for feature in features:
                props = feature.get("properties", {})
                description = props.get("description", "")
                
                normalized_desc = _normalize_string(description)
                desc_tokens = set(normalized_desc.split())
                
                overlap = len(input_tokens & desc_tokens)
                if overlap > best_score:
                    best_score = overlap
                    best_match = props.get("id")
            
            if best_match and best_score > 0:
                return best_match
            
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

async def main():
    async with aiohttp.ClientSession() as session:
        user_input = "Tie 3: Valtatie 3 3.250"
        print(f"Searching for: {user_input}\n")
        
        # Resolve section ID
        resolved_id = await resolve_section_id(session, user_input)
        print(f"Resolved ID: {resolved_id}\n")
        
        if not resolved_id:
            print("Could not resolve section ID")
            return
        
        # Fetch forecast data
        async with session.get(FORECAST_SECTIONS_URL) as resp:
            if resp.status == 200:
                data = await resp.json()
                
                for fs in data.get("forecastSections", []):
                    if fs.get("id") == resolved_id:
                        print(f"Found section: {resolved_id}\n")
                        print("Forecasts:")
                        
                        for i, f in enumerate(fs.get("forecasts", [])[:8]):
                            if f.get("type") == "FORECAST":
                                time_iso = f.get("time")
                                
                                # Parse UTC time and convert to EET
                                dt_utc = datetime.fromisoformat(time_iso.replace("Z", "+00:00"))
                                eet = timezone(timedelta(hours=2))
                                dt_eet = dt_utc.astimezone(eet)
                                time_str = dt_eet.strftime("%H:%M")
                                
                                # Get conditions
                                overall_rc = f.get("overallRoadCondition")
                                overall_text = ROAD_CONDITION_MAP.get(overall_rc, {}).get("fi", overall_rc or "")
                                
                                road_rc = f.get("forecastConditionReason", {}).get("roadCondition")
                                road_text = ROAD_CONDITION_MAP.get(road_rc, {}).get("fi", road_rc or "")
                                
                                # Make specific condition lowercase
                                if road_text:
                                    road_text = road_text[0].lower() + road_text[1:] if len(road_text) > 0 else road_text
                                
                                # Combine
                                if overall_text and road_text:
                                    condition_text = f"{overall_text}, {road_text}"
                                elif overall_text:
                                    condition_text = overall_text
                                elif road_text:
                                    condition_text = road_text
                                else:
                                    condition_text = "Ei tietoa"
                                
                                print(f"- time: '{time_str}'")
                                print(f"  condition: {condition_text}")
                        
                        return
                
                print(f"Section {resolved_id} not found in API data")

if __name__ == "__main__":
    asyncio.run(main())
