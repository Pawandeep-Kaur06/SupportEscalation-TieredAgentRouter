from agents.tier2.base_agent import run_specialist_agent


def hardware_agent(handoff):

    return run_specialist_agent(

        specialty="Hardware",

        handoff=handoff
    )