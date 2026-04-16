"""Reverse-proxy routes for Cockpit (:9090) and EveBox (:5636)."""
import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["proxy"])

_EVEBOX   = "http://127.0.0.1:5636"
_COCKPIT  = "http://127.0.0.1:9090"

# hop-by-hop headers that must not be forwarded
_HOP = {"transfer-encoding", "te", "trailers", "connection",
        "keep-alive", "proxy-authorization", "proxy-authenticate",
        "upgrade"}


async def _proxy(target: str, path: str, request: Request) -> Response:
    url = f"{target}/{path}"
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in _HOP and k.lower() != "host"}
    body = await request.body()

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                params=dict(request.query_params),
            )
        out_headers = {k: v for k, v in resp.headers.items()
                       if k.lower() not in _HOP}
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=out_headers,
            media_type=resp.headers.get("content-type"),
        )
    except httpx.ConnectError:
        return Response(
            content=_offline_page(target),
            status_code=503,
            media_type="text/html",
        )


def _offline_page(target: str) -> bytes:
    name = "EveBox" if "5636" in target else "Cockpit"
    port = "5636" if "5636" in target else "9090"
    install_hint = (
        "Run: <code>sudo /home/w01f/Hackathon/darklead/setup_tools.sh</code>"
        if name == "Cockpit"
        else f"Run: <code>/home/w01f/.local/bin/evebox server --sqlite --no-auth --port 5636</code>"
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{name} Offline</title>
<style>
  body {{ background:#0d1117; color:#8a96b0; font-family:monospace;
          display:flex; align-items:center; justify-content:center; height:100vh; margin:0; }}
  .box {{ text-align:center; max-width:480px; }}
  h2 {{ color:#dde3ef; margin-bottom:8px; }}
  .badge {{ background:#1e2d47; color:#f26d21; padding:4px 10px;
            border-radius:4px; font-size:13px; margin-bottom:16px; display:inline-block; }}
  code {{ background:#1e2d47; color:#3ecf8e; padding:6px 12px;
          border-radius:4px; display:inline-block; margin-top:8px; font-size:13px; }}
  a {{ color:#4a9ff5; }}
</style>
</head>
<body>
<div class="box">
  <div class="badge">PORT {port} OFFLINE</div>
  <h2>{name} is not running</h2>
  <p>{install_hint}</p>
  <p style="font-size:12px;margin-top:16px">
    Then <a href="javascript:location.reload()">reload this page</a>
  </p>
</div>
</body>
</html>""".encode()


# ── EveBox auto-start ─────────────────────────────────────────────────────────

@router.post("/evebox/start")
async def start_evebox():
    """Launch evebox server process if not running."""
    import subprocess, shutil, os
    from pathlib import Path

    evebox_bin = shutil.which("evebox") or str(Path.home() / ".local/bin/evebox")
    if not Path(evebox_bin).exists():
        return {"ok": False, "error": "evebox binary not found"}

    eve_dir = Path.home() / ".local/share/suricata"
    data_dir = Path.home() / ".local/share/evebox"
    eve_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal eve.json if it doesn't exist
    eve_json = eve_dir / "eve.json"
    if not eve_json.exists():
        import json, datetime
        eve_json.write_text(json.dumps({
            "timestamp": datetime.datetime.utcnow().isoformat() + "+0000",
            "event_type": "stats", "stats": {"uptime": 0}
        }) + "\n")

    try:
        proc = subprocess.Popen(
            [evebox_bin, "server",
             "--host", "127.0.0.1", "--port", "5636",
             "--sqlite", "--no-auth", "--no-tls",
             "--data-directory", str(data_dir),
             str(eve_json)],
            stdout=open("/tmp/evebox.log", "a"),
            stderr=subprocess.STDOUT,
        )
        return {"ok": True, "pid": proc.pid}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── EveBox proxy (/evebox/**) ─────────────────────────────────────────────────

@router.api_route("/evebox", methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
@router.api_route("/evebox/{path:path}", methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
async def proxy_evebox(request: Request, path: str = ""):
    return await _proxy(_EVEBOX, path, request)


# ── Cockpit proxy (/cockpit/**) ────────────────────────────────────────────────

@router.api_route("/cockpit", methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
@router.api_route("/cockpit/{path:path}", methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
async def proxy_cockpit(request: Request, path: str = ""):
    return await _proxy(_COCKPIT, path, request)
