# -*- coding: utf-8 -*-
#
# Pando documentation build configuration file, originally created by
# sphinx-quickstart on Mon Feb 24 15:00:43 2014.
#
# This file is exec()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this file.

import sys, os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('..'))


# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.intersphinx',
    'sphinx.ext.todo', 'sphinx.ext.coverage', 'sphinx.ext.ifconfig'
]

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'Pando'
copyright = u'2016, Chad Whitacre et al.'

# The full version, including alpha/beta/rc tags.
release = open('../version.txt').read().strip()
# The short X.Y version.
version = release.split('-', 1)[0]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# -- Autodoc options

autodoc_default_flags = ['members', 'undoc-members', 'special-members']
autodoc_member_order = 'bysource'

_autodoc_exclusions = {
    '__weakref__',  # special-members
    '__doc__', '__module__', '__dict__',  # undoc-members
    '__subclasshook__',  # inherited-members
}

text_type = unicode if sys.version_info[0] < 3 else str

def autodoc_skip_member(app, what, name, obj, skip, options):
    return (
        skip or
        name in _autodoc_exclusions or
        ( # __init__ with missing or empty doctsring, no point in showing it
            what in ('class', 'exception') and
            name == '__init__' and
            not obj.__doc__
        ) or
        options.inherited_members and (
            # inherited-members adds a lot of crap, we filter it here
            str(obj).startswith('<built-in method ') or
            obj is getattr(object, name, None) or
            obj is getattr(dict, name, None) or
            obj is getattr(int, name, None) or
            obj is getattr(bytes, name, None) or
            obj is getattr(text_type, name, None)
        )
    )

def setup(app):
    app.connect('autodoc-skip-member', autodoc_skip_member)


# -- Options for HTML output ---------------------------------------------------

import sphinx_rtd_theme
html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# Output file base name for HTML help builder.
htmlhelp_basename = 'Pandodoc'


# -- Options for LaTeX output --------------------------------------------------

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'Pando.tex', u'Pando Documentation',
   u'Chad Whitacre et al.', 'manual'),
]


# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'pando', u'Pando Documentation',
     [u'Chad Whitacre et al.'], 1)
]


# -- Options for Texinfo output ------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  ('index', 'Pando', u'Pando Documentation',
   u'Chad Whitacre et al.', 'Pando',
   'A Python web framework based on filesystem routing.',
   'Miscellaneous'),
]


# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'python': ('https://docs.python.org/3.5/', None),
    'aspen': ('http://core.aspen.io/en/latest/', None),
}
