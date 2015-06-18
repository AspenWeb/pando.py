# pass-through to build.py

show_targets:
	@echo "Passing through to 'python build.py $@'"...
	python build.py

%:
	@echo "Passing through to 'python build.py $@'"...
	@python build.py $@ || python build.py



.PHONY: show_targets
