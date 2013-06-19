Aspen-python Changelog
======================

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


