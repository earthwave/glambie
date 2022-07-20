![example workflow](https://github.com/earthwave/glambie/actions/workflows/glambie_test.yml/badge.svg)
![example workflow](https://github.com/earthwave/glambie/actions/workflows/glambie_deploy.yml/badge.svg)
# glambie
Public repository for the [Glacier Mass Balance Intercomparison Exercise (GlaMBIE)](https://glambie.org/).

## Installation
You don't necessarily need to clone this repository to install this package.

To start with, please ensure that you have:

* Some form of [Anaconda](https://www.anaconda.com/products/distribution)
installed (for Python 3.9). Earthwave prefers to use 
[Miniconda](https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh) on Linux.
* the [Google Cloud command line interface](https://cloud.google.com/sdk/docs/install).

Next, create a new conda environment:

```
conda create --name glambie python=3.9.7
conda activate glambie
```

And install the pip keyring backend necessary to authenticate with
Google Cloud:

```
pip install keyrings.google-artifactregistry-auth
```

Authenticate with the google cloud. One means of doing this that works well in the terminal is:
```
gcloud auth login --no-launch-browser
```


### For Use
If you simply want to use this package, read this section. If instead you want to develop (i.e. change) this package,
please read the next section.

To use the package, simply install it from the GlaMBIE Python Artifact repository: 

```
pip install glambie --extra-index-url https://europe-west1-python.pkg.dev/glambie/pr/simple/ --use-deprecated=legacy-resolver
```

You can then use this package as follows (obviously you will need to edit this section after contributing initial work to the repository):

```
python -m glambie -a <number_a> -b <number_b>
```

For more help, run:

```
python -m glambie -h
```


### For Development
To develop this package, you'll need to clone it locally. To do this, you'll need to authenticate with GitHub either using a [public / private key pair](https://docs.github.com/en/authentication/connecting-to-github-with-ssh): 

```
git clone git@github.com:earthwave/glambie.git
```

Or using a [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) in place of a password:

```
git clone https://github.com/earthwave/glambie.git
```

After cloning the repository, change directories into the newly created glambie folder.

Note that Earthwave uses VSCode (v1.69.1 at time of writing) as our integrated development environment. Earthwave's standard VSCode environment settings are included with this repository. If you wish to use VSCode, you'll need to install the Python and Pylance plugins, and [tell VSCode to use the interpreter within the environment you've just created](https://code.visualstudio.com/docs/python/environments#_select-and-activate-an-environment).

For a development install, install all of the testing requirements:

```
pip install -r .github/test_requirements.txt
```

Then install this package for development:

```
pip install -e . --extra-index-url https://europe-west1-python.pkg.dev/glambie/pr/simple/ --use-deprecated=legacy-resolver
```

You should now be able to run and pass the unit tests simply by running:

```
pytest
```

Pushing directly to main is prohibited. If you wish your work to be included, first push a separate branch to
the repository and then open a Pull Request. All branches that have not received a commit for more than 30 days
will be automatically deleted.

Note that for security reasons related to Earthwave's servers, only approved contributors may push to this repository.

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
