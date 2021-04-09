import argparse
from lp_range_analyzer.read import MPSReader
from lp_range_analyzer.analyze import full_analysis


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str, help="Path of file to read")
    args = parser.parse_args()
    model = MPSReader(args.filename).read()
    full_analysis(model)


if __name__ == '__main__':
    main()
