"""
aspen.server
++++++++++++
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import sys
from algorithm import Algorithm


def main():
    Server().main()


class Server(object):

    def __init__(self, argv=None):
        self.argv = argv

    def get_algorithm(self):
        return Algorithm.from_dotted_name('aspen.algorithms.server')

    def get_website(self, silent=True):
        """Return a website object. Useful in testing.
        """
        def work():
            algorithm = self.get_algorithm()
            state = algorithm.run(argv=self.argv, _return_after='get_website_from_argv')
            return state['website']

        if not silent:
            return work()
        else:
            class DevNull():
                def write(self, *a, **kw): pass
                def flush(self, *a, **kw): pass
            devnull = DevNull()

            try:
                sys.stdout = devnull
                website = work()
            finally:
                sys.stdout = sys.__stdout__

            return website


    def main(self, argv=None):
        """http://aspen.io/cli/
        """
        try:
            argv = argv if argv is not None else self.argv
            algorithm = self.get_algorithm()
            algorithm.run(argv=argv)
        except (SystemExit, KeyboardInterrupt):

            # Under some (most?) network engines, a SIGINT will be trapped by the
            # SIGINT signal handler above. However, gevent does "something" with
            # signals and our signal handler never fires. However, we *do* get a
            # KeyboardInterrupt here in that case. *shrug*
            #
            # See: https://github.com/gittip/aspen-python/issues/196

            pass
        except:
            import aspen, traceback
            aspen.log_dammit("Oh no! Aspen crashed!")
            aspen.log_dammit(traceback.format_exc())


if __name__ == '__main__':
    main()
