"""
Provides the class MPSReader which allows reading an .mps linear programming model.
https://en.wikipedia.org/wiki/MPS_(format)
"""
from typing import List

from .core import Bound, LPModel
from .util import print_progress


class MPSReader:
    """
    MPSReader reads an .mps file and returns a LPModel object.

    The code has been profiled to be performant and modifications should
    therefore only be made once performance has been considered / tested.
    """

    def __init__(self, filename):
        self.filename = filename
        # Function to run to read the next line
        # Start by doing nothing as we'll wait for a Keyword.
        self.function_to_run = self._do_nothing
        # The model that will be created
        self.model: LPModel = LPModel()

        # Mapping of keywords to the function that will then need to be run following the keyword.
        self.KEY_MAPPING = {
            "ROWS": self._read_row,
            "COLUMNS": self._read_column,
            "RHS": self._read_rhs,
            "BOUNDS": self._read_bound,
            "ENDATA": self._do_nothing,
        }

    def read(self):
        # Open the file and save the rows to 'lines'
        # This is faster than "for line in file:".
        with open(self.filename, "r") as file:
            lines = file.readlines()

        try:
            # For each line in the file
            for line in print_progress(lines, message="Loading model from file"):
                # Split the line based on its whitespace
                # This will also trim the \n from the end.
                split_line = line.split()

                # If there's only one word, it's a keyword
                if len(split_line) == 1:
                    # From the keyword, find the next function to run to parse the following lines
                    self.function_to_run = self.KEY_MAPPING[split_line[0]]
                    continue

                # If it's not a keyword, evaluate that function
                self.function_to_run(split_line)
        except:
            raise Exception(f"Failed to parse MPS file. (line: {split_line})")

        # The _do_nothing function returns, true
        # This ensures we really reached the end of parsing
        assert self.function_to_run(None)
        return self.model

    def _do_nothing(self, _):
        """Placeholder used when reading the first few lines or last few lines of the file."""
        return True

    def _read_row(self, row: List):
        """Read a line from the ROWS section"""
        # When reading the row definitions,
        # the first element is the type and the second is the name
        self.model.add_row(row[1], row[0])

    def _read_column(self, line: List):
        """Read a line from the COLUMNS section"""
        # The first element of a column is the variable name
        # Then it alternates between row name and coefficient value
        for i in range(1, len(line), 2):
            self.model.rows[line[i]].coefficients[line[0]] = float(line[i + 1])

    def _read_rhs(self, line: List):
        """Read a line from the RHS section"""
        # The first element in the rhs section can be dropped
        # Then it alternates between row name and rhs value
        for i in range(1, len(line), 2):
            self.model.rows[line[i]].rhs_value = float(line[i + 1])

    def _read_bound(self, line: List):
        """Read a line from the BOUNDS section"""

        # The first element in the bounds section is the bound type
        bound_type = line[0]

        # FR indicates a free variable so no bounds
        if bound_type == "FR":
            return

        # The second element is not important
        # The third is the variable on which the bound applies
        name = line[2]

        # MI is equivalent to an UP bound of 0
        if bound_type == "MI":
            bound_type = "UP"
            value = 0.0
        else:
            # The fourth is the value of the bound
            value = float(line[3])

        # If the bound doesn't already exist, create it and add it to the dictionary of bounds
        if name not in self.model.bounds:
            bound = Bound(name)
            self.model.bounds[name] = bound
        # If it does exist, retrieve it
        else:
            bound = self.model.bounds[name]

        # Set either the upper or the lower bound depending on the bound type
        if bound_type == "UP":
            bound.rhs_bound = value
        elif bound_type == "LO":
            bound.lhs_bound = value
        elif bound_type == "FX":
            bound.lhs_bound = value
            bound.rhs_bound = value
        else:
            raise Exception(f"Unknown bound type {bound_type}")
