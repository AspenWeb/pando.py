Pando Changelog
===============

0.45 - Released Mon Jan 28 2019 by @Changaco
--------------------------------------------

* BREAKING: invert the type hierarchy of `request.line` (#576)

* BREAKING: move `pando.algorithms.website` to `pando.state_chain` (#573)

* check HTTP method of requests for static files (#586)

* fix request parsing (#585)

* improve handling of request body (#578)

* work around a virtualenv bug (#577)

* improve the docs (#570, #572, #575)

* upgrade to aspen 1.0rc3 (#569 and #582)

0.44 - Released Fri Sept 9 2016 by @Changaco
--------------------------------------------

* bring back whence_raised (the location a Response was raised from) (#567)

* improve compatibility with different WSGI servers (#566)

* clean up logging (#565)

* drop `Response.charset` attribute (#563)

* switch basic test client from stateful to stateless (#564)

* fix dispatch redirects (#562)

0.43 - Released Wed Sept 7 2016 by @Changaco
--------------------------------------------

* rename from Aspen to Pando (#552) and use the new `aspen` library (#556)

* add support for python 3 (#544, #559)

* switch to stdlib `logging` module (#522)

* add no-op functions to website algorithm for easy hookage (#523)

* improve simplate interpretation (#516, #517, #518)

* add all the RFC2616 HTTP methods to the test client (#558)

* allow `Response` subclasses to modify `__str__()` (#555)

* simplify HTTP headers handling (#554)

0.42 - Released Thu Sept 10 2015 by @whit537
--------------------------------------------

* the repo is now named `aspen.py` instead of `aspen-python` (#485)

* extend the test client to support file uploads (#508)

* speclines are no longer required in simplates (#296)

* upgrade mimeparse, ahead of porting to Python 3 (#500)

* add a website.colorize_tracebacks option (#501)

* drop support for Python 2.6 (#497)

* refactor simplates internally ahead of splitting them out (#481)

* port to Windows (#482)

* protect against URL redirection attacks (#471)


0.41 - Released Thu Jul 2 2015 by @whit537
------------------------------------------

* fix a regression in simplate scoping introduced in 0.38 (#463)


0.40 - Released Mon Jun 29 2015 by @whit537
-------------------------------------------

* fix a regression in aspen.wsgi introduced in 0.39 (#460)


0.39 - Released Mon Jun 29 2015 by @whit537
-------------------------------------------

* fix two security bugs related to CRLF injection
  https://github.com/gratipay/security-qf35us/issues/1

* remove argv-based configuration; Website now takes kwargs instead (#455)

* remove exec-based configuration, i.e., configure-aspen.py (#373); use kwargs
  to Website or environment variables instead

* add a base_url configuration setting and use it in a new algorithm
  function, redirect_to_base_url (#457)

* improve the redirect API: it's now at website.redirect instead of
  request.redirect; it honors the new website.base_url; and it takes an 
  optional response object (#458)


0.38 - Released Tue Jun 23 2015 by @pjz
---------------------------------------

* refactor aspen.__main__ into aspen.serve()

* alias 'website' as 'application' in aspen.wsgi to better support some WSGI servers

* finish removing request.fs since we now have state['dispatch_result'].match

* update dependencies

* Add an autosphinx target to help sphinx migration

* prevent simplate locals from implictly leaking into `state` (#427) (Thanks Changaco!)

0.37 - Released Wed Feb 18 2015 by @pjz
---------------------------------------

* Fix some return types during error handling (#406, #398)

* Make simplates a bit more separate from Aspen (#412)

* Use algorithm state as request context

* Make convenience aliases in request context read-only (#414)

* Generate html test coverage report (Thanks Changaco!)

* Python 3 fixes to build.py and fabricate.py (Thanks Changaco!)

0.36 - Released Mon Dec 15 2014 by @pjz
---------------------------------------

* Don't return a 415 when the body is empty (Thanks @Changaco!)

* Simplify the simplate class hierarchy

* Don't show scary tracebacks when pygments is missing (#268)

* Let custom typecasters access global state. (#395)

0.35 - Released Thu Oct 30 2014 by @whit537
-------------------------------------------

* Fixes a bug in error handling (#393)

* Restores request.context (#392)

* Introduces a dispatch_result object (#389)

* Refactors the dispatcher (#389)

* Removes the request.fs attribute (#389)

* Removes the request.website attribute (#385)

* Makes the Canonizer utility more configurable (#382)

* Refactors request body parsing (#377)

* Removes `thrash` utility (#376)

* Adds support for PORT envvar to `python -m aspen` (#356)

* Fixes a bug in header parsing (#369)

0.34 - Released Tue Jul 29 2014 by @pjz
---------------------------------------

* Finally fix the dispatcher to fully work with .spt files

* Add a data-driven test suite for the dispatcher

* Add a jsonp_dump renderer

0.33 - Released Tue Jul 8 2014 by @whit537
-------------------------------------------

* Cleans up implicit casting to unicode in headers (#364)

* Fixes regression w/ request bodies in test client (#360)

* Fixes bug in request logging during exception handling (#291)

* Fixes to the aspen.io site

0.32 - Released Mon May 12 2014 by @pjz
---------------------------------------

* Fixes to the aspen.io site (Thanks @BigBlueHat!)

* Make HTTP dates always end in GMT (Thanks @Changaco!)

* Clean up error.spt a bit wrt pygmentation and show_traceback interactions

0.31 - Released Tue May  6 2014 by @pjz
---------------------------------------

* Aspen server is gone! Aspen is now a pure-WSGI app!
  ...well, okay, for dev purposes it'll run under wsgiref via
  python -m aspen

* Socket.IO support is gone! ..but not forgotten. We'll get it
  back someday, when there's a sane way to do so.

* The datapath is now much more unicode-clean

* Simplate files can now specify their encodings

* Tweaks to work better under windows (thanks @BigBlueHat!)

* Documentation is moving toward Sphinx!

* JSON support was moved into a renderer. It's no longer a special
  simplate type.

0.30 - Released Wed Mar 19 2014 by @pjz
---------------------------------------
    
* Fix traceback handling - thanks @Changaco

* Fix #267 - 404 on requests for .spt files

0.29 - Released Mon Feb 17 2014 by @pjz
---------------------------------------

* Only support negotiated simplates for errors - this simplifies the error path

* Update packaging tools and packages to be somewhat modern (thanks @Ivoz!)

0.28.3 - Released Thu Jan  9 2014 by @whit537
---------------------------------------------

* Fix bug where we were preventing tracebacks from reaching either the console
  or the browser.

* Return 400 from anti-CRLF-injection instead of 500

0.28.2 - Released Sat Jan  4 2014 by @pjz
-----------------------------------------

* Fix bug in aspen.testing.pytest_fixtures required to be fixed for
  aspen-python-plugins tests to work

0.28.1 - Released Thu Dec 19 2013 by @whit537
---------------------------------------------

* Fix regressions in server.py exception handling

0.28 - Released Thu Dec 19 2013 by @pjz
-----------------------------------------

* Update to a newer version of Algorithm

* Started using standalone filesystem_tree module

* Clean up test harness and test client to be more usable

* Add extensible typecasting for virtual path segments

0.27 - Released Tue Nov 26 2013 by @pjz
-----------------------------------------

* Major internal refactoring to use Algorithm and py.test with fixtures

* Much-improved aspen TestClient and use it for aspen's own tests

* Switch hook filters to be algorithm/flow filters

* fixed #250 - 500 if file is treated as a path

* fixed #242 - Rename UnicodeWithParams to PathParts

0.26.1 - Released Wed Oct 2 2013 by @pjz
----------------------------------------

* fixed a bug in unicode handling that broke cookies

* Allow rendered json simplates to specify per-file content-types (Thanks @ArmstrongJ!) 

* Fix #232 - doc server doesn't start - by updating doc/README with current instructions

0.26 - Released Fri Sep 27 by @pjz
----------------------------------

* Fixed #226 - converted from nosetests to py.test - this got us much
  nicer assert handling for debugging.

* Fixed #225 - added 'from future' imports to the whole thing to 1) prep
  for py3k and 2) help fix unicode handling (Thanks @nejstastnejsistene !)

* Fixed #42 - added support for rfc2396 key/value pairs in URLs (tl;dr is
  that /foo;a=b;a=c;d=e/ will go to /foo/ with an easy way to get the values
  of a (==['b','c']) and d (==['e'])

* Added some CRLF-injection protection (Thanks Berkay Aydin!)

* Added module entrypoint to allow 'python -m aspen.server' (Thanks @jaraco !)

* Fixed #165 - make it explicit which variables are available to templates
  By default all variables are available.  If you want to limit that, put
  the list of variable names in `__all__`


0.25.3 - Released 2013-08-09 by @whit537
----------------------------------------

* Fixed #212 - don't wrongly swallow IOError in configure-aspen.py

* Fixed #210 - better error message for negotiated simplate with not enough 
  pages

* Fixed #209 - tracebacks for raise Response are scary


0.25.2 - Released 2013-07-22 by @whit537
----------------------------------------

* Fixed #207 - we shouldn't strict_parse request bodies


0.25.1 - Released 2013-06-21 by @pjz
------------------------------------

A fairly minor release... unless you were hit by one of the now-fixed bugs:

* Fixed #195 - qs drops URL Encoded + and & signs

* Fixed #196 - hangs w/ gevent on Ctrl-C

* Changed redirects to be less-permanent 302s instead of 301s

* Fixed issue #175 - redirect default index files to / ; 
  Makes URLs prettier!

* Fix configuration parser list-parsing bug discovered while fixing #175. 
  The configuration parser was preserving empty-string items in its
  parsing of comma-separated lists.

* Fixed the heroku config (used for the aspen.io site) to explicitly require
  aspen-tornado since it's no longer installed by default


0.25.0 - Released 2013-06-14 by @pjz
------------------------------------

* The major change in this release is that renderers and network engines
  have both been moved to external modules.  This means that dependencies
  for aspen are now much better defined, as the plugins (aspen-* on PyPi)
  are essentially a small bit of glue code and a 'requires' on the external
  dependency, instead of the previous state where all the glue code was
  internal to the 'aspen' package and there was no 'requires' anywhere to
  say which version the glue was for.

* The other major change was the dropping of python 2.5 support - it just
  got too troublesome. Aspen now support python 2.[67] only.

* Much work was done to make aspen's build system better.

* WSGI Middleware should now work correctly - thanks dhalia!

* New pygmentized default error simplates - thanks AlexisHuet!

* Oh, and as of now we're going to try and keep up a Changelog!


