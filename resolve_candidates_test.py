#!/usr/bin/env python3
"""Test the new resolve_section_candidates() method in DigitraficClient."""

import asyncio
import aiohttp
import sys
sys.path.insert(0, '/workspaces/Digitraffic-road-conditions/custom_components/digitraffic_road')

from client import DigitraficClient

async def main():
    async with aiohttp.ClientSession() as session:
        client = DigitraficClient(session)
        query = "Tie 3: Valtatie 3 3.250"
        print(f"Query: {query}\n")
        candidates = await client.resolve_section_candidates(query)
        print(f"Found {len(candidates)} candidate(s):\n")
        for i, c in enumerate(candidates, 1):
            print(f"{i}. id={c.get('id')} description={c.get('description')} roadNumber={c.get('roadNumber')} roadSectionNumber={c.get('roadSectionNumber')}")

if __name__ == '__main__':
    asyncio.run(main())
