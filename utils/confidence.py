def calculate_confidence(scores):
    if len(scores) == 0:
        return 0.0

    top = float(scores[0])
    second = float(scores[1]) if len(scores) > 1 else 0.0

    gap = top - second

    # High confidence
    if top >= 0.55 and gap >= 0.03:
        return 0.90

    # Good confidence
    elif top >= 0.45:
        return 0.75

    # Moderate confidence
    elif top >= 0.35:
        return 0.60

    # Low confidence
    elif top >= 0.25:
        return 0.40

    # Very low confidence
    else:
        return 0.20