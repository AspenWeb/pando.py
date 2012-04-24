env:
	python ./vendor/virtualenv-1.6.4.py \
		--distribute \
		--unzip-setuptools \
		--prompt="[aspen] " \
		--never-download \
		--extra-search-dir=./vendor/ \
		env/
	./env/bin/pip install -r requirements.txt
	./env/bin/pip install -e ./

clean:
	rm -rf env

docs: env
	./env/bin/thrash ./env/bin/aspen -a:5370 -wdoc/ -p.aspen --changes_reload=1

test: env
	./env/bin/nosetests -sx tests/
