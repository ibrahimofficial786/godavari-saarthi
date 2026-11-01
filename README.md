# 🪔 GODAVARI SAARTHI

**A context-aware, multilingual pilgrim guidance and journey intelligence platform for Godavari Pushkaralu 2027.**

Problem Statement: **PS-04 – Multilingual Pilgrim Information and Digital Assistance**

Godavari Saarthi turns static pilgrim information into a personalised, verified and continuously updated guide. Pilgrims get a journey plan built around their starting point, destination ghat, language and accessibility needs. When an official announcement affects a saved journey, the app flags it and shows the update.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Personalised journey plans** | Plans based on starting city, destination ghat and needs (wheelchair, elderly, children, low vision) |
| **Announcement-driven updates** | Official announcements automatically flag the saved journeys they affect |
| **Multilingual** | Interface, journey plans and assistant answers in English, తెలుగు and हिन्दी |
| **Verified AI assistant** | Answers only from verified information (FAQs, announcements, facility status). Uses Groq or local Ollama when configured, with keyword fallback |
| **Interactive map** | OpenStreetMap (Leaflet) with ghat markers, facility status, directions and *nearest ghat to me* |
| **Facility discovery** | Water, toilets, medical camps, help desks, cloakrooms with open/closed status |
| **Accounts** | Sign up / sign in, saved journeys synced to the account, guest mode available |
| **Admin dashboard** | Publish announcements, update facility status, read pilgrim help reports |
| **Lost person / help reports** | Pilgrims can report to the control room from the Emergency tab |
| **Accessibility** | Large text, high contrast, read-aloud, accessible-route guidance |
| **Offline support** | Installable PWA with cached app and saved journeys |
| **Live weather** | Current temperature and rain from Open-Meteo |
| **Emergency contacts** | One-tap calling for 112, 108, 100 and 101 |

---

## 🧱 Tech Stack

- **Frontend:** HTML, CSS and vanilla JavaScript, as a Progressive Web App (service worker + manifest)
- **Backend:** Python 3 standard library HTTP server (no packages to install)
- **Database:** SQLite
- **Maps:** OpenStreetMap + Leaflet
- **Weather:** Open-Meteo (no key needed)
- **AI (optional):** Groq API or local Ollama

---

## 🚀 Run Locally

Requirements: **Python 3.9+**. Nothing else to install.

**Windows**
```
python server.py
```
(or double-click `run.bat`)

**Termux / Linux / macOS**
```
sh run.sh
```

Open **http://localhost:8000**. The console also prints an address for other devices on the same Wi-Fi.

---

## 🔑 Configuration

Edit the file `env/.env`:

```
GROQ_API_KEY=your_groq_key_here
ADMIN_EMAIL=you@example.com
```

- `GROQ_API_KEY` is optional. Get a free key at console.groq.com. Without it, the assistant falls back to local Ollama, then to keyword answers.
- `ADMIN_EMAIL`: the account that signs up with this email becomes the administrator. **Set it to your own email before the first run.**
- Optional: `GROQ_MODEL`, `OLLAMA_MODEL`, `PORT`, `SECRET_KEY`.

The server blocks browsers from opening the `env` folder, and `.gitignore` keeps it out of Git. Never commit real keys.

### Becoming admin
1. Click **Get started** and sign up with the `ADMIN_EMAIL` address.
2. The **Admin** tab then lets you publish announcements, change facility status and read help reports.

---

## 🗂️ Project Structure

```
godavari-saarthi/
├── server.py          # Backend: auth, API, SQLite, AI assistant, static server
├── static/
│   ├── index.html     # Landing, auth and the full pilgrim app
│   ├── sw.js          # Service worker (offline support)
│   └── manifest.json  # PWA manifest
├── env/.env           # Local keys (not committed)
├── run.bat / run.sh   # Start scripts
└── README.md
```

---

## 🔌 API Overview

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/signup`, `/api/signin` | Public | Create account, sign in |
| GET | `/api/me` | User | Current user |
| GET / PUT | `/api/journeys` | User | Saved journeys |
| GET | `/api/state` | Public | Announcements and facility status |
| PUT | `/api/admin/state` | Admin | Publish announcements, update facilities |
| POST | `/api/report` | Public | Lost person / help report |
| GET | `/api/admin/reports` | Admin | Read reports |
| POST | `/api/ask` | Public | AI assistant |

---

## 🔒 Security Notes

- Passwords are stored as salted PBKDF2 hashes.
- Signed session tokens; repeated failed sign-ins are rate limited.
- Admin endpoints require the admin role.
- Before a public deployment: use **HTTPS**, set your own `ADMIN_EMAIL`, and add password reset and email verification.

---

## ⚠️ Current Limitations

- Ghats, facilities, announcements, schedule and crowd forecast are **sample data** and must be replaced with official data.
- Ghat map coordinates are approximate and need verification.
- Telugu and Hindi text should be reviewed by native speakers.
- The free OpenStreetMap tile server is for light use only. Use a tile provider for large events.
- Phone location (nearest ghat) requires HTTPS or localhost.

---

## 🛣️ Roadmap

- Real facility locations via the OpenStreetMap Overpass API
- Road routing with OpenRouteService
- Password reset, email verification and SMS alerts
- Push notifications for announcements
- Real-time crowd density from official sources
- More languages

---

*Map data © OpenStreetMap contributors.*
