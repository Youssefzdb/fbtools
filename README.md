# 🔧 FBTools — Facebook Page Manager

> Advanced Facebook Page Management CLI Tool  
> Works on: **Kali Linux | Termux | Ubuntu | Debian**

---

## 📦 Installation

```bash
git clone https://github.com/YOUR_USERNAME/fbtools
cd fbtools
chmod +x install.sh
./install.sh
```

---

## 🚀 Usage

```bash
# Interactive menu
python3 fbtools.py

# Direct login
python3 fbtools.py --login

# Check session status
python3 fbtools.py --status

# Force token refresh
python3 fbtools.py --refresh

# Logout / clear session
python3 fbtools.py --logout
```

---

## 🔑 Authentication Flow

```
Email + Password
       │
       ▼
[1] Facebook Login → Short-lived Token (~1h)
       │
       ▼
[2] Token Exchange → Long-lived Token (~60 days)  ← requires App ID + Secret
       │
       ▼
[3] Page Token → Page Access Token (never expires if refreshed)
       │
       ▼
[4] TokenWatcher → Background thread auto-refreshes before expiry
```

### With App Credentials (Recommended)
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create an App → Get **App ID** and **App Secret**
3. Enter them during login for **60-day tokens** with auto-refresh

### Without App Credentials
- Token valid for ~1 hour
- Will prompt re-login when expired

---

## 📁 File Structure

```
fbtools/
├── fbtools.py              ← Main entry point
├── install.sh              ← Auto-installer
├── requirements.txt
├── README.md
├── core/
│   ├── auth.py             ← Authentication & token management
│   └── token_watcher.py    ← Background token refresh thread
├── config/
│   ├── session.json        ← Saved session (auto-generated)
│   └── cookies.pkl         ← Saved cookies (auto-generated)
└── logs/
    └── fbtools.log         ← Runtime logs
```

---

## ⚠️ Security Notes

- Credentials are stored **locally only** in `config/session.json`
- The `config/` directory is in `.gitignore` — never commit your session!
- Use App credentials for secure long-lived tokens

---

## 🛣️ Roadmap

- [x] Phase 1: Authentication & Token Management
- [ ] Phase 2: Post Management (create, delete, schedule)
- [ ] Phase 3: Comments & Reactions Management
- [ ] Phase 4: Analytics & Insights
- [ ] Phase 5: Messenger / Inbox Management
- [ ] Phase 6: Ads Management

---

## 📜 License

MIT License — Use responsibly.
