from agents.tier2.base_agent import run_specialist_agent


def software_agent(handoff):

    return run_specialist_agent(

        specialty="Software",

        handoff=handoff
    )