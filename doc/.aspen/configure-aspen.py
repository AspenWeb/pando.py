from aspen_io import opts, inbound


opts['show_ga'] = False
opts['base'] = ''
opts['version'] = open('../version.txt').read().strip('+')


website.hooks.inbound_early.register(inbound)
