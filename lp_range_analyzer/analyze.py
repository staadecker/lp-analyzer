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

    def get_table_header(self):
        raise NotImplemented


def make_table(rows: List[TableRow]):
    return tabulate(
        list(map(lambda r: r.get_table_row(), rows)),
        headers=rows[0].get_table_header(),
        tablefmt="github",
        floatfmt=".1"
    )


class VariableStat(TableRow):
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
        val = abs(val)
        if val < self.min_coef:
            self.min_coef = val
            self.min_coef_index = ext

        if val > self.max_coef:
            self.max_coef = val
            self.max_coef_index = ext

    def update_bound(self, val, ext):
        if val is None or val == 0:
            return
        val = abs(val)
        if val < self.min_bound:
            self.min_bound = val
            self.min_bound_index = ext

        if val > self.max_bound:
            self.max_bound = val
            self.max_bound_index = ext

    def __str__(self):
        return self.name + "\t" + str(self.min_coef) + "\t" + str(self.max_coef) + "\t" + str(
            self.min_bound) + "\t" + str(self.max_bound)

    def get_table_row(self):
        return [self.name, self.min_coef, self.max_coef, self.min_bound, self.max_bound,
                self.min_coef_index, self.max_coef_index, self.min_bound_index, self.max_bound_index]

    def get_table_header(self):
        return ["Var Name", "Min coef", "Max coef", "Min Bound", "Max bound",
                "Min coef index", "Max coef index", "Min bound index", "Max bound index"]


class RowStat(TableRow):
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
        if val is None:
            return
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

    def get_table_header(self):
        return ["Row Name", "Min coef", "Max coef", "Min RHS", "Max RHS",
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


def get_row_stats(model):
    row_stats: Dict[str, RowStat] = {}
    for full_name, row in model.rows.items():
        row_name, row_index = split_type_and_index(full_name)
        min_coef, max_coef = row.coefficient_range()

        try:
            row_stat = row_stats[row_name]
        except KeyError:
            row_stat = RowStat(row_name)
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
    row_stats = get_row_stats(model)

    str_output = f"Analyzed model in {(time.time() - start_time):.2f} s.\n"
    str_output += make_table(var_stats) + "\n\n" + make_table(row_stats)
    print(str_output)

    if outfile is not None:
        with open(outfile, "w") as f:
            f.write(str_output)
