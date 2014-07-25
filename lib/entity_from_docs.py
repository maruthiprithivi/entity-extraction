from nltk import tokenize
#from nltk.corpus import conll2000
#from nltk.chunk.util import conlltags2tree
#import json
import re, sys, ast
#import enchant, math
#from nltk.corpus import conll2000
#from nltk.chunk.util import conlltags2tree
import MySQLdb, collections
#from keyword_structure import word_struct
import urllib2
total_documents = 13000000


def show(object):
    print "showList:"
    for item in object:
        print item


def delimit_sentences(text):
  for i in range(0,len(text)):
    newsent = text[i].split('.')
  # print "inside delimiter...."
  # print newsent
    newsent = filter(lambda x: len(x)>0, newsent)
    text.remove(text[i])
    text.extend(newsent)
  return text

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
    #text = map(lambda x: re.sub('[0-9]+ ', '', x) , text)
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
      s = tokenize.sent_tokenize(t)
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
    
    text = delimit_sentences(text)
    return text
  
  def remove_url(self, text):
    for sentence in text:
      url_text = re.findall(self.url, sentence)
      url_text.extend(re.findall(self.url1,sentence))
      for url in url_text:
        sentence.replace(url,'')
      text[text.index(sentence)] = sentence
    return text

class entity_extraction:
  def __init__(self):
    self.db1 = MySQLdb.connect("ssslavedb01", "slideshare", "slideshare12345","slideshare_production" )
    self.db = MySQLdb.connect("tsslavedb01","slideshare","slideshare12345","transcripts_production" )
    self.db2 = MySQLdb.connect("ssslavedb01", "slideshare", "slideshare12345", "slideshare_categorization")
    print "creating istance"
    self.cursor = self.db.cursor()
    self.cursor1 = self.db1.cursor()
    self.cursor2 = self.db2.cursor()
    self.sentence_correction_obj = sentence_correction()
    print "done!!!!"

  def remove_non_ascii(self, slide_text):
    slide_text = slide_text.replace('\r','')
    slide_text = slide_text.replace('\t','')
    slide_text = re.sub('[^A-Za-z0-9.!% ]+', '',slide_text)   
    return ''.join([i if ord(i) < 128 else ' ' for i in slide_text])  


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

  def html_query(self, s, final_entities):
  # print "in html_query.........."
    path = 'http://192.168.6.85:6860/get_entity?query='
    s = path + s
    s = s.replace(' ','+')
    #print s
    string = urllib2.urlopen(s).read()
    l = ast.literal_eval(string)
    l = filter(lambda x: type(x)==list, l)
    #if string == '{}':
    # return final_entities
    #print l

    for temp in l:
      final_entities[temp[0]] = temp[1]
    return final_entities

  def delimit(self, data):
    p = re.compile("[\\\]+n")
    transcript_1 = p.sub("$$$", data)
    transcript_1 = transcript_1.replace("\n", "$$$")
    aa = transcript_1.split("\x0c") ## \x0c is delimitor of slide
    final_data = [a.split('$$$') for a in aa]   
    return final_data

  def get_keywords(self,slideshow_ids):
      p = re.compile("[\\\]+n")
      sql_query = "select slideshow_id, slide_text from transcripts where slideshow_id IN ("+' , '.join(slideshow_ids)+")"
      sql_query1 = "select title, description from slideshows where id IN ("+','.join(slideshow_ids)+")"
      self.cursor.execute(sql_query)
      self.cursor1.execute(sql_query1)
      transcript_result = self.cursor.fetchall()
      title_and_des_result = self.cursor1.fetchall()
      print slideshow_ids
      for row, row1 in zip(transcript_result,title_and_des_result):
        slide_id = row[0]
        total_chunks_list = []
        transcript = row[1]
        title = row1[0]
        description = row1[1]
        print slide_id
          
        transcript_data = self.delimit(transcript)
        title = self.remove_non_ascii(title)
        description = self.remove_non_ascii(description)
        description = tokenize.sent_tokenize(description)
        for des in description:
          d = self.delimit(des)
          description.remove(des)
          description.extend(d[0])
          #tags_chunks = self.get_tags(slide_id)
          
        final_entities = {}

          # for title
        final_entities = self.html_query(title.lower(), final_entities)
          #for description
        for des in description:
          if len(des)==0 or des == '\n' or des == ' ':
            continue
          final_entities = self.html_query(des.strip().lower(), final_entities)

          # for transcripts
        for text in transcript_data:
          if text==None:
            continue
          text = self.sentence_correction_obj.correct_sentence_format(text)
          # print text
          for s in text:
            s = self.remove_non_ascii(s)
      #     print s
            if len(s) ==0 or s=='\n' or s==' ':
              continue
#           print s
            final_entities = self.html_query(s.strip().lower(), final_entities)
        print len(final_entities)
        for key, val in final_entities.iteritems():
          print key, val
        #file_output = open('document_output/'+str(slide_id)+'.txt','w')
        #for key, val in final_entities.iteritems():
        #  file_output.write(key + '\t' + val + '\n')
        #file_output.close()
      # print final_entities

if __name__ == '__main__':
  print "in main...."
  entity_extraction_obj = entity_extraction()
  #f = open(sys.argv[1],'r')
  #ids = f.readlines()
  #i=0
  #while i < len(ids):
  # slideshow_ids = ids[i:i+5]
  # print slideshow_ids
  slideshow_ids = [sys.argv[1]]
  entity_extraction_obj.get_keywords(slideshow_ids)
  # i = i + 5
  #slideshow_ids = [sys.argv[1]]
  
  
