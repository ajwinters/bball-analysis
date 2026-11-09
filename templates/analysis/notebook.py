import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt

    from bball import db, real, style

    style.use()
    engine = db.engine()  # marimo SQL cells can use this connection
    here = mo.notebook_dir()  # figures/ and tables/ are saved next to this file
    return db, engine, here, mo, plt, real, style


@app.cell
def _(mo):
    mo.md("""
    # {title}

    **Question:** {question}
    """)
    return


@app.cell
def _(db):
    db.query("select season, count(distinct gameid) as games from master_nba_games "
             "group by 1 order by 1 desc limit 5")
    return


if __name__ == "__main__":
    app.run()
