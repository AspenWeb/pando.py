# deprecated in favor of build.py

%:
	@echo "make is deprecated. Trying 'python build.py $@'"...
	@python build.py $@ || python build.py
