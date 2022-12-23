# Other notes

## How to deploy new version of package to PyPi

1. Bump version
2. `python -m build`
3. `twine upload dist/*`