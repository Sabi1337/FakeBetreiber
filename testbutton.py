# app.py
import hmac, hashlib, time, json, base64, uuid, os
from flask import Flask, redirect, render_template_string, request

app = Flask(__name__)

# -----------------------------
# HARD-CODED SETTINGS (edit me)
# -----------------------------
TENANT_ID = 1                              # <- deine Kundennummer (Tenant)
STUDIO_ID = 1                              # <- optional: konkretes Studio
COURSE_ID = None                           # <- optional: konkreter Kurs
ENTRY_URL = "http://127.0.0.1:5000/"       # <- URL deiner Plattform (local/prod)
RETURN_URL = "https://example.com/danke"   # <- wohin nach der Buchung/Anmeldung
TTL_SECONDS = 600                          # <- Gültigkeit des Links (10 min)
API_SHARED_SECRET = "REPLACE-ME"           # <- MUSS exakt zum Tenant-Secret in deiner DB passen!

# -----------------------------
# Token-Helfer (HS256, base64url)
# -----------------------------
def b64u(data_bytes: bytes) -> str:
    return base64.urlsafe_b64encode(data_bytes).rstrip(b"=").decode("ascii")

def sign_hs256(input_str: str, secret: str) -> str:
    sig = hmac.new(secret.encode("utf-8"), input_str.encode("utf-8"), hashlib.sha256).digest()
    return b64u(sig)

def build_token(
    tenant_id: int,
    studio_id=None,
    course_id=None,
    return_url: str | None = None,
    ttl: int = TTL_SECONDS
) -> str:
    header = {"alg": "HS256", "typ": "JWT", "tenant_id": tenant_id}
    payload = {
        "tenant_id": tenant_id,
        "studio_id": studio_id,
        "course_id": course_id,
        "return_url": return_url or (ENTRY_URL + "dashboard/"),
        "nonce": str(uuid.uuid4()),
        "exp": int(time.time()) + ttl,
    }
    h = b64u(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p = b64u(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    s = sign_hs256(f"{h}.{p}", API_SHARED_SECRET)
    return f"{h}.{p}.{s}"

# -------------
# Routes
# -------------
@app.get("/")
def index():
    # simple page with one button that posts to /book (keine Secrets im HTML!)
    return render_template_string("""
    <!doctype html><meta charset="utf-8">
    <title>Jetzt buchen</title>
    <style>
      body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Inter,Arial,sans-serif;
           display:grid; place-items:center; min-height:100dvh; background:#0f172a; color:#e2e8f0}
      .card{background:#0b1220; border:1px solid #1e293b; border-radius:16px; padding:28px; max-width:520px; width:92%}
      h1{font-size:1.25rem; margin:0 0 8px}
      p{color:#94a3b8; margin:0 0 18px}
      form{margin-top:12px}
      button{background:#22c55e; color:#0b1220; font-weight:700; padding:12px 16px; border:0; border-radius:999px; cursor:pointer}
      button:hover{filter:brightness(1.05)}
      .sub{font-size:.9rem; color:#94a3b8}
      .row{display:flex; gap:12px; flex-wrap:wrap; margin-top:8px}
      .pill{background:#0b1220; border:1px solid #1e293b; border-radius:999px; padding:6px 10px; color:#94a3b8; font-size:.85rem}
    </style>
    <div class="card">
      <h1>Jetzt buchen</h1>
      <p class="sub">Weiter zur Buchungsplattform im sicheren Mandanten-Kontext.</p>
      <div class="row">
        <span class="pill">Tenant: {{tenant}}</span>
        {% if studio is not none %}<span class="pill">Studio: {{studio}}</span>{% endif %}
        {% if course is not none %}<span class="pill">Kurs: {{course}}</span>{% endif %}
      </div>

      <form action="/book" method="post">
        <button type="submit">Weiter zur Plattform →</button>
      </form>
    </div>
    """, tenant=TENANT_ID, studio=STUDIO_ID, course=COURSE_ID)

@app.post("/book")
def book():
    # Baut serverseitig das Token und leitet weiter.
    tok = build_token(
        tenant_id=TENANT_ID,
        studio_id=STUDIO_ID,
        course_id=COURSE_ID,
        return_url=RETURN_URL,
        ttl=TTL_SECONDS,
    )
    target = f"{ENTRY_URL}?st={tok}"
    return redirect(target, code=302)

if __name__ == "__main__":
    # Render.com o.ä. setzt oft PORT; lokal egal.
    port = int(os.getenv("PORT", "3000"))
    app.run(host="0.0.0.0", port=port)
