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

## Redaction Check

Before posting public PR text, scan for:

- drive-letter or home-directory paths;
- SSH hosts, IP addresses, ports, and machine aliases;
- personal account names and private organization names;
- cache roots, snapshot paths, temp directories, and artifact staging paths;
- command output that explains local setup rather than reviewer-relevant behavior.

If a detail is needed for reproducibility, rewrite it as a repo-relative path, public command, public model id, or stable artifact URL.
