"""Filters that keep only rows with real values.

The NBA API returns zero-filled rows for seasons before a stat was tracked, and
bballagg stores them. A plain AVG()/SUM() then mixes fake zeros with real ones.
Example (regular-season deflections per player-game): 2015-16 naive avg 0.20,
real rows only 1.51.

Use these in WHERE clauses:

    from bball import real
    sql = f"select ... from nba_boxscorehustlev2_a h where {real.where('boxscorehustlev2', 'h')}"

Copied from bballagg/notebooks/data_inventory.py (2026-10-31). bballagg has an open
issue (CLAUDE.md, Known issues 8) to store these as NULL instead; once that lands,
these filters can go.
"""

# endpoint (table name without the nba_ prefix and shard suffix) -> SQL condition.
# {a} is replaced with "alias." (or nothing).
REAL = {
    "boxscoretraditionalv3": "{a}minutes is not null and {a}minutes <> ''",
    "boxscoreadvancedv3": "{a}offensiverating <> 0",
    "boxscorefourfactorsv3": "{a}minutes is not null and {a}minutes <> ''",
    "boxscoremiscv3": "{a}minutes is not null and {a}minutes <> ''",
    "boxscorescoringv3": "{a}minutes is not null and {a}minutes <> ''",
    "boxscoreusagev3": "{a}minutes is not null and {a}minutes <> ''",
    "boxscoreplayertrackv3": "{a}distance > 0 or {a}touches > 0",
    "boxscorehustlev2": "{a}deflections > 0 or {a}contestedshots > 0",
}

# First season each stat group has real data (regular season). Fill in as checked.
FIRST_REAL_SEASON = {
    "boxscorehustlev2": "2016-17",
    "boxscoreplayertrackv3": "2013-14",
}


def where(table: str, alias: str | None = None) -> str:
    """SQL condition for real rows. Accepts 'boxscorehustlev2' or 'nba_boxscorehustlev2_a'.

    Tables without a known filter return '(true)'.
    """
    endpoint = table.removeprefix("nba_")
    if endpoint not in REAL and "_" in endpoint:
        endpoint = endpoint.rsplit("_", 1)[0]
    cond = REAL.get(endpoint, "true")
    return "(" + cond.format(a=f"{alias}." if alias else "") + ")"
