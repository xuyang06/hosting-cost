# Platform traps

These are structural catches that rule an option out whatever it costs. Last
checked 2026-11. Re-check each one on the provider's official page before
relying on it, because they change.

| Platform | Catch |
|---|---|
| Oracle Cloud Always Free | Idle instances get reclaimed, possibly without notice: 95th-percentile CPU under ~20% over 7 days, which is exactly what a quiet app looks like. 2026 reports say the free ARM allowance was cut. Capacity is often unavailable. Don't use it for anything a customer depends on. |
| Render free | Web services sleep after 15 idle minutes and take about a minute to wake. Free Postgres is deleted after 30 days. No MySQL. Background workers and cron are paid. |
| Fly.io | No free tier. Stopped machines still bill their volumes, so scale-to-zero doesn't zero out an app with a database. RAM price rose 2026-10-01. |
| Railway | Billing is account-wide: every project shares one bill. Templates can hardcode big caches (see `railway.md`). |
| Free managed databases (Neon, Aiven, etc.) | They host the database only, not the app servers. Small disk caps (~1 GB). Some cap compute hours. |
| Koyeb and other free PaaS tiers | Free-tier terms have changed often. Confirm on the official page that today's free tier exists and covers workers. |
| Any single VPS | Cheapest per GB, but you own OS updates, backups, TLS and monitoring, and one box down means every app on it is down. Some budget providers don't list every region for their cheapest plan. |

A cheap VPS (4 GB for about $5) beats per-GB billing once a usage-billed app
holds about 1–2 GB all the time. Below that, the managed platform usually
costs less in total once your time is counted.
