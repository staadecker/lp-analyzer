import argparse
import time
from lp_range_analyzer.read import MPSReader
from lp_range_analyzer.analyze import *


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str, help="Path of file to read")
    args = parser.parse_args()
    read_and_run(args.filename)


def read_and_run(filename):
    start_time = time.time()
    model = MPSReader(filename).read()
    print(f"Time taken to read model: {(time.time() - start_time):.3}")
    analyze_objective_range(model)
    print()
    analyze_coefficient_range(model)
    print()
    anaylze_rhs(model)
    print()
    anaylze_bounds(model)


if __name__ == '__main__':
    main()
