# NOVA Movie Hub

Telegram Mini App for **NOVA Guardian** — movie discovery, AI assistant, and a **separate reward/unlock module** for eligible bot file operations.

Built from the *NOVA Guardian Mini App Complete Blueprint*.

**Product tagline:** Discover. Explore. Ask AI. — NOVA Movie Hub, powered by NOVA Guardian.

---

## What this package is

| Area | Status in this scaffold |
|------|-------------------------|
| Frontend shell (AMOLED / violet) | ✅ Home, Discover, AI, Saved, Profile |
| Telegram WebApp init + expand | ✅ |
| Auth (`POST /auth/telegram`) | ✅ HMAC validate initData |
| Catalog (TMDB) | ✅ when `TMDB_API_KEY` set |
| AI discover (catalog-grounded) | ✅ Phase-1 (search grounding) |
| Watchlist | ✅ In-memory staging |
| **Operation / reward sessions** | ✅ Create → verify → deliver |
| AdsGram Reward client | ✅ SDK load + poll server status |
| Bot helpers | ✅ `bot_integration/miniapp_entry.py` |
| Full LLM AI / Mongo prod store | Phase later |

Movie **search and browsing do not require ads**. Reward UI only opens when the bot passes a session (`start_param=op_<id>`).

---

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env  # fill BOT_TOKEN, TMDB_API_KEY, secrets
uvicorn main:app --host 0.0.0.0 --port 8081
```

Health: `GET http://localhost:8081/health`

Frontend is served from the same process when `SERVE_FRONTEND=1`.

### 2. BotFather

1. `/newapp` (or `/myapps`) → attach to your bot  
2. **Web App URL** = your HTTPS origin (e.g. `https://hub.example.com/`)  
3. Direct link / startapp enabled  

### 3. AdsGram (reward only)

1. Publisher account → platform **Telegram Mini-app**  
2. Create **Reward** block → copy **Block ID**  
3. Set `ADSGRAM_BLOCK_ID` in `frontend/scripts/config.js` and optionally in `.env`  
4. Prefer **Reward URL** pointing to:

```text
https://your-api/operations/{SESSION_ID}/mark_verified?userid=[userId]
```

(Server marks verified; client never counts as proof alone.)

### 4. Wire the existing bot

Use helpers in `backend/bot_integration/miniapp_entry.py`:

1. For non-premium file request → `create_unlock_session(user_id, file_id)`  
2. Reply with `unlock_keyboard(session)` (WebApp button)  
3. After user returns / you poll `is_session_verified` → `send_indexed_file` → `mark_delivered`

Do **not** rewrite the whole filter bot — only gate eligible deliveries.

---

## API (summary)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health |
| POST | `/auth/telegram` | Validate initData → token |
| GET | `/catalog/trending` | Trending |
| GET | `/catalog/search?q=` | Search |
| GET | `/catalog/{id}` | Details |
| POST | `/ai/discover` | Grounded discovery |
| GET/POST/DELETE | `/watchlist` | Watchlist |
| POST | `/operations` | Bot creates unlock session |
| GET | `/operations/{id}` | Status (Mini App poll) |
| POST | `/operations/{id}/mark_verified` | Provider / bot verification |
| POST | `/operations/{id}/mark_delivered` | After bot sent file |

---

## Security rules (from blueprint)

- Validate Telegram `initData` on the server  
- Short-lived operation sessions + ownership checks  
- **Never** trust client “I watched the ad” as sole proof  
- Idempotent verify / deliver  
- No bot tokens or provider secrets in frontend  
- HTTPS only in production  

---

## Roadmap alignment

This scaffold covers **Phases 1–2** UI, **Phase 3** catalog wiring, **Phase 7** auth entry, **Phase 8** operation/reward module skeleton.

Next increments: JWT sessions, Mongo operation store, richer AI parsing, detail page UI, i18n (EN/TA/HI).

---

## License / branding

Original NOVA design. Do not copy Reelipse code, logos, or assets. Catalog images/metadata subject to TMDB (or your provider) terms.
