from replicate_ai.prompts import AUDITOR_PROMPT
from replicate_ai.tools.date_tool import get_current_date

auditor_subagent = {
    "name": "statistical_auditor",
    "description": (
        "Compare the agent's estimated coefficients against the paper's "
        "published table. Write a verdict to /workspace/replication_audit.md."
    ),
    "system_prompt": AUDITOR_PROMPT,
    # Filesystem tools (read_file, edit_file, ls, …) are injected by
    # FilesystemMiddleware in create_deep_agent — do not pass tool name strings.
    "tools": [get_current_date],
}