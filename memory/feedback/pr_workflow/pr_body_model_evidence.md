# PR Body Model Evidence

Use this for new model, pipeline, backend, or checkpoint adapter PRs.

Separate evidence tiers:

```markdown
### Source parity
- Scheduler / loop:
- Embedding or input order:
- Activation / normalization:
- Token or special-id behavior:
- Attention mask / padding behavior:

### Stub plumbing smoke
- Command:
- Inputs:
- Allowed conclusion: wiring / shapes only

### Real checkpoint validation
- Checkpoint:
- Tokenizer / processor status:
- Strict load:
- Command:
- Allowed conclusion:
```

Rules:

- Stub smoke cannot support real checkpoint, quality, or e2e claims.
- Clean weight load belongs under plumbing evidence, not correctness.
- Missing tokenizer, processor, config, or assets are fail-fast blockers or explicitly pending.
- Source inference must be labeled as inference, not verified parity.
