
LOWER_STAT_BOUND = 40
UPPER_STAT_BOUND = 110

def create_stat_traits(stats: dict) -> list[str]:
  traits = []

  for stat, value in stats.items():
    if value >= UPPER_STAT_BOUND:
      traits.append(f"very high {stat}")
    elif value <= LOWER_STAT_BOUND:
      traits.append(f"very low {stat}")

  return traits
