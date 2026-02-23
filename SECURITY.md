# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately via [GitHub Security Advisories](https://github.com/karbassi/mcp-ticktick/security/advisories/new).

Do not open a public issue for security vulnerabilities.

## Credential Safety

This project requires TickTick API credentials. Never commit credentials to version control:

- `TICKTICK_ACCESS_TOKEN` — OAuth access token
- `TICKTICK_CLIENT_SECRET` — OAuth client secret
- `TICKTICK_V2_SESSION_TOKEN` — Browser session cookie

Use environment variables or a secrets manager to provide these values.
