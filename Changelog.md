Aspen-python Changelog
======================

0.?? - Released
---------------

* Fixed #165 - make it explicit which variables are available to templates
  By default all variables are available.  If you want to limit that, put
  the list of variable names in __all__

0.25.3 - Released 2013-08-09 by @whit537
----------------------------------------

* Fixed #212 - don't wrongly swallow IOError in configure-aspen.py


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


