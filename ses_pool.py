#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ses_pool.py
#
# Copyright 2013 mistahowe
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.
#
# Makes use of:
# the python natural language toolkit library (nltk)
# the brown corpus
# the brill tagger
#

import os
import sys
import nltk
import pickle

text_paragraphs_sentences_phrases = []									#master array of paragraph arrays of sentence arrays of phrases
functions = []															#array of which functions have been defined
objects = ['number','string','word','phrase','point','vector']			#array of which objects have been defined
filename = str
parsed_file = file
log_file = file
method_object_indent = 0
indent = 0

ses_pool_tagger_file = open('ses_pool_tagger.pickle','rb')				#unpickle the brill tagger set object which will do most of the tagging in parse()
brill_tagger = pickle.load(open('ses_pool_tagger.pickle','rb'))

def setup_parsed_file():
	parsed_file.writelines('import math \n')

def write_to_file(parsed, phrase):
	global parsed_file, indent
	if not parsed == ' ':
		for x in range(0,indent):
			parsed_file.writelines('	')
		parsed_file.writelines(parsed)
		parsed_file.writelines('						#'+phrase)
		parsed_file.writelines('\n')

def tag(phrase):
	global log_file
	pos = {}															#this is a dictionary of lists of tuples to reference [part of speech][cardinal number starting with 0][0 for actual string or 1 for position in sentence] eg. pos['VB'][1][0] would be the string of the second verb in pos
	pos_tag=brill_tagger.tag(nltk.word_tokenize(phrase))				#here is our nltk magic. guesses the part of speech of every word. uses a custom brill tagger
	position=0
	in_quotes=False
	for word in pos_tag:												#commence screwing with grammar so that we can whittle parts of speech down from brown's  40+ parts of speech
		part = word[1]													#a temp variable so that we can screw around with grammar (we need 'word' so we can use it to reference sentence position)
		if '-' in str(part):part = part.partition('-')[0]
		if not part:part='NN'											
		if part in ('CD','CD','NP','NNS'):part = 'NN'
		if len(word[0])==1 and part<>'AT':part = 'NN'
		if part in ('CC','IN'):part = 'CC'
		if part in ('VBZ','VBN'):part = 'VB'
		if part in ('BEZ'):part = 'VB'
		if word[0] in ('print','exit','end','Print','Exit','End'):part = 'VB'
		if word[0] in ('times','minus'):part = 'CC'
		if word[0]=='less':part = 'JJR'
		if in_quotes:part = 'QUOTE'
		if word[0] in ("''",'``'):
			in_quotes = not in_quotes
			part = word[0]
		if not pos.has_key(part):										
			pos[part]=[]
		pos[part].append((word[0],position))
		position+=1
	log_file.writelines(str(pos)+'\n')
	return pos

def sort_paragraphs():													#sorts paragraphs in text_paragraphs_sentences_phrases
	global text_paragraphs_sentences_phrases, objects
	object_sections = {}
	object_sections['main']=[]
	object_sections['functions']=[]
	temp_text = []
	for paragraph in text_paragraphs_sentences_phrases:
		pos = tag(paragraph[0][0])
		if pos.has_key('TO') and pos['TO'][0][1] < pos['NN'][0][1]:
				if pos.has_key('AT'):
					if not (pos['NN'][0][0] in objects):
						print "I don't know what a " + pos['NN'][0][0] + " is. Please explain."
					object_sections[pos['NN'][0][0]].append(0,paragraph)
				object_sections['functions'].append(paragraph)
		object_sections['main'].append(paragraph)
	for section in object_sections:
		if section in objects:
			temp_text.extend(section)
	temp_text.extend(object_sections['functions'])
	temp_text.extend(object_sections['main'])
	text_paragraphs_sentences_phrases = temp_text
	return True
			
def parse_punctuation(pos,phrase,phrase_type):
	if pos.has_key('``') and pos['``'][0][1] == 0: 
		return phrase.partition("''")[0] + str(parse_phrase(phrase.partition("''")[2]))
	return False

def parse_conjunctions(pos,phrase,phrase_type):
	if pos.has_key('CC') and pos['CC'][0][0] in ('and','or'):
		if not phrase_type == 'conditional':
			write_to_file(str(parse_phrase(phrase.partition('and')[0],'normal')),phrase)
			write_to_file(str(parse_phrase(phrase.partition('and')[2],'normal')),phrase)
			return ' '
	if pos.has_key('CC') and pos['CC'][0][0] == 'plus':
		return str(parse_phrase(phrase.partition('plus')[0]))+' +'+str(parse_phrase(phrase.partition('plus')[2]))
	if pos.has_key('CC') and pos['CC'][0][0] == 'minus':
		return str(parse_phrase(phrase.partition('minus')[0]))+' -'+str(parse_phrase(phrase.partition('minus')[2]))
	if pos.has_key('CC') and pos['CC'][0][0] == 'over':
		return str(parse_phrase(phrase.partition('over')[0]))+' /'+str(parse_phrase(phrase.partition('over')[2]))
	if pos.has_key('CC') and pos['CC'][0][0] == 'times':
		return str(parse_phrase(phrase.partition('times')[0]))+' *'+str(parse_phrase(phrase.partition('times')[2]))
	return False

def parse_object_definitions(pos):
	return False

def parse_function_definitions(pos):
	return False

def parse_conditionals(pos,phrase):
	global indent
	if pos.has_key('CS'):
		subord_conjunc = pos['CS'][0]
		if subord_conjunc[0] in ('If','if'):
			write_to_file('if (' + str(parse_phrase(phrase.partition(pos['CS'][0][0])[2],'conditional'))+' ):',phrase)
			indent+=1
			if pos['VB'][0][1] < subord_conjunc[1]:
				return str(parse_phrase(phrase.partition(pos['CS'][0][0])[0]))
			else:
				return ' '
		if subord_conjunc[0] in ('while','while','As','as'):
			write_to_file('while (' + str(parse_phrase(phrase.partition(pos['CS'][0][0])[2],'conditional'))+' ):',phrase)
			indent+=1
			if pos['VB'][0][1]<subord_conjunc[1]:return ' '
			return str(parse_phrase(phrase.partition(pos['CS'][0][0])[0]))
	if pos.has_key('WRB'):
		subord_conjunc = pos['WRB'][0]
		if subord_conjunc[0] in ('When','when'):
			write_to_file('if (' + str(parse_phrase(phrase.partition(pos['WRB'][0][0])[2],'conditional'))+' ):',phrase)
			indent+=1
			if pos['VB'][0][1]<subord_conjunc[1]:return ' '
			return str(parse_phrase(phrase.partition(pos['WRB'][0][0])[0]))
			
def parse_functions(pos,phrase,phrase_type):							#parsing for functional code begins here. It will have a lot of nested if-thens out of necessity
	global indent
	if pos.has_key('VB'):												
		verb = pos['VB'][0]	
		if phrase_type not in ('expression','conditional'):
			if verb[0] in ('is','equals','equates'):
				return pos['NN'][0][0]+' ='+str(parse_phrase(phrase.partition(verb[0])[2]))
		if verb[0] in ('Set','set','Make','make','Turn','turn','Let','let'):
				if len(pos['VB'])>1:
					return pos['NN'][0][0]+' ='+str(parse_phrase(phrase.partition(pos['VB'][1][0])[2]))
				return pos['NN'][0][0]+' ='+str(parse_phrase(phrase.partition(pos['NN'][0][0])[2]))
		if verb[0] in ('add','Add'):
			return pos['NN'][1][0]+' +='+str(parse_phrase((phrase.partition(verb[0])[2]).partition('to')[0]))
		if verb[0] in ('subtract','Subtract'):
			return pos['NN'][1][0]+' -='+str(parse_phrase((phrase.partition(verb[0])[2]).partition('from')[0]))
		if pos.has_key('CC') and pos['CC'][0][0] == 'by':
			if pos.has_key('VB'):
				if pos['VB'][0][0] in ('multiply','Multiply'):
					return pos['NN'][0][0]+' = '+pos['NN'][0][0]+'*'+str(parse_phrase(phrase.partition('by')[2]))
				if pos['VB'][0][0] in ('divide','Divide'):
					return pos['NN'][0][0]+' = '+pos['NN'][1][0]+'/'+str(parse_phrase(phrase.partition('by')[2]))
				if pos['VB'][0][0] == 'multiplied':
					return pos['NN'][0][0]+' * '+str(parse_phrase(phrase.partition('multiplied')[2]))
				if pos['VB'][0][0] == 'divided':
					return pos['NN'][0][0]+' / '+str(parse_phrase(phrase.partition('divided')[2]))
		if verb[0] in ('stop','Stop','kill','Kill','end','End','exit','Exit'):
			if pos.has_key('NN'):
				if pos['NN'][0][0] in ('program','window','process',filename):
					return 'exit()'
				if pos['NN'][0][0] in ('loop','statement','while','if','test'):
					indent-=1
			else:
				return 'exit()'
		if verb[0] in ('say','Say','write','Write','print','Print','display','Display'):
			return 'print ' + str(parse_phrase(phrase.partition(verb[0])[2]))
		if verb[0] in ('ask','query','input','prompt','get'):
			write_to_file (pos['NN'][0][0]+" = (raw_input('"+pos['NN'][0][0]+"? '))",phrase)
			return "if "+pos['NN'][0][0]+".isdigit():"+pos['NN'][0][0]+" = int("+pos['NN'][0][0]+" )"
		if not verb[0] in ('is','equals','equates'):
			print 'I don\'t know how to '+verb[0]+'. Please add on a paragraph explaining how to '+verb[0]
		return False
	
def parse_expressions(pos,phrase,phrase_type):							#parsing for expressions begins here.
	if pos.has_key('CC'):	
		coord_conjunc = pos['CC'][0]
		if coord_conjunc[0] == 'and':
			if phrase_type == 'conditional':
				return str(parse_phrase(phrase.partition('and')[0])) + ' and' + str(parse_phrase(phrase.partition('and')[2]))
		if coord_conjunc[0] == 'or':
			if phrase_type == 'conditional':
				return str(parse_phrase(phrase.partition('or')[0])) + ' or' + str(parse_phrase(phrase.partition('or')[2]))
	if pos.has_key('VB'):
		verb = pos['VB'][0][0]
		if phrase_type in ('expression','conditional'):
			if verb == 'is':
				if pos.has_key('JJR'):
					adjective = pos['JJR'][0][0]
					if adjective in ('greater','larger','bigger','more'):
						if len(pos['JJR'])>1 and pos['JJR'][1][0] in ('equal','equivalent','same'):
							return str(parse_phrase(phrase.partition('is')[0]))+' >='+str(parse_phrase(phrase.partition(pos['JJR'][1][0])[2]))
						return str(parse_phrase(phrase.partition('is')[0]))+' >'+str(parse_phrase(phrase.partition(pos['JJR'][0][0])[2]))
					if adjective in ('less','smaller'):
						if len(pos['JJR'])>1 and pos['JJR'][1][0] in ('equal','equivalent','same'):
							return str(parse_phrase(phrase.partition('is')[0]))+' <='+str(parse_phrase(phrase.partition(pos['JJR'][1][0])[2]))
						return str(parse_phrase(phrase.partition('is')[0]))+' <'+str(parse_phrase(phrase.partition(pos['JJR'][0][0])[2]))
				return str(parse_phrase(phrase.partition('is')[0]))+' =='+str(parse_phrase(phrase.partition('is')[2]))
			if verb in ('equals','equates'):
				return str(parse_phrase(phrase.partition(verb)[0]))+' =='+str(parse_phrase(phrase.partition(verb)[2]))
	if pos.has_key('NN'):
		noun = pos['NN'][0][0]
		if noun in ('Sin','sin','Sine','sine'):
			return 'math.sin('+str(parse_phrase(phrase.partition(noun)[2]))+')'
		if noun in ('Cos','cos','Cosine','cosine'):
			return 'math.cos('+str(parse_phrase(phrase.partition(noun)[2]))+')'
		if noun in ('Tan','tan','Tangent','tangent'):
			return 'math.tan('+str(parse_phrase(phrase.partition(noun)[2]))+')'
		if noun in ('Square','square'):
			if len(pos['NN'])>1 and pos['NN'][1][0] == 'root':
				return 'math.sqrt('+str(parse_phrase(phrase.partition('root')[2]))+')'
			return 'math.pow('+str(parse_phrase(phrase.partition(noun)[2]))+',2)'
		if noun in ('Cube','cube'):
			if len(pos['NN'])>1 and pos['NN'][1][0] == 'root':
				return 'math.pow('+str(parse_phrase(phrase.partition('root')[2]))+',1.0/3)'
			return 'math.pow('+str(parse_phrase(phrase.partition(noun)[2]))+',3)'
		if noun in ('Log','log','Logarithm','logarithm'):
			return 'math.log('+str(parse_phrase(phrase.partition(noun)[2]))+')'
		if noun == 'pi':
			return 'math.pi'
		if noun == 'e':
			return 'math.e'
		temp = ''
		for noun in pos['NN']:
			temp = temp + ' ' + noun[0]
		return temp
	return False

def parse_phrase(phrase,phrase_type='expression'):						#recursively analyze a phrase and extract meaning
	global first_sentence
	pos = tag(phrase)
	if phrase_type=='first':
		result = parse_object_definitions(pos)
		if result:return result
		result = parse_function_definitions(pos)
		if result: return result
	result = parse_conditionals(pos,phrase)
	if result:return result
	result = parse_conjunctions(pos,phrase,phrase_type)
	if result:return result
	result = parse_punctuation(pos,phrase,phrase_type)
	if result:return result
	result = parse_functions(pos,phrase,phrase_type)
	if result:return result
	result = parse_expressions(pos,phrase,phrase_type)
	if result:return result
	return ' '															#if the sentence is meaningless, don't return anything

def parse_text_array():													#parses text_paragraphs_sentences_phrases by passing individual phrases to parse_phrase()
	global parsed_file, text_paragraphs_sentences_phrases, indent, method_object_indent
	for paragraph in text_paragraphs_sentences_phrases:
		first_sentence=True
		for sentence in paragraph:
			for phrase in sentence:	
				if first_sentence==True:
					write_to_file(str(parse_phrase(phrase,'first')),phrase)
				else:
					write_to_file(str(parse_phrase(phrase,'normal')),phrase)
			indent = method_object_indent

def main():
	global filename, parsed_file, text_paragraphs_sentences_phrases, log_file
	try:
		if len(sys.argv) == 1:
			filename = raw_input('Enter program name: ')		
		else:
			filename = sys.argv[1]
		if filename.endswith('.ses'):filename=filename.rpartition('.')[0]
		text = open(filename+'.ses')									#open the ses file
		parsed_file = open(filename+'.py','w')							#open what will be the parsed python file
		log_file = open(filename+'_logs.txt','w')
	except IOError:
		print 'Oops!  That was not a valid file name.  Try again...'	#if the ses file doesn't exist try again
		exit()
	text_string = text.read()											#a string of the entire ses file, basically unusable
	text.close()
	setup_parsed_file()
	
	text_paragraphs = text_string.split('\n')							#split text into paragraphs
	for paragraph in text_paragraphs:									#get data into the text_paragraphs_sentences_phrases array
		paragraph = paragraph+' '
		paragraph_sentences = paragraph.split('. ')						#local array for sentences cut from the paragraphs, still pretty much useless with all the punctuation
		paragraph_sentence_phrases = []									#local array for sentence arrays of phrases that will ultimately be translated into lines of code split along punctuation

		for sentence in paragraph_sentences:
		    paragraph_sentence_phrases.append(sentence.split(', '))		#array of sentence arrays of phrases to be plugged into text_paragraphs_sentences_phrases
		text_paragraphs_sentences_phrases.append(paragraph_sentence_phrases)
	
	sort_paragraphs()
	
	parse_text_array()
	
	parsed_file.close()													#close the parsed python file
	os.system('python '+filename+'.py')									#run the parsed python file. will deploy when I feel it works

if __name__ == '__main__':												#initialize the program
	main()
