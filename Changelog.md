Aspen-python Changelog
======================

0.28.3 - Released Sat Jan  9 2014 by @whit537
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


