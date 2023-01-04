import argparse
from lp_analyzer.reader import MPSReader
from lp_analyzer.analyze import full_analysis


def main():
    # Parse command line input
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str, help="Path of input file")
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        help="Specify an output text file to store the log output.",
        default=None,
    )
    args = parser.parse_args()
    main_without_argument_parser(args.input_file, args.output_file)


def main_without_argument_parser(input_file, output_file=None):
    if output_file is None:
        output_file = input_file[:-4] + "_results.txt"

    # Read input file and load into Model object
    model = MPSReader(input_file).read()

    # Analyze the model
    full_analysis(model, output_file)


if __name__ == "__main__":
    main_without_argument_parser("../examples/small_model.mps")
