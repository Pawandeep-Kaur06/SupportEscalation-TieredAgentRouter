from agents.tier2.base_agent import run_specialist_agent


def network_agent(handoff):

    return run_specialist_agent(

        specialty="Network",

        handoff=handoff
    )