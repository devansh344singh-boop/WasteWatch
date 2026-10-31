# WasteWatch AI — AI Image Screening Prototype

A single-file, no-build civic-tech frontend. Citizens can report waste; supervisors review evidence and assign cleanup partners; collectors submit cleanup proof; administrators view demo analytics.

## Run the demo frontend

1. Install Python 3 if it is not already installed.
2. Open a terminal in this folder.
3. Run:

   ```bash
   python -m http.server 8000
   ```

4. Visit http://localhost:8000 in your browser.
5. On the home page, use a quick demo role to explore the sample dashboards.

## Run with the backend

See [`backend/README.md`](backend/README.md) for Windows setup and API details. The backend serves on port 8001; the frontend static server serves on port 8000. On the sign-in page, create a citizen account to submit and track database-backed reports. The report form uses Leaflet and browser geolocation; allow location access or click the map to set the point. The home page quick-role buttons intentionally remain demo-only.

## Deploy the frontend to GitHub Pages

GitHub Pages hosts static files only. The `backend/` FastAPI service must run on a separate host for real sign-in, report uploads, and saved reports. The Pages workflow publishes only `index.html` and `map-config.js`; `.gitignore` excludes the local backend environment, SQLite database, and uploads.

After hosting the backend, set `window.WW_API_BASE` in `map-config.js` to its HTTPS URL and configure backend `CORS_ORIGINS` to include your Pages origin (for a project site, such as `https://YOUR-USER.github.io`). The same config file holds the CARTO basemap key; restrict this browser-visible key to your Pages website origin. If the API URL remains empty on Pages, demo role buttons still work, while real account actions show a message that the backend URL is not configured.

In GitHub, open **Settings → Pages** and choose **GitHub Actions** as the deployment source. Push the project to the repository's `main` branch; `.github/workflows/deploy-pages.yml` publishes the frontend on each push. GitHub Pages is a public website, so verify the repository and frontend files are safe to expose before publishing.

Use a modern browser and an internet connection for the first AI model download.

## AI image-authenticity check

At the photo-report step, the browser dynamically loads Transformers.js and the `onnx-community/ai-image-detection-ONNX` image-classification model from Hugging Face. The model runs in the browser using WASM; no Hugging Face API token or custom backend is required. The UI reports a model estimate of AI-generated likelihood, flags uncertain/high-likelihood results for supervisor review, and continues to require human review.

The first run may take a while because the JavaScript library and model weights must download. If the model cannot load (network issue, unsupported browser, or memory limits), the report is still possible but is marked for human review. The uploaded photo is processed in the browser by this implementation rather than sent to a detector API.

### Important limitations

- AI-image detection is probabilistic. A model score is not proof that a photo is genuine or synthetic, and it can make false positives and false negatives.
- This detector is fine-tuned using the CIFAKE dataset; performance on real-world phone photos and newer image generators may differ from its training data. Treat its result as a review signal only.
- The detector estimates image origin only. It does not prove the photo was taken at the reported location or time, and it does not confirm that waste is present.
- The backend stores submitted reports and enforces citizen, supervisor, collector, and administrator permissions. Sample map points, NGO records, alerts, and analytics remain demo data stored in browser localStorage.
- Browser geolocation requires permission and a secure context (localhost is allowed during development). Reports store coordinates only when supplied.

## Other checks

- Image dimensions and duplicate proximity checks are rule-based, not AI.
- NGO matching uses demo records and a weighted score in the page.
- A supervisor should review flagged reports and can override the automated recommendation.

## Deploying

This static frontend can be hosted on any static web host. The AI library and model require network access to their CDN/model files. For production, pin and audit dependencies, add server-side authentication and role authorization, retain review/audit records, and evaluate the detector on a representative dataset of real waste photos and synthetic examples before relying on it operationally.
