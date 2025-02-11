# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import pathlib
import re
import sys

from docutils.parsers.rst import directives
from sphinx.ext.autosummary import Autosummary, get_documenter
from sphinx.util.inspect import safe_getattr

sys.path.insert(0, f'{pathlib.Path(__file__).parents[2].resolve().as_posix()}/src')

import sys

project = 'MetaGen'
copyright = '2023, David Gutiérrez Avilés, José Francisco Torres, Manuel Jesús Jiménez-Navarro, and Francisco Martínez-Álvarez'
author = 'David Gutiérrez Avilés, José Francisco Torres, Manuel Jesús Jiménez-Navarro, and Francisco Martínez-Álvarez'

# The full version, including alpha/beta/rc tags
release = '0.2.0'

autosectionlabel_prefix_document = True
# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.autosummary',
    'sphinx.ext.autodoc',
    'sphinx.ext.graphviz',
    'sphinx.ext.inheritance_diagram',
    'sphinx_rtd_theme',
    'sphinx.ext.autosectionlabel'
]

# Numbering of figures, tables and code-blocks
numfig = True
numfig_format = {
    'figure': 'Figure %s'  # Sin punto en ambas por defecto
}


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

# html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_css_files = ['css/custom.css']

autodoc_mock_imports = ["sklearn","rs"]
autodoc_member_order = 'bysource'
add_module_names = False
autoclass_content = 'both'
autosummary_generate = True

