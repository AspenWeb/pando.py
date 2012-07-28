"""This is a simple tool to restart a process when it dies.

It's designed to restart aspen in development when it dies because files
have changed and you set changes_reload to 'yes'.

    http://aspen.io/thrash/

"""

def foo():

    # Import in here to capture KeyboardInterrupt during imports.
    import os
    import subprocess
    import sys
    import time

    # set unbuffered - http://stackoverflow.com/a/181654/253309
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'wb', 0)

    if len(sys.argv) < 2:
        print ("usage: %s <child> [child opts and args]"
               % os.path.basename(sys.argv[0]))
        sys.exit(1)

    BACKOFF_MIN = 0.10  # Start looping here.
    BACKOFF_MAX = 3.20  # Throttle back to here.
    PROMPT_AFTER = 60   # Give the user this much time to fix the error.
    INITIAL_WAIT = 15   # Give the user this much time to read the error.

    n = 0
    backoff = BACKOFF_MIN
    cumulative_time = 0

    while 1:

        # The child process exited.
        # =========================
        # Log restart attempts after the initial launch.

        n += 1
        backoff = min(backoff * 2, BACKOFF_MAX)
        if n > 1:
            m = "---- Restart #%s " % n
            print
            print m + ('-' * (79-len(m)))


        # Execute the child process.
        # ==========================
        # Then wait for it to return, dealing with INT.

        proc = subprocess.Popen( sys.argv[1:]
                               , stdout=sys.stdout
                               , stderr=sys.stderr
                                )
        try:
            status = proc.wait()
        except KeyboardInterrupt:
            status = proc.wait()

        if status == 75:
            print ("Received INT in child.")


        # Decide how to proceed.
        # ======================

        if n == 1:
            # This is the first time we've thrashed. Give the user time to
            # parse the (presumed) traceback.
            cumulative_time += INITIAL_WAIT
            try:
                time.sleep(INITIAL_WAIT)
            except KeyboardInterrupt:
                # Allow user to fast-track this step.

                # reset
                n = 0
                backoff = BACKOFF_MIN
                cumulative_time = 0

        elif cumulative_time < PROMPT_AFTER:
            # We've given the user time to parse the traceback. Now thrash
            # for a while.
            cumulative_time += backoff
            time.sleep(backoff)

        else:
            # We've been thrashing for a while. Pause.
            print
            try:
                raw_input("Press any key to start thrashing again. ")
            except KeyboardInterrupt:
                print

            # reset
            n = 0
            backoff = BACKOFF_MIN
            cumulative_time = 0


def main():
    try:
        foo()
    except KeyboardInterrupt:
        import time
        time.sleep(0.1)  # give child stdio time to flush
        print "Received INT in thrash, exiting."
