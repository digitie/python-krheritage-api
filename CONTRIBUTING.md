# Contributing

Use conventional commits and keep public identifiers in English. User-facing
documentation should include Korean and English where practical.

Before opening a PR:

```bash
ruff check .
mypy src/krheritage
pytest
```

Do not add PyPI publishing configuration unless the project owner reverses the
current no-PyPI decision.

