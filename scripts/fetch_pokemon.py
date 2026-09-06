import asyncio
import json
from pathlib import Path

import aiofiles
import httpx

BASE_URL = "https://pokeapi.co/api/v2"
OUTPUT_PATH = Path("data/pokemon_raw.json")
TOTAL_POKEMON = 1025
CONCURRENCY_LIMIT = 20


async def fetch_pokemon(client: httpx.AsyncClient, id: int) -> dict:
    pokemon_url = f"{BASE_URL}/pokemon/{id}"
    species_url = f"{BASE_URL}/pokemon-species/{id}"

    pokemon_result, species_result = await asyncio.gather(
        client.get(pokemon_url), client.get(species_url)
    )

    # Raise HTTP status error if one occurred
    pokemon_result.raise_for_status()
    species_result.raise_for_status()

    pokemon = pokemon_result.json()
    species = species_result.json()

    return {
        "id": id,
        "name": pokemon["name"],
        "types": [t["type"]["name"] for t in pokemon["types"]],
        "stats": {s["stat"]["name"]: s["base_stat"] for s in pokemon["stats"]},
        "abilities": [a["ability"]["name"] for a in pokemon["abilities"]],
        "sprite": pokemon["sprites"]["front_default"],
        "genus": next(
            (g["genus"] for g in species["genera"] if g["language"]["name"] == "en"), ""
        ),
        "flavor_texts": list(
            {
                f["flavor_text"].replace("\n", " ").replace("\f", " ")
                for f in species["flavor_text_entries"]
                if f["language"]["name"] == "en"
            }
        ),
        "habitat": species["habitat"]["name"] if species["habitat"] else None,
    }


async def fetch_all_pokemon():
    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)
    results = []
    failed = []

    async def fetch_with_limit(client: httpx.AsyncClient, id: int):
        async with sem:
            try:
                data = await fetch_pokemon(client, id)
                results.append(data)
            except httpx.HTTPStatusError as e:
                failed.append(id)
                print(
                    f"{id:4d} — http error: {e.response.status_code} {e.response.reason_phrase}"
                )
            except httpx.RequestError as e:
                failed.append(id)
                print(f"{id:4d} — request error: {e}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [fetch_with_limit(client, i) for i in range(1, TOTAL_POKEMON + 1)]
        await asyncio.gather(*tasks)

    results.sort(key=lambda x: x["id"])

    await create_and_write_to_file(results)

    if failed:
        print(f"✗ {len(failed)} failed: {sorted(failed)}")
    else:
        print("all pokemon fetched successfully")


async def create_and_write_to_file(result):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(OUTPUT_PATH, "w") as f:
        await f.write(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"\n✓ saved {len(result)}/{TOTAL_POKEMON} pokemon to {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(fetch_all_pokemon())
