import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import altair as alt
    import marimo as mo
    import pandas as pd

    from bball import db, real

    return alt, db, mo, pd, real


@app.cell
def _(mo):
    mo.md("""
    # Touches per foul

    **Question:** How many touches does a player get per foul called in their favor
    (fouls drawn), and how does that change across seasons?

    Use **Per foul** to swap what is counted: touches, possessions, minutes, FGA, FGM,
    FTA or FTM.
    Lower = a foul comes more often. Sources: touches from player tracking
    (`boxscoreplayertrackv3`, 2013-14 on); possessions (on the floor) from
    `boxscoreadvancedv3`; minutes, FGA, FGM, FTA, FTM from `boxscoretraditionalv3`; fouls drawn
    and committed from `boxscoremiscv3`. Every option uses the same tracking-era games.
    Fouls drawn include offensive fouls drawn on defense (charges).
    """)
    return


@app.cell
def _(db, real):
    # One row per player, season, season type. Zero-filled (untracked) rows are dropped.
    seasons = db.query(f"""
        with g as (
            select distinct gameid, season, seasontype
            from master_nba_games
            where seasontype in ('Regular Season', 'Playoffs')
        )
        select g.season, g.seasontype, t.personid,
               max(t.firstname || ' ' || t.familyname) as name,
               count(*)                   as games,
               sum(t.touches)             as touches,
               sum(a.possessions)         as possessions,
               sum(case  -- 'MM:SS'; a few rows hold bare minutes; garbled ones -> null
                     when b.minutes ~ '^[0-9]+:[0-9]{{2}}$'
                       then split_part(b.minutes, ':', 1)::int
                            + split_part(b.minutes, ':', 2)::int / 60.0
                     when b.minutes ~ '^[0-9]+$' then b.minutes::int
                   end)::float8           as minutes,
               sum(b.fieldgoalsattempted) as fga,
               sum(b.fieldgoalsmade)      as fgm,
               sum(b.freethrowsattempted) as fta,
               sum(b.freethrowsmade)      as ftm,
               sum(m.foulsdrawn)          as fouls_drawn,
               sum(m.foulspersonal)       as fouls_committed
        from nba_boxscoreplayertrackv3_a t
        join g using (gameid)
        join nba_boxscoremiscv3_a m on m.gameid = t.gameid and m.personid = t.personid
        join nba_boxscoretraditionalv3_a b on b.gameid = t.gameid and b.personid = t.personid
        -- left join: the advanced "real" filter (offensive rating <> 0) would drop real
        -- low-minute games, so possessions are taken as-is
        left join nba_boxscoreadvancedv3_a a on a.gameid = t.gameid and a.personid = t.personid
        where {real.where("boxscoreplayertrackv3", "t")}
          and {real.where("boxscoremiscv3", "m")}
          and {real.where("boxscoretraditionalv3", "b")}
        group by 1, 2, 3
    """)
    seasons
    return (seasons,)


@app.cell
def _(seasons):
    # Player picker options: label -> personid, most career touches first, so the
    # names people search for are near the top. Duplicate names get their id added.
    _career = (
        seasons.sort_values("season")
        .groupby("personid")
        .agg(name=("name", "last"), touches=("touches", "sum"))
        .sort_values("touches", ascending=False)
    )
    _dup = _career["name"].duplicated(keep=False)
    _career["label"] = _career["name"].where(~_dup, _career["name"] + " (" + _career.index + ")")
    player_options = dict(zip(_career["label"], _career.index))
    return (player_options,)


@app.cell
def _(mo, player_options):
    _defaults = [
        n for n in ["LeBron James", "James Harden", "Stephen Curry"] if n in player_options
    ]
    players = mo.ui.multiselect(
        options=player_options,
        value=_defaults,
        label="Players (type to search and add, up to 8)",
        max_selections=8,
        full_width=True,
    )
    stat = mo.ui.dropdown(
        options={
            "Touches": "touches",
            "Possessions": "possessions",
            "Minutes": "minutes",
            "FGA": "fga",
            "FGM": "fgm",
            "FTA": "fta",
            "FTM": "ftm",
        },
        value="Touches",
        label="Per foul",
    )
    foul_type = mo.ui.dropdown(
        options={"Fouls drawn": "fouls_drawn", "Fouls committed": "fouls_committed"},
        value="Fouls drawn",
        label="Foul",
    )
    season_type = mo.ui.dropdown(
        options=["Regular Season", "Playoffs"], value="Regular Season", label="Season type"
    )
    min_games = mo.ui.slider(1, 82, value=20, label="Min games in season", show_value=True)
    show_league = mo.ui.checkbox(value=True, label="League average")
    mo.vstack(
        [
            players,
            mo.hstack([stat, foul_type, season_type, min_games, show_league], justify="start"),
        ]
    )
    return foul_type, min_games, players, season_type, show_league, stat


@app.cell(hide_code=True)
def _(foul_type, min_games, player_options, players, season_type, seasons, stat):
    _f, _v = foul_type.value, stat.value
    _s = seasons[
        (seasons["seasontype"] == season_type.value)
        & (seasons["games"] >= min_games.value)
        & (seasons[_f] > 0)  # x per 0 fouls is undefined
        & seasons[_v].notna()
    ]
    seasons_axis = sorted(_s["season"].unique())

    # League line: all qualifying players pooled (sum of stat / sum of fouls), not a mean of ratios.
    league = _s.groupby("season", as_index=False)[[_v, _f]].sum()
    league["per_foul"] = league[_v] / league[_f]

    _id_to_label = {pid: lbl for lbl, pid in player_options.items()}
    picked = _s[_s["personid"].isin(players.value)].copy()
    picked["player"] = picked["personid"].map(_id_to_label)
    picked["value"] = picked[_v]
    picked["fouls"] = picked[_f]
    picked["per_foul"] = picked["value"] / picked["fouls"]
    picked = picked[["player", "season", "games", "value", "fouls", "per_foul"]]
    return league, picked, seasons_axis


@app.cell(hide_code=True)
def _(
    alt,
    foul_type,
    league,
    mo,
    pd,
    picked,
    player_options,
    players,
    season_type,
    seasons_axis,
    show_league,
    stat,
):
    # Categorical palette, fixed order (dataviz reference palette, light mode).
    PALETTE = [
        "#2a78d6",
        "#eb6834",
        "#1baf7a",
        "#eda100",
        "#e87ba4",
        "#008300",
        "#6250d6",
        "#e34948",
    ]
    _id_to_label = {pid: lbl for lbl, pid in player_options.items()}
    _order = [_id_to_label[pid] for pid in players.value]
    _label = f"{stat.selected_key} per {foul_type.selected_key.lower().replace('fouls', 'foul')}"

    _x = alt.X("season:O", sort=seasons_axis, title=None, scale=alt.Scale(domain=seasons_axis))
    _y = alt.Y("per_foul:Q", title=_label, scale=alt.Scale(zero=False))
    _color = alt.Color(
        "player:N",
        scale=alt.Scale(domain=_order, range=PALETTE[: len(_order)]),
        title=None,
        legend=alt.Legend(orient="top"),
    )
    _tip = [
        alt.Tooltip("player:N", title="Player"),
        alt.Tooltip("season:O", title="Season"),
        alt.Tooltip("per_foul:Q", title=_label, format=".1f"),
        alt.Tooltip("value:Q", title=stat.selected_key, format=",.0f"),
        alt.Tooltip("fouls:Q", title=foul_type.selected_key),
        alt.Tooltip("games:Q", title="Games"),
    ]

    # Lines get a row for every season, null where a player didn't qualify, so the
    # line breaks instead of bridging the missing season.
    _grid = pd.MultiIndex.from_product([_order, seasons_axis], names=["player", "season"])
    _line = picked.set_index(["player", "season"]).reindex(_grid).reset_index()

    _hover = alt.selection_point(fields=["season"], nearest=True, on="pointerover", empty=False)
    _layers = []
    if show_league.value:
        _layers.append(
            alt.Chart(league)
            .mark_line(strokeDash=[4, 4], strokeWidth=1.5, color="#8a8a85")
            .encode(
                x=_x,
                y=_y,
                tooltip=[
                    alt.Tooltip("season:O", title="Season"),
                    alt.Tooltip("per_foul:Q", title=f"League {_label.lower()}", format=".1f"),
                ],
            )
        )
    _layers += [
        alt.Chart(_line)
        .mark_line(strokeWidth=2, invalid="break-paths-filter-domains")
        .encode(x=_x, y=_y, color=_color),
        alt.Chart(picked)
        .mark_point(filled=True, size=70, stroke="white", strokeWidth=2, opacity=1)
        .encode(x=_x, y=_y, color=_color, tooltip=_tip),
        # Invisible wide hit targets for the vertical crosshair.
        alt.Chart(picked).mark_rule(opacity=0, strokeWidth=24).encode(x=_x).add_params(_hover),
        alt.Chart(picked)
        .mark_rule(color="#8a8a85", strokeWidth=1)
        .encode(x=_x)
        .transform_filter(_hover),
    ]
    # Direct labels at each player's last season when there are few lines.
    if 0 < len(_order) <= 4:
        _last = picked.sort_values("season").groupby("player").tail(1)
        _layers.append(
            alt.Chart(_last)
            .mark_text(align="left", dx=8, fontSize=11, color="#555")
            .encode(x=_x, y=_y, text="player:N")
        )

    chart = alt.layer(*_layers).properties(
        title=f"{_label}, {season_type.value.lower()}",
        width="container",
        height=380,
    )
    mo.ui.altair_chart(chart) if _order else mo.md("_Add a player above to plot._")
    return (chart,)


@app.cell
def _(mo, picked, stat):
    # Table view of what's plotted.
    _name = stat.selected_key.lower()
    _t = picked.round({"value": 0, "per_foul": 1}).rename(
        columns={"value": _name, "per_foul": f"{_name}_per_foul"}
    )
    mo.accordion({"Data table": mo.ui.table(_t, selection=None)})
    return


if __name__ == "__main__":
    app.run()
