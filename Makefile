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
	./env/bin/thrash ./env/bin/aspen -vDEBUG -a:5370 -rdoc/

test:
	./env/bin/nosetests -sx tests/
