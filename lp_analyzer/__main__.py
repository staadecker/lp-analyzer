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

    if args.output_file is None:
        args.output_file = args.input_file[:-4] + ".txt"

    # Read input file and load into Model object
    model = MPSReader(args.input_file).read()

    # Analyze the model
    full_analysis(model, args.output_file)


if __name__ == "__main__":
    main()
