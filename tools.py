"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── helpers ───────────────────────────────────────────────────────────────────

_SIZE_SPLIT = re.compile(r"[/\s()]+")
_WORD = re.compile(r"[a-z0-9]+")


def _size_matches(listing_size: str, wanted: str) -> bool:
    """Case-insensitive exact match, or whole-token match after splitting."""
    wanted_u = wanted.upper().strip()
    listing_u = listing_size.upper().strip()
    if listing_u == wanted_u:
        return True
    tokens = [t for t in _SIZE_SPLIT.split(listing_u) if t]
    return wanted_u in tokens


def _keyword_score(listing: dict, description: str) -> int:
    """Count how many description tokens appear in the listing text."""
    query_tokens = _WORD.findall(description.lower())
    if not query_tokens:
        return 0
    haystack = " ".join(
        [
            listing.get("title") or "",
            listing.get("description") or "",
            " ".join(listing.get("style_tags") or []),
            listing.get("category") or "",
            " ".join(listing.get("colors") or []),
            listing.get("brand") or "",
        ]
    ).lower()
    hay_tokens = set(_WORD.findall(haystack))
    return sum(1 for token in query_tokens if token in hay_tokens)


def _format_wardrobe_items(items: list[dict]) -> str:
    lines = []
    for item in items:
        colors = ", ".join(item.get("colors") or [])
        tags = ", ".join(item.get("style_tags") or [])
        notes = item.get("notes") or ""
        lines.append(
            f"- {item.get('name')} ({item.get('category')}): "
            f"colors [{colors}]; tags [{tags}]"
            + (f"; notes: {notes}" if notes else "")
        )
    return "\n".join(lines)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    Returns an empty list when nothing matches — not None, not an exception.
    """
    listings = load_listings()
    scored: list[tuple[int, dict]] = []

    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and not _size_matches(listing["size"], size):
            continue
        score = _keyword_score(listing, description)
        if score == 0:
            continue
        scored.append((score, listing))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.
    Empty wardrobe → general styling advice (still a non-empty string).
    """
    items = wardrobe.get("items") or []
    item_bits = (
        f"title={new_item.get('title')!r}, "
        f"category={new_item.get('category')!r}, "
        f"colors={new_item.get('colors')}, "
        f"style_tags={new_item.get('style_tags')}, "
        f"size={new_item.get('size')!r}, "
        f"price={new_item.get('price')}, "
        f"platform={new_item.get('platform')!r}"
    )

    if not items:
        prompt = (
            "Suggest one or two outfit ideas for this thrift find. The wearer "
            "has an empty wardrobe, so give general styling advice (colors, "
            "silhouettes, shoes, accessories) rather than naming owned pieces.\n\n"
            f"Item: {item_bits}\n\n"
            "Keep the answer to a short paragraph or two."
        )
    else:
        prompt = (
            "Suggest one or two outfits that pair this thrift find with pieces "
            "the wearer already owns. Name specific wardrobe items from the list.\n\n"
            f"New item: {item_bits}\n\n"
            f"Wardrobe:\n{_format_wardrobe_items(items)}\n\n"
            "Keep the answer to a short paragraph or two."
        )

    return generate(prompt)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.
    Empty/whitespace outfit → descriptive fallback without calling the model.
    """
    title = new_item.get("title") or "this find"
    price = new_item.get("price")
    platform = new_item.get("platform") or "thrift"

    if not (outfit or "").strip():
        return (
            f"Scored {title} for ${price} on {platform}. "
            f"Solid thrift pick — clean lines and an easy everyday vibe."
        )

    # Diagnosis (Milestone 4): labeled Price/Platform lines made the model
    # echo fields instead of writing a real caption. One prose block + a hard
    # sentence cap is the whole change.
    prompt = (
        "Write a social caption about this thrift find as if you just bought it. "
        "Use exactly 2, 3, or 4 sentences (no more). Sound like a real post, "
        "not a product listing or a receipt. In the caption, name the item once, "
        f"include the number {price} once as the price you paid, and name "
        f"{platform} once as where you got it. Do not use labels like "
        "'Price:' or 'Platform:'. You may nod at this outfit idea: "
        f"{outfit.strip()}\n\n"
        f"The find: {title}.\n"
    )
    return generate(prompt)
