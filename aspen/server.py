from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from aspen.flow import Flow


def main(argv=None):
    """http://aspen.io/cli/
    """
    try:
        flow = Flow('aspen.flows.server')
        flow.run({'argv': argv})
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
