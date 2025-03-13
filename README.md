![example workflow](https://github.com/earthwave/glambie/actions/workflows/glambie_test.yml/badge.svg)
![example workflow](https://github.com/earthwave/glambie/actions/workflows/glambie_deploy.yml/badge.svg)
# glambie
Public repository for the [Glacier Mass Balance Intercomparison Exercise (GlaMBIE)](https://glambie.org/).

## Installation
To start with, please ensure that you have some form of [Anaconda](https://www.anaconda.com/products/distribution)
installed (for Python 3.11). Earthwave prefers to use 
[Miniconda](https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh) on Linux.

Next, create a new conda environment:

```
conda create --name glambie python=3.11
conda activate glambie
```

### Installation For Use (requires Google Cloud authentication)
If you are willing to authenticate with the Google Cloud Platform, you can install this package without
having to clone this repository. This is a better option for those looking to simply use the software rather than develop it.
Note that you will need to authenticate with the Google Cloud anyway in order to access the submissions made to the GlaMBIE Submission System.

If you want to develop (i.e. change) this package, or you are unable to authenticate with the Google Cloud,
please read the "Installation For Development" section instead.

To work with the Google Cloud, first ensure that you have installed the [Google Cloud command line interface](https://cloud.google.com/sdk/docs/install).

Next, install the pip keyring backend necessary to authenticate with Google Cloud:
```
pip install keyrings.google-artifactregistry-auth
```

Authenticate with the google cloud in such a manner as to provide access to the GlaMBIE Submission System.
One means of doing this that works well in the terminal is:
```
gcloud auth application-default login
```

After that, you'll need to run:
```
gcloud auth application-default set-quota-project glambie
```

If you still experience access permissions errors when trying to load data from the GlaMBIE Submission System,
it is likely that you either intentionally do not have access (i.e. you are not a member of the GlaMBIE consortium),
or you have not yet requested access from [support@earthwave.co.uk](mailto:support@earthwave.co.uk).
When requesting access, please quote your full google email address.

The package can now be installed from the GlaMBIE Python Artifact repository: 
```
pip install glambie --extra-index-url https://europe-west1-python.pkg.dev/glambie/pr/simple
```

### Installation For Development (or when Google Cloud authentication is not possible)
To develop this package and/or install it without using the Google Cloud, you'll need to clone this repository locally.
To do this, you'll need to authenticate with GitHub either using a [public / private key pair](https://docs.github.com/en/authentication/connecting-to-github-with-ssh):
```
git clone git@github.com:earthwave/glambie.git
```

Or using a [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) in place of a password:
```
git clone https://github.com/earthwave/glambie.git
```

After cloning the repository, change directories into the newly created glambie folder.

Note that Earthwave uses VSCode (v1.69.1 at time of writing) as our integrated development environment. Earthwave's standard VSCode environment settings are included with this repository. If you wish to use VSCode, you'll need to install the Python and Pylance plugins, and [tell VSCode to use the interpreter within the environment you've just created](https://code.visualstudio.com/docs/python/environments#_select-and-activate-an-environment).

For a development install, ensure that you install all of the automated testing and linting requirements:
```
pip install -r .github/test_requirements.txt
```

Then install this package for development:
```
pip install -e .
```

You should now be able to run and pass the unit tests simply by running:
```
pytest
```

Note that you will still need to complete the `gcloud auth` steps described in the previous section
to use data from the GLaMBIE Submission System. 

Pushing directly to main is prohibited. If you wish your work to be included, first push a separate branch to
the repository and then open a Pull Request. All branches that have not received a commit for more than 30 days
will be automatically deleted.

Note that for security reasons related to Earthwave's servers, only approved contributors may push to this repository.
If you wish to make a contribution but find that you are unable to push, please email livia@earthwave.co.uk in order to request access.

## Running GlaMBIE

After completing the Installation instructions above, you can use this package as follows:
```
python -m glambie <config_file>
```

e.g. 
```
python -m glambie configuration/0_parent_config.yaml
```

## Versioning and releases
Versioning follows a simple model featuring three integers known as the major version, minor version and build number.
For example, in package version "v3.5.7", the major version is 3, the minor version is 5 and the build number is 7.

New versions of this package are automatically tagged and pushed to the Google Cloud Artifact Repo
when code is merged to main (i.e. when a Pull Request is closed). We also generate a GitHub release, although this is not otherwise used. Each new version will increment the build number
automatically. To change the major or minor build numbers, please change the contents of major_minor_version.txt.
Please also add a line in CHANGELOG.md (at the top of the file, so that reading down the file has the reader moving
backwards in time) at the same time describing what has been changed in the new major or minor version.

* The Major version should change when the package is entirely or almost entirely re-written.
This should happen every few years for a well-maintained package.
* The Minor version should change when new user-facing functionality is added to the package.
* The Build number should change whenever a bug is fixed or a small tweak is made to the package.

Note that the file `full_version.txt` should *not* exist in the repository, as it is automatically generated during deployment.

New releases are assigned a DOI via Zenodo.