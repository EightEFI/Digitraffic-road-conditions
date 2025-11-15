#!/usr/bin/env python3
"""Analyze forecast-sections metadata IDs and correlate ID parts with properties."""

import asyncio
import aiohttp
import re
from collections import defaultdict

METADATA_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections"

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(METADATA_URL) as resp:
            resp.raise_for_status()
            data = await resp.json()
        features = data.get('features', [])

        patterns = defaultdict(int)
        samples = {}
        total = 0
        for feat in features:
            props = feat.get('properties', {})
            idv = props.get('id')
            if not idv:
                continue
            parts = idv.split('_')
            patterns[len(parts)] += 1
            key = (len(parts), tuple(parts[:3]))
            if key not in samples:
                samples[key] = (idv, props)
            total += 1

        print(f"Total features: {total}\n")
        print("Observed ID part counts:")
        for k in sorted(patterns.keys()):
            print(f"  {k} parts: {patterns[k]}")

        print("\nSample IDs and properties (few examples):\n")
        count = 0
        for (plen, head), (idv, props) in list(samples.items())[:20]:
            print(f"ID: {idv}")
            for fld in ('description','roadNumber','roadSectionNumber','length','roadSegments','linkIds'):
                if fld in props:
                    print(f"  {fld}: {props.get(fld)}")
            print()
            count += 1
            if count>=10:
                break

        # Try correlations
        print("Correlations attempts:\n")
        # Check if first part equals zero-padded roadNumber
        match_roadnum = 0
        match_sectionnum = 0
        match_part3_to_segment_start = 0
        match_last_float_matches_km = 0
        samples_checked = 0
        for feat in features[:500]:
            props = feat.get('properties', {})
            idv = props.get('id')
            if not idv:
                continue
            parts = idv.split('_')
            if len(parts) >= 2:
                try:
                    p0 = int(parts[0])
                    if 'roadNumber' in props and props.get('roadNumber') == p0:
                        match_roadnum += 1
                except Exception:
                    pass
                try:
                    p1 = int(parts[1])
                    if 'roadSectionNumber' in props and props.get('roadSectionNumber') == p1:
                        match_sectionnum += 1
                except Exception:
                    pass
            if len(parts) >= 3 and 'roadSegments' in props:
                try:
                    p2 = int(parts[2])
                    # compare against any startDistance or endDistance
                    segs = props.get('roadSegments') or []
                    for s in segs:
                        if s.get('startDistance') == p2 or s.get('endDistance') == p2:
                            match_part3_to_segment_start += 1
                            break
                except Exception:
                    pass
            # last part float?
            last = parts[-1]
            try:
                fv = float(last)
                # compare to any linkIds? or maybe km marker as float
                # compare to description numeric if present
                desc = props.get('description') or ''
                m = re.search(r"(\d+\.\d+)", desc)
                if m and abs(float(m.group(1)) - fv) < 0.0001:
                    match_last_float_matches_km += 1
            except Exception:
                pass
            samples_checked += 1

        print(f"Checked samples: {samples_checked}")
        print(f"first part equals roadNumber: {match_roadnum}")
        print(f"second part equals roadSectionNumber: {match_sectionnum}")
        print(f"third part equals some roadSegment start/endDistance: {match_part3_to_segment_start}")
        print(f"last part floats matching description km pattern: {match_last_float_matches_km}")

if __name__ == '__main__':
    asyncio.run(main())
