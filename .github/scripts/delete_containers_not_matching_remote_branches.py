"""
Delete containers that do not have an accompanying branch.

The CI chain builds one container per branch per repository. This script deletes containers that do not have
an accompanying branch. This prevents containers building up endlessly in the artifact repo.

Note that the client must first be authenticated with google before this script can be run.

Currently this script is written to use purely Python builtins and shell commands.
A bespoke CI container might improve this in future.
"""
import argparse
import subprocess


def main(package_name: str, dry_run: bool) -> None:
    """
    Delete containers that do not have an accompanying branch.

    Parameters
    ----------
    package_name : str
        The name of the package to maintain in this manner.
    dry_run : bool
        If true, will complete all of the actions up to but not including deleting a container, then stop.
    """
    # if package name is not provided, assume it matches the name of this git repo, suitably reformatted
    log_prefix = 'While tidying Google Artifact Repo Docker Images: '
    if package_name is None:
        package_name = subprocess.check_output(
            'git rev-parse --show-toplevel', shell=True).decode().split('/')[-1].replace('-', '_').lower().strip('\n')
        print(log_prefix + f'no package name specified, assuming package name is {package_name}')

    # first fetch a list of all docker images (as well as other information) from the repository
    all_docker_images = subprocess.check_output(
        'gcloud artifacts docker images list europe-west1-docker.pkg.dev/glambie-0/dr', shell=True
    ).decode().split("\n")[1:-1]  # strip off header and trailing newline with indexing

    # extract only the docker image names related to this package
    # notice conversion to set and back to list again to remove multiple versions of a single image
    docker_images_for_this_package = list({
        image_str.split()[0] for image_str in all_docker_images
        if image_str.split()[0].split('/')[-1].startswith(package_name)})

    # next, fetch a list of all branches
    all_branch_refs = subprocess.check_output('git fetch --prune && git branch -r', shell=True).decode().split('\n')

    # and extract just the branch names
    branch_names_for_this_package = [
        branch_ref.split('/')[1] for branch_ref in all_branch_refs
        if 'origin' in branch_ref and 'HEAD' not in branch_ref]

    # delete docker images that do not correspond to current branches for this package
    deleted_something = False
    for image_name in docker_images_for_this_package:
        if not any(image_name.endswith(branch_name) for branch_name in branch_names_for_this_package):
            log_message = log_prefix + f'Deleted image {image_name} from the Artifact repo'
            ' as there are no corresponding branches for it in the GitHub repo.'
            if dry_run:
                print('DRY RUN, NO ACTION TAKEN: ' + log_message)
            else:
                subprocess.check_output(
                    f'gcloud artifacts docker images delete {image_name} --delete-tags --quiet', shell=True)
                print(log_message)
                deleted_something = True

    if not deleted_something:
        print(log_prefix + 'Did not delete any images.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--package_name", type=str,
        help="The package name for which to prune docker images")

    parser.add_argument(
        "--dry_run", action="store_true",
        help="If true, print which images the script plans to delete but do not actually delete them.")

    parsed_args = parser.parse_args()
    main(package_name=parsed_args.package_name, dry_run=parsed_args.dry_run)
