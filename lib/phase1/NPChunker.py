import nltk
from nltk.corpus import conll2000
from nltk.chunk.util import conlltags2tree
import json
import re, sys, binascii
import enchant, math
from nltk.corpus import conll2000
from nltk.chunk.util import conlltags2tree
import commands,math, operator
import MySQLdb, urllib, collections
from keyword_structure import word_struct
import stopword_removal
from nltk.stem.snowball import SnowballStemmer
from get_sentence import sentence_correction
total_documents = 13000000

class ConsecutiveNPChunkTagger(nltk.TaggerI): 
    def __init__(self, train_sents):
        train_set = []
        for tagged_sent in train_sents:
            untagged_sent = nltk.tag.untag(tagged_sent)
            history = []            
            for i, (word, tag) in enumerate(tagged_sent):
                featureset = npchunk_features(untagged_sent, i, history) 
                train_set.append( (featureset, tag) )
                history.append(tag)
        f=open("train_set.txt","wb")
         #print "train_set:",train_set
	for t in train_set[:200]:
		f.write(str(t))
		f.write('\n')
        f.close()
        self.classifier = nltk.DecisionTreeClassifier.train(train_set[:200])#, algorithm='megam', trace=0)
        #nltk.NaiveBayesClassifier.train(train_set[:200])#, algorithm='megam', trace=0)

    def tag(self, sentence):
        history = []
        for i, word in enumerate(sentence):
            featureset = npchunk_features(sentence, i, history)
            tag = self.classifier.classify(featureset)
            history.append(tag)
        return zip(sentence, history)

def npchunk_features(sentence, i, history):
    word, pos = sentence[i]
    #print "\n*****************************word,pos:",word,",",pos
    if i==0:
        prevword,prevpos="<START>","<START>"
    else:
        #print "\nsentence[i-1]:",sentence[i-1]
        prevword,prevpos=sentence[i-1]

    return {"pos": pos} #,"prevpos":prevpos}

class ConsecutiveNPChunker(nltk.ChunkParserI): 
    def __init__(self, train_sents):
        tagged_sents = [[((w,t),c) for (w,t,c) in nltk.chunk.tree2conlltags(sent)] for sent in train_sents]
        self.tagger = ConsecutiveNPChunkTagger(tagged_sents)

    def parse(self, sentence):
        tagged_sents = self.tagger.tag(sentence)
        conlltags = [(w,t,c) for ((w,t),c) in tagged_sents]
        
        # returns the tags
        # return conlltags

        # returns the tuple
        response_dict=dict()
        response_dict["tags"]=conlltags
        response_dict["tree"]=conlltags2tree(conlltags)
        #return str(conlltags)+"_SEPARATOR_"+str(conlltags2tree(conlltags))
        #dump=json.dumps(response_dict)
        return response_dict

def flatten(l):
	for el in l:
		if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
			for sub in flatten(el):
				yield sub
		else:
			yield el

class snowballStemmer:
	def __init__(self):
		self.stemmer = SnowballStemmer("english")

	def stem(self,keyword_score, keyword_idf_dir, keyword_tf_dir):
		stem_dict = {}
		stem_dict_score = {}
		print "in stem function.............."
		for key in keyword_score.iterkeys():
			root = self.stemmer.stem(key.keyword)
			if stem_dict.has_key(root):
				stem_dict[root]['words'].append(key)
				if key.is_title() or key.is_tag():
					stem_dict[root]['boost'] = 1
				if stem_dict[root]['tf'] < keyword_tf_dir[key]:
					stem_dict[root]['tf'] = keyword_tf_dir[key]
			else:
				stem_dict[root] = {}
				stem_dict[root]['boost'] = 0
				stem_dict[root]['words'] = []
				stem_dict[root]['words'].append(key)
				stem_dict[root]['idf'] = keyword_idf_dir[key]
				stem_dict[root]['tf'] = keyword_tf_dir[key]
				if key.is_title() or key.is_tag():
					stem_dict[root]['boost'] = 1

		for root in stem_dict.iterkeys():
			stem_dict_score[root] = stem_dict[root]['idf']*stem_dict[root]['tf']
	#	print stem_dict_score
		return stem_dict, stem_dict_score


class getIdfandTf:
	def __init__(self):
		self.fields =  ['title_unnormalized', 'description', 'transcript_en']
		self.query = "http://index11:8983/solr/core0/select?q=%s:%s&rows=1&wt=python&debugQuery=on&debug.explain.structured=true"
	
	def extract_idf(self, dictionary):
		print dictionary
		print dictionary['response']
		count = dictionary['response']['numFound']
		print count
		if count:
			return math.log(total_documents/(count+1)) + 1
		return -1

		#for key,value in ss.iteritems():
		#	ee = value['details']
		#	try:
		#		ee = value['details'][0]['details']
		#	except:
		#		ee = value['details']
		#		if e['description'][:3] == 'idf':
		#			return e['value']
		#return -1

	def get_idf(self, query):
		sum_idf = 0
		length_idf = 0
		idfs = {}
	#	idfs_list = []
		print "get_idf...."
		print query
		for field in self.fields:
			http_url = self.query % (field, urllib.quote_plus('"%s"' % query))
			output = commands.getoutput('curl -s "%s"' % (http_url))
			print eval(output)
			idf = self.extract_idf(eval(output))
			idfs[field] = idf
			if idf > 0:
				length_idf+=1
				sum_idf += idf
	#			idfs_list.append(idf)
	#	print idfs
		if idfs['title_unnormalized'] == -1 and idfs['description'] == -1:
	#		print query
			return -1
		if length_idf > 0:
			return sum_idf*1.0/len(self.fields)
		return -1

	def calculate_idf(self,total_chunks,f):
		keyword_dir = {}
	#	total_chunks = flatten(total_chunks)
		keyword_filename = f.name
	#	print list(total_chunks)
	#	flatten_total_chunks = set(map(lambda x: x.keyword.strip(), list(total_chunks)))
	#	print "**********************"
	#	print total_chunks
	#	print "**********************"	
	#	print "inside calculate_idf function................"
		for chunk in total_chunks:
			f1 = open(keyword_filename,'r')
			s = f1.readlines()
			flag=0
			for term in s:
				if term.split('\t')[0] == chunk.keyword.strip():
					idf_score = term.split('\t')[1]
					flag=1
			if flag==0:	
				#print chunk.keyword, chunk.keyword.strip()
				idf_score = self.get_idf(chunk.keyword.strip())				
				f.write(str(chunk.keyword.strip()) + '\t' + str(idf_score))
				f.write('\n')
			#print str(chunk.strip()) + '	' + str(idf_score)
	#		print chunk.keyword, idf_score			
			if chunk.is_unigram() and float(idf_score) < 6.0 and not chunk.is_tag() and not chunk.is_title():
				continue
			chunk.keyword = chunk.keyword.lower().strip()
			keyword_dir[chunk] = float(idf_score)	
		return keyword_dir

	def calculate_idf2(self,total_chunks,f):
		keyword_dir = {}
	#	total_chunks = flatten(total_chunks)
		keyword_filename = f.name
	#	print "printing inside calculate_idf2............"
	#	print total_chunks
		for chunk in total_chunks:
			#print chunk
			f1 = open(keyword_filename,'r')
			s = f1.readlines()
			flag=0
			for term in s:
				#print term
				if term.split('\t')[0] == chunk.strip():
					idf_score = term.split('\t')[1]
					flag=1
			if flag==0:	
				idf_score = self.get_idf(chunk.strip())				
				f.write(str(chunk.strip()) + '\t' + str(idf_score))
				f.write('\n')
			#print str(chunk.strip()) + '	' + str(idf_score)
			if len(chunk.strip().split())==1 and float(idf_score) < 6.0:
				continue
			chunk = chunk.lower().strip()
			keyword_dir[chunk] = float(idf_score)	
		return keyword_dir

	def get_tf(self,total_chunks):
	#	chunks = flatten(total_chunks)
		keyword_dir = {}
		keyword_temp = {}
		for word in total_chunks:
			word.keyword = word.keyword.lower().strip()
			keyword_temp[word.keyword] = 0
		set_t = []
		for word in total_chunks:
			keyword_temp[word.keyword.strip()] += 1
			if any([x.keyword.strip()==word.keyword.strip() for x in set_t]):
				continue
			set_t.append(word)
		for word in set_t:
			keyword_dir[word] = float(keyword_temp[word.keyword.strip()])
		return keyword_dir

	def get_tf2(self,total_chunks):
		total_chunks = flatten(total_chunks)
		total_chunks = list(total_chunks)
		keyword_dir = {}
		keyword_temp = {}
		for word in total_chunks:
			word = word.lower().strip()
			keyword_temp[word] = 0
		set_t = []
		for word in total_chunks:
			keyword_temp[word.lower().strip()] += 1
			if any([x.lower().strip()==word.lower().strip() for x in set_t]):
				continue
			set_t.append(word.lower().strip())
		for word in set_t:
			keyword_dir[word] = float(keyword_temp[word.strip()])
		return keyword_dir	

	def to_remove_keyword(self, val, idf_l):
	#	print "inside remove func"
	#	print idf_l
		avg = 1.0*(reduce(lambda x,y: x+y, idf_l))/len(idf_l)
		if (avg) < 0.45*val:
			#print idf_l
			#print val, avg
			return True
		return False

	def get_term_score(self,keyword_dir,f):
		keyword_filename = f.name
		to_remove_list = []
		for key,val in keyword_dir.iteritems():
			if key.is_title() or key.is_tag():
				continue
			if not key.is_unigram() and not key.empty_keyword():
				l = key.keyword.split()
				idf_l = []
			#	print key.keyword
				for word in l:
					f1 = open(keyword_filename,'r')
					s = f1.readlines()
					flag=0
					for term in s:
						if term.split('\t')[0].strip() == word:
							idf_score = term.split('\t')[1]
							flag=1
					if flag==0:	
						idf_score = self.get_idf(word)				
						f.write(str(word) + '\t' + str(idf_score) + '\n')
					idf_l.append(float(idf_score))
				if self.to_remove_keyword(val, idf_l):
					to_remove_list.append(key)		
		for key in to_remove_list:
			keyword_dir.pop(key)		 
		return keyword_dir

	def get_term_score2(self,keyword_dir,f):
		keyword_filename = f.name
		to_remove_list = []
		for key,val in keyword_dir.iteritems():
			if not len(key.strip().split()) == 1 and not len(key.strip()) == 0:
				l = key.split()
				idf_l = []
			#	print key.keyword
				for word in l:
					f1 = open(keyword_filename,'r')
					s = f1.readlines()
					flag=0
					for term in s:
						if term.split('\t')[0].strip() == word:
							idf_score = term.split('\t')[1]
							flag=1
					if flag==0:	
						idf_score = self.get_idf(word)				
						f.write(str(word) + '\t' + str(idf_score) + '\n')
					idf_l.append(float(idf_score))
			#		print word
			#		print "***"
				if self.to_remove_keyword(val, idf_l):
					#print key.keyword
					to_remove_list.append(key)		
		for key in to_remove_list:
			keyword_dir.pop(key)		 
		try:
			f1
			f1.close()
		except:
			ignore = 0
		return keyword_dir


def stopwords_removal(keyword_score,score_obj,f,keyword_tf_dir):
	to_remove=[]
	stopword_obj = stopword_removal.remove_stopword()
	#print "inside remove stopwords....."
	for key in keyword_score.iterkeys():
		#print key.keyword
		flag, word = stopword_obj.contains_stopword(key.keyword)
		if flag:
		#	print key.keyword, word
			key.keyword = word
			idf = score_obj.calculate_idf([key],f)
			idf = score_obj.get_term_score(idf,f)
			if idf.has_key(key) and keyword_tf_dir.has_key(key) and idf[key] > 7.0:
				continue
			else:
				to_remove.append(key)
	#print "to remove*****************************"			
	for key in to_remove:
	#	print key.keyword
		keyword_score.pop(key)
	return keyword_score	

def idf_list_contains(keyword_idf_dir, k):
	for key in keyword_idf_dir.iterkeys():
		if key.keyword == k.keyword:
			return key,True
	return key,False

def calculate_score(total_chunks,keyword_filename,head,file_output,f):
	score_obj = getIdfandTf()
	
	keyword_idf_dir = score_obj.calculate_idf(total_chunks,f)
	keyword_idf_dir = score_obj.get_term_score(keyword_idf_dir,f)
	#print keyword_idf_dir
	#print "printing IDFs................"
	#for key,val in keyword_idf_dir.iteritems():
	#	print key.keyword,val
	
	keyword_tf_dir = score_obj.get_tf(total_chunks)
	#print "printing TFs..............."
	#for key,val in keyword_tf_dir.iteritems():
	#	print key.keyword,val
	#print len(total_chunks)
	#print keyword_tf_dir

	keyword_score = {}			# tf * idf
	keyword_score2 = {} 		# sqrt(tf) * idf
	#print "printing................................."
	for k in keyword_tf_dir.iterkeys():
		key, exists = idf_list_contains(keyword_idf_dir, k)
		if k != key:
			#print "yesyysyyyyyyyyyyyyy"
			keyword_idf_dir[k] = keyword_idf_dir[key]
			k.keyword = key.keyword
			if key.is_title():
				k.title = key.title
			if key.is_tag():
				k.tag = key.tag
			#keyword_idf_dir.pop(key)
		if exists:
			#if keyword_tf_dir[k] == 1 and k.is_unigram() and not k.is_title() and not k.is_tag():
				#print k.keyword
			#	continue;			
			#print k.keyword, keyword_tf_dir[k] * keyword_idf_dir[k]
			keyword_score[k] = keyword_tf_dir[k] * keyword_idf_dir[k] 
			keyword_score2[k] = math.sqrt(float(keyword_tf_dir[k])) * keyword_idf_dir[k] * 1.0

	keyword_score = stopwords_removal(keyword_score,score_obj,f, keyword_tf_dir)		
	stem_obj = snowballStemmer()
	stem_dict, stem_dict_score = stem_obj.stem(keyword_score, keyword_idf_dir, keyword_tf_dir)
	#print "printing stemmed words...................."
	#for key, val in stem_dict_score.iteritems():
		#print key, val
	sorted_keyword_score = sorted(stem_dict_score.iteritems(), key=operator.itemgetter(1), reverse=True)
	#f = open('output/'+str(slide_id)+'.txt','w')
	if head:
		file_output.write("keyword" + '\t' + "Tf" + '\t' + "Idf" + '\t' + "Tf*Idf" + '\t' + "sqrt(Tf)*Idf" + '\n')
	
	for word in sorted_keyword_score:
		if stem_dict[word[0]]['idf'] < 1 and word[1] < 6.0 and stem_dict[word[0]]['boost'] ==0:
			continue
		file_output.write(str(stem_dict[word[0]]['words'][0].keyword) + '\t' + str(stem_dict[word[0]]['tf']) + '\t' + str(stem_dict[word[0]]['idf']) + '\t' + str(word[1]) + '\t' + str(math.sqrt(float(stem_dict[word[0]]['tf'])) * stem_dict[word[0]]['idf']))
		file_output.write('\n')
	f.close()

	


def show(object):
    print "showList:"
    for item in object:
        print item


def delimit_sentences(text):
	for i in range(0,len(text)):
		newsent = text[i].split('.')
	#	print "inside delimiter...."
	#	print newsent
		newsent = filter(lambda x: len(x)>0, newsent)
		text.remove(text[i])
		text.extend(newsent)
	return text



class combineNP_chunks:
	def __init__(self):
		self.english_dict = enchant.Dict("en_US")
	def combine_chunks(self,text):
		chunk=''	
		total_chunks = []
		if text == None or len(text) == 0:
			return
		if text[0][2] == 'B-NP' or text[0][2] == 'I-NP':
			text[0] = list(text[0])
			text[0][0] = text[0][0].strip('\\')
			text[0] = tuple(text[0])
			chunk += chunk + text[0][0] + ' '
			flag=1
		else:
			flag=0
		for i in range(1,len(text)):
			text[i] = list(text[i])
			text[i][0] = text[i][0].strip('\\')			#eg: "Master\\" was giving syntax error
			text[i] = tuple(text[i])
			if (text[i][2] =='I-NP' or text[i][2] == 'B-NP') and flag==0:
				
				chunk = chunk + text[i][0] + ' '
				flag = 1
			elif flag==1 and (text[i][2] == 'I-NP' or text[i][2] == 'B-NP'):
				chunk += text[i][0] + ' '
			elif flag==1 and text[i][2] == 'O':
				#if len(chunk.strip())!=0:
				if len(chunk.strip()) > 2:
					total_chunks.append(chunk.strip())
				chunk=''
				flag = 0
		if len(chunk)!=0:
			total_chunks.append(chunk)
		# if a noun(NN/NNP) follows an adjective(JJ), NP chunk is converted into a list of [[JJ, NN], JJ-NN]
		for chunk in total_chunks:
			words = chunk.split(' ')
			words = filter(lambda x: len(x)>0, words)
			final = []
			for word in words:			
				try:
					temp=[]
					ind = [x[0] for x in text].index(word)
					if text[ind][1] == 'JJ':
						#temp.append(chunk[chunk.find(word):chunk.find(word)+len(word)])
						temp.append(chunk[chunk.find(word)+len(word):])
						if len(temp[0]) > 1:
							final.append(temp[0])
				except:
					break
			final.append(chunk)
			if len(final) > 1:
				total_chunks[total_chunks.index(chunk)] = final
		
		return total_chunks

class cleanText:
	def remove_non_ascii_chars(self,chunks_list):
		#for chunk in chunks_list:
		#	print '1  ' + chunk.keyword
	#	print "removing non ascii..........."	
		for chunk in chunks_list:
			non_ascii = False
			#print chunk.keyword
			if len(chunk.keyword) == 0:
				continue
		#	print chunk.keyword
			for i in chunk.keyword:				
				if ord(i)> 128:
		#			print "here entered"
					non_ascii = True
					break
			if non_ascii:
					chunks_list.remove(chunk)
		#	print "^^^^^^^^^^"			
		return chunks_list

	def remove_special_chars(self, chunks_list):
		for chunk in chunks_list:
			chunk.keyword = re.sub('[^A-Za-z ]+', '', chunk.keyword)
			if chunk.keyword == ' ' or chunk.keyword == '\n':
				chunks_list.remove(chunk)
		return chunks_list

def trim_list(total_chunks,f):
	score_obj = getIdfandTf()
	keyword_tf_dir = score_obj.get_tf2(total_chunks)
	for chunk in total_chunks:
		if type(chunk) == list:
			#for word in chunk:
			keyword_idf_dir = score_obj.calculate_idf2(chunk,f)
			keyword_idf_dir = score_obj.get_term_score2(keyword_idf_dir,f)
		#	print keyword_idf_dir
		#	print keyword_tf_dir
			keyword_score = {}
			keyword_score2 = {}
			for k in keyword_tf_dir.iterkeys():
				#print k
				if keyword_idf_dir.has_key(k.lower().strip()):
					if keyword_tf_dir[k] == 1 and keyword_idf_dir[k] < 10.0 and len(k.strip())<2:
					#	print k, keyword_idf_dir, len(k.strip())
						continue		
					#print k, keyword_tf_dir[k] * keyword_idf_dir[k], len(k.strip())
					keyword_score[k] = keyword_tf_dir[k] * keyword_idf_dir[k] 
					keyword_score2[k] = math.sqrt(float(keyword_tf_dir[k])) * keyword_idf_dir[k] * 1.0

			sorted_keyword_score = sorted(keyword_score.iteritems(), key=operator.itemgetter(1), reverse=True)
		#	print sorted_keyword_score
			#print total_chunks.index(chunk)
			try:
				total_chunks[total_chunks.index(chunk)] = sorted_keyword_score[0][0]			
			except:
				total_chunks.remove(chunk)
	return total_chunks

	



class entity_extraction:
	def __init__(self):
		self.db1 = MySQLdb.connect("ssslavedb01", "slideshare", "slideshare12345","slideshare_production" )
		self.db = MySQLdb.connect("tsslavedb01","slideshare","slideshare12345","transcripts_production" )
		self.db2 = MySQLdb.connect("ssslavedb01", "slideshare", "slideshare12345", "slideshare_categorization")
		self.cursor = self.db.cursor()
		self.cursor1 = self.db1.cursor()
		self.cursor2 = self.db2.cursor()
		self.sentence_correction_obj = sentence_correction()
		self.combine_obj = combineNP_chunks()

	
	def title_description_chunks(self,title,description):
		title_data = nltk.tokenize.sent_tokenize(title)
		description_data = nltk.tokenize.sent_tokenize(description)
		title_data = self.sentence_correction_obj.correct_sentence_format(title_data)			
		description_data = self.sentence_correction_obj.correct_sentence_format(description_data)
		print title_data
		print description_data
		title_chunks = []
		for s in title_data:
			#print s
			#s1 = self.preprocess_slide.find_sentence_delimiter(s)
			#title_data[title_data.index(s)] = s1
			#print s1
			title_dump = kk.parse(nltk.pos_tag(nltk.word_tokenize(s)))
			title_dump['tags'] = self.sentence_correction_obj.change_lowercase(title_dump['tags'])
			#show(title_dump['tags'])
			chunks = self.combine_obj.combine_chunks(title_dump['tags'])
			if chunks and len(chunks) > 0:
				title_chunks.extend(chunks)

		title_chunks_list = []
		title_chunks = list(flatten(title_chunks))
	#	print title_chunks
		for chunk in title_chunks:
			title_chunks_list.append(word_struct(chunk,True, False))
		description_chunks = []
		for s in description_data:
			des_dump = kk.parse(nltk.pos_tag(nltk.word_tokenize(s)))
			des_dump['tags'] = self.sentence_correction_obj.change_lowercase(des_dump['tags'])
			chunks = self.combine_obj.combine_chunks(des_dump['tags'])
			if chunks and len(chunks) > 0:
				description_chunks.extend(chunks)
		des_chunks_list = []
		description_chunks = list(flatten(description_chunks))
	#	print description_chunks
		for chunk in description_chunks:
			des_chunks_list.append(word_struct(chunk,False,False))

		return title_chunks_list, des_chunks_list


	def get_tags(self, slide_id):
		sql_query2 = "select keyword_id from slideshow_zkeywords where slideshow_id =" + '"' + str(slide_id) + '"'
		self.cursor2.execute(sql_query2)
		tags_id = self.cursor2.fetchall()
		tags_list = []
		for tag in tags_id:
			s = str(tag[0])
			tags_list.append(s.strip('L'))
		if tags_list:
			sql_query3 = "select keyword from zemanta_keywords where id IN ("+','.join(tags_list)+")"
			self.cursor2.execute(sql_query3)
			tags = self.cursor2.fetchall()
			print tags
			tags_list = []
			for tag in tags:
				tags_list.append(word_struct(str(tag[0]),False, True))
		return tags_list

	def remove_non_ascii(self, slide_text):
		slide_text = slide_text.replace('\r','')
		slide_text = slide_text.replace('\t','')
		slide_text = re.sub('[^A-Za-z0-9.!% ]+', '',slide_text)    
		return ''.join([i if ord(i) < 128 else ' ' for i in slide_text])    



	def get_keywords(self,slideshow_ids,keyword_filename):
	    p = re.compile("[\\\]+n")
	    sql_query = "select slideshow_id, slide_text from transcripts where slideshow_id IN ("+' , '.join(slideshow_ids)+")"
	    sql_query1 = "select title, description from slideshows where id IN ("+','.join(slideshow_ids)+")"
	    self.cursor.execute(sql_query)
	    self.cursor1.execute(sql_query1)
	    transcript_result = self.cursor.fetchall()
	    title_and_des_result = self.cursor1.fetchall()

	    for row, row1 in zip(transcript_result,title_and_des_result):
	    	slide_id = row[0]
	    	total_chunks_list = []
	    	transcript = row[1]
	    	title = row1[0]
	    	description = row1[1]
	    	transcript_1 = p.sub("$$$", transcript)
	    	bb = transcript_1.split("\x0c")
	    	transcript_1 = transcript_1.replace("\n", "$$$")
	    	aa = transcript_1.split("\x0c") ## \x0c is delimitor of slide
	    	transcript_data = [a.split('$$$') for a in aa] ## spliting each slide content on \ns.close()
	        #transcript_data is a list of list of sentences
	        #print transcript_data
	        for slide in bb:
	        	bb[bb.index(slide)] = self.remove_non_ascii(slide)
	        description = self.remove_non_ascii(description)
	        title = self.remove_non_ascii(title)
	        #print len(aa)
	        total_chunks = [] 
	        ##################### get title, description and tags
	        title_chunks, des_chunks = self.title_description_chunks(title, description)
	        tags_chunks = self.get_tags(slide_id)
	        #####################
	        clean_obj = cleanText()
	        #title_chunks = clean_obj.remove_non_ascii_chars(title_chunks)
	        #des_chunks = clean_obj.remove_non_ascii_chars(des_chunks)
	        file_output = open('output/'+str(slide_id)+'.txt','w')
	       	#calculate_score(title_chunks, keyword_filename, True,file_output)
	       	#calculate_score(des_chunks, keyword_filename, False,file_output)
	       	#print transcript_data
	       	for text in transcript_data:
				if text==None:
					continue
				#print text
				text = self.sentence_correction_obj.correct_sentence_format(text)
				#print text
				#print "&&&&&&&&&&&&&&&&"
				for s in text:
					tokens = nltk.pos_tag(nltk.word_tokenize(s))
					dump = kk.parse(tokens)
					dump['tags'] = self.sentence_correction_obj.change_lowercase(dump['tags'])
					#show(dump['tags'])
					chunks = self.combine_obj.combine_chunks(dump['tags'])
					if chunks and len(chunks) > 0:
						total_chunks.extend(chunks)
				
	        total_chunks_list = []
	       	#print total_chunks
	       	################	opens the file for storing the final keywords with their Tf-IDf scores
	       	try:
	       		f = open(keyword_filename,'a')
	       	except:
				import os
				os.system("touch "+keyword_filename)
				f = open(keyword_filename,'a')
	       	################
	       	# selects either NP or JJ+NP depending on the Tf-Idf score
	       	
	       	total_chunks = trim_list(total_chunks,f) 
	    #   	print "after triming.................."
	    #  	print total_chunks
	       	# falttens the list
	        total_chunks = list(flatten(total_chunks))

	        for chunk in total_chunks:
	        	total_chunks_list.append(word_struct(chunk,False, False))            
	    # 	print [chunk.keyword for chunk in total_chunks_list]
	      	total_chunks_list = clean_obj.remove_non_ascii_chars(total_chunks_list)
	      	total_chunks_list = clean_obj.remove_special_chars(total_chunks_list)
	    #  	for t in total_chunks_list:
	    #  		print t.keyword,
	    #  	print
	    	
	    	total_chunks_list.extend(title_chunks)
	      	total_chunks_list.extend(des_chunks)
	      	total_chunks_list.extend(tags_chunks)
	      	print "*********************"
	      	print slide_id
	      	for t in total_chunks_list:
				print t.keyword
	      	print "*********************"
	        calculate_score(total_chunks_list,keyword_filename, True,file_output,f)
        


if __name__ == '__main__':
	train_sents = conll2000.chunked_sents('train.txt', chunk_types=['NP'])
	kk = ConsecutiveNPChunker(train_sents)
	print "got KK:",kk
	entity_extraction_obj = entity_extraction()
	#f = open(sys.argv[1],'r')
	#ids = f.readlines()
	#i=0
	#while i < len(ids):
	#	slideshow_ids = ids[i:i+5]
	#	print slideshow_ids
	slideshow_ids = [sys.argv[1]]
	entity_extraction_obj.get_keywords(slideshow_ids,sys.argv[2])
	#	i = i + 5
	#slideshow_ids = [sys.argv[1]]
	
	
