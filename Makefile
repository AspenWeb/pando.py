# deprecated in favor of build.py

show_targets %:
	@echo "make is deprecated. Trying 'python build.py $@'"...
	@python build.py $@ || python build.py

.PHONY: show_targets

