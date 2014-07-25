class word_struct:
	def __init__(self, word, val, tag_val):
		self.keyword = word.strip()
		self.title = val
		self.tag = tag_val
	def empty_keyword(self):
		if len(self.keyword.strip()) == 0:
			return True
		return False
	def is_unigram(self):
		if len(self.keyword.split()) == 1:
			return True
		return False
	
	def get_score(self, tf, boost):
		return tf*boost

	def is_title(self):
		return self.title
	def is_tag(self):
		return self.tag