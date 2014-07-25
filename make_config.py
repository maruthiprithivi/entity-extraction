import ConfigParser

config = ConfigParser.RawConfigParser()

# When adding sections or items, add them in the reverse order of
# how you want them to be displayed in the actual file.
# In addition, please note that using RawConfigParser's and the raw
# mode of ConfigParser's respective set functions, you can assign
# non-string values to keys internally, but will receive an error
# when attempting to write to a file or when you get it in non-raw
# mode. SafeConfigParser does not allow such assignments to take place.
config.add_section('Server')
config.set('Server', 'port', '6860')
config.set('Server', 'ip', 'localhost')
config.set('Server', 'domain', 'http://127.0.0.1:6860/get_entity?query=')
config.add_section('Data')
config.set('Data', 'dict_list', '../data/dict_list')
config.set('Data', 'synonym_file', '../data/synonym_file.txt')
config.set('Data', 'initial_synonym_file', '../data/synonym.txt')
config.add_section('Log')
config.set('Log', 'logfile', '../log/logfile.log')
# Writing our configuration file to 'example.cfg'
with open('config.cfg', 'wb') as configfile:
	    config.write(configfile)
