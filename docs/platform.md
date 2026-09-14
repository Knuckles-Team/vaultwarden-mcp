# Backing Platform — Vaultwarden

`vaultwarden-mcp` is a **client** of a backing Vaultwarden (or upstream
Bitwarden-compatible) server instance. This page provides a Docker recipe for deploying
one locally as an AgentConfig-selected provider endpoint.

!!! note "Backing-system recipe"
    Each connector in the ecosystem follows the same convention — a
    `docs/platform.md` recipe for the system it integrates with, accompanied by a
    sample Compose stack.

!!! warning "Development recipe only"
    This recipe has no TLS termination and stores data on a bind mount with no backup
    policy. Front it with an authenticated TLS-terminating ingress and a real backup
    schedule before using it for anything beyond local development.

## Single-node deployment (Compose)

```yaml
# docker/platform.compose.yml — local Vaultwarden instance for development
services:
  vaultwarden:
    image: vaultwarden/server:latest
    container_name: vaultwarden
    restart: unless-stopped
    environment:
      - DOMAIN=http://localhost:8080
      # SIGNUPS_ALLOWED=false once the admin account and any needed users exist.
      - SIGNUPS_ALLOWED=true
      - WEBSOCKET_ENABLED=true
      # ADMIN_TOKEN is required for the vaultwarden_admin tool group; generate one
      # with `openssl rand -base64 48` and pass it as a runtime secret reference,
      # never a literal value.
      - ADMIN_TOKEN=${VAULTWARDEN_ADMIN_TOKEN:?set-VAULTWARDEN_ADMIN_TOKEN}
    volumes:
      - vaultwarden-data:/data
    ports:
      - "127.0.0.1:8080:80"

volumes:
  vaultwarden-data:
```

```bash
docker compose -f docker/platform.compose.yml up -d
```

## After it is running

1. Create the first account through the web vault (`http://localhost:8080`), then set
   `SIGNUPS_ALLOWED=false` and restart.
2. Generate a personal API key for that account (web vault → Settings → Security → Keys)
   to obtain the `client_id`/`client_secret` pair for `credential_refs.CLIENT_ID` /
   `CLIENT_SECRET`.
3. Populate `provider_configs.vaultwarden` in `AgentConfig` — `endpoint_ref` pointing at
   this instance, the credential references above, a TLS profile once the ingress is
   TLS-terminated, and `MASTER_PASSWORD` / `ADMIN_TOKEN` references only for the tool
   groups that need them (decrypted vault operations, and `vaultwarden_admin`,
   respectively).
