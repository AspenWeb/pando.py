#!/usr/bin/env python
"""Model the life-cycle of an application as a series of four modes.

It is often valuable to maintain a distinction between various phases of an
application's lifecycle. This module calls these phases "modes," and identifies
four of them, given here in conceptual life-cycle order:

    debugging       The application is being actively debugged; exceptions
                      may trigger an interactive debugger.

    development     The application is being actively developed; however,
                      exceptions should not trigger interactive debugging.

    staging         The application is deployed in a mock-production
                      environment.

    production      The application is in live use by its end users.


The expectation is that various aspects of the application -- logging, exception
handling, data sourcing -- will adapt to the current mode. The mode is set in
the PYTHONMODE environment variable. This module provides API for interacting
with this variable. If PYTHONMODE is unset, it will be set to development when
this module is imported.

Functions

    get     Return the current PYTHONMODE setting as a lowercase string; will
              raise EnvironmentError if the (case-insensitive) setting is not
              one of debugging, development, staging, or production.

    set     Given a mode, set the PYTHONMODE environment variable and refresh
              the module's boolean members. If given a bad mode, ValueError is
              raised.

    setAPI  Refresh the module's boolean members. Call this if you ever change
              PYTHONPATH directly in the os.environ mapping.

Members

    The module defines a number of boolean attributes reflecting the current
    mode setting, including abbreviations and combinations. Uppercase versions
    of each of the following are also defined (e.g., DEBUGGING).

        Name                        True if PYTHONMODE is set to ...
        -----------------------------------------------------------------------
        debugging                   debugging
        deb                         debugging

        development                 development
        dev                         development

        staging                     staging
        st                          staging

        production                  production
        prod                        production

        debugging_or_development    debugging or development
        debdev                      debugging or development
        devdeb                      debugging or development

        staging_or_production       staging or production
        stprod                      staging or production


Example usage:

    >>> import mode
    >>> mode.set('development')     # can set the mode at runtime
    >>> mode.get()                  # and access the current mode
    'development'
    >>> mode.development            # module defines boolean constants
    True
    >>> mode.PRODUCTION             # uppercase versions are also defined
    False
    >>> mode.dev                    # as are abbreviations
    True
    >>> mode.DEBDEV, mode.stprod    # and combinations
    (True, False)


"""
__author__ = "Chad Whitacre <chad@zetaweb.com>"
__version__ = "1.0a1+"


import os


options = ('debugging', 'development', 'staging', 'production')
abbrevs = ('deb', 'dev', 'st', 'prod')
default = 'development'


def get():
    """Return the current mode.

    If PYTHONMODE is unset, it will default to development. If PYTHONMODE is set
    to an invalid value, EnvironmentError is raised.

    """
    mode = os.environ.get('PYTHONMODE', None)
    if mode is None:
        mode = os.environ['PYTHONMODE'] = default
    else:
        mode = mode.lower()
    if mode not in options:
        raise EnvironmentError("PYTHONMODE set to bad value '%s'" % mode)
    return mode


__globals = globals()
def setAPI():
    """Set the module's boolean attributes.
    """
    global __globals
    g = __globals


    # Basic API
    # =========
    # e.g., development

    mode = get()
    for name in options:
        boolean = mode == name
        g[name.lower()] = boolean # development = True
        g[name.upper()] = boolean # PRODUCTION = False


    # Abbreviations
    # =============
    # e.g., dev

    g['deb'] = g['DEB'] = g['debugging']
    g['dev'] = g['DEV'] = g['development']
    g['st'] = g['ST'] = g['staging']
    g['prod'] = g['PROD'] = g['production']


    # Combinations
    # ============
    # e.g., debugging_or_development

    debdev = g['deb'] or g['dev']
    g['debugging_or_development'] = debdev
    g['DEBUGGING_OR_DEVELOPMENT'] = debdev
    g['debdev'] = g['DEBDEV'] = debdev
    g['devdeb'] = g['DEVDEB'] = debdev
    stprod = g['staging'] or g['production']
    g['staging_or_production'] = stprod
    g['STAGING_OR_PRODUCTION'] = stprod
    g['stprod'] = g['STPROD'] = g['staging_or_production']

setAPI()


def set(mode):
    """Set the current mode.

    If mode is not one of debugging, development, staging, or production,
    ValueError is raised. After setting the variable, we refresh this module's
    boolean API.

    """
    _mode = mode.lower()
    if _mode not in options:
        raise ValueError("Bad PYTHONMODE '%s'" % mode)
    os.environ['PYTHONMODE'] = _mode
    setAPI()


if __name__ == '__main__':
    """Test the module.
    """

    import sys
    sys.stderr.write("testing...")


    # Basic exercises
    # ===============

    set('debugging')
    mode = get()
    assert mode == 'debugging'
    assert debugging
    assert DEBUGGING
    assert not development
    assert not DEVELOPMENT
    assert not staging
    assert not STAGING
    assert not production
    assert not PRODUCTION
    assert devdeb
    assert not stprod

    set('development')
    mode = get()
    assert mode == 'development'
    assert not debugging
    assert not DEBUGGING
    assert development
    assert DEVELOPMENT
    assert not staging
    assert not STAGING
    assert not production
    assert not PRODUCTION
    assert devdeb
    assert not stprod

    set('production')
    mode = get()
    assert mode == 'production'
    assert not debugging
    assert not DEBUGGING
    assert not development
    assert not DEVELOPMENT
    assert not staging
    assert not STAGING
    assert production
    assert PRODUCTION
    assert not devdeb
    assert stprod

    set('staging')
    mode = get()
    assert mode == 'staging'
    assert not debugging
    assert not DEBUGGING
    assert not development
    assert not DEVELOPMENT
    assert not production
    assert not PRODUCTION
    assert staging
    assert STAGING
    assert not devdeb
    assert stprod


    # Abbreviations
    # =============

    set('debugging')
    assert deb
    assert DEB
    assert not dev
    assert not DEV
    assert not st
    assert not ST
    assert not prod
    assert not PROD

    set('development')
    assert not deb
    assert not DEB
    assert dev
    assert DEV
    assert not st
    assert not ST
    assert not prod
    assert not PROD

    set('staging')
    assert not deb
    assert not DEB
    assert not dev
    assert not DEV
    assert st
    assert ST
    assert not prod
    assert not PROD

    set('production')
    assert not deb
    assert not DEB
    assert not dev
    assert not DEV
    assert not st
    assert not ST
    assert prod
    assert PROD




    # Combinations
    # ============

    set('debugging')
    assert devdeb
    assert DEVDEB
    assert debdev
    assert DEBDEV
    assert debugging_or_development
    assert DEBUGGING_OR_DEVELOPMENT
    assert not stprod
    assert not STPROD
    assert not staging_or_production
    assert not STAGING_OR_PRODUCTION

    set('development')
    assert devdeb
    assert DEVDEB
    assert debdev
    assert DEBDEV
    assert debugging_or_development
    assert DEBUGGING_OR_DEVELOPMENT
    assert not stprod
    assert not STPROD
    assert not staging_or_production
    assert not STAGING_OR_PRODUCTION

    set('staging')
    assert not devdeb
    assert not DEVDEB
    assert not debdev
    assert not DEBDEV
    assert not debugging_or_development
    assert not DEBUGGING_OR_DEVELOPMENT
    assert stprod
    assert STPROD
    assert staging_or_production
    assert STAGING_OR_PRODUCTION

    set('production')
    assert not devdeb
    assert not DEVDEB
    assert not debdev
    assert not DEBDEV
    assert not debugging_or_development
    assert not DEBUGGING_OR_DEVELOPMENT
    assert stprod
    assert STPROD
    assert staging_or_production
    assert STAGING_OR_PRODUCTION


    # Other tests
    # ===========

    del os.environ['PYTHONMODE']                     # should revert to default
    try:
        mode = os.environ['PYTHONMODE']
    except KeyError:
        pass
    setAPI()                        # this calls get(), which resets PYTHONMODE
    assert not debugging
    assert development
    assert not staging
    assert not production

    try:
        assert DeBugging
    except NameError:
        pass

    try:
        set('BLAGGITY')
    except ValueError:
        pass

    try:
        os.environ['PYTHONPATH'] = 'BLOOGITY'
        get()
    except EnvironmentError:
        pass

    set('DEVELOPMENT') # canonicalized to lowercase
    assert get() == 'development'


    # Doctest first
    # =============

    import doctest
    failures, tests = doctest.testmod()
    if failures > 0:
        raise SystemExit


    # w00t!
    # =====

    sys.stderr.write("all pass!\n")
