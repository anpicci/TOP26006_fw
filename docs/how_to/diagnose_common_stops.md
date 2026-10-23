# Diagnose common stops

**Problem:** a task cannot proceed under its declared gate.

Record the failed command or precondition and preserve direct evidence. Classify the cause: missing runtime capability or permission; relevant dirty state; governance hash or branch drift; unavailable network or authentication when network was authorized; missing or inconsistent evidence; or a substantive new decision boundary. Check the exact source of each requirement in [AGENTS.md](../../AGENTS.md) and [CPC.md](../../CPC.md).

Do not relabel an unexpected state as success or automatically retry after reset, clean, or stash. Complete the report for finished stages, mark later stages not started, and identify the owner decision or external change needed. [Tutorial 8](../tutorials/08_recover_from_a_stopped_task.md) shows an observed dirty-state stop.
