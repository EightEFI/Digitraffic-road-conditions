import importlib.util
from pathlib import Path
import inspect

CLIENT_PATH = Path(__file__).parent / 'custom_components' / 'digitraffic_road' / 'client.py'
spec = importlib.util.spec_from_file_location('digit', str(CLIENT_PATH))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
cls = getattr(mod, 'DigitraficClient')
print(inspect.getsource(cls.async_search_tms_stations))
