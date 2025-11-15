#!/usr/bin/env python3
"""CLI helper to list candidate section IDs and persist a user-selected override.

Usage:
  - List candidates: `python pick_section.py --list "Tie 3 3.250"`
  - Interactive pick: `python pick_section.py "Tie 3 3.250"` (prompts for choice)

This script writes `custom_components/digitraffic_road/overrides.json` with a mapping
from normalized query -> selected section ID.
"""
import argparse
import asyncio
import aiohttp
import importlib.util
from pathlib import Path

CLIENT_PY = Path(__file__).parent / 'custom_components' / 'digitraffic_road' / 'client.py'


def load_client_class():
    spec = importlib.util.spec_from_file_location("digitraffic_client", str(CLIENT_PY))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "DigitraficClient")


async def list_candidates(query: str, limit: int = 8):
    DigitraficClient = load_client_class()
    async with aiohttp.ClientSession() as session:
        client = DigitraficClient(session)
        candidates = await client.resolve_section_candidates(query, max_candidates=limit)
        if not candidates:
            print("No candidates found for:", query)
            return []
        for i, c in enumerate(candidates, start=1):
            rid = c.get('id')
            desc = c.get('description') or c.get('name') or ''
            rn = c.get('roadNumber')
            rs = c.get('roadSectionNumber')
            print(f"{i}. {rid}  (road={rn}, section={rs})\n   {desc}\n")
        return candidates


async def interactive_pick(query: str):
    candidates = await list_candidates(query)
    if not candidates:
        return
    try:
        choice = input(f"Pick a candidate number to persist as override for '{query}' (or 'q' to quit): ")
    except KeyboardInterrupt:
        print("\nAborted")
        return
    if not choice or choice.lower().startswith('q'):
        print("No changes made.")
        return
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(candidates):
            print("Invalid selection")
            return
        selected = candidates[idx]
        rid = selected.get('id')
        # write overrides file
        overrides_path = Path(__file__).parent / 'custom_components' / 'digitraffic_road' / 'overrides.json'
        overrides = {}
        if overrides_path.exists():
            try:
                overrides = json.loads(overrides_path.read_text(encoding='utf-8'))
            except Exception:
                overrides = {}
        key = load_client_class()._normalize_string(query) if False else None
        # to normalize here, reuse client's normalization by loading class and instantiating
        DigitraficClient = load_client_class()
        client = DigitraficClient(None)
        key = client._normalize_string(query)
        overrides[key] = rid
        overrides_path.write_text(json.dumps(overrides, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"Saved override: '{query}' -> {rid} (stored key: {key})")
    except ValueError:
        print("Invalid input")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('query', nargs='?', help='Search query (e.g., "Tie 3 3.250")')
    parser.add_argument('--list', action='store_true', help='Only list candidates')
    parser.add_argument('--limit', type=int, default=8, help='Max candidates to show')
    args = parser.parse_args()

    if not args.query:
        query = input('Enter section to search for: ')
    else:
        query = args.query

    if args.list:
        asyncio.run(list_candidates(query, limit=args.limit))
    else:
        asyncio.run(interactive_pick(query))


if __name__ == '__main__':
    main()
