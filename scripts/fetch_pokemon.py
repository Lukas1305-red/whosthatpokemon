import asyncio

import httpx

BASE_URL = "https://pokeapi.co/api/v2"

async def fetch_pokemon(client: httpx.AsyncClient, id: int) -> dict:
  pokemon_url = f"{BASE_URL}/pokemon/{id}"
  species_url = f"{BASE_URL}/pokemon-species/{id}"

  pokemon_result, species_result = await asyncio.gather(
    client.get(pokemon_url),
    client.get(species_url)
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
          (g["genus"] for g in species["genera"] if g["language"]["name"] == "en"),
          ""
      ),
      "flavor_texts": list({
          f["flavor_text"].replace("\n", " ").replace("\f", " ")
          for f in species["flavor_text_entries"]
          if f["language"]["name"] == "en"
      }),
      "habitat": species["habitat"]["name"] if species["habitat"] else None,
  }

