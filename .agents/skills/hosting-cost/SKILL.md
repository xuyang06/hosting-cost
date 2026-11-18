---
name: hosting-cost
description: Investigate and cut what an app's hosting costs. Use when the user asks why a hosting or cloud bill is high, wants a cheaper or free way to host, asks to compare hosting options (Railway, Fly.io, Render, a VPS, Oracle or other free tiers, managed databases), pastes a receipt or invoice, or asks to optimize, slim down, sleep, migrate or delete services or environments.
---

# Hosting cost

First measure what the app actually runs. Then compare the options that can run
that, and optimize on the one chosen. On a quiet app, the bill usually pays for
idle memory, not traffic.

## 1. Measure what runs today

- **Read the bill by line.** Compare memory, CPU, disk, network and the plan
  fee. When memory is most of it, traffic is not the problem.
- **List every process.** For each web server, worker, scheduler or cron job,
  database and cache, record its resident RAM, whether it must run all the
  time, whether it polls, and whether it needs a disk. This list is the app's
  *shape*.
- **Measure, don't read it from config.** Use the platform's metrics, `docker
  stats` or `ps`. On Railway, run `scripts/railway-usage.py`; read
  `references/railway.md` first.
- **Match the total to the receipt.** If it doesn't match, something else is
  on the same account: another project, an old environment, a forgotten
  database.
- Say how many users there are. With zero, the target is the minimum that
  keeps everything alive.

## 2. Fix the config before changing platform

Moving a misconfigured app moves the waste with it. Apply step 4's levers where
the app runs now, re-measure, and only then price alternatives against the
smaller footprint. A 1 GB database cache on 250 MB of data costs more than any
platform difference.

## 3. Compare solutions

- **Fetch current pricing** from each provider's official pricing page and
  date it. Prices and free tiers changed several times in 2025–26, so never
  quote them from memory. Cite the pages.
- **Fit first, price second.** Rule out any option that can't run the shape: a
  database that expires, a free tier with no background workers, sleeping that
  breaks a scheduler, no MySQL. `references/platform-traps.md` lists the known
  traps. Read it before recommending a free tier.
- **Price the measured footprint**, not a plan's sticker price:
  - usage-billed platforms: RAM GB × price per GB-month + CPU + disk
  - VPS: the smallest plan whose RAM fits the total with headroom
- **Count the whole cost.**
  - **Migration hours:** data dump and restore-test, secrets, DNS, cutover, and
    keeping the old setup until the new one is proven.
  - **Ongoing ops on a VPS:** OS updates, backups, TLS and monitoring.
  - **Single-machine risk:** one box going down takes every app on it down.
- **Present** a table of options with $/month, fit and the catch. Give one
  recommendation and the crossover point where it would change, e.g. "stay
  until the bill passes $X, then move to a $5 VPS".

## 4. Optimize on the chosen platform

| Signal | Lever |
|---|---|
| Database RAM far above its data size | Size the cache to the data: MySQL `innodb_buffer_pool_size`, Postgres `shared_buffers`. Check the template's start command, not just the config file. |
| A second environment (demo, staging) idling | Delete it after a tested backup, or sleep it |
| A web service that only answers requests | Turn on sleep or scale-to-zero, if no process inside it polls |
| A worker or scheduler loop | It can't sleep. Merge small loops into one process, or switch to platform cron only if that runs the same tasks |
| Too many app server workers | Fewer workers for the real traffic. Each one holds its own RAM |
| Several projects each paying a floor | Combine them on one plan or one VPS |
| A floating image tag (`mysql:9`) | Pin the running version before any restart |

- Change one thing at a time, on a non-production environment first if one
  exists. A restart is a brief outage, so say so before touching anything
  users rely on.
- **Verify the change runs, not just that the API accepted it.** Check:
  - the live process's flags
  - the server version is unchanged
  - health returns 200
  - the app is writing again after the restart, e.g. a cron table's newest
    timestamp. A 200 page may never touch the database.

## Safety

- Get explicit agreement before deleting anything or touching production.
  Before a deletion, follow `references/delete-environment.md`: back up, run a
  restore test, then delete by name.
- Keep dumps and env exports outside any repo, mode 600. They hold password
  hashes and secrets.
- A `--once` or "single run" flag on a scheduler often runs a different task
  set than the loop. Read it before converting a loop to cron.
