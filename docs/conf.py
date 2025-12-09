"""
Sphinx configuration for Contacts REST API documentation.

Notes:
- This file uses Sphinx-required lowercase variables (e.g., `project`, `author`,
  `release`, `html_theme`). Pylint's invalid-name is disabled to avoid false
  positives for these names.
"""
# pylint: disable=invalid-name

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# Signal code that we are in a docs build to avoid side-effects (like DB connections)
os.environ.setdefault("SPHINX_BUILD", "True")

project = 'Contacts REST API'
COPYRIGHT = '2025, Oleksandr Simakhin'
globals()['copyright'] = COPYRIGHT

author = 'Oleksandr Simakhin'
release = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]

# Render both Google-style and NumPy-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True

# Avoid importing heavy/optional deps during doc build
autodoc_mock_imports = [
    'fastapi',
    'sqlalchemy',
    'passlib',
    'jose',
    'email_validator',
    'cloudinary',
    'redis',
    'slowapi',
    'pydantic',
]

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': False,
    'show-inheritance': True,
}

autodoc_typehints = 'description'
autodoc_typehints_format = 'short'

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'pyramid'
html_static_path = ['_static']
