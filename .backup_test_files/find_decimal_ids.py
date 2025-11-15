#!/usr/bin/env python3
import asyncio
import aiohttp

URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections"

async def main():
    async with aiohttp.ClientSession() as s:
        async with s.get(URL) as r:
            r.raise_for_status()
            data = await r.json()
    for feat in data.get('features', []):
        props = feat.get('properties', {})
        idv = props.get('id')
        if idv and '.' in idv:
            print('ID:', idv)
            for k in ('description','roadNumber','roadSectionNumber','length','roadSegments'):
                if k in props:
                    print(' ',k,':',props.get(k))
            print()
            # limit
            break

if __name__ == '__main__':
    asyncio.run(main())
