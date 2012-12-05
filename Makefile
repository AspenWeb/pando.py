PYTHON=python

# Core Executables
# ================
# We satisfy dependencies using local tarballs, to ensure that we can build 
# without a network connection. They're kept in our repo in ./vendor.

env/bin/aspen: env/bin/pip
	./env/bin/pip install ./vendor/Cheroot-4.0.0beta.tar.gz
	./env/bin/pip install ./vendor/mimeparse-0.1.3.tar.gz
	./env/bin/pip install ./vendor/tornado-2.3.tar.gz
	./env/bin/python setup.py develop

env/bin/nosetests: env/bin/pip
	./env/bin/pip install ./vendor/nose-1.1.2.tar.gz
	./env/bin/pip install ./vendor/snot-0.6.tar.gz

env/bin/pip:
	$(PYTHON) ./vendor/virtualenv-1.7.1.2.py \
		--distribute \
		--unzip-setuptools \
		--prompt="[aspen] " \
		--never-download \
		--extra-search-dir=./vendor/ \
		env/

env: env/bin/pip


# Doc / Smoke
# ===========

docs: env/bin/aspen
	./env/bin/aspen -a:5370 -wdoc/ -pdoc/.aspen --changes_reload=1

smoke: env/bin/aspen
	@mkdir smoke-test && echo "Greetings, program!" > smoke-test/index.html
	./env/bin/aspen -w smoke-test


# Testing
# =======

test: env/bin/aspen env/bin/nosetests
	./env/bin/nosetests -sx tests/

-coverage-env: env/bin/pip
	./env/bin/pip install coverage nosexcover

-pylint-env: env/bin/pip
	./env/bin/pip install pylint

nosetests.xml coverage.xml: env/bin/nosetests -coverage-env
	./env/bin/nosetests \
		--with-xcoverage \
		--with-xunit tests \
		--cover-package aspen 

pylint.out: -pylint-env
	./env/bin/pylint --rcfile=.pylintrc aspen | tee pylint.out

analyse: pylint.out coverage.xml nosetests.xml
	@echo done!


# Jython
# ======

vendor/jython-installer.jar:
	#@wget "http://downloads.sourceforge.net/project/jython/jython/2.5.2/jython_installer-2.5.2.jar?r=http%3A%2F%2Fwiki.python.org%2Fjython%2FDownloadInstructions&ts=1336182239&use_mirror=superb-dca2" -O ./vendor/jython-installer.jar
	@wget "http://search.maven.org/remotecontent?filepath=org/python/jython-installer/2.5.3/jython-installer-2.5.3.jar" -O ./vendor/jython-installer.jar

jython_home: vendor/jython-installer.jar
	@java -jar ./vendor/jython-installer.jar -s -d jython_home

jenv: jython_home
	PATH=`pwd`/jython_home/bin:$$PATH jython ./vendor/virtualenv-1.7.1.2.py \
		--python=jython \
		--distribute \
		--unzip-setuptools \
		--prompt="[aspen] " \
		--never-download \
		--extra-search-dir=./vendor/ \
		jenv/
	./jenv/bin/pip install -r requirements.txt
	./jenv/bin/pip install -e ./
	# always required for jython since it's ~= python 2.5
	./jenv/bin/pip install simplejson

jython-nosetests.xml: jenv
	./jenv/bin/jython ./jenv/bin/nosetests --with-xunit tests --xunit-file=jython-nosetests.xml --cover-package aspen

jython-test: jython-nosetests.xml


# Clean
# =====

clean:
	python setup.py clean -a
	rm -rf env .coverage coverage.xml nosetests.xml pylint.out jenv \
		vendor/jython-installer.jar jython_home jython-nosetests.xml dist \
		smoke-test
	find . -name \*.pyc -delete
	find . -name \*.class -delete
