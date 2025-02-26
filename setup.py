import os
from pathlib import Path
from setuptools import find_packages, setup
from codecs import open as codecs_open

about = {}
base_path = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    return Path(__file__).resolve().parent.joinpath(*parts).read_text().strip()


with codecs_open(os.path.join(base_path, "src", "unifi_sync", "__version__.py"), "r", "utf-8") as f:
    exec(f.read(), about)

with codecs_open("README.md", "r", "utf-8") as f:
    readme = f.read()

with codecs_open("CHANGELOG.md", "r", "utf-8") as f:
    changelog = f.read()

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=readme,
    long_description_content_type="text/markdown",
    platforms=["macOS", "POSIX", "Windows"],
    author=about['__author__'],
    python_requires=">=3.8",
    url=about['__url__'],
    author_email=about['__author_email__'],
    license=about['__license__'],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires={},
    include_package_data=True,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
        "Development Status :: 5 - Production/Stable",
    ],
    project_urls={
        "Documentation": about['__url__'],
        "Source": about['__git_project__'],
    },
)
