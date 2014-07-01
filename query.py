import sys, urllib2, ast
import utility

class entity_extraction:
	def __init__(self):
		self.utilObj = utility.utilFunctions()

	def html_query(self, query):
	#	print "in html_query.........."
		path = 'http://127.0.0.1/get_entity?query='
		query = path + query
		query = query.replace(' ','+')
	#	print s
		string = urllib2.urlopen(query).read()
		entity_list = ast.literal_eval(string)
		entity_list = filter(lambda e: type(e)==list , entity_list)
		return entity_list
	#	if string == '{}':
	#		return final_entities
	#	l = string.split(',')
	#	for entity in l:
	#		temp = entity.split(':')
	#		final_entities[temp[0].split('"')[1]] = temp[1].split('"')[1]
	#	return final_entities

	def get_entity(self, queries, output_file):
		print queries[0]
		queries = self.utilObj.clean(queries)
		f = open(output_file,'w')
		final_entities = ''
		for query in queries:
			print query
			if len(query):
				final_entities = self.html_query(query)
			f.write(query + '\t' + str(final_entities) + '\n')
		f.close()

if __name__ == '__main__':
	f = open(sys.argv[1], 'r')
	queries = f.readlines()
	queries = [query.strip('\n') for query in queries]
	#print queries
	f.close()
	entity_obj = entity_extraction()
	entity_obj.get_entity(queries, sys.argv[2])
