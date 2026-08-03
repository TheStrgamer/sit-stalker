# SiT Housing Availability Monitor

A small Python bot that monitors specific SiT housing units through the SiT GraphQL API and sends a Discord notification when a room becomes available.

It is designed to run automatically using **GitHub Actions**, so you do not need to keep your own computer running.

## Features

- Checks specific SiT housing units
- Uses the SiT GraphQL API (no browser automation required)
- Detects when unavailable rooms become available
- Sends notifications through Discord webhooks
- Stores previous availability state to avoid duplicate notifications
- Runs automatically on a schedule with GitHub Actions

---

## How it works

The workflow is:

```
GitHub Actions
  |
  v
Run Python checker periodically
  |
  v
Query SiT GraphQL API
  |
  v
Compare with previous state
  |
  v
Room becomes available?
  |
  v
Send Discord notification
```

---

## Setup

### 1. Fork or clone the repository

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

### 2. Install dependencies locally (optional)

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

**Linux/macOS:**

```bash
source .venv/bin/activate
```

**Windows:**

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Configuration

### 3. Configure housing units

Edit `config.py`:

```python
UNIT_IDS = [
    "12345",
    "67890",
]
```

Add the SiT rental object IDs you want to monitor. The script checks only these units.

#### Finding unit IDs

Open a SiT housing page, e.g. `https://bolig.sit.no/`.

The unit ID is visible in the URL:

```
https://bolig.sit.no/en/unit/abc123/
```

The ID is `abc123`. Add it to `UNIT_IDS`.

---

## Discord Notifications

### 4. Create a Discord webhook

In Discord:

1. Open your server settings
2. Go to **Integrations**
3. Select **Webhooks**
4. Create a new webhook
5. Copy the webhook URL

It will look like:

```
https://discord.com/api/webhooks/...
```

### 5. Add the webhook to GitHub Secrets

Do not put the webhook URL directly in the code.

In your GitHub repository, go to:

```
Settings → Secrets and variables → Actions → New repository secret
```

Create:

- **Name:** `DISCORD_WEBHOOK_URL`
- **Value:** your Discord webhook URL

The GitHub workflow automatically provides this value when running the script.

---

## GitHub Actions Setup

The repository contains:

```
.github/
└── workflows/
    └── check.yml
```

This runs the checker automatically.

Example schedule:

```yaml
schedule:
  - cron: "*/15 * * * *"
```

This checks every 15 minutes. You can change the interval using GitHub cron syntax.

Examples:

**Every hour:**

```yaml
cron: "0 * * * *"
```

**Every 30 minutes:**

```yaml
cron: "*/30 * * * *"
```

### Running manually

You can also run it manually:

```
Repository → Actions → Check SiT availability → Run workflow
```

Useful for testing.

---

## Files

```
.
├── check_availability.py     # Main checker
├── config.py                 # Your housing configuration
├── state.json                # Previous availability state
├── requirements.txt          # Python dependencies
└── .github/
    └── workflows/
        └── check.yml          # GitHub Actions schedule
```

---

## Local testing

Set your Discord webhook locally:

**Linux/macOS:**

```bash
export DISCORD_WEBHOOK_URL="your webhook"
python check_availability.py
```

**Windows PowerShell:**

```powershell
$env:DISCORD_WEBHOOK_URL="your webhook"
python check_availability.py
```