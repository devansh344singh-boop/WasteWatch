# WasteWatch AI backend

FastAPI + SQLAlchemy backend for the supplied single-file WasteWatch frontend. SQLite is used for local development; `DATABASE_URL` can point to PostgreSQL when deployed.

## Run on Windows

From this `backend` directory in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and set JWT_SECRET to a long random value before using real accounts.
uvicorn app.main:app --reload --port 8001
```

API docs: <http://localhost:8001/docs>. Health check: <http://localhost:8001/health>.

Serve the frontend in a second terminal from its folder with `py -m http.server 8000`, then open <http://localhost:8000>. The frontend defaults to `http://localhost:8001`; set `window.WW_API_BASE` before the inline frontend script to change it. The backend CORS default permits the local static server.

Create a citizen account through the frontend register page. Public registration always creates a citizen. To grant supervisor, collector, or admin access, use a trusted administrative provisioning process; never accept a role from public registration. The quick role buttons on the landing page remain demo-only and do not grant backend privileges.

## API overview

- `GET /health`
- `POST /api/users/register` JSON `{ "name", "email", "password" }`
- `POST /api/users/login` JSON `{ "email", "password" }`
- `GET /api/users/me` with bearer token
- `POST /api/reports` multipart fields `category`, `severity`, `description`, optional `latitude`, `longitude`, `location_text`, and file `image`
- `GET /api/reports?status=review&category=Plastic`
- `GET /api/reports/{report_id}`
- `PATCH /api/reports/{report_id}/status` JSON `{ "status": "verified", "remarks": "..." }`
- `PATCH /api/reports/{report_id}/assign` JSON `{ "collector_email": "..." }` (supervisor/admin; the account must already have collector role)
- `DELETE /api/reports/{report_id}`

Protected calls use `Authorization: Bearer <access_token>`. Citizens see only their own reports; collectors only see tasks assigned to their account email. Review and cleanup status transitions are checked on the server. Images are inspected using Pillow, limited to JPEG/PNG/WebP, 8 MB, and 40 megapixels, saved under `uploads/`, and exposed through `/uploads/{generated_name}`. Passwords use Argon2 hashes. AI fields start as null / `not_configured`, with human review required.

## Frontend boundaries

Real sign-up/sign-in and report submission/listing now use the API. The report form uses Leaflet/OpenStreetMap, lets a user place a pin, and can ask the browser for current coordinates. Browser geolocation requires the user's permission; localhost works for development, while deployed sites need HTTPS. The page's seeded map reports, simulated NGO directory/matching, alerts, audit trail, analytics, appeals, and before/after demo are still browser demo data. Existing browser AI-image-origin screening remains a separate probabilistic review signal; it is not a waste classifier and is not sent as a backend prediction. Collector proof image upload and NGO matching remain demo features.

Leaflet is loaded from the official CDN. The app uses CARTO basemap tiles because the OpenStreetMap Foundation's public tile endpoint blocked this app. Create a CARTO basemap key at <https://carto.com/basemaps/>, then paste it into `map-config.js` as the value of `window.WW_MAP_TILE_KEY`. Restrict the key to your website origin (for local development, `localhost:8000`). Keep the visible OpenStreetMap and CARTO attribution on the map. CARTO's free tier has fair-use limits; use a suitable plan or self-host tiles for production traffic.

## Database and AI

SQLite DB and upload files are local development storage. For PostgreSQL, install a PostgreSQL driver and set `DATABASE_URL` to a `postgresql+psycopg://...` URL. Production also needs managed database migrations, private object storage, HTTPS, a strong secret manager value, rate limiting, backups, and audited role provisioning.

`app/services.py` separates image storage from report routes and defines the no-prediction classifier adapter. Put a TorchScript model path in `WASTE_CLASSIFIER_MODEL`; extend `app/ml/preprocessing.py` and the `WasteClassifier` adapter once the model's input/output contract is settled. Add each future feature (quality, severity, duplicate detection, cleanup verification) as its own service. Do not treat model scores as final decisions.
