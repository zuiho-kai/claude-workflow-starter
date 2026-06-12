# Serving Fail-Fast And Cleanup

## Startup Gates

Before a long serving or benchmark run:

- verify nontrivial CLI flags with `--help`
- check model/data paths exist
- set offline/cache environment variables intentionally
- start with logs redirected to a known file
- monitor health endpoint, PID, and first error signatures

Do not start a sweep before one minimal request completes.

## Failure Ownership

Separate:

- code bug
- dependency or ABI mismatch
- missing model/data artifact
- scheduler/resource issue
- stale venv or editable install

Report the owner clearly. Do not call an environment blocker a model regression.

## Cleanup

At the end of a run:

- kill this run's process group or explicit project process pattern
- exit nested container/scheduler shells
- verify scheduler state
- verify GPU memory is back to idle

Do not rely on "the command ended" as cleanup proof.
