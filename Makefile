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

-analyse-env: env
	./env/bin/pip install coverage nosexcover pylint

analyse: -analyse-env
	./env/bin/nosetests --with-xcoverage --with-xunit tests --cover-package aspen 
	./env/bin/pylint --rcfile=.pylintrc aspen | tee pylint.out

