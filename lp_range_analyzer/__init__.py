from typing import List, Optional, Dict
from enum import Enum
import time


class CustomLineIteratorDone(Exception):
    pass


class LineIterator:
    # We don't use isspace() since it is slow.
    SPACES = (" ", "\n", "\t")

    def __init__(self):
        self.line = None
        self.n = None
        self.position = None

    def set(self, line):
        self.position = 0
        self.line = line
        self.n = len(line)

    def read_value(self):
        i = self.position
        while i < self.n and self.line[i] in LineIterator.SPACES:
            i += 1

        if i == self.n:
            raise CustomLineIteratorDone

        start = i

        while i < self.n and not self.line[i] in LineIterator.SPACES:
            i += 1
        if i == self.n:
            raise CustomLineIteratorDone

        end = i
        self.position = i
        return self.line[start:end]


class Row:
    """A row in the model (either Objective, Bound or Constraint)"""

    def __init__(self, name=None):
        self.name = name


class ExpressionRow(Row):
    """A row with an expression (either Objective or Constraint)"""

    def __init__(self, name):
        super(ExpressionRow, self).__init__(name)
        self.coefficients = {}

    def set_variable_coefficient(self, variable_name, value):
        self.coefficients[variable_name] = value

    def print(self):
        print(self.name, end=": ")
        for variable, coefficient in self.coefficients.items():
            print(f"+ {coefficient} * {variable}", end="\t")


class Objective(ExpressionRow):
    """The Objective row. For now isn't different from just an ExpressionRow."""

    def __init__(self, name):
        super(Objective, self).__init__(name)


class Constraint(ExpressionRow):
    """A Constraint in the model."""
    symbol_mapping = {"L": "<=", "G": ">=", "E": "="}

    def __init__(self, name, constraint_type):
        super(Constraint, self).__init__(name)
        self.rhs_value = None
        self.constraint_type = constraint_type

    def set_rhs(self, value):
        self.rhs_value = value

    def print(self):
        super(Constraint, self).print()  # Print the expression
        print(f"{self.symbol_mapping[self.constraint_type]}\t{self.rhs_value}")  # The print the RHS


class Bound(Row):
    def __init__(self, name):
        super(Bound, self).__init__(name)
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
        self.rows: Dict[ExpressionRow] = {}
        self.bounds = {}

    def add_row(self, row: ExpressionRow):
        assert row.name not in self.rows
        self.rows[row.name] = row
        if isinstance(row, Objective):
            self.objective = row

    def set_bound(self, name, low=None, high=None):
        if name not in self.bounds:
            bound = Bound(name)
            self.bounds[name] = bound
        else:
            bound = self.bounds[name]
        bound.lhs_bound = low
        bound.rhs_bound = high

    def get_row(self, row_name) -> ExpressionRow:
        return self.rows[row_name]

    def print_model(self):
        if self.objective is None:
            print("No objective specified")
        else:
            self.objective.print()

        print()

        for constraint in self.rows.values():
            if isinstance(constraint, Objective):
                continue
            constraint.print()

        for bound in self.bounds.values():
            bound.print()


class ReaderState(Enum):
    INITIAL = 0
    ROWS = 1
    COLUMNS = 2
    RHS = 3
    BOUNDS = 4
    DONE = 5


class MPSReader:
    def __init__(self, filename):
        self.state = ReaderState.INITIAL
        self.filename = filename
        self.model: LPModel = LPModel()

    def read(self):
        with open(self.filename, "r") as file:
            iterator = LineIterator()
            for line in file:
                iterator.set(line)
                if self.state == ReaderState.INITIAL:
                    if line == "ROWS\n":
                        self.state = ReaderState.ROWS
                elif self.state == ReaderState.ROWS:
                    if line == "COLUMNS\n":
                        self.state = ReaderState.COLUMNS
                    else:
                        self._read_row(iterator)
                elif self.state == ReaderState.COLUMNS:
                    if line == "RHS\n":
                        self.state = ReaderState.RHS
                    else:
                        self._read_column(iterator)
                elif self.state == ReaderState.RHS:
                    if line == "BOUNDS\n":
                        self.state = ReaderState.BOUNDS
                    else:
                        self._read_rhs(iterator)
                elif self.state == ReaderState.BOUNDS:
                    if line == "ENDATA\n" or line == "ENDATA":
                        self.state = ReaderState.DONE
                    else:
                        self._read_bound(iterator)
                else:
                    raise Exception(f"Unknown state {self.state}")

        assert self.state == ReaderState.DONE

        return self.model

    def _read_row(self, row: LineIterator):
        row_type = row.read_value()
        name = row.read_value()
        if row_type == "N":
            if self.model.objective is not None:
                raise Exception("Objective function already defined")
            self.model.add_row(Objective(name))
        else:
            self.model.add_row(Constraint(name, row_type))

    def _read_column(self, line: LineIterator):
        var_name = line.read_value()

        while True:
            try:
                row_name = line.read_value()
            except CustomLineIteratorDone:
                break
            value = line.read_value()
            self.model.get_row(row_name).set_variable_coefficient(var_name, value)

    def _read_rhs(self, line: LineIterator):
        line.read_value()  # First element is useless

        while True:
            try:
                row_name = line.read_value()
            except CustomLineIteratorDone:
                break
            value = line.read_value()
            self.model.get_row(row_name).rhs_value = value

    def _read_bound(self, line: LineIterator):
        bound_type = line.read_value()
        line.read_value()  # Second value can be dropped
        name = line.read_value()
        value = line.read_value()

        if bound_type == "UP":
            self.model.set_bound(name, high=value)
        elif bound_type == "LO":
            self.model.set_bound(name, low=value)
        else:
            raise Exception(f"Unknown bound type {bound_type}")


def main(filename):
    start_time = time.time()
    model = MPSReader(filename).read()
    print(f"Time taken to read model: {time.time() - start_time}")
    model.print_model()
