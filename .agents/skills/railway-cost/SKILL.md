---
name: railway-cost
description: Find and cut what a Railway account is paying for. Use when the user asks why Railway costs so much, wants a lower or free bill, pastes a Railway receipt or invoice, or asks to optimize, slim down, sleep or delete Railway services or environments. Works on any project on the account.
---

# Railway cost

Railway bills each resident MB and vCPU per minute, across every project on the
account. An idle app pays for what it holds in memory, not for traffic.

## 1. Read the bill, then measure

- On a receipt, compare Memory vs vCPU vs Network. On a quiet app memory is
  usually over 90%; that rules out traffic and CPU as the problem.
- `scripts/railway-usage.py` ranks every service on the account by $/month, with
  the start command, image and sleep flag that usually explain it. Needs
  `railway login`. Add `--days 30` for a month, `--project NAME` for one.
- Check the account total roughly matches the receipt. If it doesn't, something
  unmeasured is billing (another project, an old deployment).
- Never fix from reading code alone. Measure first; the obvious suspect is
  often small (a php-fpm pool looked guilty here and was 100 MB of 2.3 GB).

## 2. Usual culprits, in order of payoff

| Signal | Cause | Fix |
|---|---|---|
| MySQL near 1 GB with little data | Railway's MySQL template puts `--innodb-buffer-pool-size=1G` in the start command | Size the pool to the data: 128M with no users, 256M for a small pilot |
| Same services in two environments | A second environment (demo/staging) running a full idle copy | Delete it, after the backup in `references/delete-environment.md` |
| A web service that only answers requests | Always on, idle | `--sleep on`; it wakes on the next request |
| A worker or scheduler loop | Polls a queue or DB, so it can never sleep | Leave it, or change code (see traps) |
| Floating image tag (`mysql:9`) | Next restart may silently upgrade | Pin the running version, e.g. `mysql:9.7.4` |

Find a database's real size and how much of its cache is used before choosing a
pool size. The `information_schema.tables` data+index total, and
`Innodb_buffer_pool_pages_data` × 16 KB.

## 3. Change one thing at a time

`scripts/railway-set.py PROJECT ENV SERVICE [--start-command ...] [--image ...] [--sleep on|off]`
prints before/after and changes nothing until `--apply`. It resolves names
itself, so never pass raw IDs for production.

- Do a non-production environment first when one exists.
- Pin the image in the same change as a config change, so the restart can't
  also upgrade the server.
- A restart is a brief outage. Say so before touching a service with users.

## 4. Verify, every time

The API returns `true` once a change is accepted, not once it runs, and a
redeploy can replay old settings. Confirm all of:

- The running process has the new flags: `railway ssh` into the service and read
  `/proc/1/cmdline`.
- The server version is unchanged, the container started once (one
  `Starting Container` in `railway logs`), and the app's health URL returns 200.
- The app is writing again *after* the restart time, e.g. a cron table's newest
  timestamp. A 200 page may never touch the database.
- For sleep: the deployment status reaches `SLEEPING` after ~10 quiet minutes,
  and a request wakes it.

## Traps

- **`railway ssh` word-splits a one-line command.** Start `sh -c` with a newline:
  `sh -c 'true` + newline + the real command. Otherwise it fails like an auth error.
- **A `--once` flag on a scheduler loop** usually runs a different task set than
  the loop. Read it before turning a loop into a Railway cron.
- **Sleep needs silence.** Anything that polls (queue workers, schedulers, a DB
  they keep busy) never sleeps; inbound traffic from scanners does wake services.
- **In zsh, `$VAR:x` is a modifier.** Write `${C}:path` in `git show`.

## Deleting an environment

Irreversible: volumes and variables go with it. Get the user's explicit go-ahead,
then follow `references/delete-environment.md`.
