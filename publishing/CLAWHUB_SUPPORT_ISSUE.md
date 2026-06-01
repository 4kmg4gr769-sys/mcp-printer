Title: GitHub account lookup fails after GitHub username rename during package publish

## Summary

Publishing an OpenClaw code plugin fails with `GitHub account lookup failed` after my GitHub username was renamed.

## Current GitHub / ClawHub identity state

- GitHub API current login: `SteveVillari`
- GitHub org that owns the source repo: `Villocity-Labs`
- ClawHub CLI `whoami`: `4kmg4gr769-sys`
- ClawHub publisher created successfully: `villocity-labs`

I have logged out of the ClawHub CLI and completed a fresh device login, but ClawHub still returns the old GitHub username.

## Source repo

https://github.com/Villocity-Labs/mcp-printer

The repo is public and the package source path is:

```text
openclaw-plugin
```

## Dry run succeeds

```sh
clawhub package publish openclaw-plugin \
  --owner villocity-labs \
  --source-repo Villocity-Labs/mcp-printer \
  --source-ref main \
  --source-commit 3dd66063a793ddc1f326c787f461a4896df9942c \
  --source-path openclaw-plugin \
  --dry-run \
  --json
```

Dry-run output:

```json
{
  "source": "github:Villocity-Labs/mcp-printer@main:openclaw-plugin",
  "name": "openclaw-plugin-openclaw-mcp-printer",
  "displayName": "MCP Printer",
  "family": "code-plugin",
  "version": "0.1.0",
  "commit": "3dd66063a793ddc1f326c787f461a4896df9942c",
  "files": 5,
  "totalBytes": 3783
}
```

## Real publish fails

```sh
clawhub package publish openclaw-plugin \
  --owner villocity-labs \
  --source-repo Villocity-Labs/mcp-printer \
  --source-ref main \
  --source-commit 3dd66063a793ddc1f326c787f461a4896df9942c \
  --source-path openclaw-plugin \
  --changelog "Initial public release of the Villocity Labs MCP Printer OpenClaw plugin." \
  --clawscan-note "This plugin connects OpenClaw to a local MCP printer server. The server can send jobs to configured OctoPrint or Moonraker printers using user-provided local/network printer endpoints and credentials." \
  --json
```

Error:

```text
Error: GitHub account lookup failed
    at requireGitHubAccountAge (../../convex/lib/githubAccount.ts:64:80)
    at async publishPackageImpl (../convex/packages.ts:5138:62)
    at async handler (../convex/packages.ts:5476:6)
```

## Expected behavior

After fresh GitHub OAuth/device login, ClawHub should resolve the current GitHub identity (`SteveVillari`) and allow publishing to the `villocity-labs` publisher, or provide a self-service way to refresh the linked GitHub username.

## Question

Can the ClawHub account profile / GitHub identity cache be refreshed or relinked for this account?
