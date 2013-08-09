# Raise an IOError. Previously this would be caught in
# Configurable.run_config_scripts(), and it would mistakenly
# report that the config file didn't exist.
with open('this file should not exist'): pass
