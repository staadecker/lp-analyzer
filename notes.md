# Other notes

## How to deploy new version of package to PyPi

1. Bump version in `pyproject.toml`
2. `python -m build`
3. `twine upload dist/*`

## How to regenerate `small_model_results.txt`

Just re-run `__main__.py`.