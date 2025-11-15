#!/usr/bin/env python3
"""Get all unique road condition values from the API."""

import asyncio
import aiohttp

FORECAST_SECTIONS_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections/forecasts"

async def get_all_conditions():
    async with aiohttp.ClientSession() as session:
        async with session.get(FORECAST_SECTIONS_URL) as resp:
            if resp.status == 200:
                data = await resp.json()
                
                conditions = set()
                overall_conditions = set()
                
                for fs in data.get("forecastSections", []):
                    for f in fs.get("forecasts", []):
                        # Get roadCondition from forecastConditionReason
                        rc = f.get("forecastConditionReason", {}).get("roadCondition")
                        if rc:
                            conditions.add(rc)
                        
                        # Get overallRoadCondition
                        oc = f.get("overallRoadCondition")
                        if oc:
                            overall_conditions.add(oc)
                
                print("All unique 'roadCondition' values from API:")
                for cond in sorted(conditions):
                    print(f"  - {cond}")
                
                print("\nAll unique 'overallRoadCondition' values from API:")
                for cond in sorted(overall_conditions):
                    print(f"  - {cond}")

if __name__ == "__main__":
    asyncio.run(get_all_conditions())
