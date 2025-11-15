#!/usr/bin/env python3
"""Check what overall conditions the API is returning."""

import asyncio
import aiohttp

FORECAST_SECTIONS_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections/forecasts"

async def check_conditions():
    async with aiohttp.ClientSession() as session:
        async with session.get(FORECAST_SECTIONS_URL) as resp:
            if resp.status == 200:
                data = await resp.json()
                
                section_id = "00003_250_00000_1_0"
                
                for fs in data.get("forecastSections", []):
                    if fs.get("id") == section_id:
                        print("Forecasts for Tie 3:\n")
                        
                        for i, f in enumerate(fs.get("forecasts", [])[:5]):
                            if f.get("type") == "FORECAST":
                                time_iso = f.get("time")
                                overall = f.get("overallRoadCondition")
                                road = f.get("forecastConditionReason", {}).get("roadCondition")
                                print(f"{time_iso}: overall={overall}, road={road}")

if __name__ == "__main__":
    asyncio.run(check_conditions())
