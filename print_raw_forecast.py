#!/usr/bin/env python3
"""Resolve and print raw forecast JSON for a given human-readable section title.

Usage: python print_raw_forecast.py

This script resolves a user-entered title to the API section ID using the
forecast-sections metadata endpoint, then downloads the full forecasts feed
and prints the matching `forecastSection` object as raw JSON.
"""
import asyncio
import aiohttp
import json
import re
from typing import Optional

FORECAST_SECTIONS_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections/forecasts"
FORECAST_SECTIONS_METADATA_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections"

QUERY = "Tie 3: Valtatie 3 3.250"


def _normalize_string(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


async def resolve_section_id(session: aiohttp.ClientSession, user_input: str) -> Optional[str]:
    if re.match(r"^[0-9]{5}_\d+", user_input):
        return user_input
    async with session.get(FORECAST_SECTIONS_METADATA_URL) as resp:
        resp.raise_for_status()
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


async def main():
    async with aiohttp.ClientSession() as session:
        print(f"Resolving: '{QUERY}'")
        section_id = await resolve_section_id(session, QUERY)
        print(f"Resolved ID: {section_id}\n")
        if not section_id:
            print("Could not resolve section ID")
            return

        print("Downloading full forecasts feed (this may be large)...")
        async with session.get(FORECAST_SECTIONS_URL) as resp:
            resp.raise_for_status()
            data = await resp.json()

        # Find the matching forecastSection object
        match = None
        for fs in data.get("forecastSections", []):
            if fs.get("id") == section_id:
                match = fs
                break

        if not match:
            print(f"Section {section_id} not found in forecast feed")
            return

        # Pretty-print raw JSON for the matching section
        print(json.dumps(match, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
