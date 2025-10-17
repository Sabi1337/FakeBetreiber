import os, time, hmac, hashlib, json, base64
from flask import Flask, redirect, url_for

app = Flask(__name__)

TENANT_ID = int(os.getenv("TENANT_ID", "1"))
STUDIO_ID = os.getenv("STUDIO_ID")          # optional
COURSE_ID = os.getenv("COURSE_ID")          # optional
ENTRY_URL = os.getenv("ENTRY_URL")          # z.B. http://127.0.0.1:5000/
RETURN_URL = os.getenv("RETURN_URL")        # z.B. https://kunde.de/danke
TTL_SECONDS = int(os.getenv("TTL_SECONDS", "600"))
API_SHARED_SECRET = os.getenv("API_SHARED_SECRET")  # MUSS mit deinem Backend übereinstimmen!

def b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def sign(payload: dict, secret: str, header: dict) -> str:
    head = b64u(json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    body = b64u(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    mac = hmac.new(secret.encode("utf-8"), f"{head}.{body}".encode("ascii"), hashlib.sha256).digest()
    sig = b64u(mac)
    return f"{head}.{body}.{sig}"

@app.route("/")
def index():
    return (
        "<html><body style='font-family:system-ui;background:#0b1020;color:#fff;display:grid;place-items:center;height:100vh'>"
        "<a href='/go' style='padding:14px 22px;border-radius:12px;background:#3b82f6;text-decoration:none;color:white;font-weight:600;box-shadow:0 8px 30px #0006'>"
        "Jetzt reservieren</a></body></html>"
    )

@app.route("/go")
def go():
    assert API_SHARED_SECRET and ENTRY_URL, "Env VARS fehlen"
    now = int(time.time())
    payload = {
        "nonce": f"btn-{now}",
        "exp": now + TTL_SECONDS,
        "studio_id": int(STUDIO_ID) if STUDIO_ID else None,
        "course_id": int(COURSE_ID) if COURSE_ID else None,
        "return_url": RETURN_URL,
    }
    header = {"alg": "HS256", "typ": "JWT", "tenant_id": TENANT_ID}
    token = sign(payload, API_SHARED_SECRET, header)
    sep = "&" if "?" in ENTRY_URL else "?"
    return redirect(f"{ENTRY_URL}{sep}st={token}", code=302)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
