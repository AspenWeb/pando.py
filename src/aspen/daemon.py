# -*- coding: iso-8859-1 -*-

## Copyright 2006 by LivingLogic AG, Bayreuth/Germany.
## Copyright 2006 by Walter Dörwald
##
## All Rights Reserved
##
## See __init__.py for the license


ur"""
<par>This module can be used on UNIX to fork a daemon process. It is based
on <link href="http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012">Jürgen Hermann's Cookbook recipe</link>.</par>


<par>An example script might look like this:</par>

<example>
<prog>
from ll import daemon

counter = daemon.Daemon(
	stdin="/dev/null",
	stdout="/tmp/daemon.log",
	stderr="/tmp/daemon.log",
	pidfile="/var/run/counter/counter.pid",
	user="nobody"
)

if __name__ == "__main__":
	if counter.service():
		import time
		sys.stdout.write("Daemon started with pid %d\n" % os.getpid())
		sys.stdout.write("Daemon stdout output\n")
		sys.stderr.write("Daemon stderr output\n")
		c = 0
		while True:
			sys.stdout.write('%d: %s\n' % (c, time.ctime(time.time())))
			sys.stdout.flush()
			c += 1
			time.sleep(1)
</prog>
</example>
"""


__version__ = "$Revision: 1.13 $"[11:-2]
# $Source: /data/cvsroot/LivingLogic/Python/core/src/ll/daemon.py,v $

import sys, os, signal, pwd, grp


class Daemon(object):
	"""
	The <class>Daemon</class> class provides methods for <pyref method="start">starting</pyref>
	and <pyref method="stop">stopping</pyref> a daemon process as well as
	<pyref method="service">handling command line arguments</pyref>.
	"""
	def __init__(self, stdin="/dev/null", stdout="/dev/null", stderr="/dev/null", pidfile=None, user=None, group=None):
		"""
		<par>The <arg>stdin</arg>, <arg>stdout</arg>, and <arg>stderr</arg> arguments
		are file names that will be opened and be used to replace the standard file
		descriptors in <lit>sys.stdin</lit>, <lit>sys.stdout</lit>, and
		<lit>sys.stderr</lit>. These arguments are optional and default to
		<lit>"/dev/null"</lit>. Note that stderr is opened unbuffered, so if it
		shares a file with stdout then interleaved output may not appear in the
		order that you expect.</par>

		<par><arg>pidfile</arg> must be the name of a file. <method>start</method>
		will write the pid of the newly forked daemon to this file. <method>stop</method>
		uses this file to kill the daemon.</par>

		<par><arg>user</arg> can be the name or uid of a user. <method>start</method>
		will switch to this user for running the service. If <arg>user</arg> is
		<lit>None</lit> no user switching will be done.</par>

		<par>In the same way <arg>group</arg> can be the name or gid of a group.
		<method>start</method> will switch to this group.</par>
		"""
		self.stdin = stdin
		self.stdout = stdout
		self.stderr = stderr
		self.pidfile = pidfile
		self.user = user
		self.group = group

	def openstreams(self):
		"""
		Open the standard file descriptors stdin, stdout and stderr as specified
		in the constructor.
		"""
		si = open(self.stdin, "r")
		so = open(self.stdout, "a+")
		se = open(self.stderr, "a+", 0)
		os.dup2(si.fileno(), sys.stdin.fileno())
		os.dup2(so.fileno(), sys.stdout.fileno())
		os.dup2(se.fileno(), sys.stderr.fileno())
	
	def handlesighup(self, signum, frame):
		"""
		Handle a <lit>SIG_HUP</lit> signal: Reopen standard file descriptors.
		"""
		self.openstreams()

	def handlesigterm(self, signum, frame):
		"""
		Handle a <lit>SIG_TERM</lit> signal: Remove the pid file and exit.
		"""
		if self.pidfile is not None:
			try:
				os.remove(self.pidfile)
			except (KeyboardInterrupt, SystemExit):
				raise
			except Exception:
				pass
		sys.exit(0)

	def switchuser(self, user, group):
		"""
		Switch the effective user and group. If <arg>user</arg> is <lit>None</lit>
		and <arg>group</arg> is nothing will be done. <arg>user</arg> and <arg>group</arg>
		can be an <class>int</class> (i.e. a user/group id) or <class>str</class>
		(a user/group name).
		"""
		if group is not None:
			if isinstance(group, basestring):
				group = grp.getgrnam(group).gr_gid
			os.setegid(group)
		if user is not None:
			if isinstance(user, basestring):
				user = pwd.getpwnam(user).pw_uid
			os.seteuid(user)
			if "HOME" in os.environ:
				os.environ["HOME"] = pwd.getpwuid(user).pw_dir

	def start(self):
		"""
		Daemonize the running script. When this method returns the process is
		completely decoupled from the parent environment.
		"""
		# Finish up with the current stdout/stderr
		sys.stdout.flush()
		sys.stderr.flush()
	
		# Do first fork
		try:
			pid = os.fork()
			if pid > 0:
				sys.stdout.close()
				sys.exit(0) # Exit first parent
		except OSError, exc:
			sys.exit("%s: fork #1 failed: (%d) %s\n" % (sys.argv[0], exc.errno, exc.strerror))
	
		# Decouple from parent environment
		os.chdir("/")
		os.umask(0)
		os.setsid()
	
		# Do second fork
		try:
			pid = os.fork()
			if pid > 0:
				sys.stdout.close()
				sys.exit(0) # Exit second parent
		except OSError, exc:
			sys.exit("%s: fork #2 failed: (%d) %s\n" % (sys.argv[0], exc.errno, exc.strerror))
	
		# Now I am a daemon!
	
		# Switch user
		self.switchuser(self.user, self.group)

		# Redirect standard file descriptors (will belong to the new user)
		self.openstreams()
	
		# Write pid file (will belong to the new user)
		if self.pidfile is not None:
			open(self.pidfile, "wb").write(str(os.getpid()))

		# Reopen file descriptions on SIGHUP
		signal.signal(signal.SIGHUP, self.handlesighup)

		# Remove pid file and exit on SIGTERM
		signal.signal(signal.SIGTERM, self.handlesigterm)

	def stop(self):
		"""
		Send a <lit>SIG_TERM</lit> signal to a running daemon. The pid of the
		daemon will be read from the pidfile specified in the constructor.
		"""
		if self.pidfile is None:
			sys.exit("no pidfile specified")
		try:
			pidfile = open(self.pidfile, "rb")
		except IOError, exc:
			sys.exit("can't open pidfile %s: %s" % (self.pidfile, str(exc)))
		data = pidfile.read()
		try:
			pid = int(data)
		except ValueError:
			sys.exit("mangled pidfile %s: %r" % (self.pidfile, data))
		os.kill(pid, signal.SIGTERM)

	def service(self, args=None):
		"""
		<par>Handle command line arguments and start or stop the daemon accordingly.</par>

		<par><arg>args</arg> must be a list of command line arguments (including the
		program name in <lit>args[0]</lit>). If <arg>args</arg> is <lit>None</lit>
		or unspecified <lit>sys.argv</lit> is used.</par>

		<par>The return value is true, if <option>start</option> has been specified
		as the command line argument, i.e. if the daemon should be started.</par>
		"""
		if args is None:
			args = sys.argv
		if len(args) < 2 or args[1] not in ("start", "stop"):
			sys.exit("Usage: %s (start|stop)" % args[0])
		if args[1] == "start":
			self.start()
			return True
		else:
			self.stop()
			return False
