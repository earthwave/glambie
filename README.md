![example workflow](https://github.com/earthwave/glambie/actions/workflows/glambie_test.yml/badge.svg)
![example workflow](https://github.com/earthwave/glambie/actions/workflows/glambie_deploy.yml/badge.svg)
# glambie
This repository serves as a template for the creation of new Earthwave Python Packages.
Please copy this template (the entire repository) to create all new Earthwave Python Packages.

This template is intended to support the development of a Python Package specifically, so its interpretation
of "deployment" / "production" is the uploading of a new version of a package to the Google Python Artifact Registry.
It does not cover all of the work needed to upload a containerised service to a Kubernetes Cluster.

## Adapting the template for your project
### Making a copy of the template
If you're unfamiliar with GitHub or with CI/CD, please ask a Software Engineer to help you set up this template. You should start by hitting the "Use This Template" button and creating a new repository with your preferred package name. Remember to carefully consider the name! 

### Updating the names in the template and triggering the first successful workflow
The next thing you should do is clone the repository and make a single commit to a **new branch** in which you have changed both "glambie"  to "\<your new package\>" everywhere in the code, including for **file names and folder names**. Remember also to look for "glambie" and change those instances as well. It is important to make this change now, or you won't be able to set up branch protection later.

Push this change and wait for the CI chain to complete succesfully (a green tick on the actions page). This should take a few minutes at most. Once that happens, merge your first branch to main and delete it. You should see the deploy stage completing succesfully and the first version of your new package being published to the [Google Python Artifact Registry](https://console.cloud.google.com/artifacts/python/earthwave-sys-0/europe-west1/ewpr).
Look under the "actions" tab for a green tick. if you see an orange circle, wait for it to finish and result in a green tick (you may need to refresh the page).

If you see one red x (the first run, a failed "deploy") and two green ticks, you're ready to proceed. If not, go back and make sure you've updated all instances of "glambie" and "glambie", including for file names and folder names, and push again.

### Updating the General settings
you should now change some settings for your new repository. Hit "Settings" from the top menu and then "General" on the left menu.

Ensure the following are *not* ticked:
* Template repository
* Require contributors to sign off on web-based commits
* Wikis
* Issues
* Projects
* Allow squash merging
* Allow rebase merging

Ensure the following *are* ticked:
* Always suggest updating pull request branches
* Allow auto-merge
* Automatically delete head branches

### Setting up Collaborators and teams
In order for the GitHub Code Owners feature to work with GitHub teams,
teams need to be given explicit write access to the repository. The Base Role does not cover this.
Under the "Collaborators and Teams" tab, add at minimum the engineering team (with admin privileges),
plus any additional teams that are relevant to the repository.

### Setting up branch protection
The next thing you need to set up is branch protection rules. These are *not* automatically copied over
from the template repository. Hit "Settings" from the top menu, then "branches" on the left menu, then "add rule" on the right.
Only one branch protection rule needs to be added (for main).
You can see the correct configuration [here, in the branch protection rules for the template](https://github.com/earthwave/glambie/settings/branch_protection_rules/26319410). Type "main" into the Branch name pattern box.

Ensure the following *are* ticked:
* Require a pull request before merging
* Require approvals (and set the Required number of approvals before merging to 1)
* Require status checks to pass before merging
* Require branches to be up to date before merging
* Select the following status checks:
    * test / build_test
    * test / lint
    * test / unit_test
* Require conversation resolution before merging
* Include administrators

Ensure that none of the other options are ticked.

### Adopting a working standard
Earthwave works to three software standards: Null, Basic and Operational.
You'll need to select a standard to work to based upon what kind of project you're completing,
and then apply the steps described below.

#### **Working to the Null Standard**
The Null Standard is a standard that does not have any particular requirements. It represents full laissez faire development. 
This standard is only appropriate for code that you are **almost certain** will never be used by anyone other than you. 
If there's anyone else working on the project, you should adopt the Basic Standard. If you expect any of the code
the project produces to be re-used in any other project (even a later iteration of the current project),
you should adopt the Basic Standard.

As the Null Standard has no requirements, there's no need for you to use this template to work to the Null Standard.
Simply create a new repository and enjoy!

#### **Working to the Basic Standard**
Most Earthwave projects should be completed to at least the Basic Standard. This Standard is for any project that is 
intended to last more than a few months, or be completed by more than one individual. Even if you are working on a 
small project alone, we strongly recommend that you work to this standard.

Consider updating the default `.github/CODEOWNERS` file to reflect the people working on your project.
Try to organise your project via a [GitHub Team](https://docs.github.com/en/organizations/organizing-members-into-teams/about-teams)
rather than listing individuals, as it is easier to add and remove people from a GitHub team rather than from
a number of different repositories. The syntax is described [in GitHub's documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners).
When you open a Pull Request, reviews will automatically be requested from the people and teams in that file.

If you're working at the Basic Standard, you should be able to use the template for your project without modifying
anything in the `.github` directory. Various VSCode settings are baked into this template in the `.vscode` directory.

For simplicity, please hit the "Use This Template" button on GitHub itself, rather than cloning and
then re-uploading this repository.

#### **Working to the Operational Standard**
Many Earthwave projects should be completed to the Operational Standard. This standard is for any project that 
contributes to the production of an operational product or service (whether intentionally or not). If you're working 
to the higher Operational Standard, you need to swap in two files:
1. Delete `.github/test_requirements.txt` and rename `.github/test_requirements_operational.txt` to `.github/test_requirements.txt`.
2. Delete `setup.cfg` and rename `setup_operational.cfg` to `setup.cfg`.

Additionally, delete the line `notebooks_allowed: true` from `.github/workflows/glambie_test.yml`

This repository is written to the Basic Standard, and so will not pass the CI chain at the Operational Standard.
You'll need to make some improvements first, as indicated by the CI chain.

### Final updates
Note that after you've finished adapting the template for your use, you should re-write this README file so that it
discusses your project in more detail. You should update the project description in setup.py for the same reason.

## Installation for Use
If you simply want to use this package, read this section. If instead you want to develop (i.e. change) this package,
please read the next section. If you don't know what a Conda environment is or how to use one, please stop here and
ask one of the Earthwave software engineers to help you out. 

Note that this section does not explain how to setup a Conda environment, because we assume that if you're
simply using the package, you're already using Earthwave's standard dev environment, or an unrelated environment. 
If you're having to setup an environment yourself anyway, follow the environment setup instructions
in the next section before continuing here.

To install this package into your local Conda
(or other Python) environment, first install the pip keyring backend necessary to authenticate with
Google Cloud (if you haven't already):

```
pip install keyrings.google-artifactregistry-auth
```
Authenticate with the google cloud (one means of doing this that works well over an ssh terminal is
to run `gcloud auth login --no-launch-browser` and follow the simple instructions) and then download and install
the latest version from the Earthwave Python Google Artifact Repository:

```
pip install glambie --extra-index-url https://europe-west1-python.pkg.dev/earthwave-sys-0/ewpr/simple/ --use-deprecated=legacy-resolver
```

You can then use this package as follows (obviously you will need to edit this section after copying this template):

```
python -m glambie -a <number_a> -b <number_b>
```

For more help, run:

```
python -m glambie -h
```


## Installation for Development
To develop this package, please clone the repository:

```
git clone https://github.com/earthwave/glambie.git
cd glambie
```

Then create a new conda environment:

```
conda create --name my_env python=3.9.7
conda activate my_env
```

If you're using VSCode, note that you'll need to [tell VSCode to use the interpreter within the environment you've just created](https://code.visualstudio.com/docs/python/environments#_select-and-activate-an-environment).

Then install all of the testing requirements:

```
pip install -r .github/test_requirements.txt
```

Next, install the google artifact repo keyring backend for pip:

```
pip install keyrings.google-artifactregistry-auth
```

Authenticate with the google cloud (one means of doing this that works well over an ssh terminal is
to run `gcloud auth login --no-launch-browser` and follow the simple instructions) and then download and install
the latest version from the Earthwave Python Google Artifact Repository:

Then finally install this package for development:

```
pip install -e . --extra-index-url https://europe-west1-python.pkg.dev/earthwave-sys-0/ewpr/simple/ --use-deprecated=legacy-resolver
```

You should now be able to run and pass the unit tests simply by running:

```
pytest
```

Pushing directly to main is prohibited. If you wish your work to be included, first push a separate branch to
the repository and then open a Pull Request. All branches that have not received a commit for more than 30 days
will be automatically deleted.

## Versioning and releases
Versioning follows a simple model featuring three integers known as the major version, minor version and build number.
For example, in package version "v3.5.7", the major version is 3, the minor version is 5 and the build number is 7.

New versions of this package are automatically tagged and pushed to the Google Cloud Artifact Repo
when code is merged to main (i.e. when a Pull Request is closed). We don't geneate GitHub releases as this would
represent a duplication of the Google Cloud Repo. Each new version will increment the build number
automatically. To change the major or minor build numbers, please change the contents of major_minor_version.txt.
Please also add a line in CHANGELOG.md (at the top of the file, so that reading down the file has the reader moving
backwards in time) at the same time describing what has been changed in the new major or minor version.

* The Major version should change when the package is entirely or almost entirely re-written.
This should happen every few years for a well-maintained package.
* The Minor version should change when new user-facing functionality is added to the package.
* The Build number should change whenever a bug is fixed or a small tweak is made to the package.

Note that the file `full_version.txt` should *not* exist in the repository, as it is automatically generated during deployment.
