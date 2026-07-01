# BRIEF.md — Tennis "Deuce in Next Two Games" Live Scanner & Alerter

## 1. The bet & the edge

bet365 offers a rolling in-play market: **will a deuce occur in the next two games?**
(YES = at least one of the next two games reaches deuce; NO = neither does.) The price is roughly
fixed (commonly ~4/6 on one side) regardless of matchup. Edge: the true chance of a deuce depends
heavily on how tight the service games are, but the price doesn't move to match.

Goal: **monitor all live matches, and from the start of the second set, alert when a match is a value
YES or NO** — so you're not eyeballing dozens of concurrent matches by hand. You then confirm the
bet365 price and place the bet manually.

## 2. The maths

Let `d` = probability a single game reaches deuce. The next two games are almost always one hold from
**each** player, so use each server's own rate:

- P(NO)  = `(1 − d_A)(1 − d_B)`   (deuce_A next game, deuce_B the game after)
- P(YES) = `1 − (1 − d_A)(1 − d_B)`

Robust early-match fallback (before per-server rates settle): use the match-average `d` in
`P(NO) = (1 − d)²`, `P(YES) = 1 − (1 − d)²`. Note `1 − (1−d)² = 2d − d²`, **not** `2d`.

**Odds:** fractional `a/b` → decimal `1 + a/b` → implied `b/(a+b)`. So **4/6 = 60%** (not 66%).

**Decision rule (compute EV live, don't hard-code d):** with required safety margin `m`,

- Bet NO  when `P(NO)  · O_no  − 1 ≥ m`
- Bet YES when `P(YES) · O_yes − 1 ≥ m`

where `O_no`, `O_yes` are the live decimal odds on each side. **Default `m = 0.10`.**

**Buffered single-game thresholds at 4/6 (for intuition / sanity display):**

| EV buffer m | NO: bet when d < | YES: bet when d > |
|---|---|---|
| 0% (break-even) | 22.5% | 36.75% |
| 5% | 20.6% | 39.2% |
| **10% (default)** | **18.8%** | **41.7%** |
| 15% | 16.9% | 44.3% |

Formulae: NO `d < 1 − √((1+m)/O)`;  YES `d > 1 − √(1 − (1+m)/O)`.

## 3. Estimating d (per server, per match)

The in-match empirical rate is noisy: SE ≈ `√(d(1−d)/n)` (n=6 → ±17%). Mitigations, all baked in:

1. **Alert only from the second set.** By then a full first set (~6–13 games) has been observed, which
   tames the small-sample noise. Keep updating as the match grows.
2. **Pre-match prior** from serve/return stats: `d = 20·p³·(1−p)³`, `p` = server point-win prob
   (server SPW blended with returner RPW, surface-adjusted). Peaks (~31%) at p=0.5, falls for big servers.
3. **Shrinkage:** blend prior with in-match observations, weighted by games seen. Per-server rates are
   very sample-hungry (each player serves ~half the games), so lean on the prior for the A/B split and
   let the match-level rate calibrate the overall level.

## 4. Data / API layer (keep bet365 manual)

Do NOT scrape bet365 — automated access breaches T&Cs and trips anti-bot/limitation. Use a licensed
tennis API for detection; place bets by hand.

**Recommended providers (prototype on a free trial first):**

- **API-Tennis** (api-tennis.com) — live scores, point-by-point, in-play odds, WebSocket push;
  14-day trial; low-cost plans. Best fit for a solo build (push feed = no polling).
- **Goalserve** — point-by-point every 5s, pre-match + in-play odds; ATP/WTA/Challenger/ITF;
  30-day trial; entry ~$150/mo. Very complete (polling-based).
- **Tennis API / matchstat (RapidAPI)** — point-by-point, WebSocket on top plan, in-play odds
  (bet365 among sources), plus serve/return career stats for the prior; free + paid tiers.
- **Sportradar** — official, point-by-point, 4,000+ comps. Scale-up option; overkill to start.

**What you need from the feed:**
- List of all live events (to fan out across matches).
- Current game point-score (deuce = a game reaching 40-40) — available from live-score payloads;
  point-by-point/timeline as the definitive fallback. Deuce games sit at 40-40 long enough that even
  5s polling catches them.
- Who serves the next game (for A/B in the two-game formula).
- Serve/return stats per player/surface for the prior (same provider can supply this).

## 5. Architecture

- **Ingest:** WebSocket (preferred) or poll all live events.
- **State per match:** games played, deuce flags per game, per-server deuce counts, next server order,
  set number. Gate alerting on `set ≥ 2`.
- **Estimate:** d_A, d_B via prior + in-match shrinkage.
- **Value:** compute EV for YES and NO from live/assumed price with margin `m = 0.10`.
- **Alert:** push (Telegram bot / email / desktop) with match, servers, games seen, d_A/d_B, side,
  price used, EV, suggested stake. Debounce so you don't re-fire on every point.
- **You:** confirm real bet365 price, place bet manually. (If no live deuce-market price feed, alert
  states the assumed 4/6 and you verify on screen.)

## 6. Build phases

**Phase A — Backtest / calibration (first):** historical data (Jeff Sackmann `tennis_atp`/`tennis_wta`,
Match Charting Project). Fit the `p → d` prior, measure real deuce rates by surface/tour, simulate the
2-game bet at the fixed price, confirm the edge clears margin, walk-forward validate. Establish which
regime carries the edge and the right `m`.

**Phase B — Live scanner + alerter (second):** wire the API, per-match state, EV eval, alerts.

## 7. Outputs

- **Alert:** match, servers, games observed, d_A/d_B (with confidence), side, price, EV, stake.
- **Backtest report:** ROI, hit rate, edge by regime, sensitivity to assumed price, to `m`, and to the
  set-2 gate.

## 8. Staking & risk

- Fractional Kelly (¼ or less); unit caps; stop-loss.
- bet365 limits/gubs winning accounts fast on niche in-play markets — treat as a design constraint.
- Confirm the price really is near-constant, and record BOTH sides' prices.
- Feeds have a few seconds' latency and occasional corrections — fine here, but place between games.
- Gamble within your means.

## 9. Open decisions (for you)

- Provider: API-Tennis vs Goalserve for the prototype (budget vs coverage of lower tiers)?
- Alert channel: Telegram / email / desktop?
- Bet universe: ATP + WTA + Challengers + ITF, or a subset (softer lower-tier markets vs data quality)?
- Assume fixed 4/6, or verify the live price per alert?
