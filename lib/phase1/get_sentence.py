import re, nltk
class sentence_correction:
	def __init__ (self):
		self.bullet_type1 = '\xc3\xa2\xe2\x82\xac\xe2\x80\x9c'
		self.bullet_type2 = '\xc3\xa2\xe2\x82\xac\xc2\xa2'
		self.url = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+' 
		self.url1 = '(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'


	def is_ascii(self,word):
		for char in word:
			if ord(char) > 128:
				return False
		return True

	def correct_sentence_format(self, text):
		i = 0
		text = map(lambda x: re.sub('[0-9]+ ', '', x) , text)
		text = filter(lambda x: len(x)>1, text)
		#text = self.remove_special_chars(text)
		text = self.remove_url(text)
		while i < range(0,len(text)-1):
			if i >= len(text)-1:
				break
			if len(text[i+1])==0:
				text.remove(text[i+1])
				i=i+1
				continue
			if (text[i+1][0].islower() or self.is_ascii(text[i+1].split()[0])) and text[i+1].split()[0]!=self.bullet_type2 and text[i+1].split()[0] !=self.bullet_type1:
				text[i:i+2] = [' '.join(text[i:i+2])]
			else:
				i=i+1
		for t in text:
			s = nltk.tokenize.sent_tokenize(t)
			if len(s) > 1:
				text.remove(t)
				text.extend(s)
		i=0
		while i < range(0,len(text)):
			#print i,len(text)
			#print text[i]
			if i >= len(text):
				break
			if (i+1>=len(text) or len(text[i+1])==0) and i<len(text)-1:
				i=i+1
				continue
			s = text[i].split()[0]
			if s == self.bullet_type2 or s==self.bullet_type1:
				text[i] = text[i].replace(s,'')
				#print i
				if i+1 < len(text) and text[i+1].split()[0] != self.bullet_type2 and text[i+1].split()[0] !=self.bullet_type1:
					text[i:i+2] = [' '.join(text[i:i+2])]
				else:
					i=i+1
			else:
				i=i+1

		for i in range(0,len(text)):
			if  text[i].find(self.bullet_type1) != -1:
				text[i] = text[i].replace(self.bullet_type1,' ')
			if  text[i].find(self.bullet_type2) != -1:
				text[i] = text[i].replace(self.bullet_type2,' ')
		
		text = self.delimit_sentences(text)
		return text

	def delimit_sentences(self, text):
		for i in range(0,len(text)):
			newsent = text[i].split('.')
		#	print "inside delimiter...."
		#	print newsent
			newsent = filter(lambda x: len(x)>0, newsent)
			text.remove(text[i])
			text.extend(newsent)
		return text	

	def change_lowercase(self,text):
		for i in range(0,len(text)):
			if text[i][1] != 'NNP' and text[i][1] != 'CD' and text[i][1] != 'NN' and text[i][1] != 'NNS':
			    text[i] = list(text[i]) 
			    if text[i][0].islower() == False or text[i][1] == 'DT' or text[i][1] == 'PRP' or text[i][1] == 'VBD':
				text[i][0] = text[i][0].lower()
			    	text[i][2] = 'O'
			    text[i] = tuple(text[i]) 

		return text

	def remove_url(self, text):
		for sentence in text:
			url_text = re.findall(self.url, sentence)
			url_text.extend(re.findall(self.url1,sentence))
			for url in url_text:
				sentence.replace(url,'')
			text[text.index(sentence)] = sentence
		return text
