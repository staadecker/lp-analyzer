"""
Provides functions to analyze a Model.
"""
from tabulate import tabulate
from typing import Dict, List
import math

from .core import LPModel
from .util import print_progress

include_obj_coef = False


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

        def format_cell(c):
            if c == float("inf") or c == 0:
                return ""
            elif type(c) == float:
                return f"{c:.1e}"
            else:
                return c

        return map(format_cell, self.get_table_row())


def make_table(rows: List[TableRow]):
    return tabulate(
        map(lambda r: r.get_formatted_table_row(), rows),
        headers=rows[0].get_table_header(),
        tablefmt="github",
        disable_numparse=True,  # Parsing is done upstream
    )


class VariableStat(TableRow):
    """
    A row in a table for the variables in the model.
    Stores statistic information on that row notably,
    - Minimum coefficient for that variable
    - Maximum coefficient for that variable
    - Minimum bound for that variable
    - Maximum bound for that variable
    - Geometric mean of upper bound and number of upper bounds
    - Geometric mean of lower bounds and number of lower bounds
    """

    def __init__(self, name):
        self.name = name
        self.min_coef = float("inf")
        self.max_coef = 0
        self.min_bound = float("inf")
        self.max_bound = 0
        self.min_coef_index = None
        self.max_coef_index = None
        self.min_bound_index = None
        self.max_bound_index = None
        self.geom_lower_count = 0
        self.geom_lower_sum = 0
        self.geom_upper_count = 0
        self.geom_upper_sum = 0
        self.indexes = set()
        self.count = 0

    def update_coef(self, val, ext):
        val = abs(val)  # We only care about magnitude of coefficients

        # If coef is less than the minimum update the minimum
        if val < self.min_coef:
            self.min_coef = val
            self.min_coef_index = ext

        # If coef is more than the max update the max
        if val > self.max_coef:
            self.max_coef = val
            self.max_coef_index = ext

    def update_bound_min_max(self, val, ext):
        # If bound is less than min update min
        if val < self.min_bound:
            self.min_bound = val
            self.min_bound_index = ext

        # If bound is more than max update the max
        if val > self.max_bound:
            self.max_bound = val
            self.max_bound_index = ext

    def update_lower_bound(self, val, ext):
        # If the bound is None or 0 skip it
        if val is None or val == 0:
            return

        # We only care about bound magnitude
        val = abs(val)

        self.update_bound_min_max(val, ext)

        self.geom_lower_count += 1
        self.geom_lower_sum += math.log(val)

    def update_upper_bound(self, val, ext):
        # If the bound is None or 0 skip it
        if val is None or val == 0:
            return

        # We only care about bound magnitude
        val = abs(val)

        self.update_bound_min_max(val, ext)

        self.geom_upper_count += 1
        self.geom_upper_sum += math.log(val)

    def __str__(self):
        return (
            self.name
            + "\t"
            + str(self.min_coef)
            + "\t"
            + str(self.max_coef)
            + "\t"
            + str(self.min_bound)
            + "\t"
            + str(self.max_bound)
        )

    def get_table_row(self):
        # Calculate the geometric mean for the upper and lower bounds.
        lower_mean = (
            None
            if self.geom_lower_count == 0
            else math.exp(self.geom_lower_sum / self.geom_lower_count)
        )
        upper_mean = (
            None
            if self.geom_upper_count == 0
            else math.exp(self.geom_upper_sum / self.geom_upper_count)
        )
        if (self.min_coef, self.min_coef_index) == (self.max_coef, self.max_coef_index):
            self.min_coef = "--"
            self.min_coef_index = "--"
        return [
            self.name,
            len(self.indexes),
            int(self.count / len(self.indexes)),
            self.min_coef,
            self.max_coef,
            self.min_bound,
            self.max_bound,
            self.min_coef_index,
            self.max_coef_index,
            self.min_bound_index,
            self.max_bound_index,
            self.geom_lower_count,
            lower_mean,
            self.geom_upper_count,
            upper_mean,
        ]

    @staticmethod
    def get_table_header():
        return [
            "Var Name",
            "Col Count",
            "Avg Col Non-Zeroes",
            "Min coef",
            "Max coef",
            "Min Bound",
            "Max bound",
            "Min coef index",
            "Max coef index",
            "Min bound index",
            "Max bound index",
            "Lower Bound Count",
            "Lower Bound Geometric Mean",
            "Upper bound count",
            "Upper bound geometric mean",
        ]


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
        self.min_rhs = float("inf")
        self.max_rhs = 0
        self.min_coef = float("inf")
        self.max_coef = 0
        self.count = 0
        self.num_rows = 0

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
        if (self.min_coef, self.min_coef_ext) == (self.max_coef, self.max_coef_ext):
            self.min_coef = "--"
            self.min_coef_ext = "--"
        if (self.min_rhs, self.min_rhs_ext) == (self.max_rhs, self.max_rhs_ext):
            self.min_rhs = "--"
            self.min_rhs_ext = "--"
        return [
            self.name,
            self.num_rows,
            int(self.count / self.num_rows),
            self.min_coef,
            self.max_coef,
            self.min_rhs,
            self.max_rhs,
            self.min_coef_ext,
            self.max_coef_ext,
            self.min_rhs_ext,
            self.max_rhs_ext,
        ]

    @staticmethod
    def get_table_header():
        return [
            "Constraint Name",
            "Row count",
            "Avg row non-zeroes",
            "Min coef",
            "Max coef",
            "Min RHS",
            "Max RHS",
            "Min coef index",
            "Max coef index",
            "Min RHS index",
            "Max RHS index",
        ]


class DensityTableRow(TableRow):
    def __init__(self, var_name, count):
        self.var_name, self.count = var_name, count

    def get_table_row(self):
        return [self.var_name, self.count]

    @staticmethod
    def get_table_header():
        return ["Variable", "Row Count"]


def get_variable_stats(model):
    var_stats = {}
    for row in print_progress(
        model.rows.values(), message="Analyzing variable coefficients"
    ):
        # Skip the objective, we want values only in the matrix
        if row.is_objective and not include_obj_coef:
            continue
        for var_name, coef in row.coefficients.items():
            var_name, var_index = split_type_and_index(var_name)

            try:
                var_stat = var_stats[var_name]
            except KeyError:
                var_stat = VariableStat(var_name)
                var_stats[var_name] = var_stat

            var_stat.update_coef(coef, row.row_name)
            var_stat.indexes.add(var_index)
            var_stat.count += 1

    for bound in print_progress(
        model.bounds.values(), message="Analyzing variable bounds"
    ):
        var_name, var_index = split_type_and_index(bound.name)

        try:
            var_stat = var_stats[var_name]
        except KeyError:
            var_stat = VariableStat(var_name)
            var_stats[var_name] = var_stat

        var_stat.update_lower_bound(bound.lhs_bound, var_index)
        var_stat.update_upper_bound(bound.rhs_bound, var_index)

    return list(var_stats.values())


def get_constraint_stats(model):
    row_stats: Dict[str, ConstraintStat] = {}
    for full_name, row in print_progress(
        model.rows.items(), message="Analyzing constraints"
    ):
        min_pair, max_pair = row.coefficient_range()
        min_var, min_coef = min_pair
        max_var, max_coef = max_pair
        row_name, row_index = split_type_and_index(full_name)

        try:
            row_stat = row_stats[row_name]
        except KeyError:
            row_stat = ConstraintStat(row_name)
            row_stats[row_name] = row_stat

        row_stat.update_min_coef(min_coef, min_var)
        row_stat.update_max_coef(max_coef, max_var)
        row_stat.update_rhs(row.rhs_value, row_index)
        row_stat.num_rows += 1
        row_stat.count += len(row.coefficients)

    return list(row_stats.values())


def find_dense_columns(model: LPModel, n=10):
    """
    Unused method that returns the dense columns. For now,
    the average density of an equation is sufficient.
    """
    densities = {}
    for row in model.rows.values():
        for var, coef in row.coefficients.items():
            if var not in densities:
                densities[var] = 1
            else:
                densities[var] += 1

    densities = tuple(sorted(densities.items(), key=lambda x: x[1], reverse=True))[:n]
    densities = tuple(map(lambda d: DensityTableRow(d[0], d[1]), densities))

    return densities


def split_type_and_index(name):
    row_type, _, index = name.partition("(")
    index = index[: index.find(")")]
    return row_type, index


def full_analysis(model, outfile):
    var_stats = get_variable_stats(model)
    constraint_stats = get_constraint_stats(model)

    str_output = (
        "Created by Martin Staadecker's LP analyzer tool. Enjoy! (https://github.com/staadecker/lp-analyzer)\n\n"
        + make_table(var_stats)
        + "\n\n"
        + make_table(constraint_stats)
    )

    if outfile is not None:
        with open(outfile, "w") as f:
            f.write(str_output)
    else:
        print(str_output)
