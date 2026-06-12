# Remote Basics

## Reconnaissance First

Before changing code for a remote-only failure, collect:

- hostname and working directory
- branch and commit
- Python/venv path
- package versions that own the failing path
- model or data cache roots
- whether an existing runbook/script already works

Do not assume two machines share path layout because they share an IP range, cloud provider, or scheduler.

## Command Shape

PowerShell -> SSH -> shell -> container quoting is fragile. Prefer writing a script, uploading it, then checking:

```bash
wc -c script.sh
sed -n '1,40p' script.sh
bash -n script.sh
```

## Reduce Probes

On shared machines, avoid repeated one-off SSH commands. Keep a control session and write status to files when a run is long.

## Debugging vs Deployment

Use direct remote scripts for exploratory debugging. Commit/push/pull only when the local change is ready to validate as a real branch state.
