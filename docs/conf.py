# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# Insert path into the system.
import sys
import os

sys.path.insert(0, os.path.abspath('../src'))

from unifi_sync import UnifiSyncClient

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = UnifiSyncClient.__title__
copyright = UnifiSyncClient.__copyright__
author = UnifiSyncClient.__author__
version = UnifiSyncClient.__version__
release = UnifiSyncClient.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

extensions = [
    'sphinx_rtd_theme',
    'sphinx.ext.autodoc',
]

html_theme = "sphinx_rtd_theme"

html_theme_options = {
    'version_selector': True,
    'language_selector' : True,
}

rst_prolog = f"""
.. |git_project| replace:: {UnifiSyncClient.__git_project__}
.. |git_repo| replace:: {UnifiSyncClient.__git_repo__}
.. |git_repouser| replace:: {UnifiSyncClient.__git_repouser__}
.. |git_reponame| replace:: {UnifiSyncClient.__git_reponame__}
.. |description| replace:: {UnifiSyncClient.__description__}
.. |title| replace:: {UnifiSyncClient.__title__}
"""
