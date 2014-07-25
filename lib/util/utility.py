import re,sys
import porter_stemmer, ConfigParser

class utilFunctions:
  regex1 = '[^A-Za-z0-9.\' ]+'
  regex2 = '[^A-Za-z0-9\' ]+'

  def __init__(self):
    self.p = porter_stemmer.PorterStemmer()
    self.config = ConfigParser.ConfigParser()
    self.config.read('../config.cfg')
    self.sections = self.config.sections()
  
  # tokenizes the sentence
  def tokenize(self,sentence):    
    return sentence.split(' ')

  # removes non-ascii and some special characters from the words in the sentence  
  def clean(self, words):
    words = [word.strip().lower() for word in words]
    for word in words:
      if len(re.findall('^\d', word)):
        words[words.index(word)] = re.sub(utilFunctions.regex1, '',word)
      else:
        words[words.index(word)] = re.sub(utilFunctions.regex2, '',word)
    words = filter(lambda x: len(x) > 0, words)
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
  
  def __add_synonym(self):
    f = open(self.config.get('Data', 'initial_synonym_file'),'r')
    lines = f.readlines()
    f.close()
    synonym_dict = {}
    for line in lines:
      word = line.strip('\n').split('\t')
      if synonym_dict.has_key(word[0]):
        synonym_dict[word[0]] += ' ' + word[1].lower()
      elif synonym_dict.has_key(word[1]):
        synonym_dict[word[1]] += ' ' + word[0].lower()
      else:
        synonym_dict[word[0]] = ''
        synonym_dict[word[0]] += ' ' + ' ' + word[1].lower()
    f = open(self.config.get('Data', 'synonym_file'),'w')
    for key, val in synonym_dict.iteritems():
      f.write(key + '\t' + val + '\n')
    return synonym_dict

  def get_synonym(self, words):
    f = open(self.config.get('Data', 'synonym_file'),'r')
    lines = f.readlines()
    f.close()
    for i in range(0, len(words)):
      for line in lines:
        key = line.split('\t')[0]
        l = line.strip('\n').split('\t')[1].split()
        if words[i] in l:
          words[i] = key
          break
    return words
      

  # forms a dictionary from the list of various entity types
  def get_dict(self):
    f = open(self.config.get('Data', 'dict_list'),'r')
    files = f.readlines()
    f.close()
    final_dict = {}
    valid_entities = []
    for filename in files:
    # print filename
      filename = filename.strip()
      f = open('../data/'+filename, 'r')
      lines = f.readlines()
      filename = filename.split('.')[0]
      for line in lines:
        words = line.strip('\n').split()
        words = self.stem(words)
        valid_entities.append(' '.join(c.lower() for c in words))
        for i in range(0, len(words)):
          entity_type = filename + self.__get_type(i,len(words))
          if not final_dict.has_key(words[i].lower()):
            final_dict[words[i].lower()] = []       
          if entity_type not in final_dict[words[i].lower()]:
            final_dict[words[i].lower()].append(entity_type)

    
    #synonym_dict = self.__add_synonym()
    f = open(self.config.get('Data', 'synonym_file'),'r')
    synonyms = f.readlines()
    # modify the word dictionary
    for line in synonyms:
      key = line.split('\t')[0]
      l = line.strip('\n').split('\t')[1].split()
      for word in l:
        if final_dict.has_key(word):
          if final_dict.has_key(key):
            final_dict[key].extend(final_dict[word])
          else:
            final_dict[key] = final_dict[word]
          final_dict.pop(word)
    

    # modify the valid entities list
    for i in range(0, len(valid_entities)):
      tokens = valid_entities[i].split()
      flag = 0
      for token in tokens:
        flag = 0
        for line in synonyms:
          key = line.split('\t')[0]
          l = line.strip('\n').split('\t')[1].split()
          if token in l:
            tokens[tokens.index(token)] = key
            flag = 1
            break
      valid_entities[i] = ' '.join(c for c in tokens)

    print "dictionary is loaded"
    size = len(final_dict)
    #for i in range(0, size):
    #  final_dict['dummy-'+str(i)] = str(i)
    # print len(final_dict)
    return valid_entities, final_dict





