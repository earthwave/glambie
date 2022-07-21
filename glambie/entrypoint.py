"""
The single comand line entrypoint for the package.
Currently a placeholder
"""
import argparse


def main():
    # Build the argument parser
    parser = argparse.ArgumentParser(
        prog='glambie', description='Glambie entry point.')
    parser.add_argument('-config', dest='config', type=str, help='The first integer')

    # parse the input arguments
    args = parser.parse_args()

    config = args.config
    print(config)
