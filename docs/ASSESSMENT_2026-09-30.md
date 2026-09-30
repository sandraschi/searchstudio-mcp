# SearchStudio - Assessment and Work Plan (2026-09-30)

Written by Claude (Opus 5.5) a few hours after the repo was started, for opencode to
execute. Read-only assessment; no code was changed. Baseline at time of writing:
`pytest` 16 passed, `ruff check` clean, `ruff format --check` clean.

A repo this young is mostly plans - that is expected, not a criticism. The point of
this doc is to set the direction before the plans harden into the wrong shape.

---

## 1. The vision (Sandra's framing, keep this as the north star)

Every dev needs voice in their projects without tearing their hair out collecting and
integrating the components - that is what VoiceStudio solved. **Every dev equally needs
a powerful meta search that does not conk out at random times.** And like voice, search
is an extremely wide field. All of these are "a search":

| Query | What it actually needs |
|---|---|
| "gimme papers about the first sitagliptin meds" | Academic/medical vertical (PubMed / Europe PMC, OpenAlex, Crossref, arxiv-mcp). Synonym expansion (drug brand name, development code). Sort by date **ascending** because the user asked for "first". |
| "indian restaurants in Alsergrund" | Places vertical: geocode the district (Nominatim), query OSM (Overpass: `amenity=restaurant` + `cuisine=indian` inside the area), web for reviews/opening hours. Web search alone is weak here. |
| "tell me about our robotics repos" | Fleet/internal vertical: fleet registry, repo READMEs under `D:\Dev\repos`, mcp-central-docs. The open web cannot answer this at all. |
| "AMD World Labs acquisition, newest first" | News/fresh vertical: time-filtered SERP + news-capable providers. |

**Consequence for the design:** the product is not "one fan-out over 5 web-ish
providers". It is **intent routing to verticals**, each vertical a small curated plan
(which providers, how to rewrite the query, how to sort), all sharing the fan-out +
receipts engine that already exists. Then AI workflows on top (skill builder, dossier,
fact check) that consume those verticals.

The existing engine (parallel fan-out, mandatory receipts, health ledger, no fakes) is
exactly the right foundation. Keep it; build upward.

---

## 2. Comparison with VoiceStudio (debpalash/VoiceStudio)

VoiceStudio: local-first open-source ElevenLabs alternative (cloning, voice design,
dubbing, dictation, transcription, audiobooks), AGPL-3.0, tens of thousands of stars
(sources disagree on the exact count).

| VoiceStudio | SearchStudio today |
|---|---|
| Sells **outcomes**: Create -> Produce -> Connect | Sells **plumbing**: providers, kinds, health |
| Each workflow is a finished pipeline (reference clip -> model -> text -> audio; video -> alignment -> synthesis -> export) | One primitive (`super_search`) plus diagnostics |
| One workspace/screen per workflow, screenshots of each | Screens for the plumbing (Providers, Logs, Tools) |
| One-command install + "install with prompt" | Points at a Releases page that does not exist |
| Models are an implementation detail | Providers are the README headline |

**Lesson:** providers are our "models". Push them one layer down. The top layer is a
list of things you can get done (verticals + workflows), each producing a finished
result with receipts.

---

## 3. Findings

### 3.1 Honesty bugs (fix first - the repo's whole pitch is "receipts, no lies")

1. **Phantom MCP resource.** `webapp/src/pages/SkillsPage.tsx` states the skill is
   exposed as MCP resource `skill://super-search`. Nothing in `src/` registers any
   resource. Either register it or remove the sentence.
2. **Dead button.** The `super-search` card in SkillsPage is a `<button>` with no handler.
3. **Promise chain order bug.** SkillsPage: `.finally(...)` runs before `.catch(...)`,
   so loading clears before the error is set. Use `.then().catch().finally()`.
4. **README overclaims.** Hero sentence lists TVTropes and PubMed; "What You Can Do"
   lists memory vault and aiwatcher feed; "4 personalities" (ChatPage has 3 + Custom).
   None of the first four exist yet.
5. **Quick Install is a dead end.** "Download searchstudio-{version}.mcpb from Releases":
   no tags, no GitHub releases exist, and the built file is actually
   `dist/searchstudio-mcp-v0.1.0.mcpb`.
6. **`time_filter` is accepted and ignored** (echoed back as "informational"). The
   README's own first example prompt asks for "newest first". Silent no-op params are
   the same class of lie as silent zeros.

### 3.2 Architecture gaps that block the vision

1. **No intent routing / verticals.** Every query hits the same 5 providers.
   Restaurants and drug papers get the same treatment.
2. **Snippets only.** No step fetches page content. PRD non-goal "own page extractor" is
   fine, but some fetch path is needed (Tavily's own content, Jina Reader, or the
   fleet `fetch` MCP). Research workflows cannot work from 200-char snippets.
3. **No sampling.** No `ctx.sample()` anywhere: no query planning, no synthesis.
4. **No evidence persistence.** SQLite holds health rows only; nothing to cite later.
5. **Provider set is web-heavy.** Knowledge = Wikipedia only; fleet-local = arxiv-mcp only.

### 3.3 Hygiene

- **Four names for one thing:** repo `searchstudio-mcp`, package `super_search_mcp`,
  skill `super-search`, tool `searchops`, env prefix `SUPER_SEARCH_*`. Decision for
  Sandra (see section 6) - do NOT rename unilaterally.
- Uncommitted at time of writing: `docs/PRD.md` (untracked), `providers/wikipedia.py`
  (ruff-format reflow of the UA string only).
- The canonical fleet registry is `D:\Dev\repos\mcp-central-docs\operations\fleet-registry.json`
  (113 KB; searchstudio already has an entry). `opencode-cli-mcp\fleet-registry.json` is a tiny
  local copy - do not use it as the source for the fleet vertical.
- `operations/WEBAPP_PORTS.md` lists the backend as "FastAPI + MCP HTTP"; it is Starlette.
  Cosmetic, fix when next touching mcd.

### 3.4 README: is it opaque? Yes.

- First sentence is insider jargon (fan-out, pipes, receipts, fleet, crossconnects).
- ~40% of the page is a provider glossary. Useful, but belongs in docs/ONBOARDING.md.
- No input -> output example; example prompts are near the bottom.
- "Receipts" and "flakiness matrix" are never explained to a newcomer.
- The strongest pitch is buried: **search that tells you when it is failing you,
  instead of quietly returning nothing.**

---

## 4. Target architecture

```
query
  -> router            (rules first, LLM fallback; decision shown in receipts;
                        caller can force vertical=...)
  -> vertical plan     (providers, query rewrites/synonyms, sort, filters)
  -> fan-out           (EXISTING engine: parallel, receipts, health ledger)
  -> [fetch]           (optional: page content for top N, via provider content/Jina/fetch)
  -> [synthesize]      (optional: ctx.sample / local Ollama, with citations)
  -> result + receipts (receipts now also say: routed as X, time_filter honored by A,B
                        ignored by C, fetched N pages)
```

### Verticals (initial set)

| Vertical | Providers (keyless-first) | Notes |
|---|---|---|
| `web` | OpenSERP-local, DDG, Tavily | Exists today |
| `news` | Tavily (topic=news, time range), DDG with date filter, OpenSERP | Needs real `time_filter` |
| `academic` | Europe PMC or PubMed E-utilities, OpenAlex, Crossref, arxiv-mcp, Wikipedia | Synonym expansion; date sort both ways |
| `places` | Nominatim (geocode) + Overpass (OSM POIs), web for reviews | Nominatim policy: real User-Agent, max 1 req/s, cache results |
| `fleet` | mcp-central-docs/operations/fleet-registry.json, READMEs under D:\Dev\repos, mcp-central-docs, arxiv-mcp depot | Local only, never leaves the machine |
| `code` | GitHub search, PyPI/npm registries, StackExchange | Later |

**Check each API's current auth/rate-limit terms before implementing** (do not rely on
model memory; some keyless APIs have started requiring free keys).

### Tool surface (proposal)

- `searchops(operation="search", query, vertical="auto", ...)` - new default op.
  Keep `super_search` as a working alias (it becomes `vertical="web"`-ish fan-out).
- `researchops(operation=...)` - AI workflows, added ONE AT A TIME and only when they
  work end to end (repo rule: no stubs in the tool surface):
  - `skill_build` - first workflow, see section 5
  - `dossier` - deep research report with citations + gap list
  - `fact_check` - verdict, supporting vs contradicting sources, agreement level
  - `freshness` - "what changed since date X" (travelprep, aiwatcher consumers)
  - `landscape` - prior art / competitors for a new repo idea

---

## 5. First AI workflow: `skill_build`

Test case (use verbatim): **"find out everything about REAPER DAW and make a good
skill for an MCP server repo"**.

1. **Plan** (sampling): decompose into facets. For REAPER: official docs + ReaScript API
   (Lua / EEL2 / Python), OSC and web remote control, extensions (SWS, ReaPack,
   js_ReaScriptAPI), existing REAPER MCP servers (competition), versions and breaking
   changes, pitfalls from forum.cockos.com.
2. **Search** each facet via the router/verticals, with domain filters where useful
   (reaper.fm, forum.cockos.com, github.com). Receipts show which facets came back thin.
3. **Fetch** top N pages per facet.
4. **Store evidence**: (facet, claim/quote, url, fetched_at). New SQLite table. Dates
   from the real clock, never the model.
5. **Draft** (sampling) into a fixed SKILL.md template: frontmatter + triggers, API
   surface map, workflows, gotchas, version notes, sources.
6. **Verify**: every claim maps to stored evidence; unsupported claims are dropped or
   marked; thin facets listed explicitly ("no source found for X").
7. **Emit**: write the skill, surface it in the Skills page.

Differentiator: the skill ships with its own receipts - which claims are sourced and
which facets are thin. Almost no skill generator does that.

**Open overlap question (unverified):** memops exposes `adn_skillstudio` and
`make_skill_advanced`, and there is an Anthropic `skill-creator` skill. Likely clean
split: SearchStudio = research + evidence + verification, memops/skill-creator =
packaging. Confirm with Sandra before building step 7.

---

## 6. Decisions for Sandra (do not decide these unilaterally)

1. **Naming:** unify on `searchstudio` everywhere (package `searchstudio_mcp`, env
   `SEARCHSTUDIO_*`, skill `searchstudio`)? Recommended yes, and early, before
   consumers exist. It touches many files, so it needs its own multi-commit plan.
2. **Fetch path:** Jina Reader, fleet `fetch` MCP, or provider-native content only?
3. **LLM backends:** confirm the three-mode design in section 9.4 (sampling / server-side
   Ollama+API / host-driven) and the per-stage model tiering in 9.3.
4. **skill_build vs memops skillstudio** boundary (section 5).
5. **Research ownership:** searchstudio owns the fleet's one research engine; memops
   research tools become thin clients (section 9.5)? Recommended yes.
6. **Product surface:** "Infrastructure tier, no app" (PRD) vs "public repo strangers star".
   These pull against each other; decide whether the webapp becomes the app (section 8).

---

## 7. Work packages for opencode (in order)

Fleet rules apply to every package: max 5 files per commit, timestamped `.bak` before
editing 3+ files, ASCII-only prose (no em dashes), `just ci` green before each commit,
read the relevant `D:\Dev\repos\mcp-central-docs\standards\` files first (at minimum
`TOOL_DESIGN_STANDARDS.md` and `VERIFICATION_STANDARDS.md`).

### WP0 - Commit the stray state
- Commit `docs/PRD.md`, the `wikipedia.py` reflow, and this assessment + `HANDOVER.md`.
- Done when: `git status` clean.

### WP1 - Honesty fixes (section 3.1)
- Register the super-search skill as an MCP resource, OR remove the claim. To register it,
  copy the pattern from a fleet repo that already does it (e.g. arxiv-mcp or discord-mcp,
  which expose `skill://*/SKILL.md`) - do not invent one.
- SkillsPage: make the card non-interactive (div) or give it a real action; fix
  `.then().catch().finally()` order.
- ChatPage/README: make personality count and text agree.
- Done when: a test lists MCP resources and finds `skill://super-search` (if registered);
  `bun run biome:ci` / `tsc --noEmit` / pytest green.

### WP2 - `time_filter` for real
- Implement per provider where the API supports it (Tavily time range; DDG date param;
  others: check). Receipt gains `time_filter_applied: bool`.
- Unsupported providers: still run, receipt says the filter was not applied.
- Done when: mocked tests prove the param reaches the request for supporting providers
  and the receipt flag is correct for all.

### WP3 - README rewrite (section 3.4)
- Lead with the vision from section 1 and the four example queries.
- One real input -> output example with receipts (run it live, paste real output).
- A "Status" table: works today / in progress / planned. Nothing planned in the hero.
- Move the provider glossary to docs/ONBOARDING.md; README links to it.
- Quick Install: either cut a real GitHub release v0.1.0 (ask Sandra first - that is
  publishing) or replace with the working dev install from INSTALL.md.
- Done when: every claim in the README is true today.

### WP3b - Competitor read (before any new architecture)
- Read the code of `robbyczgw-cla/web-search-plus-mcp` (13 search + 6 extraction providers,
  routing diagnostics, research mode - closest to our concept, ~0 stars) and
  `Aas-ee/open-webSearch` (~1.3k stars, keyless multi-engine).
- Answer in `docs/COMPETITION.md`: how do they route, which providers, what do they do
  better, why has the closer one not taken off?
- Done when: the doc exists and WP4 design notes reference it.

### WP4 - Router + first new vertical (`places`)
- `router.py`: rules first (place words + known place, "paper/study/trial", "our repos",
  date words), returns (vertical, reason). LLM fallback can come later.
- `verticals/` with a plan per vertical; `web` wraps the current fan-out unchanged.
- Providers: `nominatim.py`, `overpass.py`. Real User-Agent, 1 req/s limit, cache.
- `searchops(operation="search", vertical="auto")`; `super_search` keeps working.
- **Migrate `backend.py` from Starlette to FastAPI in this package** (fleet standard reversed
  2026-09-30, see `mcp-central-docs/standards/STARLETTE_NO_PYDANTIC_STANDARD.md`). Why here:
  the router adds endpoints, research (WP8) adds nested request bodies and job status, and
  outside consumers (GPT Researcher adapter, aiwatcher, travelprep) need an OpenAPI spec
  and `/docs`. FastMCP already loads Pydantic (measured in this venv: pydantic 2.13.5),
  so the switch costs almost nothing. Define `SearchHit` / `ProviderReceipt` /
  `FanoutResult` as Pydantic models once and use them for both the MCP output schemas
  and OpenAPI. Keep the `/mcp` mount as documented (path="/", lifespan folded in;
  BUG-008, BUG-038) and prove it with a real MCP client call, not only startup.
  Separate commit, before the router wiring.
- Done when: mocked tests for router decisions and both providers; live manual check of
  "indian restaurants in Alsergrund" documented in the PR/commit body.
- Likely more than 5 files: split into router commit, providers commit, wiring commit.

### WP5 - `academic` vertical
- Providers: Europe PMC or PubMed E-utilities, OpenAlex, Crossref (check current terms).
- Query rewrite: synonyms (brand/generic/dev code) via simple table now, sampling later.
- Sort by date ascending when the query says first/earliest/original.
- Done when: "papers about the first sitagliptin meds" returns early trial papers first
  (live check documented), mocked tests green.

### WP6 - `fleet` vertical
- Index repo name + README first paragraph + registry metadata; plain local search.
- Never sends anything off-machine.
- Done when: "tell me about our robotics repos" lists the right repos (live check).

### WP7 - LLM layer + fetch + evidence store
- `llm.py`: one internal call `llm(stage, prompt, ...)`. Backends: `ctx.sample()`,
  Anthropic API, Ollama. A fallback order per stage is set in config (section 9.3). The
  current date is injected into every prompt from the real clock.
- Fetch path per decision 6.2; evidence table as in section 5 step 4.
- Depends on decisions 6.2 and 6.3.
- Done when: mocked tests prove the fallback chain (sampling unavailable -> Ollama ->
  API) and that each stage uses the backend configured for it.

### WP8 - Research loop + `researchops(operation="skill_build")`
- Research loop per section 9.2 (plan, search in parallel, read, compress, find gaps,
  repeat until the budget runs out or results stop adding anything, cite, verify).
- All three execution modes from section 9.4; host-driven mode needs a strict
  next-step contract and evidence kept on the server between calls.
- REAPER test case from section 5. Depends on WP7 and decisions 6.4/6.5.

### WP9 - `fact_check` (SAFE-style) and `freshness`
- `fact_check`: split the claim into single facts, search for each, give a verdict per
  fact plus an overall one.
- `freshness`: time-filtered research against a baseline date (for travelprep and
  aiwatcher).

---

## 8. Concept, competition and prospects

**Positioning:** the search layer for agents. Every field (web, places, academic, news,
your own fleet), never fails silently. Honest failure reporting is why people trust it;
the breadth of fields is the product; local/private sources treated as equals is what
makes it ours.

**Competition (checked 2026-09-30):**
- MCP search servers are small: open-webSearch ~1.3k stars, mcp-searxng ~840,
  web-search-plus-mcp ~0 (the closest to our concept, which shows the concept alone does
  not attract users).
- The layer next to us is big: Perplexica (~32k stars, open-source Perplexity, has
  "focus modes", a light form of our fields idea), GPT Researcher (plan -> parallel
  search -> scrape -> cited report, pluggable search backends), SearXNG (the meta-search
  engine many of these run on).
- The biggest threat is "good enough" built-in search in Claude, ChatGPT and opencode.
  Our pitch lands exactly where that fails, so the demo must show the failure and the
  rescue side by side.

**Why VoiceStudio's formula only partly carries over:**
- Voice components are hard to put together (models, weights, GPU), so bundling is
  valuable in itself. Search APIs are easy to wrap; our hard part is reliability,
  routing and quality, which are less visible.
- VoiceStudio's demo is visceral (hear your cloned voice). Ours must be too: built-in
  search says nothing, SearchStudio answers with sources and shows which providers
  were blocked. Or: REAPER skill built in 90 s from N sources.
- VoiceStudio is an end-user app; infrastructure MCP servers get used but not starred
  (decision 6.6).
- Voice models do not change under you; search endpoints do, constantly (DDG blocking,
  OpenSERP-Google is legally grey, Nominatim/Overpass usage policies). The health log
  turns that maintenance load into a feature.
- AI-assisted integration of scattered tools works (VoiceStudio shows it), but the moat is
  thin: anyone can repeat it. What protects us is being first with a good demo, keeping it
  maintained, and distribution.

**Prospects:** clearly worth it as fleet infrastructure (aiwatcher, travelprep, arxiv,
skill building all benefit). As a public repo, the default outcome is likely hundreds to
low thousands of stars. Breaking out needs the fields visibly working (the four example
queries with real output), one killer workflow, and a surface beyond MCP.

**Distribution idea:** get into them rather than competing. Build a SearchStudio search
backend for GPT Researcher, and one for SearXNG users.

---

## 9. Research, not just search

### 9.1 What memops has today (read 2026-09-30, advanced-memory-mcp)
- `research_orchestrator` (tools/research_orchestrator.py) does not research anything. Its
  "plan" is fixed text (`f"What is {topic} and how does it work?"`, `f'"{topic}"
  overview'`, a hardcoded list of sources to check) followed by "Next steps for Claude".
  No model plans and nothing runs.
- `make_skill_advanced._generate_research_queries` hardcodes stale years ("latest research
  developments 2024 2025", "new treatment options 2024"). This breaks the date-grounding
  rule; a fix task was filed separately.
- research_orchestrator output is full of literal `[UNICODE]` placeholders (left behind by
  an emoji-stripping sweep). Same fix task.
- The real part: `make_skill_advanced` `research_driven_skill` does search web, GitHub,
  arXiv and TVTropes and then calls sampling, but it plans with keyword rules, works from
  snippets only, and has no claim-to-source record.
- The one idea worth keeping: handing the plan back to the calling agent to carry out
  (section 9.4 mode 3).

### 9.2 Prior art to learn from
| System | Idea to take |
|---|---|
| Anthropic multi-agent research system (engineering write-up, 2025) | A lead agent plans and runs parallel sub-agents; each returns condensed findings, not raw pages; a separate citation pass at the end |
| GPT Researcher | Planner -> parallel researchers -> publisher; pluggable search backends |
| Stanford STORM / Co-STORM | Questions from several simulated expert viewpoints -> outline -> cited article; ideal for "find out everything about X" |
| Jina DeepSearch / node-DeepResearch | search -> read -> reason loop; each round asks "what is still missing?"; stops when the budget runs out or results stop adding anything |
| LangChain open_deep_research | Supervisor + sub-researchers; findings compressed between steps |
| DeepMind SAFE / FActScore | Split a long answer into single facts, check each with a search |

What they share, and memops lacks: a model does the planning, the loop repeats until
the gaps close, it reads whole pages rather than snippets, it keeps a claim-to-source
record, and verification is a separate step.

### 9.3 A different model tier for each step
| Step | Volume | Default backend |
|---|---|---|
| Query expansion, relevance filtering, pulling facts out of pages | High, low stakes | Local Ollama |
| Planning, finding gaps, final writing | Low, high stakes | Strong model (Fable/Opus via sampling or API) |
| Verification | Medium | A **different** model from the writer, so it does not just agree with itself |

### 9.4 Three execution modes (sampling with tools, SEP-1577, only works in Claude Desktop today)
1. **Sampling:** the host's model does the thinking. Best quality, no extra cost.
   Use it for short steps.
2. **The server uses its own models (Ollama / API key):** works in any IDE. Use it for
   long background runs (a research run makes dozens of model calls; a long chain of
   sampling round trips through the host is likely fragile). If the host supports MCP
   long-running tasks, use them instead of blocking one call.
3. **The calling agent does the thinking:** the server returns the plan plus the next
   step, the calling agent (e.g. opencode on DS4) does the reasoning and calls back. The
   evidence is kept on the server between calls.

The mode is picked at run time from the client's capabilities and the configuration.
All three use the same research loop and evidence store.

### 9.5 Ownership
One research engine for the fleet, in searchstudio: search, reading pages, evidence,
the research loop, verification. memops keeps storing results as notes and packaging
skills; its `adn_web_search` and research tools call searchstudio instead of keeping a
parallel engine (already in PRD Phase 3). Decision 6.5.

---

## Sources

VoiceStudio:
- https://github.com/debpalash/VoiceStudio
- https://www.besthub.dev/articles/voicestudio-local-first-open-source-voice-platform-for-cloning-dubbing-tts-8315f8ed2488
- https://ossinsight.io/analyze/debpalash/VoiceStudio

Competition (star counts from directory snapshots, not re-checked on GitHub):
- https://enterprisedna.co/directories/mcp/aas-ee-open-websearch
- https://enterprisedna.co/directories/mcp/ihor-sokoliuk-mcp-searxng
- https://enterprisedna.co/directories/mcp/robbyczgw-cla-web-search-plus-mcp
- https://github.com/rinaldowouterson/mcp-open-webresearch
- https://oosmetrics.com/repo/ItzCrazyKns/Perplexica
- https://learn.engineering.vips.edu/agent-protocols/gpt-researcher

The prior art in section 9.2 is named from model knowledge and has not been re-checked for
this doc; verify the current state of each before copying any design.
