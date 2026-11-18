# hosting-cost

An agent skill for Claude Code and Codex. It finds out what an app's hosting
really costs, compares the options that could run the app, and cuts the bill
on whichever one you choose.

1. **Measure** what runs today, process by process: RAM, whether it must
   always run, whether it polls, whether it needs a disk. On a quiet app the
   bill is mostly idle memory, not traffic.
2. **Fix the config first.** Moving a misconfigured app moves the waste with
   it. A database cache sized at 1 GB for 250 MB of data costs more than any
   platform difference.
3. **Compare solutions** using current official pricing, fetched and dated,
   never quoted from memory. It rules out options that can't run the app,
   prices the measured footprint, and counts migration and ops time. The
   result is one recommendation and the point at which it would change.
4. **Optimize** on the chosen platform one change at a time, then verify the
   running process, not the API's `true`.

It includes known platform traps (`references/platform-traps.md`), such as
idle reclamation on Oracle's free tier, Render's expiring free Postgres and
Fly volumes billing while machines are stopped. Railway has a full playbook
and scripts.

## Install

```sh
git clone https://github.com/xuyang06/hosting-cost
ln -s "$PWD/hosting-cost/.agents/skills/hosting-cost" ~/.claude/skills/hosting-cost   # Claude Code
ln -s "$PWD/hosting-cost/.agents/skills/hosting-cost" ~/.agents/skills/hosting-cost   # Codex
```

Then ask "why is my hosting bill so high?" or "is there a cheaper way to host
this?"

## Railway scripts

Both need `railway login` (or `RAILWAY_API_TOKEN`) and only the Python standard
library.

| Script | What it does |
|---|---|
| `scripts/railway-usage.py` | Read-only. Ranks every service by average and peak memory, vCPU and estimated $/month, showing its start command, image and sleep flag. Accepts `--days`, `--project` and `--json`. |
| `scripts/railway-set.py PROJECT ENV SERVICE` | Changes `--start-command`, `--image` or `--sleep on/off`. Resolves names to IDs, refuses ambiguous names, and only prints the change until you pass `--apply`. |

## License

MIT
