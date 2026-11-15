"""CI-only TLS gateway smoke test with fictional farm input, never real data."""
import argparse
import base64
import json
import os
from pathlib import Path
import ssl
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-farm", type=Path)
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Run this throwaway-credential smoke check only in its isolated CI job.")
    base = os.environ["STAGING_ORIGIN"]
    context = ssl.create_default_context(cafile=os.environ["STAGING_CA"])
    auth = "Basic " + base64.b64encode(b"ci-reviewer:ci-only-not-a-secret").decode()

    def request(path, method="GET", data=None, authenticated=True, origin=None):
        headers = {"Authorization": auth} if authenticated else {}
        if origin:
            headers["Origin"] = origin
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = Request(base + path, method=method, headers=headers,
                      data=None if data is None else json.dumps(data).encode())
        for attempt in range(20):
            try:
                response = urlopen(req, context=context, timeout=5)
                break
            except HTTPError as error:
                response = error
                break
            except URLError:
                if attempt == 19:
                    raise
                time.sleep(0.5)
        with response:
            return response.status, response.read(), response.headers

    if args.verify_farm:
        farm_id = args.verify_farm.read_text().strip()
        assert request("/api/v1/farms/" + farm_id)[0] == 200
        print("PASS: fictional farm survives backend restart.")
        return
    for path in ("/", "/api/v1/health", "/api/v1/ready", "/api/v1/farms/unknown"):
        assert request(path, authenticated=False)[0] == 401
    assert request("/")[0] == 200
    assert request("/api/v1/ready")[0] == 200
    assert request("/api/v1/farms/unknown")[0] == 404
    assert request("/api/v1/farms", "POST", {}, origin="https://bad.example")[0] == 403
    assert request("/api/v1/farms", "POST", {}, origin=base)[0] == 422
    assert request("/api/v1/health", origin="https://bad.example")[2].get("Access-Control-Allow-Origin") is None
    assert request("/api/v1/health", origin=base)[2]["Access-Control-Allow-Origin"] == base
    profile = json.loads((Path(__file__).resolve().parents[2] / "data/fixtures/farm.synthetic.json").read_text())
    status, body, _ = request("/api/v1/farms", "POST", profile, origin=base)
    assert status == 201
    (Path(os.environ["RUNNER_TEMP"]) / "staging-farm-id").write_text(json.loads(body)["id"])
    print("PASS: private TLS gateway, authentication, CORS, write boundary and fictional farm creation.")


if __name__ == "__main__":
    main()
