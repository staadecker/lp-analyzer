import lp_range_analyzer
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str, help="Path of file to read")
    args = parser.parse_args()

    lp_range_analyzer.main(args.filename)


if __name__ == '__main__':
    main()
