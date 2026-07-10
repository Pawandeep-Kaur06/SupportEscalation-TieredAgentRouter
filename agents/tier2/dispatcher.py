from agents.tier2.auth_agent import auth_agent
from agents.tier2.network_agent import network_agent
from agents.tier2.hardware_agent import hardware_agent
from agents.tier2.software_agent import software_agent


SPECIALISTS = {
    "authentication": ("Authentication", auth_agent),
    "network": ("Network", network_agent),
    "hardware": ("Hardware", hardware_agent),
    "software": ("Software", software_agent),
}


def dispatch(handoff):

    category = handoff.get("category", "general").lower()

    specialist, handler = SPECIALISTS.get(
        category,
        ("Software", software_agent)
    )

    result = handler(handoff)
    result["specialist"] = specialist

    return result
