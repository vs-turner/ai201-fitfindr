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

FitFindr takes a thrift shopping ask in plain language and runs a short planning loop over three tools. It parses keywords, size, and a price ceiling from the query, searches a local listings file, picks the top match, asks the model for outfit ideas against the user’s wardrobe, and writes a short fit card caption. When search returns an empty list, the run stops after that step and names what to try changing.

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



**Branch rule:** After `search_listings`, check `session["search_results"]`. If the list is empty, set `session["error"]` to a message that names what the user could change (widen price, drop or change size, try different keywords) and return. If the list has items, set `session["selected_item"]` to the first result, then call `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex in `parse_query()`. It pulls `under` / `below` / `max` price phrases and `size …` out of the string, then strips a short filler prefix like `looking for`. What remains is `description`. That dict lands in `session["parsed"]`.

**What moves through the session:** `parsed` → `search_results` → `selected_item` (first result) → `outfit_suggestion` → `fit_card`. Each tool writes into the session. The next step reads from it. On empty search, `error` is set and `fit_card` stays unset.

---



## Sample Run



**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   For an effortless Y2K streetwear look, pair the butterfly baby tee with the **baggy straight-leg jeans**...

  Fit card: Still pinching myself over scoring this Y2K Baby Tee — Butterfly Print on depop. For just $18.0...
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print([(r['id'], r['title'], r['price']) for r in search_listings('graphic tee', max_price=30)])"
[('lst_002', 'Y2K Baby Tee — Butterfly Print', 18.0), ('lst_006', 'Graphic Tee — 2003 Tour Bootleg Style', 24.0), ('lst_017', 'Mesh Long-Sleeve Top — Black', 15.0), ('lst_033', 'Vintage Band Tee — Faded Grey', 19.0), ('lst_011', 'Low-Rise Cargo Pants — Khaki', 27.0), ('lst_015', 'Vintage Graphic Hoodie — Faded Black', 26.0)]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
**Outfit 1: Casual Streetwear**
Pair the vintage Levi's 501 jeans with the **White ribbed tank top** tucked in, layered under the **Oversized grey crewneck sweatshirt**. Accessorize with the **Brown leather belt**, **Chunky white sneakers**, and the **Black crossbody bag** for an effortless, classic streetwear look.

**Outfit 2: Edge & Denim**
Style the medium-wash jeans with the **Black cropped zip hoodie** and the **Vintage black denim jacket** layered on top for a cool double-denim contrast. Finish the outfit with the **Black combat boots** and the **Black crossbody bag** for an edgy, vintage-inspired vibe.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Still can't believe I found these Vintage Levi's 501 Jeans — Medium Wash just sitting there on depop. Snagged them for only $38.0 and they fit like a absolute glove. Honestly, they're going to live with my favorite white sneakers all fall.
```

---



## How I Used AI



**Moment 1**

- *What I asked for:* help implementing `search_listings` from the Tool Inventory, with size matching and keyword scoring
- *What came back:* a draft that used a substring check for size, so asking for `"S"` also matched listings sized `"US 9"`
- *What I changed:* switched to splitting listing sizes on `/`, spaces, and parentheses, then matching whole tokens only

**Moment 2**

- *What I asked for:* wire `run_agent` so an empty search stops before the later tools, with every result stored in the session
- *What came back:* a draft that kept the top listing in a local variable and passed it straight into `suggest_outfit`
- *What I changed:* wrote each tool result into the session and read the next inputs back out of the session so `selected_item` stays checkable against `search_results[0]`



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