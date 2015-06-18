# pass-through to build.py

show_targets:
	@echo "Passing through to 'python3 build.py $@'"...
	python3 build.py

%:
	@echo "Passing through to 'python3 build.py $@'"...
	@python3 build.py $@ || python3 build.py



.PHONY: show_targets
