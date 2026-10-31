import sys
import os

if sys.platform == "win32":
    try:
        sys.path.insert(0, r"c:\Users\pkatt\OneDrive\Desktop\Projects\University_Ranking_Analytics\university_ranking-main")
        from app.core import orjson_shim
        sys.modules["orjson"] = orjson_shim
        from app.core import ormsgpack_shim
        sys.modules["ormsgpack"] = ormsgpack_shim
        sys.modules["xarray"] = None
        sys.modules["statsmodels"] = None
    except Exception:
        pass

os.chdir(r"c:\Users\pkatt\OneDrive\Desktop\Projects\University_Ranking_Analytics\university_ranking-main")
sys.path.insert(0, r"c:\Users\pkatt\OneDrive\Desktop\Projects\University_Ranking_Analytics\university_ranking-main")

os.environ["LANGSMITH_TEST_TRACKING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

import pytest

exit_code = pytest.main([
    "tests/test_database.py",
    "tests/test_analytics.py",
    "tests/test_api.py",
    "tests/test_agent.py",
    "tests/test_evaluations.py",
    "tests/test_frontend.py",
    "-v",
    "-p", "no:langsmith_plugin",
    "-p", "no:anyio",
    "-p", "no:asyncio",
    "--capture=no"
])
sys.exit(exit_code)
