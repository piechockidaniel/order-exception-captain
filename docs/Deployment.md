# ResolveDesk — Order Exception Captain deployment and recovery guide

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

Docker Compose V2 is preferred. If this computer only has the older standalone
tool, replace `docker compose` with `docker-compose` in the command above.

### Fallback when Docker Buildx is unavailable

If Compose reports that Buildx is missing, either install Docker Buildx or use
this equivalent local-only fallback. It builds the same image and preserves
SQLite data in a named Docker volume:

```powershell
docker build -t order-exception-captain:local .
docker run --rm -p 127.0.0.1:8000:8000 --env OEC_OPERATOR_TOKEN --volume order-exception-captain-data:/app/data order-exception-captain:local
```

This fallback is for the isolated demo only. It does not make the service
public or connect an external system.

## Live VPS demo

The current ResolveDesk — Order Exception Captain synthetic demo is served at
[`https://oec.connect-the-dots.biz`](https://oec.connect-the-dots.biz). It is
an intentionally small native deployment, not an AgentCore deployment:

- a systemd service runs Uvicorn on `127.0.0.1:8010` as the non-login `oec`
  user;
- OpenLiteSpeed proxies that private service and terminates HTTPS;
- the SQLite database and its backups persist in
  `/var/lib/order-exception-captain/`; and
- Certbot renews the dedicated certificate and triggers an OpenLiteSpeed
  graceful reload after renewal.

The corresponding server templates are versioned under
[`deploy/`](../deploy/). The live instance is running release
`3a24f88d51e74a8c49f2c1928a64d5aa0908c4a2`, deployed and verified on
2026-09-03.

### Token origin and handling

The VPS deployment creates `OEC_OPERATOR_TOKEN` and `OEC_ADMIN_TOKEN` once,
only when no token file already exists. Each value is generated on the VPS with
`openssl rand -hex 32` (a 256-bit random value). They are application access
tokens, not AWS, Bedrock, WooCommerce, GitHub, or SSH credentials.

The values are stored in `/etc/order-exception-captain/oec.env`, owned by
`root` with `0600` permissions. systemd reads the file when starting the
service; the dashboard retains a submitted token in page memory only. The
values are deliberately absent from the repository, service unit, logs,
screenshots, demo video, and public Devpost text.

Only the VPS administrator should retrieve them, from a controlled terminal:

```powershell
ssh root@connect-the-dots.biz 'cat /etc/order-exception-captain/oec.env'
```

That command prints sensitive values. Do not paste its output into chat,
source files, commit messages, a screen recording, or a public submission. If
temporary reviewer access is needed, communicate a separately rotated token
through the submission platform's protected testing instructions, then rotate
it after the judging period.

`OEC_OPERATOR_TOKEN` permits the operator desk to read incidents and record
approve/reject/dry-run decisions. `OEC_ADMIN_TOKEN` is separate and is required
to simulate or publish policy changes. Neither token enables a real
WooCommerce scan until server-side Read credentials are separately configured.

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
