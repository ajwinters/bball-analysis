---
title: Touches per foul
question: "How many touches does a player get per foul called in their favor (fouls drawn), and how does that change across seasons?"
status: active   # idea | active | done | dropped
created: 2026-11-09 19:10
tags: ["officiating", "players", "tracking-era"]
data: bballagg Postgres, run 2026-11-09 (boxscoreplayertrackv3_a, boxscoremiscv3_a, boxscoretraditionalv3_a, master_nba_games; regular season + playoffs 2013-14 to 2026-27)
---

# Touches per foul

## Question

How many touches does a player get per foul called in their favor (fouls drawn), and how does that change across seasons?

## Findings

## Notes

- Touches: `nba_boxscoreplayertrackv3_a.touches` (tracking era, 2013-14 on). Fouls drawn and committed: `nba_boxscoremiscv3_a.foulsdrawn` / `foulspersonal`. Zero-filled rows dropped with `bball.real`.
- The notebook can also count minutes, FGA or FGM per foul (from `nba_boxscoretraditionalv3_a`), over the same tracking-era games. Minutes are parsed from `MM:SS`; 191 of ~845k rows are garbled (`-3:00`, `0:0-18`) and count as null.
- League, regular season, 20+ games: ~12 minutes, ~4.0-4.8 FGA and ~2 FGM per foul drawn. Harden: ~5 minutes per foul drawn through 2019-20, 7-10 after.
- Fouls drawn include offensive fouls drawn on defense (charges), not only fouls on the player's own touches.
- League line pools all qualifying players (sum of touches / sum of fouls), not a mean of player ratios.
- First look: Harden goes from ~11-12 touches per foul drawn (2013-14 to 2019-20) to 16-23 from 2020-21 on, matching the 2021-22 "non-basketball move" rule change. LeBron drifts from ~13 to ~19-22. League sits around 20-22 every season.
