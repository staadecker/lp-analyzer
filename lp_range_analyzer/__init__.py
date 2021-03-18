from typing import Dict, Optional

# Used when printing rows. RHS values are on the left, hence why >= and <= are flipped.
SYMBOL_MAPPING = {"L": ">=", "G": "<=", "E": "=", "N": "Obj:"}


class Row:
    """A constraint or the objective function in the model."""

    def __init__(self, name: str, row_type=None):
        """
        :param name: name of the row
        :param row_type: letter representing the row type according to the MPS format (must be a key in SYMBOL_MAPPING)
        """
        self.name: str = name
        self.row_type: str = row_type
        self.coefficients: Dict[str, float] = {}
        self.rhs_value: Optional[float] = 0.0  # Need float since that's what's expected in analysis

    def print(self):
        print(self.name, end=":\t")
        if self.rhs_value is not None:
            print(self.rhs_value, end="\t")
        print(f"{SYMBOL_MAPPING[self.row_type]} ", end="")
        for var_name, coefficient in self.coefficients.items():
            if coefficient > 0:
                print("+", end="")
            if coefficient == 1:
                print(f"{var_name}", end="\t")
            else:
                print(f"{coefficient}*{var_name}", end="\t")
        print()


class Bound:
    """A bound on a variable"""

    def __init__(self, name: str):
        self.name = name
        self.lhs_bound = None
        self.rhs_bound = None

    def print(self):
        if self.lhs_bound is not None and self.rhs_bound is not None:
            print(self.lhs_bound, "<=", self.name, "<=", self.rhs_bound)
        elif self.rhs_bound is not None:
            print(self.name, "<=", self.rhs_bound)
        elif self.lhs_bound is not None:
            print(self.lhs_bound, "<=", self.name)
        else:
            print("unbounded ", self.name)


class LPModel:
    """The linear model. Contains all the rows, variable boounds and objective function."""

    def __init__(self):
        self.objective: Optional[Row] = None  # Reference to the objective function
        self.rows: Dict[str, Row] = {}
        self.bounds: Dict[str, Bound] = {}

    def add_row(self, name, row_type):
        assert name not in self.rows  # Make sure it doesn't already exist (don't want to overwrite)
        self.rows[name] = Row(name, row_type)
        if row_type == "N":
            if self.objective is not None:
                raise Exception("Can't set objective, it already exists")
            self.objective = self.rows[name]
            self.objective.rhs_value = None  # No RHS value for the objective function

    def print_model(self):
        print("OBJECTIVE")
        self.objective.print()
        print("\nCONSTRAINTS")
        for row in self.rows.values():
            if row.row_type != "N":
                row.print()
        print("\nBOUNDS")
        for bound in self.bounds.values():
            bound.print()
