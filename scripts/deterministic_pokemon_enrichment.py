def create_stat_traits(stats: dict, thresholds: dict) -> list[str]:
    traits = []

    for stat, value in stats.items():
        threshold = thresholds[stat]
        if value >= threshold["high"]:
            traits.append(f"very high {stat}")
        elif value <= threshold["low"]:
            traits.append(f"very low {stat}")

    return traits
