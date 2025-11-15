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
        print('Calling async_search_tms_stations...')
        res = await client.async_search_tms_stations(q)
        print('async_search_tms_stations returned', len(res), 'items')
        for r in res[:10]:
            print('->', r.get('id'), r.get('names') or r.get('name'))

        print('\nRunning inline scan (same logic)')
        async with session.get('https://tie.digitraffic.fi/api/tms/v1/stations', headers={"Accept":"application/json"}) as resp:
            data = await resp.json()
            features = data.get('features', [])
        norm = client._normalize_string(q)
        tokens = set(norm.split())
        found = []
        for feat in features:
            props = feat.get('properties', {})
            names = props.get('names') or {}
            cands = [names.get(k, '') for k in ('fi','sv','en')] + [props.get('name','')]
            for cand in cands:
                if not cand:
                    continue
                norm_cand = client._normalize_string(cand)
                if norm_cand == norm:
                    found.append((100, props))
                    break
                common = tokens & set(norm_cand.split())
                if common:
                    found.append((len(common), props))
                    break
        # dedup
        best = {}
        for score,p in found:
            pid = p.get('id')
            if pid not in best or score > best[pid][0]:
                best[pid] = (score,p)
        scored = sorted((s,p) for s,p in best.values())
        scored.reverse()
        print('inline scan found', len(scored), 'items')
        for s,p in scored[:10]:
            print(s, p.get('id'), p.get('name'))

if __name__ == '__main__':
    asyncio.run(main())
