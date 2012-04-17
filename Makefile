default: env
	./env/bin/pip install -r requirements.txt

dev: env
	./env/bin/pip install -r requirements.dev.txt
	./env/bin/pip install -e ./

env:
	python2.7 ./vendor/virtualenv-1.6.4.py \
		--distribute \
		--unzip-setuptools \
		--prompt="[aspen] " \
		--never-download \
		--extra-search-dir=./vendor/ \
		env/

clean:
	rm -rf env

run: env
	./env/bin/thrash ./env/bin/aspen -a:5370 -wdoc/ -p.aspen

test:
	./env/bin/nosetests -sx tests/
