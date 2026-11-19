# SiT Housing Availability Monitor

A small Python bot that monitors SiT housing through the SiT GraphQL API and sends a Discord notification when a room becomes available.

Out of the box it watches every room in **Moholt allmenning** (2, 5, 7, 8 and 11) that has a private bathroom and a kitchen shared by 15 people — 600 rooms.

It is designed to run automatically using **GitHub Actions**, so you do not need to keep your own computer running.

## Features

- Finds rooms by building, housing type and kitchen size, or watches exact room IDs
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
Find matching rooms (SiT CMS: address, type, kitchen size)
  |
  v
Query their availability (SiT GraphQL API)
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

### 3. Configure which rooms to watch

Edit `config.py`. Every room matching **all** of these is watched; set one to `None` to ignore it:

```python
BUILDING_ADDRESS = "Moholt allmenning"  # or "Moholt allmenning 5" for one building
HOUSING_TYPE = "HybelKB"                # dorm with own bathroom in a collective
SHARING_KITCHEN = 15                    # people sharing the kitchen
EXTRA_UNIT_IDS = []                     # exact rooms to add, e.g. ["MAL5-501"]
```

Housing type codes: `HybelKB` (own bathroom, collective), `HybelK` (shared bathroom, collective), `2rompar` (1-bedroom apartment in a collective), `1-roms`, `2-roms`, `3-roms`, ... (apartments).

Room details come from SiT's CMS, so the list updates itself if SiT adds or removes rooms. Rooms that SiT is not offering on the portal right now are skipped until they are listed again.

#### Finding unit IDs

The unit ID is visible in the URL of a room page:

```
https://bolig.sit.no/en/unit/mal5-501/
```

The ID is `MAL5-501` (floor 5, room 01). Add it to `EXTRA_UNIT_IDS`.

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