import re,sys
import porter_stemmer

class utilFunctions:
	regex1 = '[^A-Za-z0-9.\' ]+'
	regex2 = '[^A-Za-z0-9\' ]+'
	synonym_list = ['fb : facebook', 'ds : data structures', 'comp : computer']

	def __init__(self):
		self.p = porter_stemmer.PorterStemmer()
  
  # tokenizes the sentence
	def tokenize(self,sentence):
		return sentence.split()

	# removes non-ascii and some special characters from the words in the sentence	
	def clean(self, words):
		words = [word.strip().lower() for word in words]
		for word in words:
			if len(re.findall('^\d', word)):
				words[words.index(word)] = re.sub(utilFunctions.regex1, '',word)
			else:
				words[words.index(word)] = re.sub(utilFunctions.regex2, '',word)
		return words

	def __get_type(self, index, length):
		if length == 1:
			return '-0'
		if index == 0:
			return '-S'
		elif index == length-1:
			return'-E'
		else:
			return '-I'
  
  # uses porter stemmer to stem the list of words 
	def stem(self, words):
		words = [self.p.stem(word, 0, len(word)-1) for word in words]
		return words

  # forms a dictionary from the list of various entity types
	def get_dict(self):
		f = open('../data/dict_list','r')
		files = f.readlines()
		f.close()
		final_dict = {}
		valid_entites = []
		for filename in files:
		#	print filename
			filename = filename.strip()
			f = open('../data/'+filename, 'r')
			lines = f.readlines()
			filename = filename.split('.')[0]
			for line in lines:
				valid_entites.append(line.split('\n')[0].lower())
				words = line.split()
				for i in range(0, len(words)):
					entity_type = filename + self.__get_type(i,len(words))
					if not final_dict.has_key(words[i].lower()):
						final_dict[words[i].lower()] = []				
					if entity_type not in final_dict[words[i].lower()]:
						final_dict[words[i].lower()].append(entity_type)
		print "dictionary is loaded"
		return valid_entites, final_dict

