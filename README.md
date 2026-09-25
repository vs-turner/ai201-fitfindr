# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---



Note: First commit, used python [app.py](http://app.py) fields to observe the listing fields, including id, title, description, category, size, condition, price, colors, brand, and platform it is being sold on.

## What This Does



---



## Tool Inventory



### `search_listings`

- **What it does:** Filters `data/listings.json` by optional size and price, scores the rest by keyword overlap with the description, and returns the best matches first (at most `config.SEARCH_RESULT_LIMIT`).
- **Inputs:**
  - `description` (`str`): keywords for what the user wants (e.g. `"vintage graphic tee"`). Used only for scoring. Never raises if empty, but an empty description yields score 0 for every listing, so the result is empty.
  - `size` (`str | None`): size to filter by, or `None` to skip size filtering. Match is case-insensitive. A listing matches when, after uppercasing both sides, either the listing `size` equals `size`, or `size` appears as a whole token when the listing size is split on `/`, whitespace, and parentheses. So `"M"` matches `"M"`, `"M/L"`, and `"S/M"`. `"S"` does **not** match `"US 9"`. `"L"` does **not** match `"XL"`.
  - `max_price` (`float | None`): inclusive price ceiling, or `None` to skip price filtering. Keep a listing when `listing["price"] <= max_price`.
- **Returns:** A `list[dict]` of matching listing dicts, highest keyword-overlap score first, length ≤ `config.SEARCH_RESULT_LIMIT`. Drop any listing with score 0. Each dict has: `id` (`str`), `title` (`str`), `description` (`str`), `category` (`str`), `style_tags` (`list[str]`), `size` (`str`), `condition` (`str`), `price` (`float`), `colors` (`list[str]`), `brand` (`str | None`), `platform` (`str`).
- **When it has nothing:** Returns `[]` (empty list). Never `None`. Never an exception. The loop branches on this.



### `suggest_outfit`

- **What it does:** Calls the model (via `generate()`) to suggest one or two outfits that pair a chosen thrift listing with what the user already owns.
- **Inputs:**
  - `new_item` (`dict`): one listing dict in the same shape `search_listings` returns (at least `title`, `category`, `colors`, `style_tags`, `size`, `price`, `platform`).
  - `wardrobe` (`dict`): has key `items` (`list[dict]`). Each wardrobe item has `id` (`str`), `name` (`str`), `category` (`str`), `colors` (`list[str]`), `style_tags` (`list[str]`), `notes` (`str | None`). `items` may be empty.
- **Returns:** A non-empty `str`: one or two outfit suggestions. If `wardrobe["items"]` is non-empty, name specific pieces from that list. If `wardrobe["items"]` is empty, return general styling advice for `new_item` alone (still a non-empty string, do not raise).
- **When it has nothing:** There is no “no outfit” empty case for the loop. An empty wardrobe still returns a non-empty advice string. If the model is unreachable, that is handled in `run_agent` (not inside this tool) via `ModelUnavailable`.



### `create_fit_card`

- **What it does:** Calls the model (via `generate()`) to write a short social-style caption about the find, using the outfit suggestion and the listing.
- **Inputs:**
  - `outfit` (`str`): the outfit suggestion string from `suggest_outfit`.
  - `new_item` (`dict`): the same listing dict that went into `suggest_outfit` (needs at least `title`, `price`, `platform`).
- **Returns:** A `str` caption, two to four sentences, that mentions the item, its price, and its platform once each, and sounds like a real post rather than a product blurb.
- **When it has nothing:** If `outfit` is empty or whitespace-only, return a short descriptive fallback string about the item (still a `str`, not `None`, not an exception) instead of calling the model / raising. The planning loop’s empty branch is on search, not on this tool.

---



## Planning Loop



**Branch rule:** If `search_listings` returns an empty list, set `session["error"]` to a message that tells the user what to change (widen price, drop or change size, try different keywords) and return the session without calling `suggest_outfit` or `create_fit_card`. Otherwise, take the first result as `session["selected_item"]` and go to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** 

**What moves through the session:**

---



## Sample Run



**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

```

```
$ python -c "from tools import suggest_outfit; ..."

```

```
$ python -c "from tools import create_fit_card; ..."

```

---



## How I Used AI



**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*



---



## Run Log — Before




| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1.        |        |       |       |       |       |       |         |
| 2.        |        |       |       |       |       |       |         |
| 3.        |        |       |       |       |       |       |         |
| 4.        |        |       |       |       |       |       |         |
| 5.        |        |       |       |       |       |       |         |


**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---



## Verdicts and Diagnoses




| #   | Criterion | Target | Verdict | How I decided |
| --- | --------- | ------ | ------- | ------------- |
| 1   |           |        |         |               |
| 2   |           |        |         |               |
| 3   |           |        |         |               |
| 4   |           |        |         |               |
| 5   |           |        |         |               |


**Diagnoses**

---



## Loop Trace



**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** 

---



## The Improvement



**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After


| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1.        |        |       |       |       |       |       |         |
| 2.        |        |       |       |       |       |       |         |
| 3.        |        |       |       |       |       |       |         |
| 4.        |        |       |       |       |       |       |         |
| 5.        |        |       |       |       |       |       |         |


**Did it help, and how do I know:**



---



## What's Still Broken





---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**