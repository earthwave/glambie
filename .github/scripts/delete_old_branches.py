"""
Delete branches where the HEAD commit is older than x days, 30 by default.

This is mainly to keep the repository tidy, but also serves as a subtle incentive to complete Pull Requests.

Currently this script is written to use purely Python builtins and shell commands.
A bespoke CI container might improve this in future.
"""
import argparse
from datetime import datetime
import subprocess


def main(branch_age_limit_days: int, dry_run: bool) -> None:
    """
    Delete branches where the HEAD commit is older than a certain number of days.

    Parameters
    ----------
    branch_age_limit_days : int
        Will delete all branches where the HEAD commit is older than this number of days.
    dry_run : bool
        If true, will complete all the steps up to but not including the actual deletion of a branch, then stop.
    """
    log_prefix = 'While tidying branches: '

    # fetch a list of all branches
    all_branch_refs = subprocess.check_output('git fetch --prune && git branch -r', shell=True).decode().split('\n')

    # and extract just the branch names
    branch_names = [
        branch_ref.split('/')[1] for branch_ref in all_branch_refs
        if 'origin' in branch_ref and 'HEAD' not in branch_ref]

    # don't consider protected branches (but do consider branches that simply contain the words "master" or "main")
    for protected_branch_name in ('main', 'master'):
        if protected_branch_name in branch_names:
            branch_names.remove(protected_branch_name)

    # for each branch, get the time since the last commit
    # There are 86,400 seconds per day.
    deleted_something = False
    for branch_name in branch_names:
        posix_date_of_youngest_commit = int(subprocess.check_output(
            f'git log -n 1 origin/{branch_name} --date=unix | grep Date', shell=True
        ).decode().split()[1])
        days_since_last_commit = int((datetime.utcnow().timestamp() - posix_date_of_youngest_commit) // 86400)
        print(log_prefix + f'The last commit on remote branch {branch_name} was made {days_since_last_commit} '
              f'days ago, which is younger than the limit of {branch_age_limit_days} days.')

        if days_since_last_commit > branch_age_limit_days:
            # The branch is too old and will be deleted
            log_message = (log_prefix + f'Deleted branch {branch_name} because the last commit was '
                           f'{days_since_last_commit} days old, which is older than the limit of '
                           f'{branch_age_limit_days} days.')
            if dry_run:
                print('DRY RUN, NO ACTION TAKEN: ' + log_message)
            else:
                subprocess.check_output(f'git push origin --delete {branch_name}', shell=True)
                print(log_message)
                deleted_something = True

    if not deleted_something:
        print(log_prefix + 'Did not delete any branches.')


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--branch_age_limit_days", type=int, default=30,
        help="The script will delete branches whose most recent commit is older than this.")

    parser.add_argument(
        "--dry_run", action="store_true",
        help="If true, prints which branches the script plans to delete but do not actually delete them.")

    parsed_args = parser.parse_args()
    main(branch_age_limit_days=parsed_args.branch_age_limit_days, dry_run=parsed_args.dry_run)
