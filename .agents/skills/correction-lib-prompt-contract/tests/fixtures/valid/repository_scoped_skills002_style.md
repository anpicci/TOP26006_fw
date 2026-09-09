# Mechanical-lint example

```text
prompt_id: repository_scoped_example
stage_id: prepare
commit_expected: yes
do_not_commit: no
future_repository_contract: supplied_by_live_authority
```

This inert fixture demonstrates that a new supplied field is retained and does
not fail merely because the helper does not recognize it.

```yaml
stage_id: inspect
unknown_future_field: local_stage_value
```

The repeated local-field contract is block-scoped; this second block remains
separately inspectable.
