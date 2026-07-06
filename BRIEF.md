# DEUCE VALUE STRATEGY — Consolidated Brief

*Supersedes the earlier BRIEF.md / CHANGES.md / CHANGES-v2.md. One canonical spec.*

---

## 0. The thesis (what and why)

bet365 runs an in-play market: **will a deuce occur in the next two games?** The price looks
roughly fixed (commonly ~4/6) regardless of how the match is actually playing. But the real chance
of a deuce swings widely with how tight the service games are. Where our estimate of the true
deuce rate diverges from that fixed price, there's value. We estimate the rate live, bet the value
side manually on bet365, and stop when the match tells us we're wrong.

**The entire edge rests on one unproven assumption: that the price really is near-constant and
mispriced.** If it isn't — or if it quietly moves with the match favourite — there is no edge.
So the first task is not to build; it's to prove that (Phase 0).

---

## 1. The maths (reference)

- Single-game deuce probability: `d`. The next two games are ~one hold each, so:
  - `P(NO)  = (1 − d_A)(1 − d_B)`   (A serves next, B the game after)
  - `P(YES) = 1 − (1 − d_A)(1 − d_B)`
  - Early fallback (before per-server splits settle): `P(NO) = (1 − d)²` with match-level `d`.
- Theoretical rate from server point-win prob `p`: `d = 20·p³·(1 − p)³` (peaks ~31% at p=0.5,
  falls sharply as the server dominates). Used for the pre-match prior.
- Odds: fractional `a/b` → decimal `1 + a/b` → implied `b/(a+b)`. **4/6 = 1.667 = 60%.**
- EV of a bet at decimal `O` with win prob `P`: `EV = P·O − 1`.
- Break-even single-game rate at 4/6: **NO d < 22.5%**, **YES d > 36.75%**.
- With a 10% EV buffer at 4/6: **NO d < 18.8%**, **YES d > 41.7%**.

---

## 2. Architecture: four separate machines

| Machine | Question | Owns |
|---|---|---|
| **Estimation** | What's the true deuce rate *now*? | prior, windowing, shrinkage, floors |
| **Selection** | Is this a bet worth firing? | EV threshold + conviction filters |
| **Staking** | How much? | Kelly, taper, floors, caps |
| **Risk control** | When do we stop? | hysteresis, breaker, side-flip, match cap |

The golden rule: **selection may use raw observed rates, but estimation for EV and staking must
always use the shrunk/floored number.**

---

## 3. Estimation — getting `d`

1. **Pre-match prior.** `d = 20·p³·(1−p)³`, `p` from serve/return stats, surface-adjusted.
2. **In-match, windowed.** Rolling window (last 10 non-tiebreak games). Never cumulative.
3. **Shrinkage.** `d_est = (deuces + K·prior) / (games + K)`, `K ≈ 4`.
4. **Floor/ceiling.** `clamp(d_est, 0.08, 0.42)`.

---

## 4. Selection — which edges to act on

**Primary trigger:** `EV ≥ margin` (default 0.10) from shrunk d_est and live odds.

**Conviction filters (optional quality gate):**
- **Set 1** (≥8 games, cumulative): NO only if rate == 0%; YES only if > 50%.
- **Set 2+** (windowed): NO only if < 10%; YES only if > 40%.

---

## 5. Staking

- Quarter-Kelly (`0.25`), loss taper (`0.5^streak`), set-1 reduction (`×0.5`).
- `MIN_STAKE`, per-match loss cap. Stakes are advisory; bets placed by hand.

---

## 6. Risk control

- **Hysteresis:** fire on entry (EV ≥ 0.10); re-arm only after EV drops below 0.
- **Short-window veto:** 2+ deuces in last 6 games suspends NO.
- **Loss-streak breaker:** 3 consecutive losses halts that side.
- **Side-flip:** breaker halts only the losing side.

---

## 7. Data & tooling

- **Live:** API-Tennis `get_livescore`, poll ~20s.
- **bet365 stays manual.**

---

## 8. Build order

- Phase 0: Validate the market (log prices, confirm near-constant).
- Phase 1: Backtest & calibrate on historical data.
- Phase 2: Paper trade (log-only mode).
- Phase 3: Go live, small.
