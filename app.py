import os, time, hmac, json, base64
from hashlib import sha256
from flask import Flask, redirect

app = Flask(__name__)

# --- ENV ---
TENANT_ID        = int(os.getenv("TENANT_ID", "1"))
STUDIO_ID        = os.getenv("STUDIO_ID")       # optional
COURSE_ID        = os.getenv("COURSE_ID")       # optional
ENTRY_URL        = os.getenv("ENTRY_URL")       # z.B. http://127.0.0.1:5000/
RETURN_URL       = os.getenv("RETURN_URL")      # optional
TTL_SECONDS      = int(os.getenv("TTL_SECONDS", "600"))
API_SHARED_SECRET= os.getenv("API_SHARED_SECRET")  # MUSS gesetzt sein

# --- JWT-Helfer (HS256, URL-safe) ---
def b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def sign(payload: dict, secret: str, header: dict | None = None) -> str:
    header = header or {"alg": "HS256", "typ": "JWT"}
    h = b64u(json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    p = b64u(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    msg = f"{h}.{p}".encode("ascii")
    sig = hmac.new(secret.encode("utf-8"), msg, sha256).digest()
    return f"{h}.{p}.{b64u(sig)}"

@app.route("/")
def index():
    # simpler Button direkt als HTML
    return """
        <html><body style="font-family:system-ui;padding:32px">
          <h2>Demo: Jetzt reservieren</h2>
          <p>Dieser Button baut das signierte Mandanten-Token und leitet zu deiner Plattform um.</p>
          <a href="/go" style="display:inline-block;padding:12px 16px;
             background:#2563eb;color:#fff;border-radius:8px;text-decoration:none;">
             Jetzt reservieren
          </a>
        </body></html>
    """

@app.route("/go")
def go():
    # Fehlende ENV sauber melden
    missing = [k for k, v in {
        "API_SHARED_SECRET": API_SHARED_SECRET,
        "ENTRY_URL": ENTRY_URL
    }.items() if not v]
    if missing:
        return (f"Missing ENV vars: {', '.join(missing)}", 500)

    now = int(time.time())
    payload = {
        "nonce": f"btn-{now}",           # Replay-Schutz
        "exp": now + TTL_SECONDS,        # Ablaufzeit
        "studio_id": int(STUDIO_ID) if STUDIO_ID else None,
        "course_id": int(COURSE_ID) if COURSE_ID else None,
        "return_url": RETURN_URL,
    }
    header = {"alg": "HS256", "typ": "JWT", "tenant_id": TENANT_ID}
    token = sign(payload, API_SHARED_SECRET, header)

    # an deine Plattform (lokal oder prod) weiterleiten
    sep = "&" if "?" in ENTRY_URL else "?"
    return redirect(f"{ENTRY_URL}{sep}st={token}", code=302)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
