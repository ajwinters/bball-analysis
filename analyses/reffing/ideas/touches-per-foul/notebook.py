import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import warnings

    import altair as alt
    import marimo as mo
    import pandas as pd

    from bball import db, real

    return alt, db, mo, pd, real, warnings


@app.cell
def _(mo):
    mo.md("""
    # Touches per foul

    **Question:** How many touches does a player get per foul called in their favor
    (fouls drawn), and how does that change across seasons?

    Pick what to count per foul: touches, minutes, field goal attempts or makes.
    Lower = a foul comes more often. Touches come from player tracking
    (`boxscoreplayertrackv3`, 2013-14 on); minutes, FGA and FGM from
    `boxscoretraditionalv3`; fouls drawn and committed from `boxscoremiscv3`.
    Every stat uses the same games (tracking era), so the options are comparable.
    Fouls drawn include offensive fouls drawn on defense, so charge-takers look
    better than their touches alone would suggest.
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
               count(*)                as games,
               sum(t.touches)          as touches,
               sum(m.foulsdrawn)       as fouls_drawn,
               sum(m.foulspersonal)    as fouls_committed,
               sum(case  -- 'MM:SS'; a few rows hold bare minutes; garbled ones -> null
                     when b.minutes ~ '^[0-9]+:[0-9]{{2}}$'
                       then split_part(b.minutes, ':', 1)::int + split_part(b.minutes, ':', 2)::int / 60.0
                     when b.minutes ~ '^[0-9]+$' then b.minutes::int
                   end)::float8        as minutes,
               sum(b.fieldgoalsattempted) as fga,
               sum(b.fieldgoalsmade)   as fgm
        from nba_boxscoreplayertrackv3_a t
        join g using (gameid)
        join nba_boxscoremiscv3_a m on m.gameid = t.gameid and m.personid = t.personid
        join nba_boxscoretraditionalv3_a b on b.gameid = t.gameid and b.personid = t.personid
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
    stats = mo.ui.multiselect(
        options={"Touches": "touches", "Minutes": "minutes", "FGA": "fga", "FGM": "fgm"},
        value=["Touches", "Minutes", "FGA", "FGM"],
        label="Per foul (one panel each)",
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
            mo.hstack([stats, foul_type, season_type, min_games, show_league], justify="start"),
        ]
    )
    return foul_type, min_games, players, season_type, show_league, stats


@app.cell(hide_code=True)
def _(foul_type, min_games, pd, player_options, players, season_type, seasons, stats):
    STAT_NAMES = {"touches": "Touches", "minutes": "Minutes", "fga": "FGA", "fgm": "FGM"}
    _f = foul_type.value
    _s = seasons[
        (seasons["seasontype"] == season_type.value)
        & (seasons["games"] >= min_games.value)
        & (seasons[_f] > 0)  # x per 0 fouls is undefined
    ]
    seasons_axis = sorted(_s["season"].unique())
    _id_to_label = {pid: lbl for lbl, pid in player_options.items()}
    _picked = _s[_s["personid"].isin(players.value)]

    # Long format: one row per (player or league, season, stat).
    _rows, _league = [], []
    for _v in stats.value:
        _p = _picked[_picked[_v].notna()]
        _rows.append(
            pd.DataFrame(
                {
                    "player": _p["personid"].map(_id_to_label),
                    "season": _p["season"],
                    "games": _p["games"],
                    "stat": STAT_NAMES[_v],
                    "value": _p[_v],
                    "fouls": _p[_f],
                    "per_foul": _p[_v] / _p[_f],
                }
            )
        )
        # League: all qualifying players pooled (sum of stat / sum of fouls), not a mean of ratios.
        _l = _s[_s[_v].notna()].groupby("season", as_index=False)[[_v, _f]].sum()
        _league.append(
            pd.DataFrame(
                {"season": _l["season"], "stat": STAT_NAMES[_v], "per_foul": _l[_v] / _l[_f]}
            )
        )
    _cols = ["player", "season", "games", "stat", "value", "fouls", "per_foul"]
    picked = pd.concat(_rows) if _rows else pd.DataFrame(columns=_cols)
    league = pd.concat(_league) if _league else pd.DataFrame(columns=["season", "stat", "per_foul"])
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
    warnings,
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
    _foul = foul_type.selected_key.lower().replace("fouls", "foul")
    _panels = list(dict.fromkeys(picked["stat"]))  # stats in picker order
    _single = len(_panels) == 1

    _x = alt.X("season:O", sort=seasons_axis, title=None, scale=alt.Scale(domain=seasons_axis))
    _color = alt.Color(
        "player:N",
        scale=alt.Scale(domain=_order, range=PALETTE[: len(_order)]),
        title=None,
        legend=alt.Legend(orient="top"),
    )

    # One hover param shared by all panels: hovering a season marks it everywhere.
    # Altair warns when it merges the copies across panels; that merge is the point.
    warnings.filterwarnings("ignore", message="Automatically deduplicated selection")
    _hover = alt.selection_point(
        name="season_hover", fields=["season"], nearest=True, on="pointerover", empty=False
    )

    def _panel(name):
        _d = picked[picked["stat"] == name]
        # Lines get a row for every season with a null value where a player didn't
        # qualify, so the line breaks instead of bridging the missing season.
        _grid = pd.MultiIndex.from_product([_order, seasons_axis], names=["player", "season"])
        _line = _d.set_index(["player", "season"]).reindex(_grid).reset_index()
        _label = f"{name} per {_foul}"
        _y = alt.Y("per_foul:Q", title=_label, scale=alt.Scale(zero=False))
        _tip = [
            alt.Tooltip("player:N", title="Player"),
            alt.Tooltip("season:O", title="Season"),
            alt.Tooltip("per_foul:Q", title=_label, format=".1f"),
            alt.Tooltip("value:Q", title=name, format=",.0f"),
            alt.Tooltip("fouls:Q", title=foul_type.selected_key),
            alt.Tooltip("games:Q", title="Games"),
        ]
        _base = alt.Chart(_d).encode(x=_x, y=_y, color=_color)
        _layers = []
        if show_league.value:
            _layers.append(
                alt.Chart(league[league["stat"] == name])
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
            _base.mark_point(filled=True, size=60, stroke="white", strokeWidth=2, opacity=1).encode(
                tooltip=_tip
            ),
            # Invisible wide hit targets for the vertical crosshair.
            alt.Chart(_d).mark_rule(opacity=0, strokeWidth=24).encode(x=_x).add_params(_hover),
            alt.Chart(_d)
            .mark_rule(color="#8a8a85", strokeWidth=1)
            .encode(x=_x)
            .transform_filter(_hover),
        ]
        # Direct labels at each player's last season: single wide panel, few lines only.
        if _single and len(_order) <= 4:
            _last = _d.sort_values("season").groupby("player").tail(1)
            _layers.append(
                alt.Chart(_last)
                .mark_text(align="left", dx=8, fontSize=11, color="#555")
                .encode(x=_x, y=_y, text="player:N")
            )
        return alt.layer(*_layers).properties(
            title=_label,
            width="container" if _single else 330,
            height=380 if _single else 220,
        )

    if not _order:
        _out = mo.md("_Add a player above to plot._")
    elif not _panels:
        _out = mo.md("_Pick at least one stat to count per foul._")
    else:
        chart = (
            _panel(_panels[0]) if _single else alt.concat(*[_panel(n) for n in _panels], columns=2)
        ).properties(
            title=alt.TitleParams(
                f"Per {_foul}, {season_type.value.lower()}", anchor="start", fontSize=14
            )
        )
        _out = mo.ui.altair_chart(chart)
    _out
    return


@app.cell
def _(mo, picked):
    # Table view of what's plotted: one row per player-season, a column pair per stat.
    if len(picked):
        _t = picked.pivot_table(
            index=["player", "season", "games", "fouls"],
            columns="stat",
            values=["value", "per_foul"],
            sort=False,
        )
        _t.columns = [
            f"{s.lower()}" if v == "value" else f"{s.lower()}_per_foul" for v, s in _t.columns
        ]
        _t = _t.reset_index().round(1)
    else:
        _t = picked
    mo.accordion({"Data table": mo.ui.table(_t, selection=None)})
    return


if __name__ == "__main__":
    app.run()
