from typing import List, Dict
import time

SYMBOL_MAPPING = {"L": "<=", "G": ">=", "E": "=", "N": "Obj"}


class ExpressionRow:
    """A Constraint in the model."""

    def __init__(self, name, constraint_type=None):
        self.name = name
        self.coefficients: Dict[str, float] = {}
        self.constraint_type: str = constraint_type
        self.rhs_value = None

    def print(self):
        print(self.name, end=": ")
        for variable, coefficient in self.coefficients.items():
            print(f"+ {coefficient} * {variable}", end="\t")
        print(f"{SYMBOL_MAPPING[self.constraint_type]}\t{self.rhs_value}")  # The print the RHS


class Bound:
    def __init__(self, name):
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
            print("unbounded", self.name)


class LPModel:
    def __init__(self):
        self.objective = None
        self.rows: Dict[str, ExpressionRow] = {}
        self.bounds: Dict[str, Bound] = {}

    def add_row(self, row: ExpressionRow):
        assert row.name not in self.rows
        self.rows[row.name] = row
        if row.constraint_type == "N":
            self.objective = row

    def print_model(self):
        if self.objective is None:
            print("No objective specified")
        else:
            self.objective.print()

        print()

        for constraint in self.rows.values():
            if constraint.constraint_type == "N":
                continue
            constraint.print()

        for bound in self.bounds.values():
            bound.print()


class MPSReader:
    def __init__(self, filename):
        self.function_to_run = self._do_nothing
        self.filename = filename
        self.model: LPModel = LPModel()
        self.KEY_MAPPING = {
            "ROWS": self._read_row,
            "COLUMNS": self._read_column,
            "RHS": self._read_rhs,
            "BOUNDS": self._read_bound,
            "ENDATA": self._do_nothing
        }

    def read(self):
        with open(self.filename, "r") as file:
            lines = file.readlines()

        for line in lines:
            split_line = line.split()
            if len(split_line) == 1:
                self.function_to_run = self.KEY_MAPPING[split_line[0]]
                continue

            self.function_to_run(split_line)

        assert self.function_to_run(None)

        return self.model

    def _do_nothing(self, line):
        return True

    def _read_row(self, row: List):
        self.model.add_row(ExpressionRow(row[1], row[0]))

    def _read_column(self, line: List):
        for i in range(1, len(line), 2):
            self.model.rows[line[i]].coefficients[line[0]] = float(line[i + 1])

    def _read_rhs(self, line: List):
        for i in range(1, len(line), 2):
            self.model.rows[line[i]].rhs_value = float(line[i + 1])

    def _read_bound(self, line: List):
        bound_type = line[0]
        name = line[2]
        value = float(line[3])

        if name not in self.model.bounds:
            bound = Bound(name)
            self.model.bounds[name] = bound
        else:
            bound = self.model.bounds[name]

        if bound_type == "UP":
            bound.rhs_bound = value
        elif bound_type == "LO":
            bound.lhs_bound = value
        else:
            raise Exception(f"Unknown bound type {bound_type}")


def main(filename):
    start_time = time.time()
    model = MPSReader(filename).read()
    print(f"Time taken to read model: {time.time() - start_time}")
    # model.print_model()
