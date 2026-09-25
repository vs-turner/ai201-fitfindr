# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
I picked 4 of 5 instead of 5 of 5 because `search_listings` is a plain keyword overlap score. Small changes in wording can drop every listing to score 0 even when a human would say the data has a match. I will add some flexibility just for false negatives in search.

---

## 2. An query with no matches stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change in 5 of 5 tries.

**Why this target:**
5 of 5 is fair here because this path does not depend on the model. Empty
search returns `[]` every time for an impossible query, and the branch is plain Python:. If the list is empty, set `session["error"]` and return. If this fails once, the loop is wrong.

---

## 3. Selected item is the same object the next tool receives

Given a matching query that produces at least one search result, in 5 of 5
tries both of these hold: (1) `session["selected_item"]["id"]` equals
`session["search_results"][0]["id"]`, and (2) the `suggest_outfit` trace step
shows `inputs["new_item"]["id"]` equal to that same `id`.

**Why this target:** State wiring is deterministic code with no model call, so 5 of 5 seems reasonable. Matching on title alone would miss a swap between two similarly named listings. Checking only `session["selected_item"]` would miss a bug that stores
the right item in the session but passes a different dict into the next tool.
`id` is unique in the data, so a scorer does not need to ask what “the same
item” means.

---

## 4. Fit card stays usable across model variance

Run the agent 5 times on the same matching query. In at least 4 of 5 runs, the
fit card is a non-empty string of 2 to 4 sentences that mentions both the
selected item’s `price` (as a number) and its `platform` (as a substring). The
5 cards need not be identical, and at least 2 of the 5 must differ by more than
whitespace.

**Why this target:** The fit card calls a model, so word-for-word sameness is not necessary. Price + platform + length is something a person can score from the session alone. I kept the threshold at 4 of 5 leaves room for one model miss without pretending a flaky caption is a pass.

---

## 5. Search respects the price ceiling

Given a query that states an explicit max price (for example `under $30`), in
5 of 5 tries every listing in `session["search_results"]` has
`price` less than or equal to that max. An empty `search_results` list still
passes, because there is no over-budget item to catch.

**Why this target:**
Price filtering is local code over floats, not a model judgment, so 5 of 5 is
appropriate. A softer target would hide a bug that returns a $45 jacket for an
“under $30” ask. I care about this because a wrong price makes the later outfit
and fit card look fine while the agent already failed the user’s constraint.

---

