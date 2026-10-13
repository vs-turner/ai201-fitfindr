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

Produced by `run_eval.py::main` (caching off, 5 tries). Full evidence: `results/run_2026-10-13_1541_before.md`. Loop: `agent.py::run_agent`.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1. Matching query completes all three tools + fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Empty search stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item id matches item passed to suggest_outfit | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card usable across model variance | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Search respects the price ceiling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Real output from one try**, pasted as text, naming the file and function that produced it:

**Criterion 1** — Try 1 — `results/run_2026-10-13_1541_before.md` ← `run_eval.py::run_once` / `agent.py::run_agent`

```
- stopped early: no
- selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
- search_results: 10

Fit card:
Finally scored this Y2K Baby Tee — Butterfly Print on depop and I am obsessed. Paid just $18.0 and the fit is literally so good. Can't wait to style it with some baggy denim for the ultimate off-duty look!

Trace includes: search_listings (via MCP) → select_item → suggest_outfit → create_fit_card
```

**Criterion 2** — Try 1 — same file / functions

```
- stopped early: yes — No listings matched that search. Try different keywords, drop or change the size, or widen the price ceiling.
- selected_item: (none)
- search_results: 0

[3] branch
      →    empty search — stopping before suggest_outfit / create_fit_card
```

**Criterion 3** — Try 1 — same file / functions

```
- selected_item: Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
[3] select_item
      →    selected_item.id=lst_007; search_results[0].id=lst_007
[4] suggest_outfit
      →    inputs['new_item']['id']=lst_007
```

**Criterion 4** — Try 1 — same file / functions (all 5 cards differed; each had price + platform in 2–4 sentences)

```
Fit card:
Found the absolute cutest Y2K Baby Tee — Butterfly Print scrolling on depop this week. It was only $18.0 and honestly fits like a dream. Can't wait to style it with some baggy denim for the ultimate early-2000s streetwear look!
```

**Criterion 5** — Try 1 — same file / functions

```
[2] search_listings (via MCP)
      →    prices=[18.0, 24.0, 19.0, 26.0, 15.0, 22.0, 27.0, 20.0, 30.0, 12.0]; max_price=30.0
```

---



## Verdicts and Diagnoses

| # | Criterion | Target | Verdict | How I decided |
| --- | --------- | ------ | ------- | ------------- |
| 1 | Matching query completes all three tools + fit card | 4 of 5 | MET | 5/5 tries finished with search, outfit, and a non-empty fit card. No early stop. Trace shows all three tools. |
| 2 | Empty search stops before tool 2 | 5 of 5 | MET | 5/5 tries: search returned `[]`, branch set `session["error"]` naming keywords/size/price, and `suggest_outfit` never ran. |
| 3 | Selected item id matches item passed to suggest_outfit | 5 of 5 | MET | 5/5 tries: `selected_item.id` equals `search_results[0].id`, and the suggest_outfit trace note shows the same id in `inputs['new_item']['id']`. |
| 4 | Fit card usable across model variance | 4 of 5 | MET | 5/5 cards were 2 to 4 sentences and mentioned price and platform. All five cards differed by more than whitespace. |
| 5 | Search respects the price ceiling | 5 of 5 | MET | 5/5 tries: every price in `search_results` was <= 30.0 for `under $30`. |

**Diagnoses**

I missed nothing. Every criterion met its target on the before run in `results/run_2026-10-13_1541_before.md`.

Were the targets low? Partly. Criteria 2, 3, and 5 are plain Python (branch, session wiring, price filter), so 5 of 5 is the right bar and hitting it only shows those paths are wired correctly, not that they were hard. Criterion 1 used a query the data always matches (`vintage graphic tee under $30`), so the 4 of 5 slack for keyword false negatives never got stress-tested. Criterion 4 left room for one model miss, and the model never used it: price and platform are already in the `create_fit_card` prompt, so the model mostly repeats them.

The criterion I would tighten is 4. I would keep the same scoring rules (2 to 4 sentences, price number, platform substring, at least two cards that differ) but raise the target from 4 of 5 to 5 of 5. With caching off and temperature at 0.9, five usable cards is a fair ask; leaving a free miss makes a prompt that already feeds price and platform look safer than it is.

No criterion rewrite. None of them were unmeasurable. Soft targets are not the same as a broken criterion.

---



## Loop Trace

Triggered failures (what the agent said):

- **Empty search** (`designer ballgown size XXS under $5`):
  `No listings matched that search. Try different keywords, drop or change the size, or widen the price ceiling.`
- **Empty wardrobe** (`denim jacket under $50 --empty-wardrobe`): no crash; `suggest_outfit` returned general styling advice (non-empty string) naming silhouettes/colors/shoes instead of owned pieces, then a fit card.
- **Model unavailable** (one character flipped in `GEMINI_API_KEY`, fresh query `olive corduroy overshirt under $45 size M`):
  `The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. FitFindr stopped before writing a fit card — fix the key or your connection, then try this search again.`

**Happy path** (`python app.py ask 'vintage graphic tee under $30' --trace`)

```
[1] parse_query
      in:  dict with keys: query
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] select_item
      in:  dict with keys: from
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  dict with keys: new_item, wardrobe_items
      out: For an effortless Y2K streetwear look, pair the butterfly baby tee with the **baggy straight-leg jeans** to ba…
[5] create_fit_card
      in:  dict with keys: outfit, new_item
      out: Still pinching myself over scoring this Y2K Baby Tee — Butterfly Print on depop. For just $18.0, it instantly …
```

**Empty search** (`python app.py ask 'designer ballgown size XXS under $5' --trace`)

```
[1] parse_query
      in:  dict with keys: query
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
[3] branch
      →    empty search — stopping before suggest_outfit / create_fit_card
```

**On the MCP move:** `search_listings` is registered in `mcp_server.py` and called from `run_agent` via `mcp_client.call_tool`. The happy-path and empty-search traces both label that step `search_listings (via MCP)`.

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