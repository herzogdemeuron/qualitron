# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import datetime
import revitron_sphinx_theme

sys.path.insert(0, os.path.abspath('../..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../lib'))

project = 'Qualitron'
copyright = '2022, Yskert Schindel'
author = 'Yskert Schindel'
release = '0.1'

master_doc = 'index'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.coverage',
]

autodoc_mock_imports = ['revitron', 'pyrevit', 'Autodesk', 'clr', 'System', 'Microsoft', 'wpf']

add_module_names = False

napoleon_google_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

templates_path = ['_templates']
exclude_patterns = ['modules.rst']

ogp_site_url = "https://qualitron.readthedocs.io/"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'revitron_sphinx_theme'
html_theme_options = {
    'navigation_depth': 2,
    'github_url': 'https://github.com/qualitron/qualitron',
    'color_scheme': 'dark'
}

html_logo = '_static/qualitron.png'
html_title = 'Qualitron'

html_static_path = ['_static']
