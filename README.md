# Sit floor-availability watcher

Checks bolig.sit.no's own GraphQL API every N minutes for a free room on
your floor, and notifies you by phone push (ntfy) and/or email the moment
one opens up. No browser automation needed — it's a plain, lightweight
HTTP request, so it's very cheap to run on a Pi.

## 1. Install (Pi or PC, Linux/macOS/WSL)

```bash
cd sit-watcher
pip install requests --break-system-packages   # drop the flag if not on Debian/Ubuntu
```

That's the only dependency.

## 2. Configure

```bash
cp config.example.py config.py
nano config.py
```

- `UNIT_IDS` is already filled in with your floor (MAL5-501 through
  MAL5-515). Edit if you want to watch a different set.
- **Push notifications (recommended, easiest):** install the free [ntfy app](https://ntfy.sh)
  on your phone, pick any unique topic name (e.g. `sit-floor5-erik-93x2`),
  put it in `NTFY_TOPIC`, and subscribe to that same topic in the app.
  No accounts, no API keys.
- **Email (optional, in addition to or instead of push):** fill in
  `EMAIL_TO`, `SMTP_USER`, `SMTP_PASS`. For Gmail you need an
  ["app password"](https://myaccount.google.com/apppasswords), not your
  normal login password (2-factor auth must be on).

## 3. Test it once

```bash
python3 check_availability.py
```

It'll print each unit's status and either "No newly available rooms" or
a list of ones that just opened up. Run it a second time — it should
again say "No newly available rooms" since nothing changed since the
last run.

To force-test the notification path: open `state.json` after the first
run, change one unit's `"isAvailable"` to `false`, save, and re-run — it
should now fire a notification for that unit.

## 4. Run it automatically (cron)

```bash
crontab -e
```

Add a line to check every 5 minutes (adjust the path):

```
*/5 * * * * cd /home/pi/sit-watcher && /usr/bin/python3 check_availability.py >> log.txt 2>&1
```

Since this just hits a small JSON API (not a full page load), every 5
minutes is very light — feel free to go more frequent if you want, just
don't go overboard out of courtesy to their backend.

## Notes

- `state.json` remembers what it last saw, so you're only notified once
  per newly-opened unit, not on every run. Delete `state.json` to reset
  and re-notify on current state.
- If Sit changes their API (new endpoint, new field names), the script
  will need a small update — but GraphQL APIs like this tend to be more
  stable than scraping HTML/CSS classes.
- `availableFrom` in the response tells you the date a unit becomes
  available, which may be in the future — a unit shows `isAvailable: true`
  once bookable, worth checking that date if you want to be picky about
  move-in timing.
