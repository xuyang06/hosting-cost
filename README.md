# railway-cost

An agent skill for Claude Code and Codex that finds what a Railway account is
paying for and cuts it safely.

On a quiet app, Railway's bill is mostly idle RAM, not traffic. This skill
measures every service on the account, ranks them by $/month, and walks through
the usual culprits in order of payoff:

- **MySQL near 1 GB with little data.** Railway's MySQL template hardcodes
  `--innodb-buffer-pool-size=1G` in the start command.
- **Duplicate idle environments**, such as a demo or staging copy.
- **Always-on web services** that could use App Sleeping.
- **Floating image tags** that upgrade silently on restart.

It changes one thing at a time, dry-runs by default, and verifies the running
process rather than the API's `true`. Before deleting an environment, it backs
up and restore-tests the data.

## Install

Copy or symlink the skill folder into your agent's skills directory:

```sh
git clone https://github.com/xuyang06/railway-cost
ln -s "$PWD/railway-cost/.agents/skills/railway-cost" ~/.claude/skills/railway-cost   # Claude Code
ln -s "$PWD/railway-cost/.agents/skills/railway-cost" ~/.agents/skills/railway-cost   # Codex
```

Then ask "why is my Railway bill so high?"

## Scripts

Both need `railway login` (or `RAILWAY_API_TOKEN`) and only the Python standard
library.

| Script | What it does |
|---|---|
| `scripts/railway-usage.py` | Read-only. Ranks every service by average and peak memory, vCPU and estimated $/month, showing its start command, image and sleep flag. Accepts `--days`, `--project` and `--json`. |
| `scripts/railway-set.py PROJECT ENV SERVICE` | Changes `--start-command`, `--image` or `--sleep on/off`. Resolves names to IDs, refuses ambiguous names, and only prints the change until you pass `--apply`. |

## License

MIT
