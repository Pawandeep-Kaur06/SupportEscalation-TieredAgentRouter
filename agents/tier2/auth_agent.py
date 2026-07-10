from agents.tier2.base_agent import run_specialist_agent


def auth_agent(handoff):

    return run_specialist_agent(

        specialty="Authentication",

        handoff=handoff
    )