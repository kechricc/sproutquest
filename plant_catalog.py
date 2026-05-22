"""SproutQuest plant catalog + owner-controlled bonus scoring.

The backend owns the catalog so the frontend only has to render what it's told.
Each entry is keyed by the species' scientific name (what Plant.id returns) and
carries the display data (emoji, common name) plus the kid-friendly blurbs.

SCORING
-------
Every plant scores DEFAULT_BASE_POINTS (10), then the first finder of a species
in a hunt earns 2x. There are no rarity tiers.

MASTER BONUS LIST — make certain plants score higher
----------------------------------------------------
You (the owner) can promote any plant to a higher value WITHOUT code changes:

  1. Edit `bonus_plants.json` (next to this file). Map a plant to its point
     value. The key may be a scientific name ("Asclepias syriaca") OR the
     friendly catalog key ("milkweed"). Keys starting with "_" are ignored.

  2. Or set the BONUS_PLANTS environment variable to the same JSON (handy on
     Railway — change which plants score higher per area without redeploying).
     The env var takes precedence over the file.

The first-finder 2x bonus still applies on top of whatever value you set.
"""

import json
import os
from pathlib import Path

DEFAULT_BASE_POINTS = 10

# Keyed by scientific name (the identity Plant.id returns at species level).
PLANT_CATALOG = {
    "Taraxacum officinale": {
        "key": "dandelion",
        "emoji": "🌼",
        "common_name": "Dandelion",
        "base_points": DEFAULT_BASE_POINTS,
        "about": "Originally from Europe, every part is edible. Brought to North America "
                 "intentionally by colonists as a food source.",
        "forage": "Leaves edible raw in salads when young. Flowers can be made into wine. "
                  "Roots roasted as a coffee substitute.",
        "climate": "Herbicide use to eliminate dandelions harms pollinators that depend on "
                   "them as an early-spring food source.",
    },
    "Morchella esculenta": {
        "key": "morel",
        "emoji": "🍄",
        "common_name": "Yellow Morel",
        "base_points": DEFAULT_BASE_POINTS,
        "about": "One of the most prized edible mushrooms. Distinctive honeycomb cap, hollow "
                 "interior. Fruits briefly in spring.",
        "forage": "Always cook before eating. Look for fully hollow stem when sliced. Peak "
                  "season April-May in Illinois.",
        "climate": "Declining as ash trees disappear due to the Emerald Ash Borer, an invasive "
                   "beetle introduced accidentally from Asia.",
    },
    "Trillium grandiflorum": {
        "key": "trillium",
        "emoji": "🌷",
        "common_name": "White Trillium",
        "base_points": DEFAULT_BASE_POINTS,
        "about": "Takes 7 years to grow from seed to flower. One of Illinois's most beautiful "
                 "spring wildflowers.",
        "forage": "Do not pick — collecting the flower kills the plant. Leave these alone to "
                  "protect the population.",
        "climate": "Populations collapsing due to overgrazing by deer and woodland habitat "
                   "destruction from development.",
    },
    "Phlox divaricata": {
        "key": "phlox",
        "emoji": "🌸",
        "common_name": "Wild Blue Phlox",
        "base_points": DEFAULT_BASE_POINTS,
        "about": "Native Illinois woodland wildflower. Important nectar source for early "
                 "butterflies and hummingbirds in spring.",
        "forage": "Not edible but critical for the native ecosystem. Plant in your garden to "
                  "support pollinators.",
        "climate": "Being displaced by invasive garlic mustard which changes soil chemistry and "
                   "crowds out native woodland plants.",
    },
    "Alliaria petiolata": {
        "key": "garlic_mustard",
        "emoji": "🌿",
        "common_name": "Garlic Mustard",
        "base_points": DEFAULT_BASE_POINTS,
        "about": "Invasive plant from Europe now spreading across North American woodlands. "
                 "Releases chemicals that harm native plants.",
        "forage": "Edible — leaves have a mild garlic flavor. Can be used in pesto or salads. "
                  "Actually worth removing when you find it.",
        "climate": "One of the most damaging woodland invaders in Illinois. Crowds out native "
                   "spring wildflowers and changes soil chemistry.",
    },
    "Asclepias syriaca": {
        "key": "milkweed",
        "emoji": "🌺",
        "common_name": "Common Milkweed",
        "base_points": DEFAULT_BASE_POINTS,
        "about": "The only plant monarch butterflies can lay eggs on. Without milkweed, monarchs "
                 "cannot reproduce.",
        "forage": "Young shoots can be cooked like asparagus. Flower clusters can be battered and "
                  "fried. Confirm ID carefully first.",
        "climate": "Monarch populations have crashed 80% since the 1990s largely because herbicide "
                   "use eliminated milkweed at field edges.",
    },
    "Monarda fistulosa": {
        "key": "bergamot",
        "emoji": "🪻",
        "common_name": "Wild Bergamot",
        "base_points": DEFAULT_BASE_POINTS,
        "about": "Native prairie plant related to oregano. Leaves smell strongly of "
                 "lavender-oregano when crushed.",
        "forage": "Leaves can be used as an oregano substitute in cooking. Tea from leaves has "
                  "natural antimicrobial properties.",
        "climate": "Prairie plants like wild bergamot have lost over 99% of their Illinois habitat "
                   "to agriculture and development.",
    },
    "Trifolium pratense": {
        "key": "clover",
        "emoji": "🍀",
        "common_name": "Red Clover",
        "base_points": DEFAULT_BASE_POINTS,
        "about": "Red clover is a fluffy pink wildflower that bees absolutely love. It came from "
                 "Europe and now grows in fields and lawns all over North America.",
        "forage": "The flower heads are edible and can be dried for a mild, sweet tea. Only nibble "
                  "wild plants after a grown-up confirms they haven't been sprayed.",
        "climate": "Clover quietly feeds the soil with nitrogen, but heavy weed-killer use on lawns "
                   "wipes it out — along with the bees that depend on it.",
    },
}

# Case-insensitive lookup by scientific name.
_LOOKUP = {name.strip().lower(): entry for name, entry in PLANT_CATALOG.items()}

_BONUS_FILE = Path(__file__).with_name("bonus_plants.json")


def _coerce_overrides(data, source):
    """Turn a {plant: points} mapping into a normalized lowercase dict."""
    out = {}
    if not isinstance(data, dict):
        print(f"[plant_catalog] Ignoring {source}: expected a JSON object.")
        return out
    for k, v in data.items():
        if not isinstance(k, str) or k.startswith("_"):
            continue  # underscore keys are notes/examples
        try:
            out[k.strip().lower()] = int(v)
        except (ValueError, TypeError):
            print(f"[plant_catalog] Ignoring bonus entry {k!r}={v!r} in {source}: not an integer.")
    return out


def _load_bonus_overrides():
    """Load the owner's bonus list from bonus_plants.json, then BONUS_PLANTS env (env wins)."""
    overrides = {}
    if _BONUS_FILE.exists():
        try:
            overrides.update(_coerce_overrides(json.loads(_BONUS_FILE.read_text(encoding="utf-8")),
                                               "bonus_plants.json"))
        except ValueError as exc:
            print(f"[plant_catalog] bonus_plants.json is not valid JSON, ignoring: {exc}")
    raw_env = os.environ.get("BONUS_PLANTS")
    if raw_env:
        try:
            overrides.update(_coerce_overrides(json.loads(raw_env), "BONUS_PLANTS env"))
        except ValueError as exc:
            print(f"[plant_catalog] BONUS_PLANTS env is not valid JSON, ignoring: {exc}")
    return overrides


_BONUS_OVERRIDES = _load_bonus_overrides()


def reload_bonus_overrides():
    """Re-read the bonus list at runtime (e.g. after editing the file). Returns the new map."""
    global _BONUS_OVERRIDES
    _BONUS_OVERRIDES = _load_bonus_overrides()
    return _BONUS_OVERRIDES


def _effective_base_points(scientific_name, key, fallback):
    """Owner bonus list wins (by scientific name, then by friendly key); else the catalog value."""
    sci = (scientific_name or "").strip().lower()
    if sci in _BONUS_OVERRIDES:
        return _BONUS_OVERRIDES[sci]
    k = (key or "").strip().lower()
    if k in _BONUS_OVERRIDES:
        return _BONUS_OVERRIDES[k]
    return fallback


def get_plant_info(scientific_name, common_name=None):
    """Return display + scoring + blurb data for a species.

    Falls back to generated text for species not in the hardcoded catalog, and
    applies the owner's bonus list to base_points. Field names match what
    /api/identify returns to the frontend.
    """
    entry = _LOOKUP.get((scientific_name or "").strip().lower())
    if entry:
        info = {
            "key": entry["key"],
            "emoji": entry["emoji"],
            "plant_name": entry["common_name"],
            "scientific_name": scientific_name,
            "base_points": entry["base_points"],
            "about": entry["about"],
            "forage_note": entry["forage"],
            "climate_impact": entry["climate"],
        }
    else:
        info = _generic_info(scientific_name, common_name)

    info["base_points"] = _effective_base_points(scientific_name, info["key"], info["base_points"])
    return info


def _generic_info(scientific_name, common_name=None):
    """Two-sentence kid-friendly blurbs for any species not in the catalog."""
    display = common_name or scientific_name or "This plant"
    key = (scientific_name or common_name or "unknown").strip().lower().replace(" ", "_")
    return {
        "key": key,
        "emoji": "🌱",
        "plant_name": common_name or scientific_name,
        "scientific_name": scientific_name,
        "base_points": DEFAULT_BASE_POINTS,
        "about": f"{display} is a plant you discovered out in the wild! Every species you find is "
                 f"a little piece of the local ecosystem.",
        "forage_note": f"We don't have foraging notes for {display} yet. Golden rule: never eat any "
                       f"wild plant unless a trusted grown-up or expert says it's safe.",
        "climate_impact": f"Like many wild plants, {display} can be affected by habitat loss, "
                          f"pollution, and our changing climate. Protecting wild spaces helps it "
                          f"keep growing.",
    }
