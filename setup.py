import os

from setuptools import find_packages
from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

if os.path.exists("full_version.txt"):
    with open("full_version.txt", "r", encoding="utf-8") as fh:
        """
        Note that this file is generated by the CI chain based on the git tag
        (by .github/scripts/define_new_version_number.py)
        It should not be present in the repository by default.
        """
        version_number = fh.read()
else:
    version_number = 'v0.0.0'  # default value when under development

setup(
    name='glambie',
    version=version_number,
    description='Public software developed for the Glacier Mass Balance Intercomparison Exercise (GlaMBIE)',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Earthwave Ltd',
    author_email='info@earthwave.co.uk',
    url='https://github.com/earthwave/glambie',
    python_requires=">=3.11",
    license='MIT',
    packages=find_packages(),
    # note requirements listed ininstall_requires should be the *minimum required*
    # in order to allow pip to resolve multiple installed packages properly.
    # requirements.txt should contain a specific known working version instead.
    install_requires=[
        'google-cloud-storage',
        'numpy>1.15',
        'pandas>1.2',
        'matplotlib>3.0',
        'scipy>1.6',
        'pyyaml'
    ],
)
