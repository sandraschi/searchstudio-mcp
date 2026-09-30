# SearchStudio — User Guide

Welcome to SearchStudio. This guide teaches the product through doing: short
tutorials for every job, real dialogues for every failure, and advanced
notes for developers wiring it into their own repos. No prerequisites beyond
an installed server and curiosity.

## Part 1 — First search (5 minutes)

**You:** "Super-search the AMD World Labs acquisition."

That's it. One sentence, no parameters. Behind it, five providers fire at
once: the fleet-local depot, Wikipedia, OpenSERP, DuckDuckGo, and Tavily (if
keyed). What comes back has two parts — learn to read both:

1. **Hits** — merged results, best kind first. Click through; snippets are
   provider-supplied claims, not verdicts.
2. **Receipts** — one line per provider: answered or blocked, how many hits,
   how slow. Green across the board means full coverage. A red line means
   that pipe was skipped — the results are partial, and the receipt says why.

Try a second query right away, something local and answerable: "Hollabrunn."
Wikipedia should answer with the town, the Napoleonic battle, the district.
The arxiv depot should stay silent (no preprints on Weinviertel history —
correct silence). Seeing a provider correctly find nothing builds the same
trust as seeing one find something.

Third query, a niche how-to: "best sourdough hydration percentage." Watch
the kinds complement each other: knowledge gives technique, serp gives
arguments. This is the product's shape — local first, curated second, web
third.

## Part 2 — Workflows

### Breaking news (mode=any, wide fan-out)

News under 48 hours old lives in exactly one index at first. Defaults still
work, but say the magic words: "newest first, any provider that answers."
Behind the scenes that is mode=any with full kinds. Expect single-provider
coverage and distrust unanimous silence — "nobody reports this yet" is a
finding about freshness, not falsehood. Re-run in a few hours; newly indexed
engines appear like tide coming in.

Example dialogue:

> You: "What are the reported terms of the AMD–World Labs deal, newest first?"
> SearchStudio: 6 hits (2 Tavily, 3 OpenSERP-google, 1 DDG). Wikipedia silent
> (too new for the encyclopedia — correct). Receipts: arxiv-mcp ok/0 (no
> preprints on M&A — correct), OpenSERP-bing blocked (rate limit, normal).
> Answer leads with the reported $8B figure flagged as *reported*, notes the
> expected January close as *announced, not closed*, and lists which pipes
> contributed. That last sentence is the difference between an answer and
> evidence.

### Shopping and comparing (limit up, receipts on)

"Compare robot vacuum lidar vs camera navigation, more results." Raise the
limit (20–30) — comparison needs breadth. Read across providers deliberately:
Tavily ranks AI-clean, DDG surfaces forums and Reddit threads where owners
complain, Wikipedia gives the technology baseline. The truth is usually the
intersection: what the encyclopedia explains, owners confirm, and reviewers
measure. When providers disagree, say so and name who said what — merged
results are not consensus.

### Debugging the fleet (provider_health first)

"Which providers are healthy right now?" Ask this *before* promising
coverage, and *after* any outage. The scoreboard shows success rate, p50
latency, and blocks per provider over 24 hours. Zero attempts anywhere
means nobody has searched today — run a search before concluding anything.
A provider at 0% with connection errors is transport (Docker? sibling up?);
at 100% blocked it is engine-side (backoff, switch providers, try later).

### Travel freshness (time-sensitive, narrow providers)

"Any travel advisories for Japan this week?" Freshness beats breadth here:
prefer serp kinds, short queries, and re-query on demand rather than caching
conclusions. Advisories change daily. Note the query date in your reasoning
("as of 2026-09-30") — temporal grounding is a fleet hard rule for exactly
this reason. When the answer matters (visas, safety), follow the link to the
primary source; snippets are leads.

### Academic digging (fleet-local first)

"Find preprints on mechanistic interpretability." The fleet-local depot
(arXiv fan-out) leads; Wikipedia frames; serp adds blogs and commentary.
For exact papers, quoted titles work best. For surveys, ask for the survey
 explicitly ("survey papers on…") — keyword soup returns fragments, not maps.
Check sibling health when fleet-local is silent: the depot can only serve
what its own backends index.

### Trivia night (knowledge first)

"Is Naruto a bald guy?" Wikipedia answers (no — spiky blond; the confusion
is probably Krillin). TVTropes queries arrive via crossconnect in Phase 2;
until then, knowledge + serp cover trivia fine. Trivia is the lowest-stakes
way to learn receipts: watch which pipes answer silly questions fastest.

## Part 3 — When it breaks (dialogues)

**"Search returned nothing at all."**

> You: "Super-search quantum teapots."
> SearchStudio: 0 hits. Receipts: openserp-local failed ("unreachable —
> is Docker Desktop running?"), arxiv-mcp failed (sibling down), Tavily
> unconfigured, Wikipedia ok/0, DDG blocked.
> Reading: nothing was searched except Wikipedia (which genuinely has no
> quantum teapots). Start Docker, retry. The emptiness was transport, not
> truth. If all receipts had been ok with 0 hits, *then* "doesn't exist"
> becomes sayable — and even then, say which pipes agreed.

**"One provider always fails."**

> OpenSERP-google blocked three runs in a row while bing answers. Normal.
> Engines judge your IP independently per minute; the identity of the
> blocked engine rotates. The provider tries engines in order and reports
> the last error — read it, don't fight it. If google is persistently
> blocked for days, your IP reputation needs a rest (or a proxy pool, which
> is a Cloud-customer problem, not yours).

**"Tavily says not configured."**

> Expected without a key — it is a setup hint, not an error. Free key at
> tavily.com (1k calls/month, no card), set TAVILY_API_KEY in env, restart
> the backend. Keyless providers keep working meanwhile; nothing is gated
> behind the key.

**"It's slow."**

> Per-provider 20s timeouts, 8s connect cap; the slowest blocked provider
> sets the floor. Receipts show who. Narrow kinds (drop serp for local
> questions), lower limit, or mode=any to take the fastest kind with hits.
> Chronic slowness from one provider with ok=true is usually that provider's
> upstream, not us — the ledger quantifies it over days.

**"Results look stale."**

> Check the published stamps on hits (when providers supply them). For
> freshness-critical queries, say "newest first" (mode + recency wording)
> and prefer Tavily/engines over the depot and Wikipedia. Breaking news
> takes hours to propagate across indexes — re-run later rather than
> assuming silence.

**"The answer contradicts itself."**

> Good — that means providers disagree and merging preserved the
> disagreement instead of averaging it away. Attribute per provider, prefer
> primary sources (papers, official docs, data) over commentary, and say
> "sources differ" out loud. A search tool that hides disagreement is a
> rumor mill with receipts.

## Part 4 — Advanced (developers, agents, crossconnects)

**Calling from another MCP server:** HTTP POST-equivalent via GET
`/api/search?q=&kinds=&providers=&limit=&mode=`, or MCP `searchops` over
the `/mcp` endpoint. Keep client timeouts short (10–15s) and treat total
failure as "fall back to current behavior," never as an error to surface.
One hop only: SearchStudio never calls back into consumers, so cycles are
structurally impossible.

**aiwatcher pattern:** kinds=serp, limit=5, mode=any. Hits are leads for
the distillation pipeline; receipts are confidence. Total failure keeps
RSS-only behavior. Register the companion snippet and /apps badge.

**travelprep pattern:** time-sensitive queries, provider allowlists, limit
10, aggressive client-side caching (advisories change daily). Re-query on
user request, never on a timer.

**memops delegation (Phase 3):** route provider=auto to super_search,
preserving response shape. Research chains inherit receipts — provenance
for free. Coordinate rollout; blast radius is the whole memory pipeline.

**Adding a provider (future you):** one module under providers/ honoring
the (hits, receipt) contract and the (query, limit=...) keyword-callable
signature (the dispatch test enforces it), register in the provider list,
add the scoreboard entry automatically via the ledger, document the key or
courtesy policy, add a row to the webapp provider cards. No fan-out changes
needed — the engine is kind-agnostic by design.

**Running the matrix:** Providers page → "Run flakiness matrix," or
self_test op. Three canonical probes, per-provider counts and failures.
Interesting rows go to the fleet incident log (patterns doc). Run after
Docker restarts, new keys, new providers, and quarterly for the record.

## Part 5 — FAQ

**Do I need Docker?** Only for OpenSERP-local. Everything else works without it.

**Do I need any API key?** No. Keys unlock Tavily (and later Exa/Brave); keyless covers web, knowledge, and fleet-local fully.

**Why did the same query give different results twice?** Independent bot-luck per engine per minute, plus index churn. Fan-out narrows the variance; it cannot eliminate it. The matrix quantifies your personal variance — run it.

**Can I trust a single-provider answer?** Provisionally. Ask for a second provider explicitly ("same query, Wikipedia only, then serp only") when it matters.

**Does SearchStudio store my queries?** The health ledger stores provider, timestamp, counts, and latency — never query text. Your questions stay yours.

**Why no AI answers, just links?** Condensing arrives in Phase 3 (local-first, cloud opt-in). Phase 1 optimizes the unglamorous foundation: every pipe answering, every gap declared. Answers built on hidden gaps are the thing we're eliminating.

**Who do I tell about a broken provider?** The receipts already told us (ledger). For persistent breakage, file it with timestamps from the Providers page — "google blocked since Tuesday" beats "search feels off."

## Part 6 — First week curriculum (guided exercises)

Do one per day. Each takes ten minutes and teaches one muscle.

**Day 1 — receipts literacy.** Search anything. Before reading hits, read receipts only: which providers answered, latencies, counts. Predict the result quality from receipts alone, then check. Repeat with three queries. Goal: receipts-first becomes reflex.

**Day 2 — kind scoping.** Same query three times: kinds=all, kinds=serp, kinds=knowledge. Compare what each kind uniquely contributes. Learn which questions are local-shaped (fleet topics), knowledge-shaped (entities, techniques), serp-shaped (news, opinions, products).

**Day 3 — provider allowlists.** Same query with providers=wikipedia vs providers=duckduckgo vs providers=tavily (if keyed). Notice ranking differences: encyclopedic vs forum-flavored vs AI-ranked. Notice failure differences: which degrades gracefully, which errors loudly.

**Day 4 — breaking news drill.** Pick a story under 48h old. Search with mode=balanced, then mode=any. Count contributing providers. Re-run in the evening; count again. Watch coverage arrive in real time and learn what "too new to be indexed" looks like — the most misread search outcome there is.

**Day 5 — health and matrix.** Open Providers, read every card. Run the flakiness matrix. Screenshot the scoreboard (mental or literal). This is your baseline; every future "search feels off" gets compared against it instead of vibes.

**Day 6 — failure injection.** Stop Docker (or disconnect network briefly). Search. Read the receipts: the outage should be *named* (unreachable, which service, what to check). Restart, re-run, confirm green. You now trust the failure paths because you have seen them work.

**Day 7 — teach it.** Explain receipts, kinds, and modes to someone (or write it down). Teaching is the retention test; whatever you fumble is tomorrow's re-read.

## Part 7 — Getting the most from each provider

**arxiv-mcp (fleet-local).** Best for: anything the fleet itself knows — preprints, methods, papers. Query like a researcher: keywords over titles/abstracts, quoted exact titles for known papers. It returns author-prefixed snippets with published stamps — sort newest-first for fast fields, relevance for settled ones. When it returns nothing, check whether its backend is up before concluding the topic is uncovered; a down sibling looks identical to an empty field except in receipts. Follow arXiv links for PDFs; follow DOI links for published versions.

**Wikipedia.** Best for: entities, places, techniques, history, definitions. Query the noun ("Hollabrunn", "lidar", "Treaty of Versailles"), not the question — search matches titles best, and the intro extract answers most questions in three sentences. Use it to frame unknowns fast, then spend serp effort on what Wikipedia omits (opinions, news, edge cases). Never cite it; always mine its references — the real value is the bibliography at the bottom, which search snippets never show. Open the article for those.

**OpenSERP-local.** Best for: broad web coverage with engine choice. When results skew, remember engines differ: Google for mainstream, Bing for Microsoft-ecosystem and some international content, Yandex for Russian-language and regional freshness, Baidu for Chinese-language, Ecosia as an independent-failure-domain spare. Short keyword queries beat sentences here. If all engines fail at once, suspect Docker/transport first (receipts say so explicitly) — engine blocking is almost always partial, never unanimous.

**DuckDuckGo.** Best for: unfiltered breadth, forums, and independence from Google-index thinking. Short plain queries; DDG truncates and mangles long natural language. Privacy posture is a bonus, not the point here — the point is a second opinion from a different index and different bot-luck. When DDG is the *only* engine answering, say so: single-source answers get provisional trust only.

**Tavily (keyed).** Best for: hard questions needing AI-ranked relevance, and freshness (topic=news queries). Write full natural-language questions, not keywords — it was built for LLM-shaped input. Scores are Tavily-native; never compare them with other providers' orderings. Free tier is 1k/month: spend it on questions where ranking quality matters (research, shopping, decisions), not on navigational lookups a keyless pipe answers free. Watch usage in the Providers scoreboard by volume over weeks, not per query.

## Part 8 — Power patterns (weekly habits)

**Monday sweep:** run provider_health, glance at success rates. Anything below 50% for a week gets investigated (transport? key expired? engine permanently blocking?). This five-minute ritual is the entire maintenance program for most users.

**Research flows (multi-query):** hard questions decompose. First query broad (map the space, all kinds), second query narrow per promising thread (kind-scoped), third query adversarial ("criticism of X", "X limitations", "X vs Y"). Never accept the first result set as the whole picture on decisions that matter — the fan-out gives breadth, but depth is the caller's job.

**Scripted sweeps:** the same question on a schedule (new papers on X weekly, price checks, advisory watches). Cache results client-side with timestamps; re-query on schedule, diff against last time, report only changes. SearchStudio is stateless by design — the schedule and the memory live with the caller (aiwatcher and travelprep do exactly this).

**Source triangulation:** for any claim that will be repeated (docs, posts, decisions), confirm across kinds: fleet-local or knowledge for the baseline, serp for corroboration, primary source via followed link for the citation. One-kind confirmation is a lead; two-kind is evidence; primary-source is citable. Say which level each claim reached.

**Receipts journaling:** when something important fails (deadline research, incident response), save the receipts alongside the answer. "Searched 2026-09-30, Tavily + Wikipedia answered, OpenSERP blocked" is provenance that survives the week — and it is what turns a chat answer into an auditable finding.

## Part 9 — Migrating from raw Google habits

If your current workflow is "open google.com, type, click," here is the translation:

- **The search box is the same; the reading is new.** Hits work like always. Receipts are the new muscle — ten seconds per search, worth it forever.
- **Stop opening twelve tabs to compare engines.** That was manual fan-out. One query now does it, with deduplication and latencies attached.
- **"No results" used to mean "try different words."** Now read receipts first: no results with failed pipes means retry the pipes, not the words. Only rephrase when all pipes answered and found nothing.
- **Bookmarks become allowlists.** Your "check these three sites" habit becomes providers= or kinds= parameters. Same selectivity, zero tab management.
- **Freshness anxiety ("is this current?")** gets a real answer: published stamps on hits, recency wording in queries, re-runs over hours for breaking stories. The tool shows its work; make showing yours a habit too.

You are done with the guide when receipts-first feels obvious. Go search something fresh.

## Part 10 — Full worked sessions (watch the method, not just the answers)

**Session A: "Is my Docker setup the reason search is empty?"**

> You: "Super-search LiDAR object detection survey, limit 20."
> SearchStudio: 0 hits. Receipts: openserp-local failed ("unreachable — is Docker Desktop running?"), arxiv-mcp failed (sibling down), Tavily unconfigured, Wikipedia ok/0, DDG blocked.
> You (reading receipts, not rephrasing): two transports down, one stub, one genuine empty, one blocked. This is not a query problem.
> You: check Docker Desktop — not running. Start it, wait for the engine, confirm the openserp container on :7000. Check the sibling backend — restart it.
> You: re-run the identical query.
> SearchStudio: 17 hits. Wikipedia: survey-adjacent overviews. arxiv-mcp: three recent preprints with published stamps. OpenSERP-google: blogs, GitHub repos, a benchmark table. DDG: two forum threads with practitioner complaints. Tavily: stub receipt (still keyless — fine).
> You: read the preprints for methods, the benchmark for numbers, the forums for failure modes. Answer cites all three strata and notes Tavily-shaped AI ranking as the missing (unkeyed) perspective.
> Lesson: the fix was infrastructure, the query never changed, and receipts told you that in ten seconds. A single-engine user would have rephrased five times and blamed the topic.

**Session B: "Which robot vacuum navigation is actually better?"**

> You: "Super-search robot vacuum lidar vs camera navigation comparison, limit 25."
> SearchStudio: 24 hits. Receipts all green except OpenSERP-yandex blocked (normal Tuesday).
> Pass 1 (map): Wikipedia gives the technology baseline (how each navigation family works). Skim for vocabulary: SLAM, VSLAM, structured light, cliff sensors.
> Pass 2 (measure): Tavily top hits (AI-ranked) point to two detailed comparison reviews with test methodology. Open with skepticism — reviews monetize via affiliate links; note that bias out loud.
> Pass 3 (lived experience): DDG surfaces owner threads ("lidar blind in black furniture hell", "camera needs light, useless under beds"). These contradict the reviews' neatness — keep both, attribute both.
> Pass 4 (adversarial): "robot vacuum lidar limitations problems" and separately "camera navigation failures." Confirm the failure catalog from pass 3 with independent sources.
> Answer shape: baseline (Wikipedia) → measured claims (reviews, bias-flagged) → lived contradictions (forums, attributed) → verdict conditional on the asker's home ("dark rooms and black furniture: lidar; bright open plan on a budget: camera is fine"). Every claim carries its stratum. Nothing is averaged; disagreement is preserved and labeled.
> Lesson: comparison shopping is the fan-out's home game — breadth across strata beats depth in one index, and the method (map, measure, experience, adversarial) transfers to every "which X is better" question you will ever ask.

## Part 11 — The ten commandments (tape to monitor)

1. Read receipts before hits.
2. Empty + failed pipes means nothing was searched. Empty + all green means genuinely nothing found.
3. Name exclusions out loud whenever results inform a decision.
4. Breaking news gets wide fan-out and provisional trust, never verdicts.
5. Snippets are claims from URLs, never facts. Follow links for load-bearing answers.
6. Scores don't cross providers. Order within, never between.
7. One engine failing is Tuesday. All failing is transport — check Docker, sibling, network, in that order.
8. Re-run breaking stories over hours; indexes arrive like tide.
9. Spend paid calls on hard questions, keyless on everything else.
10. A search tool that explains its gaps beats a cleverer one that hides them — hold us to that, and hold yourself to reading the gaps.

## Part 12 — Setup walkthroughs (every provider path, end to end)

**OpenSERP-local (Docker).** Install Docker Desktop (winget: Docker.DockerDesktop). Verify virtualization is enabled in BIOS first — without it the engine can never start, and every symptom looks like a search bug instead. Launch Docker Desktop, wait for the engine (a minute or two on cold boot), then start the openserp container bound to 127.0.0.1:7000 with restart-unless-stopped. Verify with a plain browser or curl call to /google/search?text=test&limit=1 — one JSON result means the pipe is live. Then run a SearchStudio query and confirm the openserp-local receipt flips to ok. Pull the image monthly (restart recreates the container, never the image — an old image fights last year's bot defenses). If results degrade over weeks with no config change, pull first, theorize second.

**Tavily key.** Sign up at tavily.com (free tier, 1k calls/month, no card). Copy the key into the TAVILY_API_KEY environment variable — host config or local .env, never the repo, never chat. Restart the backend (running processes cannot adopt new env). Verify on the Providers page or via provider_health: tavily flips from "not configured" to ready. Spend strategy from day one: keyless pipes for breadth and navigational lookups, Tavily for questions where ranking quality decides (research, comparisons, decisions). At 1k/month, that discipline lasts; indiscriminate routing burns it in days.

**arxiv-mcp sibling.** Clone and start the sibling backend on :10770 per its INSTALL (or confirm the fleet instance is already running — check its /api/health). Set ARXIV_MCP_BASE_URL if yours differs. Verify with a fleet-local-only query ("diffusion transformers") — hits with paper IDs and published stamps mean the crossconnect is live. When fleet-local returns nothing, check the sibling's health before concluding the topic is uncovered; a down sibling and an empty field look identical except in receipts, and only receipts tell them apart.

**Ollama chat.** Install Ollama, pull any chat model (qwen3:8b is a fine start on modest hardware), confirm :11434 answers. Open the Chat page: the model field should auto-fill resident-first (already-loaded models win — no cold reload), the skill line should read skill:super-search, personalities should switch the system prompt visibly. No model means a clear "Ollama down" assistant message, never a fake reply. Chat is local-first by doctrine: cloud LLMs are opt-in later, never the default path.

**Full-stack verification (ten minutes, do once).** Backend /api/health green with all expected providers listed. Webapp Dashboard shows provider cards; Settings shows key states. One query per kind (fleet-local: a methods topic; knowledge: a place name; serp: a news topic) with receipts read each time. Flakiness matrix run once for the baseline screenshot. Ollama chat round-trip. When all of that passes, the installation is proven — not installed, proven. Anything failing points at exactly one setup walkthrough above; fix that section, re-run its verification, move on.

## Part 13 — Outgrowing this guide (what's next)

**File incidents, not vibes.** "Search feels off" helps nobody; "OpenSERP-google blocked since Tuesday, receipts attached" fixes things. The Providers page gives timestamps, the matrix gives reproduction. Good incident reports are the project's immune system — the flakiness log in the fleet docs is built entirely from reports like yours.

**Request providers with evidence.** "Add Exa" is a wish; "Exa covers neural queries Tavily mangles — here are three queries where keyless pipes fail and Exa's demo answers" is a specification. The provider interface is one module plus registration; evidence-driven requests get built, wishes get roadmapped.

**Wire a consumer.** Got a repo that needs fresh facts (advisories, prices, papers, docs)? The crossconnect cookbook in the system prompt has the patterns; the travel freshness template is the worked example. One hop, soft degradation, receipts flowing downstream. Consumers are how an aggregator proves it aggregates.

**Star and share honestly.** If SearchStudio earned it — a star, a post, a demo of receipts catching a dead pipe live. The honest demo converts better than any feature list: run a query with Docker stopped, show the receipts naming the outage, start Docker, re-run green. That ten-second arc is the whole product thesis in miniature: never silent, always receipted.

**Stay current cheaply.** Pull the OpenSERP image monthly. Glance at provider_health Mondays. Re-run the matrix quarterly. Total maintenance: minutes per month. The product does the worrying about the arms race; your job is just not running February's binary in September.

## Appendix — Quick reference card

- `super_search(query)` — ask anything; add `kinds=` to scope, `providers=` to allowlist, `limit=` 1–50, `mode=any` for fastest-kind-wins.
- `provider_health` — who is up, who is blocked, p50s. Read before promising coverage.
- `self_test` — three probes, full receipts. Run after infra changes.
- Empty + failed receipts = nothing searched. Empty + all green = genuinely nothing found.
- One red pipe = name it and continue. All red = transport; check Docker, sibling, network.
- Tavily unconfigured = setup hint, not error. Keys in env, never in chat or repo.
- Breaking news: fan out wide, trust provisionally, re-run over hours.
