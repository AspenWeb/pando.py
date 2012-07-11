python vendor\virtualenv-1.7.1.2.py ^
		--distribute ^
		--unzip-setuptools ^
		--prompt="[aspen] " ^
		--never-download ^
		--extra-search-dir=vendor ^
		env
env\Scripts\pip install vendor\nose-1.1.2.tar.gz
env\Scripts\pip install -e .\