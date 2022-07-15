"""
Works out what the next version number should be and writes it to a file.

The rest of the CI chain then reads this file and applies the appropriate tags and setup.py "version=" entries.

Currently this script is written to use purely Python builtins and shell commands.
A bespoke CI container might improve this in future.
"""

import argparse
import re
import subprocess


def main(version_txt_filename: str, major_minor_version_txt_filename: str) -> None:
    """
    Works out what the next version number should be and writes it to version_txt_filename.

    Parameters
    ----------
    version_txt_filename : str
        The filename that will contain the full version number once the script is complete in the format "v1.2.3" etc.
    major_minor_version_txt_filename : str
        The filename that should contain the major and minor version numbers before the script is called,
        in the format "v1.2" etc.
    """
    # grab all of the repository version tags (removing the newline at the end)
    log_prefix = 'while defining new version number: '
    try:
        version_tags = subprocess.check_output(
            'git tag --sort=authordate | grep v', shell=True).decode().split("\n")[:-1]
    except subprocess.CalledProcessError:
        print(log_prefix + 'Did not detect any tags previously existing in this repository.')
        version_tags = []

    # load the current major/minor version number
    with open(major_minor_version_txt_filename, "r") as file:
        major_minor_version = file.readlines()[0]
        assert major_minor_version.startswith("v")
        print(log_prefix + f'Major/minor version number read from file {major_minor_version_txt_filename} '
              f'as {major_minor_version}')

    # find the latest tag matching major_minor_version.txt and use it to set the build number
    # note we iterate through version_tags in reverse time order
    found_previous_build_of_this_major_minor_version = False
    for tag in reversed(version_tags):
        if major_minor_version in tag and not found_previous_build_of_this_major_minor_version:
            print(log_prefix + f'Found tag {tag} which appears to indicate last matching build.')
            found_previous_build_of_this_major_minor_version = True
            current_build_number = re.findall(r'\d+', tag)[-1]
            new_version_number = tag[:tag.rfind(current_build_number)] + str(int(current_build_number) + 1)

    # if there is no previous build, we want to publish build number 0
    if not found_previous_build_of_this_major_minor_version:
        new_version_number = major_minor_version + '.0'
        print(log_prefix + f'Did not find any tags matching major/minor version {major_minor_version}, '
              f'so publishing {new_version_number}.')

    # save the version number to file for use in the rest of the CD chain
    with open(version_txt_filename, "w") as file:
        file.write(new_version_number)
        print(log_prefix + f'Wrote new version number {new_version_number} to {version_txt_filename}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version_txt_filename", type=str, default='full_version.txt',
        help="This script will create a file with this name containing the next verison number.")

    parser.add_argument(
        "--major_minor_version_txt_filename", type=str, default='major_minor_version.txt',
        help="This script will read a file with this name assuming it contains the major and minor version numbers in"
             " the format 'v1.2' or similar."
    )

    parsed_args = parser.parse_args()
    main(version_txt_filename=parsed_args.version_txt_filename,
         major_minor_version_txt_filename=parsed_args.major_minor_version_txt_filename)
