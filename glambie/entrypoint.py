"""
The single command line entry point for the package.
Currently a placeholder
"""
import argparse


def main():
    # Build the argument parser
    parser = argparse.ArgumentParser(
        prog='glambie', description='GlaMBIE entry point.')
    parser.add_argument('-config', dest='config', type=str, help='The config path')

    # parse the input arguments
    args = parser.parse_args()

    config = args.config
    print(config)
