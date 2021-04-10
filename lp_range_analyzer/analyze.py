"""
Provides functions to analyze a Model.
"""
from tabulate import tabulate

show_full_rows = False


def analyze_objective_range(model):
    min_coef, max_coef = float('inf'), 0
    min_var, max_var = None, None
    for variable, coefficient in model.objective.coefficients.items():
        abs_coefficient = abs(coefficient)
        if abs_coefficient < min_coef:
            min_coef = abs_coefficient
            min_var = variable
        if abs_coefficient > max_coef:
            max_coef = abs_coefficient
            max_var = variable

    if show_full_rows:
        print("Full objective is: ", end="")
        model.objective.print()

    return [["Min Objective", min_coef, None, min_var],
            ["Max Objective", None, max_coef, max_var]]


def analyze_coefficient_range(model):
    min_coef, max_coef = float('inf'), 0
    min_row, max_row = None, None
    min_var, max_var = None, None
    for row in model.rows.values():
        if model.objective == row:
            continue
        for variable, coefficient in row.coefficients.items():
            abs_coefficient = abs(coefficient)
            if abs_coefficient < min_coef:
                min_coef = abs_coefficient
                min_row = row
                min_var = variable
            if abs_coefficient > max_coef:
                max_coef = abs_coefficient
                max_row = row
                max_var = variable

    if show_full_rows:
        print("Full max row is: ", end="")
        max_row.print()
        print("Full min row is: ", end="")
        min_row.print()

    return [["Min Coef", min_coef, None, min_var],
            ["Max Coef", None, max_coef, max_var]]


def anaylze_rhs(model):
    min_rhs, max_rhs = float('inf'), 0
    min_row, max_row = None, None
    for row in model.rows.values():
        if row.rhs_value is None or row.rhs_value == 0.0:
            continue
        abs_rhs = abs(row.rhs_value)
        if abs_rhs < min_rhs:
            min_rhs = abs_rhs
            min_row = row
        if abs_rhs > max_rhs:
            max_rhs = abs_rhs
            max_row = row

    if show_full_rows:
        print("Full max rhs row is: ", end="")
        max_row.print()
        print("Full min rhs row is: ", end="")
        min_row.print()

    return [["RHS min", min_rhs, None, min_row.row_name], ["RHS Max", None, max_rhs, max_row.row_name]]


def anaylze_bounds(model):
    min_bound_value, max_bound_value = float('inf'), 0
    min_bound, max_bound = None, None
    for bounds in model.bounds.values():
        for bound in (bounds.lhs_bound, bounds.rhs_bound):
            if bound is None:
                continue
            abs_bound = abs(bound)
            if abs_bound < min_bound_value:
                min_bound_value = abs_bound
                min_bound = bounds
            if abs_bound > max_bound_value:
                max_bound_value = abs_bound
                max_bound = bounds

    if show_full_rows:
        print("Full max bound row is: ", end="")
        max_bound.print()
        print("Full min bound row is: ", end="")
        min_bound.print()

    return [["Min Bound", min_bound.lhs_bound, min_bound.rhs_bound, min_bound.name],
            ["Max Bound", max_bound.lhs_bound, max_bound.rhs_bound, max_bound.name]]


class AnalyzeVariable:
    def __init__(self, name):
        self.name = name
        self.min_coef = float('inf')
        self.max_coef = 0
        self.min_bound = float('inf')
        self.max_bound = 0

    def __str__(self):
        return self.name + "\t" + str(self.min_coef) + "\t" + str(self.max_coef) + "\t" + str(
            self.min_bound) + "\t" + str(self.max_bound)

    def get_table_row(self):
        return [self.name, self.min_coef, self.max_coef, self.min_bound, self.max_bound]


def analyze_by_variable_type(model):
    all_vars = {}
    for row in model.rows.values():
        for var_name, coef in row.coefficients.items():
            var_name = var_name[:var_name.find("(")]  # Drop the index
            coef = abs(coef)
            if var_name in all_vars:
                var = all_vars[var_name]
            else:
                var = AnalyzeVariable(var_name)
                all_vars[var_name] = var
            var.min_coef = min(var.min_coef, coef)
            var.max_coef = max(var.max_coef, coef)

    for bound in model.bounds.values():
        var_name = bound.name[:bound.name.find("(")]
        if var_name in all_vars:
            var = all_vars[var_name]
        else:
            var = AnalyzeVariable(var_name)
            all_vars[var_name] = var
        for limit in [bound.lhs_bound, bound.rhs_bound]:
            if limit is None or limit == 0:
                continue
            limit = abs(limit)
            var.min_bound = min(var.min_bound, limit)
            var.max_bound = max(var.max_bound, limit)

    table = []

    for var in all_vars.values():
        table.append(var.get_table_row())

    out = tabulate(table, headers=["Var Name", "Min coef", "Max coef", "Min Bound", "Max bound"], tablefmt="github",
                 floatfmt=".2")
    return out

class AnalyzeRow:
    def __init__(self, name):
        self.name = name
        self.min_rhs = float('inf')
        self.max_rhs = 0
        self.min_coef = float('inf')
        self.max_coef = 0

    def get_table_row(self):
        return [self.name, self.min_coef, self.max_coef, self.min_rhs, self.max_rhs]

def analyze_by_row_type(model):
    all_rows = {}
    for row in model.rows.values():
        row_name = row.row_name[:row.row_name.find("(")]  # Drop the index
        min_coef, max_coef = row.coefficient_range()
        if row_name in all_rows:
            analyze_row = all_rows[row_name]
        else:
            analyze_row = AnalyzeRow(row_name)
            all_rows[row_name] = analyze_row
        analyze_row.min_coef = min(analyze_row.min_coef, min_coef)
        analyze_row.max_coef = max(analyze_row.max_coef, max_coef)
        if row.rhs_value is not None:
            analyze_row.min_rhs = min(analyze_row.min_rhs, abs(row.rhs_value))
            analyze_row.max_rhs = max(analyze_row.max_rhs, abs(row.rhs_value))

    table = []

    for row in all_rows.values():
        table.append(row.get_table_row())

    out = tabulate(table, headers=["Row Name", "Min coef", "Max coef", "Min RHS", "Max RHS"], tablefmt="github",
                   floatfmt=".2")
    return out


def full_analysis(model, outfile):
    # Analyze the main groups
    table = []
    table.extend(analyze_objective_range(model))
    table.extend(analyze_coefficient_range(model))
    table.extend(anaylze_rhs(model))
    table.extend(anaylze_bounds(model))

    output = tabulate(table, headers=["Type", "Min", "Max", "Var"], tablefmt="github", floatfmt=".2")
    output += "\n\n"

    # Analyze by variable
    output += analyze_by_variable_type(model)
    output += "\n\n"

    # Analyze by row type
    output += analyze_by_row_type(model)

    print(output)

    if outfile is not None:
        with open(outfile, "w") as f:
            f.write(output)

