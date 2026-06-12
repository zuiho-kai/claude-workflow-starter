# Project Architecture Notes

Use this file as the public template for project-specific architecture facts. Keep secrets, hostnames, private model names, customer names, and local absolute paths out of the committed version.

## Entrypoints

- CLI:
- API/server:
- Batch/offline workflow:
- Tests or smoke commands:

## Ownership Map

| Area | Owner module | Notes |
| --- | --- | --- |
| Request parsing | `<path>` | Normalize external fields here. |
| Scheduling/orchestration | `<path>` | Owns lifecycle and state transitions. |
| Model or core algorithm | `<path>` | Owns semantic decisions. |
| Output formatting | `<path>` | Owns public response schema. |

## Contracts

For every public field, config key, or cross-module bridge, record:

- Ingress:
- Normalization:
- Owner:
- Consumer:
- Failure mode:
- Tests/docs:

## Known Boundaries

- What must stay in the framework layer:
- What must stay in model or algorithm owner code:
- What is project-specific and should not be generalized:

## Local Setup

Put real machine details in gitignored files such as `docs/remote_server.md`, not here.
