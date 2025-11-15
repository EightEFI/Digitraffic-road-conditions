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
        print("Query:", q)
        norm_q = client._normalize_string(q)
        print("Normalized query:", norm_q)
        tokens = set(norm_q.split())

        async with session.get('https://tie.digitraffic.fi/api/tms/v1/stations', headers={"Accept":"application/json"}) as resp:
            print('Stations endpoint status:', resp.status)
            data = await resp.json()
            features = data.get('features', [])

        found = []
        for feat in features:
            props = feat.get('properties', {})
            names = props.get('names') or {}
            cand_list = [names.get(k, '') for k in ('fi','sv','en')] + [props.get('name','')]
            for cand in cand_list:
                if not cand:
                    continue
                norm_cand = client._normalize_string(cand)
                common = tokens & set(norm_cand.split())
                if common:
                    found.append((props.get('id'), cand, norm_cand, common))
                    break

        print('Found', len(found), 'candidate stations with token overlap')
        for pid, cand, norm_cand, common in found[:20]:
            print(pid, cand, '->', norm_cand, 'common=', common)


if __name__ == '__main__':
    asyncio.run(main())
