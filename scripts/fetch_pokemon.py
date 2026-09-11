import asyncio
import json
from pathlib import Path

import aiofiles
import httpx
import numpy as np

# MARK: - Constants
BASE_URL = "https://pokeapi.co/api/v2"
OUTPUT_PATH = Path("data/pokemon_raw.json")

TOTAL_POKEMON = 1025
CONCURRENCY_LIMIT = 20


GENERATION_TO_REGION = {
    "generation-i": "kanto",
    "generation-ii": "johto",
    "generation-iii": "hoenn",
    "generation-iv": "sinnoh",
    "generation-v": "unova",
    "generation-vi": "kalos",
    "generation-vii": "alola",
    "generation-viii": "galar",
    "generation-ix": "paldea",
}


STARTER_IDS = {
    # Gen 1 - Kanto
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    # Gen 2 - Johto
    152,
    153,
    154,
    155,
    156,
    157,
    158,
    159,
    160,
    # Gen 3 - Hoenn
    252,
    253,
    254,
    255,
    256,
    257,
    258,
    259,
    260,
    # Gen 4 - Sinnoh
    387,
    388,
    389,
    390,
    391,
    392,
    393,
    394,
    395,
    # Gen 5 - Unova
    495,
    496,
    497,
    498,
    499,
    500,
    501,
    502,
    503,
    # Gen 6 - Kalos
    650,
    651,
    652,
    653,
    654,
    655,
    656,
    657,
    658,
    # Gen 7 - Alola
    722,
    723,
    724,
    725,
    726,
    727,
    728,
    729,
    730,
    # Gen 8 - Galar
    810,
    811,
    812,
    813,
    814,
    815,
    816,
    817,
    818,
    # Gen 9 - Paldea
    906,
    907,
    908,
    909,
    910,
    911,
    912,
    913,
    914,
}


# MARK: - Helpers


def calculate_stat_thresholds(pokemon_list):
    stat_names = pokemon_list[0]["stats"].keys()

    thresholds = {}

    for stat in stat_names:
        values = [pokemon["stats"][stat] for pokemon in pokemon_list]

        thresholds[stat] = {
            "low": np.percentile(values, 10),
            "high": np.percentile(values, 90),
        }

    return thresholds


def clean_text(text: str) -> str:
    return text.replace("\n", " ").replace("\f", " ").strip()


def get_english_genus(species: dict) -> str:
    return next(
        (
            genus["genus"]
            for genus in species["genera"]
            if genus["language"]["name"] == "en"
        ),
        "",
    )


def get_english_flavor_texts(species: dict) -> list[str]:
    return list(
        {
            clean_text(entry["flavor_text"])
            for entry in species["flavor_text_entries"]
            if entry["language"]["name"] == "en"
        }
    )


def get_evolution_details(chain: dict) -> list[dict]:
    """
    Flatten an evolution chain into a list of species names and IDs.

    Example:
    [
        {"id": 1, "name": "bulbasaur"},
        {"id": 2, "name": "ivysaur"},
        {"id": 3, "name": "venusaur"}
    ]
    """

    result = []

    def walk(node: dict):
        species_url = node["species"]["url"]
        species_id = int(species_url.rstrip("/").split("/")[-1])

        result.append(
            {
                "id": species_id,
                "name": node["species"]["name"],
            }
        )

        for evolution in node["evolves_to"]:
            walk(evolution)

    walk(chain)

    return result


# MARK: fetch_evolution_chain
async def fetch_evolution_chain(
    client: httpx.AsyncClient,
    species: dict,
) -> dict:
    """
    Fetch and flatten the evolution chain for a Pokémon species.
    """

    chain_url = species["evolution_chain"]["url"]

    response = await client.get(chain_url)
    response.raise_for_status()

    chain = response.json()

    evolution_line = get_evolution_details(chain["chain"])

    # Find this Pokémon in the evolution line.
    current_id = species["id"]

    current_index = next(
        (
            index
            for index, pokemon in enumerate(evolution_line)
            if pokemon["id"] == current_id
        ),
        0,
    )

    return {
        "line": evolution_line,
        "stage": current_index + 1,
        "stages": len(evolution_line),
        "is_final": current_index == len(evolution_line) - 1,
    }


# MARK: - fetch_pokemon
async def fetch_pokemon(
    client: httpx.AsyncClient,
    id: int,
) -> dict:

    pokemon_url = f"{BASE_URL}/pokemon/{id}"
    species_url = f"{BASE_URL}/pokemon-species/{id}"

    pokemon_result, species_result = await asyncio.gather(
        client.get(pokemon_url),
        client.get(species_url),
    )

    pokemon_result.raise_for_status()
    species_result.raise_for_status()

    pokemon = pokemon_result.json()
    species = species_result.json()

    generation = species["generation"]["name"]

    # Evolution chain requires one additional request.
    evolution = await fetch_evolution_chain(client, species)

    return {
        "id": id,
        "name": pokemon["name"],
        "genus": get_english_genus(species),
        "types": [type_data["type"]["name"] for type_data in pokemon["types"]],
        "stats": {stat["stat"]["name"]: stat["base_stat"] for stat in pokemon["stats"]},
        "abilities": [ability["ability"]["name"] for ability in pokemon["abilities"]],
        "moves": [move["move"]["name"] for move in pokemon["moves"]],
        "height": pokemon["height"],
        "weight": pokemon["weight"],
        "base_experience": pokemon["base_experience"],
        "capture_rate": species["capture_rate"],
        "growth_rate": species["growth_rate"]["name"],
        "evolution": evolution,
        "habitat": (species["habitat"]["name"] if species["habitat"] else None),
        "generation": generation,
        "region": GENERATION_TO_REGION.get(
            generation,
            "unknown",
        ),
        "color": species["color"]["name"],
        "is_starter": id in STARTER_IDS,
        "is_legendary": species["is_legendary"],
        "is_mythical": species["is_mythical"],
        "flavor_texts": get_english_flavor_texts(species),
        "sprite": pokemon["sprites"]["front_default"],
    }


# MARK: - fetch_all_pokemon
async def fetch_all_pokemon():

    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)

    results = []
    failed = []

    async def fetch_with_limit(
        client: httpx.AsyncClient,
        id: int,
    ):
        async with sem:
            try:
                data = await fetch_pokemon(client, id)
                results.append(data)

                print(f"✓ {id:4d} — {data['name']}")

            except httpx.HTTPStatusError as e:
                failed.append(id)

                print(
                    f"✗ {id:4d} — HTTP error: "
                    f"{e.response.status_code} "
                    f"{e.response.reason_phrase}"
                )

            except httpx.RequestError as e:
                failed.append(id)

                print(f"✗ {id:4d} — request error: {e}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [fetch_with_limit(client, i) for i in range(1, TOTAL_POKEMON + 1)]

        await asyncio.gather(*tasks)

    results.sort(key=lambda x: x["id"])

    await create_and_write_to_file(results)
    print(f"\n✓ saved {len(results)}/{TOTAL_POKEMON} pokemon to {OUTPUT_PATH}")

    stat_thresholds = calculate_stat_thresholds(results)
    await create_and_write_to_file(
        stat_thresholds, output_path=Path("data/thresholds.json")
    )

    if failed:
        print(f"✗ {len(failed)} failed: {sorted(failed)}")
    else:
        print("✓ all pokemon fetched successfully")


# MARK: - create_and_write_to_file
async def create_and_write_to_file(result, output_path=OUTPUT_PATH):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    async with aiofiles.open(
        output_path,
        "w",
    ) as f:
        await f.write(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        )


# MARK: - main
if __name__ == "__main__":
    asyncio.run(fetch_all_pokemon())
