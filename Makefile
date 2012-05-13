env:
	python ./vendor/virtualenv-1.7.1.2.py \
		--distribute \
		--unzip-setuptools \
		--prompt="[aspen] " \
		--never-download \
		--extra-search-dir=./vendor/ \
		env/
	./env/bin/pip install -r requirements.txt
	./env/bin/pip install -e ./

clean:
	rm -rf env .coverage coverage.xml nosetests.xml pylint.out

docs: env
	./env/bin/thrash ./env/bin/aspen -a:5370 -wdoc/ -p.aspen --changes_reload=1

test: env
	./env/bin/nosetests -sx tests/

-coverage-env: env
	./env/bin/pip install coverage nosexcover

-pylint-env: env
	./env/bin/pip install pylint

nosetests.xml coverage.xml: -coverage-env
	./env/bin/nosetests --with-xcoverage --with-xunit tests --cover-package aspen 

pylint.out: -pylint-env
	./env/bin/pylint --rcfile=.pylintrc aspen | tee pylint.out

analyse: pylint.out coverage.xml
	@echo done!

vendor/jython-installer.jar:
	@wget "http://downloads.sourceforge.net/project/jython/jython/2.5.2/jython_installer-2.5.2.jar?r=http%3A%2F%2Fwiki.python.org%2Fjython%2FDownloadInstructions&ts=1336182239&use_mirror=superb-dca2" -O ./vendor/jython-installer.jar

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

