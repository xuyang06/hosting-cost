# Railway

Read when the app runs on Railway or Railway is being priced.

**Billing.** Railway bills resident RAM and vCPU per minute, across every
project on the account. The Hobby plan's fee includes an equal amount of usage,
so a small app pays the fee and nothing more.

## Measure

`scripts/railway-usage.py` ranks every service on the account by $/month. For
each service it shows the start command, image and sleep flag, which usually
explain a high number. Run `railway login` first.

- `--days 30` measures a month.
- `--project NAME` limits it to one project.
- `--mem-price` / `--cpu-price` set the prices so the estimate matches a
  receipt.

## Change

`scripts/railway-set.py PROJECT ENV SERVICE [--start-command ...] [--image ...] [--sleep on|off]`
resolves names itself and refuses ambiguous ones. It prints the before and
after and changes nothing until `--apply`. Never pass raw IDs for production.

## Known causes

- **The MySQL template's start command** hardcodes
  `--innodb-buffer-pool-size=1G`, so MySQL grows to about 1 GB however small
  the data is. Size it to the data:
  - 128M with no users, 256M for a small pilot
  - data size: the `information_schema.tables` data+index total
  - pages actually cached: `Innodb_buffer_pool_pages_data` × 16 KB

  Pin the image (e.g. `mysql:9.7.4`) in the same change.
- **App Sleeping** only works for services nothing polls. Inbound traffic,
  scanners included, wakes them. The deployment shows `SLEEPING` after about
  10 quiet minutes.

## Verify

- **Read the running flags**, not the mutation's `true`: `railway ssh` into the
  service, then read `/proc/1/cmdline`. A redeploy can replay old settings.
- **Check the restart in `railway logs`:** exactly one `Starting Container`
  line, and the same server version as before.

## Traps

- **API returns 403:** the GraphQL API
  (`https://backboard.railway.com/graphql/v2`) returns 403 without a
  `User-Agent` header. That is Cloudflare, not a permissions problem.
- **`railway ssh` fails like an auth error:** it word-splits a one-line
  command. Start `sh -c` with a newline: `sh -c 'true` + newline + the real
  command.
- **zsh eats `:x` after a variable:** in zsh, `$VAR:x` is a modifier. Write
  `${VAR}:path`.
