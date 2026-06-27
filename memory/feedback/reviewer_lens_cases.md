# Reviewer Lens Cases

Keep examples mechanism-first:

- A generic code check can miss duplicated algorithms, wrong owner placement, non-contiguous ids, and unnecessary knobs.
- A module-owner review can miss project-owner concerns such as public API, test placement, PR body freshness, and endpoint bad paths.
- Finding closure can be mistaken for full diff review; full review needs diff census, semantic trace, and garbage pass.
- Streaming happy paths can pass while structured errors, engine failures, and delta semantics are broken.
