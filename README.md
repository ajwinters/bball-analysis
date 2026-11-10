# bball-analysis

NBA analytics on data collected by [bballagg](https://github.com/ajwinters/bballagg) (sister repo). Each area of interest is a folder in `analyses/`; each specific question in it is a folder directly inside the area, with its own marimo notebook, figures and notes. The area's own files start with `_` so they list together above the ideas.

- **[INDEX.md](INDEX.md)**: every analysis and idea, with status and tags.
- **[IDEAS.md](IDEAS.md)**: not started yet.

```bash
pixi run new reffing                                     # analyses/reffing/
pixi run new reffing/late-calls-by-crew-chief -q "Calls in the last 5 minutes, by crew chief"
pixi run edit analyses/reffing/late-calls-by-crew-chief/notebook.py
pixi run index                             # rebuild INDEX.md
```

Data is read from a local Postgres database built by bballagg and isn't included here.
