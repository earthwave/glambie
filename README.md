![example workflow](https://github.com/earthwave/glambie/actions/workflows/glambie_test.yml/badge.svg)
![example workflow](https://github.com/earthwave/glambie/actions/workflows/glambie_deploy.yml/badge.svg)
# glambie
Public repository for the [Glacier Mass Balance Intercomparison Exercise (GlaMBIE)](https://glambie.org/).

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
pip install glambie --extra-index-url https://europe-west1-python.pkg.dev/glambie/pr/simple/ --use-deprecated=legacy-resolver
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
pip install -e . --extra-index-url https://europe-west1-python.pkg.dev/glambie/pr/simple/ --use-deprecated=legacy-resolver
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
