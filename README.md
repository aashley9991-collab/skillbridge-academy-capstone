# SkillBridge Academy Capstone

A locally runnable enrollment and admissions project for SkillBridge Academy. It is built with Python, HTML, CSS, and vanilla JavaScript; the server uses only local RAG answers when Gemini is not configured.

## The six deliverables

1. **Brand identity and creatives** — `brand-assets/` contains the Falcon Academy SVG logo and favicon, brand guidelines, and two social ad images.
2. **Enrollment website and admin panel** — `website/index.html` is the responsive landing page; `website/admin.html` provides the password-protected lead dashboard.
3. **Student lead magnet** — `deliverables/Student-Freelancing-Starter-Kit.pdf`, with its generator at `deliverables/generate_pdf.py`.
4. **Content pipeline and promo reel** — `marketing/` contains the prompt library, import-ready content calendar, reel generator, and rendered vertical MP4.
5. **Admissions chatbot and voice assistant** — integrated into the website and grounded in `data/knowledge_base.json`; voice uses the browser's native Web Speech API.
6. **Automation, research, and client pitch** — `pitch-and-research/` includes the Google Apps Script webhook, cited market brief, interactive pitch deck, and PDF export.

## Run locally

Requires Python 3.10 or later. From the project root:

```powershell
python -m pip install -r requirements.txt
python website/server.py
```

Then open:

- Website: <http://localhost:8000>
- Admin panel: <http://localhost:8000/admin.html> (also available at `/website/admin.html`)
- Client pitch: <http://localhost:8000/pitch-and-research/client-pitch.html>

The local admin password defaults to `admin123` for demonstration. Set `ADMIN_PASSWORD` to a strong, unique value before any hosted deployment. Do not expose the development default to the public internet.

## Gemini API key (optional)

Keep API keys private. The server reads `GEMINI_API_KEY` from the process environment or a `.env` file in the parent folder of this project. Never put the key in browser JavaScript or commit a `.env` file. For a single PowerShell session:

```powershell
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
python website/server.py
```

The chatbot answers from the verified local knowledge base. If Gemini is configured, it may classify an ambiguous question into a vetted answer category; it does not author admissions answers. Local RAG works without Gemini. Set `SKILLBRIDGE_DISABLE_GEMINI=1` to force offline behavior.

## Optional Google Sheets integration

Deploy `pitch-and-research/google-apps-script.js` as a Google Apps Script web app, then set its HTTPS `/exec` URL as `GOOGLE_APPS_SCRIPT_WEBHOOK_URL` in the parent `.env` file or process environment. The local lead record is saved first; webhook failures do not discard it. Enabling this integration sends inquiry details to Google Sheets. Keep the webhook URL private.

The local `/api/leads` endpoint stores inquiries in `data/leads.json`; that file is excluded from Git because it can contain personal information.

## Static hosting (GitHub Pages)

The website detects unavailable API routes and falls back to the verified `data/knowledge_base.json` (with an embedded copy for offline fallback). Chat answers, scholarship flags, inquiries, and Admin Panel status changes then use browser `localStorage`; they are private to that browser and are not sent to SkillBridge or shared across devices. The static demo Admin Panel password is `admin123`, but it is visible in client-side code and is not security. Do not collect real student personal information or use this mode for actual admissions. Use the Python server with a protected deployment and persistent storage for real leads. Voice input depends on browser Web Speech support and microphone permission.

## Regenerate assets

Install the requirements, then run the scripts from the project root:

```powershell
python brand-assets/generate_ads.py
python deliverables/generate_pdf.py
python marketing/generate_reel.py
python pitch-and-research/export_deck_pdf.py
```

The promo reel uses `edge-tts` and `imageio-ffmpeg`; internet access may be required to generate voice audio.

## Deploy on Render

Create a **Web Service** from this repository's `main` branch. Choose Python, then set:

- Build command: `python -m pip install -r requirements.txt`
- Start command: `python website/server.py`
- Plan: Free

In the service's **Environment** settings, set `ADMIN_PASSWORD` to a strong, unique secret before deploying. Optionally add `GEMINI_API_KEY` and `GOOGLE_APPS_SCRIPT_WEBHOOK_URL`; keep these values in Render's environment settings, not in Git. Render supplies `PORT`; the server binds to `0.0.0.0` and uses that port.

The website and routes are served at the domain root: `/`, `/admin.html`, `/deliverables/...`, `/brand-assets/...`, `/pitch-and-research/...`, and `/api/...`. The Admin Panel login uses the configured `ADMIN_PASSWORD`.

Render Free services spin down when idle, and their filesystem is ephemeral. The Admin Panel's local lead file can be lost when the service restarts or redeploys. The optional Sheets webhook can forward new inquiries, but the current dashboard still reads the local file; use a persistent datastore before relying on hosted lead history.
