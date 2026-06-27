# PR Body Privacy

Public PR text should contain reviewer-facing reproducible evidence, not local or remote work logs.

## Allowed

- public command or repo-relative script;
- public model id, version, or dependency version;
- PR head or run checkout when provenance needs it;
- workload and result table;
- stable artifact URL.

## Forbidden

- local absolute paths;
- remote hostnames, usernames, ports, machine aliases, or account names;
- venv, cache, model-cache, scratch, or temp paths;
- credential details;
- local dependency blockers;
- internal probes and failed private attempts.

If only an internal probe ran, do not present it as Test Result. Say validation is pending or run the real public/reviewer-relevant path.
