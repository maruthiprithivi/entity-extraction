'''
Assumptions:
1. A word cannot be a part of two entities appearing consecutively.
2. the tag-list for each word is not very large. 
'''

import util.utility
import json, collections, re
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import parse_qs
  
class extractEntity:
	entites_with_versions = ['technology', 'books', 'lessons', 'chapters', 'operating system']
	regex_version = '^[0-9]+.[0-9x]+.[0-9x]+|^[0-9]+.[0-9x]+'

	def __init__(self):
		print "creating extractEntity instance"
		self.utilObj = util.utility.utilFunctions()
		self.valid_entities, self.word_dict = self.utilObj.get_dict()

	# checks is the given word is a unigram entity. 	
	# input: word <type 'str'> , stem_word <type 'str'>
	# output: word <type 'str'>, is_unigram <type 'bool'>, value < type 'str'>
	def __is_unigram_entity(self,word, stem_word):
		try:
			tags = self.word_dict[word]
			tags = self.__remove_nonStart_tags(tags)
			ignore = tags[0]
		except:
			tags = self.word_dict[stem_word]
			tags = self.__remove_nonStart_tags(tags)			
			word = stem_word
		for tag in tags:
			if tag.split('-')[1] == '0':
				return word, True, tag.split('-')[0]
		return word,False,"ignore"

	# removes tags from start_tags (S-tag) if list of corresponding intermediate tag (I-tag) is not found in current_tags list
	# input: start_tags <type 'list'> , current_tags <type 'list'> 
	# output: start_tags <type 'list'>
	def __remove_tags(self, start_tags, current_tags):
		to_remove = []
		for tag in range(0,len(start_tags)):
			temp = start_tags[tag].split('-')
			try:
				index = current_tags.index(temp[0]+'-I')
			except:
				to_remove.append(start_tags[tag])
		start_tags = filter(lambda x: x not in to_remove, start_tags)	
		return start_tags

	# removes tags which are not the start tags (S-TAG) from start_tags 	
	# input: start_tags <type 'list'>
	#	output: start_tags <type 'list'>
	def __remove_nonStart_tags(self,start_tags):
		for tag in start_tags:
			if tag.split('-')[1] == 'I' or tag.split('-') == 'E':
				start_tags.remove(tag)
		return start_tags

	# processes the window between (start, end_i) and returns the longest entity starting with the start_word (start_word = words[start])
	# input: start <type 'int'>, end_i <type 'int'>, start_tags <type 'list'>
	# output: longest_entity <type 'str'>, value <type 'str'>, next_index <type 'int'>
	def process_prevWindow(self, start, end_i, start_tags):
		i, end = start+1, end_i+1
		final_i = end
		temp_entity = {}
		word, is_unigram, val = self.__is_unigram_entity(self.words[start], self.stemmed_words[start])
		if is_unigram:
			temp_entity[word] = val
		
		while i < end and len(start_tags):
			try:
				current_tags = list(self.word_dict[self.words[i]])
			except:
				current_tags = list(self.word_dict[self.stemmed_words[i]])
				self.words[i] = self.stemmed_words[i]
			for start_tag in start_tags:
				start_entity_type = start_tag.split('-')
				for tag in current_tags:
					current_entity_type = tag.split('-')
					if start_entity_type[0] == current_entity_type[0] and current_entity_type[1] == 'E':
						e = ' '.join(c for c in self.words[start:i+1])
						if e in self.valid_entities:
							temp_entity[e] = start_entity_type[0]
							break

			start_tags = self.__remove_tags(start_tags, current_tags)
			if len(start_tags):
				i += 1
		
		entity = self.__get_longest_entity(temp_entity)
		
		if entity != -1:
			next_i = start + len(entity.split())
			self.final_entity[entity] = temp_entity[entity]
			self.final_list.append((entity, temp_entity[entity]))
			return entity, temp_entity[entity], next_i
		else:
			next_i = start + 1
			return entity, -1, next_i


	# get_entity loops over the sentence, segments it and retrieves entities
	# input: sentence <type 'str'>
	# output: final_list <type 'list'>
	def get_entity(self,sentence):
		self.words = self.utilObj.tokenize(sentence)
		self.words = self.utilObj.clean(self.words)
		# stores stemmed-version of words in the sentence
		self.stemmed_words = self.utilObj.stem(self.words)
		prev_entity = ''
		# stores the list of temporary entites starting with words[start]
		temp_entity = {}		
		# stores the final dictionary of entities	
		self.final_entity = collections.OrderedDict()
		# initialization of variables, iterators and flags 			
		i, start, start_flag, entity, val = 0, -1, 0, -1, -1	
		start_tags, current_tags = [], []
		# stores the segmented query with entity types
		self.final_list = []		
		
		while i <= len(self.words):
			
			# for cases where query end with a possible entity. eg- event planning india
			if i==len(self.words):			
				if start_flag:
					entity, val, i = self.process_prevWindow(start, i-1, start_tags)
					start_flag = 0
				else:
					i += 1
				if entity == -1 and i <= len(self.words):
					self.final_list.append((self.words[i-1]))
				start = -1
				continue

			# for words which are present in the dictionary	
			if self.word_dict.has_key(self.words[i]) or self.word_dict.has_key(self.stemmed_words[i]):		
				if not start_flag:
					# if word exists in dictionary
					try:			
						start_tags = list(self.word_dict[self.words[i]])
						start_tags = self.__remove_nonStart_tags(start_tags)
						ignore = start_tags[0]
					# if stemmed word exists in dictionary	
					except:			
						start_tags = list(self.word_dict[self.stemmed_words[i]])
						self.words[i] = self.stemmed_words[i]
						start_tags = self.__remove_nonStart_tags(start_tags)
					if len(start_tags):
						start_flag = 1
						start = i	
					else:
						self.final_list.append((self.words[i]))
				i += 1
		
			# for words which are not present in the dictionary	
			else:								
				if start != -1:
					# processing the previous window lying between (start, i-1)
					entity, val, i = self.process_prevWindow(start, i-1, start_tags)		
					i-=1
				if entity == -1:
					self.final_list.append((self.words[i]))
				start_flag = 0
				start = -1
				i+=1
				# checking if the next word is a version for an entity-with-version
				if i < len(self.words) and entity != -1 and val != -1 and entity != prev_entity:
					value = self.__check_version(entity, self.final_entity[entity], i)
					if value != -1:
						self.final_entity[entity] = value
						index = self.final_list.index((entity, val))
						self.final_list[index] = (entity, val+' : with version')
					prev_entity = entity
				entity = -1

		return self.final_list

  # checks if the current word is the version of the previously found entity
  # input: entity <type 'str'>, value <type 'str'>, index <type 'int'>
  # output: value <type 'str'> | <type 'int'>
	def __check_version(self, entity, val, index):
		if val in extractEntity.entites_with_versions:
			version = re.findall(extractEntity.regex_version,self.words[index])
			if len(version):
				val = val + ' version: ' + str(version[0])
				return val
		return -1

	# returns the longest entity from the list of entities
	# input: temp_entity <type 'list'>
	# output: entity <type 'str'>	
	def __get_longest_entity(self, temp_entity):
		length = 0
		final = -1
		for e,v in temp_entity.iteritems():
			if length < len(e.split()):
				length = len(e.split())
				final = e
		return final

# parses the html request to the extractEntity class for sentence segmentation and entity extraction
# input: path <type 'str'>
# output: final_entity <type 'list'>
def parse(path):
        if '?' in path:
            path, tmp = path.split('?',1)
            qs = parse_qs(tmp)

        # function call to get_entity function to retrieve a list of entities
        if path == '/get_entity':
        	final_entity = entityObj.get_entity(str(qs['query'][0]))
        	return final_entity

class MyHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):        
        print("Just received a GET request")
        # parses http request to parse function
        final_entity = parse(self.path)	
        self.wfile.write(json.dumps(final_entity))


if __name__ == '__main__':	
	# creates a server
	server = HTTPServer(('localhost', 80), MyHandler)	
	try:	
		print('Started http server')
		entityObj = extractEntity()       
		server.serve_forever()
		path = server.do_GET()
	except KeyboardInterrupt:
		print('^C received, shutting down server')
		server.socket.close()
	





