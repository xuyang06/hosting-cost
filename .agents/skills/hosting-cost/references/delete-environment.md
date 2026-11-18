# Deleting a Railway environment

Read this only when the user has agreed to delete an environment. Everything in
it is lost on delete: databases, volumes, variables, domains.

## 1. Back up to the user's machine, outside any repo

Dumps hold password hashes and secrets. Use a dated folder, mode 700, e.g.
`~/<project>-backups/railway-<env>-<date>/`.

- **Databases.** List schemas first (`SHOW DATABASES`). Dump through
  `railway ssh` as gzip + base64 so the terminal can't corrupt binary, then
  decode locally and `gzip -t` it:
  `mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers --set-gtid-purged=OFF --databases <schemas> | gzip | base64 -w0`
  (Postgres: `pg_dump -Fc`.)
- **Restore-test it.** Load the dump into a throwaway local container of the
  same image version and compare table counts and a few row counts against the
  live database. A file that decompresses can still fail to restore.
- **Volumes.** `tar -czf - <mount> | base64 -w0` through `railway ssh` on the
  service that mounts it; skip caches and logs. Check the tenant/config files
  you'd need to boot are in it.
- **Variables.** `railway variables --environment ENV --service SVC --json` for
  every service. Railway deletes them with the environment.
- `chmod 600` everything.

## 2. Delete by name, with a guard

Resolve the environment ID from its name, confirm it belongs to the right
project and is not `production`, then call `environmentDelete(id)`.
Afterwards list environments again and check the old URL returns 404 and
production still returns 200.

## 3. Clean up the repo

Grep for the environment name and its URL. Fix anything that would now send a
person or a script to a dead URL. Onboarding checklists and deploy scripts
matter most. Don't default live scripts to production, because some of them
write data.
