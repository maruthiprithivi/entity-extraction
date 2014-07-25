#import nltk
import re
#from nltk.stem.snowball import SnowballStemmer
class utilFunctions:
	
	def __init__(self):
		self.synonym_list = ['fb : facebook', 'ds : data structures', 'comp : computer']

	def tokenize(self,sentence):
		return sentence.split()

	def clean(self, words):
		words = [word.strip().lower() for word in words]
		for word in words:
			if len(re.findall('^[0-9]', word)):
				words[words.index(word)] = re.sub('[^A-Za-z0-9.\' ]+', '',word)
			else:
				words[words.index(word)] = re.sub('[^A-Za-z0-9\' ]+', '',word)
		words = filter(lambda x: len(x) > 0, words)
		return words

	def get_type(self, index, length):
		if length == 1:
			return '-0'
		if index == 0:
			return '-S'
		elif index == length-1:
			return'-E'
		else:
			return '-I'



	def get_dict(self):
		f = open('dict_list','r')
		files = f.readlines()
		f.close()
		final_dict = {}
		valid_entites = []
		for filename in files:
		#	print filename
			filename = filename.strip()
			f = open(filename, 'r')
			lines = f.readlines()
			filename = filename.split('.')[0]
			for line in lines:
				valid_entites.append(line.split('\n')[0].lower())
				words = line.split()
				for i in range(0, len(words)):
					entity_type = filename + self.get_type(i,len(words))
					if not final_dict.has_key(words[i].lower()):
						final_dict[words[i].lower()] = []				
					if entity_type not in final_dict[words[i].lower()]:
						final_dict[words[i].lower()].append(entity_type)

		#for key,value in final_dict.iteritems():
		#	print key, value
		print "dictionary is loaded"
		return valid_entites, final_dict

