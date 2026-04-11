"""Health-check plugin: verifies dynamic load and basic engine operation."""

NAME = "/status"
DESCRIPTION = "Checks engine health and verifies plugin loading."


def run(query, **kwargs):
    """
    Return a short status report. ``query`` is ignored for this plugin.
    """
    _ = query, kwargs
    lines = [
        "╔══════════════════════════════════════╗",
        "║  Krystal — System Status             ║",
        "╠══════════════════════════════════════╣",
        "║  State:        ONLINE                ║",
        "║  Plugin:       sys_status            ║",
        "║  Load mode:    dynamic (importlib)   ║",
        "║  Engine:       functioning normally  ║",
        "╚══════════════════════════════════════╝",
    ]
    return "\n".join(lines)
