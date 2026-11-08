# bball-analysis

NBA analytics on data collected by [bballagg](https://github.com/ajwinters/bballagg) (sister repo). Each analysis is a folder in `analyses/` with a marimo notebook, figures and notes; smaller ideas inside it live in `ideas/`.

- **[INDEX.md](INDEX.md)**: every analysis and idea, with status and tags.
- **[IDEAS.md](IDEAS.md)**: not started yet.

```bash
pixi run new shooting corner-threes        # analyses/shooting-corner-threes/
pixi run edit analyses/shooting-corner-threes/notebook.py
pixi run index                             # rebuild INDEX.md
```

Data is read from a local Postgres database built by bballagg and isn't included here.
