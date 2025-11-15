#!/usr/bin/env python3
"""Print top metadata matches for a query and details for the resolved ID."""

import asyncio
import aiohttp
import re
from typing import List, Tuple

METADATA_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections"
QUERY = "Tie 3: Valtatie 3 3.250"


def _normalize(s: str) -> str:
    s = s or ""
    s = s.lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def score_match(query_tokens: set, desc: str) -> int:
    desc_tokens = set(_normalize(desc).split())
    return len(query_tokens & desc_tokens)


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(METADATA_URL) as resp:
            resp.raise_for_status()
            data = await resp.json()
        features = data.get('features', [])
        qnorm = _normalize(QUERY)
        qtokens = set(qnorm.split())
        scored: List[Tuple[int, dict]] = []
        for feat in features:
            props = feat.get('properties', {})
            desc = props.get('description') or props.get('name') or ''
            s = score_match(qtokens, desc)
            scored.append((s, props))
        scored.sort(key=lambda x: (-x[0], x[1].get('id', '')))
        print(f"Top 8 matches for '{QUERY}':\n")
        for s, props in scored[:8]:
            print(f"score={s} id={props.get('id')} description={props.get('description')} roadNumber={props.get('roadNumber')} roadSectionNumber={props.get('roadSectionNumber')}")
        
        # Also print full props for best match
        best = scored[0][1]
        print("\nBest match properties:\n")
        for k,v in best.items():
            print(f"{k}: {v}")

if __name__ == '__main__':
    asyncio.run(main())
