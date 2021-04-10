"""
Provides functions to analyze a Model.
"""
from tabulate import tabulate


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


class AnalyzeRow:
    def __init__(self, name):
        self.name = name
        self.min_rhs = float('inf')
        self.max_rhs = 0
        self.min_coef = float('inf')
        self.max_coef = 0

    def get_table_row(self):
        return [self.name, self.min_coef, self.max_coef, self.min_rhs, self.max_rhs]


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
    # Analyze by variable
    output = analyze_by_variable_type(model)
    output += "\n\n"

    # Analyze by row type
    output += analyze_by_row_type(model)

    print(output)

    if outfile is not None:
        with open(outfile, "w") as f:
            f.write(output)

