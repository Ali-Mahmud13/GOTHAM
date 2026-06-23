import json
import re
from langchain_core.messages import HumanMessage
from ..state import AgentState, report_progress
from ..system_prompt import (
    COMPLETENESS_CHECK_PROMPT, SCOPE_CHECK_PROMPT, CLARITY_CHECK_PROMPT,
    COMBINED_CLARITY_CHECK_PROMPT,
)
from app.core.llm import get_llm
import logging
import time
from ..tools.helper.benchmark import record, reset, summary

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _parse_clarity_json(content: str) -> dict | None:
    """
    Parse the combined clarity check JSON response.
    Returns dict with keys: complete, in_scope, clear — or None on failure.
    Handles models that wrap JSON in ```json ... ``` fences.
    """
    # Strip markdown fences if present
    text = re.sub(r"```(?:json)?", "", content).strip()
    # Find the first {...} block
    match = re.search(r"\{[^}]+\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


async def check_clarity_node(state: AgentState) -> AgentState:
    report_progress(1, "Analyzing request")
    # Reset benchmark timings at the start of each new request
    reset()
    _node_start = time.perf_counter()

    llm = get_llm(temperature=0)

    user_message = state["messages"][-1].content
    logger.info(f"Starting clarity check for message: '{user_message}'")

    conversation_history = "\n".join([
        f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
        for msg in state["messages"][:-1]
    ])

    # ── Regex bypass: common assessment patterns are always COMPLETE ──
    assessment_patterns = [
        r'assess.*P\d{3,}',
        r'check.*P\d{3,}',
        r'evaluate.*P\d{3,}',
        r'test.*P\d{3,}',
        r'run.*P\d{3,}',
        r'^P\d{3,}$',
    ]
    for pattern in assessment_patterns:
        if re.search(pattern, user_message, re.IGNORECASE):
            logger.info(f"BYPASS: Message matches assessment pattern '{pattern}' - marking as complete")
            record("Node Total: check_clarity [BYPASS]\n", time.perf_counter() - _node_start)
            state["incomplete"] = "no"
            state["inscope"] = "yes"
            state["clear"] = "yes"
            return state

    # ── Single combined LLM call (replaces 3 sequential calls) ───────
    logger.info("Combined clarity check: sending single LLM call...")
    combined_prompt = COMBINED_CLARITY_CHECK_PROMPT.format(
        conversation_history=conversation_history,
        user_message=user_message,
    )
    _t = time.perf_counter()
    response = await llm.ainvoke([HumanMessage(content=combined_prompt)])
    record("LLM Call: check_clarity (combined 3-in-1)", time.perf_counter() - _t)

    parsed = _parse_clarity_json(response.content)

    if parsed is not None:
        # Successfully parsed — apply all three fields
        is_complete  = bool(parsed.get("complete", True))
        is_in_scope  = bool(parsed.get("in_scope", True))
        is_clear     = bool(parsed.get("clear", True))
        logger.info(f"Parsed combined response: complete={is_complete}, in_scope={is_in_scope}, clear={is_clear}")
    else:
        # JSON parse failed — conservative fallback: let the message through
        logger.warning(
            f"Failed to parse combined clarity JSON: {repr(response.content)!r:.200}. "
            "Defaulting to complete=True, in_scope=True, clear=True."
        )
        is_complete = True
        is_in_scope = True
        is_clear    = True

    state["incomplete"] = "no" if is_complete else "yes"
    state["inscope"]    = "yes" if is_in_scope else "no"
    state["clear"]      = "yes" if is_clear else "no"

    logger.info(
        f"Final clarity state — incomplete: {state['incomplete']}, "
        f"inscope: {state['inscope']}, clear: {state['clear']}"
    )

    record("Node Total: check_clarity", time.perf_counter() - _node_start)

    return state