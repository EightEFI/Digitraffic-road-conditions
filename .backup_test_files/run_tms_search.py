import asyncio
import aiohttp
import importlib.util
from pathlib import Path

CLIENT_PATH = Path(__file__).parent / 'custom_components' / 'digitraffic_road' / 'client.py'


def load_client_class():
    spec = importlib.util.spec_from_file_location("digitraffic_client", str(CLIENT_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "DigitraficClient")


async def main():
    DigitraficClient = load_client_class()
    async with aiohttp.ClientSession() as session:
        client = DigitraficClient(session)
        q = "Tie 3 Vaasa"
        print("Searching TMS for:", q)
        res = await client.async_search_tms_stations(q)
        print(f"Found {len(res)} matches")
        for i, r in enumerate(res, 1):
            print(i, r.get('id'), r.get('names') or r.get('name'))

if __name__ == '__main__':
    asyncio.run(main())
