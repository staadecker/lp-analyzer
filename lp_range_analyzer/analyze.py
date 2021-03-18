"""
Provides functions to print the range of values
"""
import time

show_full_rows = False

def analyze_objective_range(model):
    start_time = time.time()
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

    print(f"Analyzed coefficients in {(time.time() - start_time):.3}")
    print(f"Coefficients range from {min_coef:.3} * {min_var} to {max_coef:.3} * {max_var}")
    if show_full_rows:
        print("Full objective is: ", end="")
        model.objective.print()


def analyze_coefficient_range(model):
    start_time = time.time()
    min_coef, max_coef = float('inf'), 0
    min_row, max_row = None, None
    min_var, max_var = None, None
    for row in model.rows.values():
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

    print(f"Analyzed coefficients in {(time.time() - start_time):.3}")
    print(f"Coefficients range from {min_coef:.3} * {min_var} to {max_coef:.3} * {max_var}")
    if show_full_rows:
        print("Full max row is: ", end="")
        max_row.print()
        print("Full min row is: ", end="")
        min_row.print()


def anaylze_rhs(model):
    start_time = time.time()
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

    print(f"Analyzed rhs in {(time.time() - start_time):.3}")
    print(f"RHS range is ({min_rhs:.3}, {max_rhs:.3})")
    if show_full_rows:
        print("Full max rhs row is: ", end="")
        max_row.print()
        print("Full min rhs row is: ", end="")
        min_row.print()

def anaylze_bounds(model):
    start_time = time.time()
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

    print(f"Analyzed bounds in {(time.time() - start_time):.3}")
    print(f"Bounds range is ({min_bound_value:.3}, {max_bound_value:.3})")
    print("Full max bound row is: ", end="")
    max_bound.print()
    print("Full min bound row is: ", end="")
    min_bound.print()
