from typing import Dict, Optional, Tuple

# Mapping of row types to user friendly outputs. Used when printing rows.
# RHS values are on the left, hence why >= and <= are flipped.
SYMBOL_MAPPING = {"L": ">=", "G": "<=", "E": "=", "N": "Obj:"}


class LPModel:
    """Represents a linear model. Contains all the rows, variable bounds and objective function."""

    def __init__(self):
        self.objective: Optional[Row] = None  # Reference to the objective function
        self.rows: Dict[str, Row] = {}  # Will include the objective function
        self.bounds: Dict[str, Bound] = {}

    def add_row(self, row_name: str, row_type: str):
        assert (
            row_name not in self.rows
        )  # Make sure it doesn't already exist (don't want to overwrite)
        self.rows[row_name] = Row(row_name, row_type)
        if row_type == "N":  # If row is the objective row
            if self.objective is not None:
                raise Exception("Can't set objective, it already exists")
            self.objective = self.rows[row_name]
            self.objective.rhs_value = None  # No RHS value for the objective function
            self.rows[row_name].is_objective = True

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


class Row:
    """A constraint or the objective function in the model."""

    def __init__(self, row_name: str, row_type=None):
        """
        :param row_name: name of the row
        :param row_type: letter representing the row type according to the MPS format (must be a key in SYMBOL_MAPPING)
        """
        self.row_name: str = row_name
        self.row_type: str = row_type
        self.coefficients: Dict[str, float] = {}
        self.rhs_value: Optional[
            float
        ] = 0.0  # Need float since that's what's expected in analysis
        self.is_objective: bool = False  # Can be overidden after creation

    def print(self):
        print(self.row_name, end=":\t")
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

    def coefficient_range(
        self,
    ) -> Tuple[Tuple[Optional[str], float], Tuple[Optional[str], float]]:
        """
        Returns two tuples containing the name and value of the minimum and maximum coefficient for this row.
        """
        absolute_coefficients = tuple(
            filter(
                lambda k_v: k_v[1] != 0,
                map(lambda k_v: (k_v[0], abs(k_v[1])), self.coefficients.items()),
            )
        )
        if absolute_coefficients:
            return min(absolute_coefficients, key=lambda k_v: k_v[1]), max(
                absolute_coefficients, key=lambda k_v: k_v[1]
            )
        return (None, float("inf")), (None, 0)


class Bound:
    """A bound on a variable"""

    def __init__(self, name: str):
        self.name: str = name
        self.lhs_bound: Optional[float] = None
        self.rhs_bound: Optional[float] = None

    def print(self):
        if self.lhs_bound is not None and self.rhs_bound is not None:
            print(self.lhs_bound, "<=", self.name, "<=", self.rhs_bound)
        elif self.rhs_bound is not None:
            print(self.name, "<=", self.rhs_bound)
        elif self.lhs_bound is not None:
            print(self.lhs_bound, "<=", self.name)
        else:
            print("unbounded ", self.name)
