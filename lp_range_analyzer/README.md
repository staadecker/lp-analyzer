# Developer documentation

Here is the role of each file in this folder.

1. `__init__.py` is empty and simply indicates that this folder
is a Python package.
   
2. `core.py` defines the core classes that are used elsewhere.
Notably, `LPModel`, `Row` and `Bound` which represent the
   linear model, a row in the model, and a single variable bound,
   respectively.
   
3. `reader.py` defines `MPSReader`. `MPSReader(filename).read()` will
read the provided `.mps` file and return a `LPModel` object.
   
4. `analyze.py` contains `full_analysis(...)` which will output
different information useful for debugging numerical issues.
   
5. `__main__.py` can be run to read then analyze a `.mps` file in
one step. File paths and output files can be passed in as command
   line arguments.