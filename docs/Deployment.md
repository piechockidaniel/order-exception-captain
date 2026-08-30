# Deployment and recovery guide

This guide prepares an isolated operator demo. It is not authorisation to
connect a store, carrier, payment provider, or customer-messaging system.

## Containerised local deployment

Set a 16+-character operator token through a host secret mechanism, then run
the container template. The port is deliberately bound to loopback; put a
TLS-terminating, identity-aware proxy in front of it before any wider exposure.

```powershell
$env:OEC_OPERATOR_TOKEN = "<secret-held-outside-the-repository>"
docker compose up --build
```

Visit `http://127.0.0.1:8000/`, choose **Unlock operator desk**, and enter the
same token. The container health check verifies the public `/health` endpoint
and SQLite connectivity. It does not expose incident data.

## Activity and failure visibility

The dashboard displays the latest scan status. An authenticated operator can
request `GET /activity` for the most recent 1–50 privacy-safe records: mode,
outcome, aggregate counts, and a generic failure description. Do not treat it
as a replacement for central logs or an alerting service.

## Backup, retention, and rollback

Create a point-in-time SQLite backup without stopping the service:

```powershell
uv run order-exception-captain-backup --database data/order-exception-captain.sqlite3 --output-directory backups
```

The command refuses a missing source or an existing target, uses SQLite's
online backup API, validates `PRAGMA integrity_check`, and only then promotes
the new backup. `backups/` is ignored by Git. Copy verified backups to an
encrypted, access-controlled location; retain daily backups for at least 30
days until an organisation-specific policy is approved.

To roll back, stop the service, preserve the current database under a new
incident-labelled filename, copy a verified backup into the configured database
path, then restart and check `/health`, `/activity`, and one known audit trail.
Do this only with an authorised incident owner: rollback removes newer local
approval and audit records.

## Before any non-synthetic integration

1. Put the service behind HTTPS and SSO or an identity-aware proxy.
2. Confirm backup location, retention owner, restore test cadence, and log
   destination.
3. Select one integration and approve its data fields and side-effect policy.
4. Keep every adapter dry-run by default and retain named human approval.
