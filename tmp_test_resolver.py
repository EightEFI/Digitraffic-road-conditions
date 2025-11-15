import asyncio
import aiohttp
import importlib.util
from pathlib import Path

CLIENT_PATH = Path(__file__).parent / "custom_components" / "digitraffic_road" / "client.py"


def load_client_class():
    spec = importlib.util.spec_from_file_location("digitraffic_client", str(CLIENT_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "DigitraficClient")


async def main():
    DigitraficClient = load_client_class()
    async with aiohttp.ClientSession() as session:
        client = DigitraficClient(session)
        inputs = ["Tie 3 3.252", "Tie 3 3.250", "Valtatie 3 3.250"]
        for q in inputs:
            resolved = await client.resolve_section_id(q)
            print(f"Query: {q!r} -> Resolved ID: {resolved}")


if __name__ == '__main__':
    asyncio.run(main())
