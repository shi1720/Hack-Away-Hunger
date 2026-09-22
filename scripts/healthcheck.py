"""Container-local liveness check that respects the configured trusted Host."""
import os
import urllib.request

host = os.environ.get("PANTRY_ALLOWED_HOSTS", "127.0.0.1").split(",")[0].strip()
request = urllib.request.Request("http://127.0.0.1:8000/api/health", headers={"Host": host})
with urllib.request.urlopen(request, timeout=3) as response:
    if response.status != 200:
        raise SystemExit(1)
