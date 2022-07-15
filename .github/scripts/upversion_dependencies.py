"""
Create Pull Requests suggesting that repositories that depend on this one change their dependency versions.

Scans through Earthwave's repositories looking for any that cite this repository
as a dependency in their requirements.txt files. It then creates a branch on those repositories where the only change
is to update the version of this repository depended upon by that repository to the latest version
(a change to the requirements.txt file). Lastly, it opens a Pull Request on that repository.

This is clearly something that Dependabot might be able to do better, but for now, here's a script.
Note that we make use of the GitHub CLI, which is already installed into the repository containers.
"""
import argparse
from datetime import datetime, timedelta
import os
import shutil
import subprocess


def main(this_package_name: str, this_repo_name: str, this_package_version: str,
         dry_run: bool, repo_age_limit_days: int) -> None:
    """
    Create Pull Requests suggesting that repositories that depend on this one change their dependency versions.

    Parameters
    ----------
    this_package_name: str
        The name of this package - the one to scan for instances of within other repositories' requirements.txt files.
    this_repo_name : str
        The name of this repository. Used to avoid checking own repository for dependency issues.
    this_package_version : str
        The version of this package. Will open a branch in other repos where this package's version in requirements.txt
        is set to this_package_version, and then raise pull requests.
    dry_run : bool
        If true, complete all work up to but not including an actual git push, then stop.
    repo_age_limit_days : int
        Don't check repositories that were last pushed to more than this number of days ago.
    """
    log_prefix = 'While raising Pull Requests to up-version dependencies: '

    assert this_package_version.startswith("v")  # assume we get the tag passed in
    this_package_version = this_package_version[1:]  # remove the v prefix

    # Check that the environment variable used for non-interactive GitHub CLI authentication is set.
    # Note this needs to be set to a Personal Access Token with the appropriate permissions
    assert "GH_TOKEN" in os.environ

    # get a list of all non-archived earthwave repositories that were
    # last pushed to less than repo_age_limit_days days ago
    age_limit_iso_str = (
        datetime.now() - timedelta(days=repo_age_limit_days)).astimezone().replace(microsecond=0).isoformat()

    earthwave_repo_names_raw = subprocess.check_output(
        f'gh search repos org:earthwave archived:false pushed:">{age_limit_iso_str}" --limit 1000',
        shell=True, timeout=60).decode()

    # assemble a list of other repositories
    other_earthwave_repo_names = [
        line.split()[0] for line in earthwave_repo_names_raw.split("\n")
        if line.startswith("earthwave") and not line.split()[0].endswith(this_repo_name)]

    # create a working directory specifically for this job
    starting_dir = os.getcwd()
    working_dir = os.path.join(starting_dir, 'dependency_working')
    os.mkdir(working_dir)
    os.chdir(working_dir)

    for repo_name in other_earthwave_repo_names:
        # for each repo, shallow clone the default branch and cd into it
        print("-----------------------------------")
        print(log_prefix + f"Attempting to shallow-clone {repo_name}")
        upversion_branch_name = f"upversion_{this_package_name}_to_{this_package_version}"
        subprocess.check_output(f"git clone --depth=1 https://$GH_TOKEN@github.com/{repo_name}.git", shell=True)
        os.chdir(repo_name.split('/')[1])
        subprocess.check_output(f"git branch {upversion_branch_name}", shell=True)
        subprocess.check_output(f"git checkout {upversion_branch_name}", shell=True)

        requirements_txt_path = os.path.join(os.getcwd(), "requirements.txt")
        if os.path.exists(requirements_txt_path):
            print(log_prefix + f"Found a requirements.txt in {repo_name}.")
            # load up the requirements.txt and look for this repo in it
            with open(requirements_txt_path) as file:
                requirements = file.readlines()

            # if a line refers to the specified package, replace it with the new version
            is_dependent_upon_this_package = False
            for i, requirement in enumerate(requirements):
                if requirement.startswith(this_package_name):
                    is_dependent_upon_this_package = True
                    requirements[i] = "".join([this_package_name, '==', this_package_version, '\n'])
                    print(log_prefix + f"set version for package {this_package_name} to {this_package_version} "
                          f"in requirements.txt in new branch {upversion_branch_name} in {repo_name}.")

            if is_dependent_upon_this_package:
                if dry_run:
                    print(log_prefix + "DRY RUN: Stopping here. Nothing committed or pushed.")
                else:
                    # overwrite the requirements.txt file
                    with open(requirements_txt_path, "w") as file:
                        file.writelines(requirements)

                    # check whether anything changed
                    # if we write the same thing that's already there, we need to avoid trying to commit
                    try:
                        subprocess.check_output('git diff --exit-code', shell=True)
                        print(log_prefix + f"The version of {this_package_name} in the requirements.txt in {repo_name}"
                              + f" already matches {this_package_version}, so I don't need to raise a Pull Request.")
                    except subprocess.CalledProcessError:
                        # something changed, so we need to commit and push it

                        # stage, commit and push
                        subprocess.check_output('git add requirements.txt', shell=True)
                        subprocess.check_output(
                            f'git commit -m "upversion dependency {this_package_name} to {this_package_version}"',
                            shell=True)
                        subprocess.check_output('git push -u origin HEAD', shell=True)

                        # open pull request
                        subprocess.check_output(
                            f'gh pr create --head {upversion_branch_name} '
                            f'--title "Increment version of dependency {this_package_name}" '
                            f'--body "This package depends upon {this_package_name}. '
                            f'Version {this_package_version} has been recently released. '
                            'Please consider updating the version upon which this package depends."',
                            shell=True, timeout=60)

                        print(log_prefix + "Pull request raised in dependent package.")
            else:
                print(log_prefix + f"The requirements.txt in {repo_name} "
                      f"does not include {this_package_name}, so taking no action.")

        else:
            print(log_prefix + f"Did not find a requirements.txt in {repo_name}, so taking no action.")

        # change back to the working directory and delete the shallow clone, ready for the next repo check
        os.chdir('..')
        shutil.rmtree(repo_name.split('/')[1])

    # return to the starting directory and delete the working directory
    os.chdir(starting_dir)
    shutil.rmtree(working_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--this_package_name", type=str, required=True,
        help="The name of this python package")

    parser.add_argument(
        "--this_repo_name", type=str, required=True,
        help="The name of this repository (in a format e.g. 'earthwave/reponame')")

    parser.add_argument(
        "--this_package_version", type=str, required=True,
        help="The version of this python package to set in the requirements.txt files of dependencies")

    parser.add_argument(
        "--repo_age_limit_days", type=int, required=True,
        help="Repositories with default branches that were last pushed to more than this "
        "number of days ago will not be checked.")

    parser.add_argument(
        "--dry_run", action="store_true",
        help="If true, prints which images it plans to delete but does not actually delete them.")

    parsed_args = parser.parse_args()
    main(this_package_version=parsed_args.this_package_version,
         this_repo_name=parsed_args.this_repo_name,
         this_package_name=parsed_args.this_package_name,
         repo_age_limit_days=parsed_args.repo_age_limit_days,
         dry_run=parsed_args.dry_run)
