# University Ranking Analytics Core Application
import sys

if sys.platform == "win32":
    try:
        from app.core import orjson_shim
        sys.modules["orjson"] = orjson_shim
        from app.core import ormsgpack_shim
        sys.modules["ormsgpack"] = ormsgpack_shim
    except Exception:
        pass
