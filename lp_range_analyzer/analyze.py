"""
Provides functions to analyze a Model.
"""
from tabulate import tabulate
from typing import Dict, List
import time


class TableRow:
    """A row that can be printed as part of a table."""

    def get_table_row(self):
        raise NotImplemented

    @staticmethod
    def get_table_header():
        raise NotImplemented

    def get_formatted_table_row(self):
        """
        Gets the row and if a cell is 0 or inf, replace it with an empty string.
        """
        return map(lambda c: "" if c == 0 or c == float("inf") else c, self.get_table_row())


def make_table(rows: List[TableRow]):
    return tabulate(
        map(lambda r: r.get_formatted_table_row(), rows),
        headers=rows[0].get_table_header(),
        # Specify how the table should look, notably 1 significant digit.
        tablefmt="github",
        floatfmt=".1"
    )


class VariableStat(TableRow):
    """
    A row in a table for the variables in the model.
    Stores statistic information on that row notably,
    - Minimum coefficient for that variable
    - Maximum coefficient for that variable
    - Minimum bound for that variable
    - Maximum bound for that variable
    """
    def __init__(self, name):
        self.name = name
        self.min_coef = float('inf')
        self.max_coef = 0
        self.min_bound = float('inf')
        self.max_bound = 0
        self.min_coef_index = None
        self.max_coef_index = None
        self.min_bound_index = None
        self.max_bound_index = None

    def update_coef(self, val, ext):
        val = abs(val) # We only care about magnitude of coefficients

        # If coef is less than the minimum update the minimum
        if val < self.min_coef:
            self.min_coef = val
            self.min_coef_index = ext

        # If coef is more than the max update the max
        if val > self.max_coef:
            self.max_coef = val
            self.max_coef_index = ext

    def update_bound(self, val, ext):
        # If the bound is None or 0 skip it
        if val is None or val == 0:
            return
        # We only care about bound magnitude
        val = abs(val)

        # If bound is less than min update min
        if val < self.min_bound:
            self.min_bound = val
            self.min_bound_index = ext

        # If bound is more than max update the max
        if val > self.max_bound:
            self.max_bound = val
            self.max_bound_index = ext

    def __str__(self):
        return self.name + "\t" + str(self.min_coef) + "\t" + str(self.max_coef) + "\t" + str(
            self.min_bound) + "\t" + str(self.max_bound)

    def get_table_row(self):
        return [self.name, self.min_coef, self.max_coef, self.min_bound, self.max_bound,
                self.min_coef_index, self.max_coef_index, self.min_bound_index, self.max_bound_index]

    @staticmethod
    def get_table_header():
        return ["Var Name", "Min coef", "Max coef", "Min Bound", "Max bound",
                "Min coef index", "Max coef index", "Min bound index", "Max bound index"]


class ConstraintStat(TableRow):
    """
    Represents a row in a table that stores the statistics on each constraint.
    Notably we store,
    - The minimum and maximum right-hand side constant for the constraint
    - The minimum and maximum coefficients for that constaint
    - The specific index of the constraint on which the above statistics are found
    """
    def __init__(self, name):
        self.name = name
        self.min_coef_ext = None
        self.max_coef_ext = None
        self.min_rhs_ext = None
        self.max_rhs_ext = None
        self.min_rhs = float('inf')
        self.max_rhs = 0
        self.min_coef = float('inf')
        self.max_coef = 0

    def update_rhs(self, val, ext):
        # If constaint is None, it's likely the objective function, we skip
        if val is None:
            return
        val = abs(val)
        if val < self.min_rhs:
            self.min_rhs = val
            self.min_rhs_ext = ext
        if val > self.max_rhs:
            self.max_rhs = val
            self.max_rhs_ext = ext

    def update_min_coef(self, val, ext):
        if val < self.min_coef:
            self.min_coef = val
            self.min_coef_ext = ext

    def update_max_coef(self, val, ext):
        if val > self.max_coef:
            self.max_coef = val
            self.max_coef_ext = ext

    def get_table_row(self):
        return [
            self.name,
            self.min_coef,
            self.max_coef,
            self.min_rhs,
            self.max_rhs,
            self.min_coef_ext,
            self.max_coef_ext,
            self.min_rhs_ext,
            self.max_rhs_ext
        ]

    @staticmethod
    def get_table_header():
        return ["Constraint Name", "Min coef", "Max coef", "Min RHS", "Max RHS",
                "Min coef index", "Max coef index", "Min RHS index", "Max RHS index"]


def get_variable_stats(model):
    var_stats = {}
    for row in model.rows.values():
        for var_name, coef in row.coefficients.items():
            var_name, var_index = split_type_and_index(var_name)

            try:
                var_stat = var_stats[var_name]
            except KeyError:
                var_stat = VariableStat(var_name)
                var_stats[var_name] = var_stat

            var_stat.update_coef(coef, var_index)

    for bound in model.bounds.values():
        var_name, var_index = split_type_and_index(bound.name)

        try:
            var_stat = var_stats[var_name]
        except KeyError:
            var_stat = VariableStat(var_name)
            var_stats[var_name] = var_stat

        var_stat.update_bound(bound.lhs_bound, var_index)
        var_stat.update_bound(bound.rhs_bound, var_index)

    return list(var_stats.values())


def get_constraint_stats(model):
    row_stats: Dict[str, ConstraintStat] = {}
    for full_name, row in model.rows.items():
        row_name, row_index = split_type_and_index(full_name)
        min_coef, max_coef = row.coefficient_range()

        try:
            row_stat = row_stats[row_name]
        except KeyError:
            row_stat = ConstraintStat(row_name)
            row_stats[row_name] = row_stat

        row_stat.update_min_coef(min_coef, row_index)
        row_stat.update_max_coef(max_coef, row_index)
        row_stat.update_rhs(row.rhs_value, row_index)

    return list(row_stats.values())


def split_type_and_index(name):
    row_type, _, index = name.partition("(")
    index = index[:index.find(")")]
    return row_type, index


def full_analysis(model, outfile):
    start_time = time.time()
    var_stats = get_variable_stats(model)
    constraint_stats = get_constraint_stats(model)

    str_output = f"Analyzed model in {(time.time() - start_time):.2f} s.\n"
    str_output += make_table(var_stats) + "\n\n" + make_table(constraint_stats)

    if outfile is not None:
        with open(outfile, "w") as f:
            f.write(str_output)

    print(str_output)
