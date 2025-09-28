from google.adk.tools.tool_context import ToolContext

# --------------------------------------------------------------------------
## Loop Control Tool
# --------------------------------------------------------------------------

def exit_loop(tool_context: ToolContext):
    """
    Stops the current agent workflow or loop.

    This tool should be called by an agent when it determines that its task
    is complete and the process should be finalized (e.g., when a report
    is approved). It signals the system to escalate and stop further iterations.
    """
    print(
        f"The workflow has met the criteria for completion."
    )
    # The 'escalate' action tells the agent runtime to stop the current loop.
    tool_context.actions.escalate = True

    # Tools should always return a dictionary.
    return {}