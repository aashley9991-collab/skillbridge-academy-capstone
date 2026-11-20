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
- Admin panel: <http://localhost:8000/website/admin.html>
- Client pitch: <http://localhost:8000/pitch-and-research/client-pitch.html>

The local admin password is `admin123` for demonstration. Do not expose this development configuration to the public internet.

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

## Regenerate assets

Install the requirements, then run the scripts from the project root:

```powershell
python brand-assets/generate_ads.py
python deliverables/generate_pdf.py
python marketing/generate_reel.py
python pitch-and-research/export_deck_pdf.py
```

The promo reel uses `edge-tts` and `imageio-ffmpeg`; internet access may be required to generate voice audio.
