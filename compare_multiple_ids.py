#!/usr/bin/env python3
"""Fetch forecast entries for a list of candidate IDs and print their forecasts."""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone, timedelta

FORECAST_SECTIONS_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections/forecasts"
CANDIDATES = [
    "00003_250_00000_1_0",
    "00003_250_01836_1_263.626",
    "00003_250_04429_1_0",
]

async def main():
    async with aiohttp.ClientSession() as session:
        print("Downloading full forecasts feed...")
        async with session.get(FORECAST_SECTIONS_URL) as resp:
            resp.raise_for_status()
            data = await resp.json()
        fs_map = {fs.get('id'): fs for fs in data.get('forecastSections', [])}
        for cid in CANDIDATES:
            print('\n=== ID:', cid, '===')
            fs = fs_map.get(cid)
            if not fs:
                print('  Not found in feed')
                continue
            for f in fs.get('forecasts', []):
                if f.get('type') == 'FORECAST':
                    print('  time:', f.get('time'), 'overall:', f.get('overallRoadCondition'), 'road:', f.get('forecastConditionReason', {}).get('roadCondition'))

if __name__ == '__main__':
    asyncio.run(main())
