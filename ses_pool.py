import os
import sys
import nltk
import pickle

text_paragraphs_sentences_clauses = []  								#master array of paragraph arrays of sentence arrays of clauses
functions = []															#array of which functions have been defined
objects = ['number','string','word','phrase','point','vector']			#array of which objects have been defined
filename = str
parsed_file = file
method_object_indent = 0
indent = 0

ses_pool_tagger_file = open('ses_pool_tagger.pickle','rb')				#unpickle the brill tagger set object which will do most of the tagging in parse()
brill_tagger = pickle.load(open('ses_pool_tagger.pickle','rb'))

def setup_parsed_file():
	parsed_file.writelines('import math\n')

def tag(clause):
	pos = {}															#this is a dictionary of lists of tuples to reference [part of speech][cardinal number starting with 0][0 for actual string or 1 for position in sentence] eg. pos['VB'][1][0] would be the string of the second verb in pos
	pos_tag=brill_tagger.tag(nltk.word_tokenize(clause))				#here is our nltk magic. guesses the part of speech of every word. uses a custom brill tagger
	position=0
	for word in pos_tag:												#commence screwing with grammar so that we can whittle parts of speech down from brown's  40+ parts of speech
		part = word[1]													#a temp variable so that we can screw around with grammar (we need 'word' so we can use it to reference sentence position)
		if not part:part='NN'											
		if part in ('CD','NP'):part = 'NN'
		if len(word[0])==1 and part<>'AT':part = 'NN'
		if part in ('CC','IN'):part = 'CC'
		if part.startswith('VB'):part = 'VB'
		if part in ('BEZ'):part = 'VB'
		if word[0]=='print':part = 'VB'
		if word[0]=='times':part = 'CC'
		if word[0]=='minus':part = 'CC'
		if not pos.has_key(part):										
			pos[part]=[]
		pos[part].append((word[0],position))
		position+=1
	return pos

def sort_paragraphs():													#sorts paragraphs in text_paragraphs_sentences_clauses
	return text_paragraphs_sentences_clauses.reverse()

def parse_object_definitions(pos):
	return False

def parse_function_definitions(pos):
	return False

def parse_conditionals(pos,clause):
	global indent
	if pos.has_key('CS'):
		subord_conjunc = pos['CS'][0]
		if subord_conjunc[0] == 'if':
			indent+=1
			return 'if (' + str(parse_clause(clause.partition(pos['CS'][0][0])[2],'expression'))+'):'
	
def parse_functions(pos,clause,clause_type):							#parsing for functional code begins here. It will have a lot of nested if-thens out of necessity
	if pos.has_key('VB'):												
		verb = pos['VB'][0]	
		if clause_type!='expression':
			if verb[0] in ('is','equals','equates'):
				return pos['NN'][0][0]+'='+str(parse_clause(clause.partition(verb[0])[2]))
		if verb[0] in ('Set','set','Make','make','Turn','turn','Let','let'):
				if len(pos['VB'])>1:
					return pos['NN'][0][0]+'='+str(parse_clause(clause.partition(pos['VB'][1][0])[2]))
				return pos['NN'][0][0]+'='+str(parse_clause(clause.partition(pos['NN'][0][0])[2]))
		if verb[0] in ('add','Add'):
			return pos['NN'][1][0]+'+='+str(parse_clause(clause.partition(verb[0])[2]).partition('to')[0])
		if verb[0] in ('subtract','Subtract'):
			return pos['NN'][1][0]+'-='+str(parse_clause(clause.partition(verb[0])[2]).partition('from')[0])
		if verb[0] in ('stop','Stop','kill','Kill','end','End'):
			if pos.has_key('NN'):
				if pos['NN'][0][0] in ('program','window','process',filename):
					return 'exit()'
			else:
				return 'exit()'
		if verb[0] in ('say','Say','write','Write','print','Print','display','Display'):
			return 'print ' + str(parse_clause(clause.partition(verb[0])[2]))
		if verb[0] in ('ask','query','input','prompt'):
			return pos['NN'][0][0]+'= raw_input('+pos['NN'][0][0]+')'
		print 'I don\'t know how to '+verb[0]+'. Please add on a paragraph explaining how to '+verb[0]
		return False
	
def parse_expressions(pos,clause):										#parsing for expressions begins here.
	if pos.has_key('CC'):												
		coord_conjunc = pos['CC'][0]
		if coord_conjunc[0] == 'plus':
			return pos['NN'][0][0]+'+'+str(parse_clause(clause.partition('plus')[2]))
		if coord_conjunc[0] == 'minus':
			return pos['NN'][0][0]+'-'+str(parse_clause(clause.partition('minus')[2]))
		if coord_conjunc[0] == 'over':
			return pos['NN'][0][0]+'/'+str(parse_clause(clause.partition('over')[2]))
		if coord_conjunc[0] == 'times':
			return pos['NN'][0][0]+'*'+str(parse_clause(clause.partition('times')[2]))
		if coord_conjunc[0] == 'by':
			if pos.has_key('VB'):
				if pos['VB'][0][0] == 'multiplied':
					return pos['NN'][0][0]+'*'+str(parse_clause(clause.partition('multiplied')[2]))
				if pos['VB'][0][0] == 'divided':
					return pos['NN'][0][0]+'/'+str(parse_clause(clause.partition('divided')[2]))
	if pos.has_key('VB'):
		verb = pos['VB'][0][0]
		if verb == 'is':
			if pos.has_key('JJR'):
				adjective = pos['JJR'][0][0]
				if adjective in ('greater','larger','bigger','more'):
					if len(pos['JJR'])>1 and pos['JJR'][1][0] in ('equal','equivalent','same'):
						return str(parse_clause(clause.partition('is')[0]))+'>='+str(parse_clause(clause.partition(pos['JJR'][1][0])[2]))
					return str(parse_clause(clause.partition('is')[0]))+'>'+str(parse_clause(clause.partition(pos['JJR'][0][0])[2]))
				if adjective in ('less','smaller'):
					if len(pos['JJR'])>1 and pos['JJR'][1][0] in ('equal','equivalent','same'):
						return str(parse_clause(clause.partition('is')[0]))+'<='+str(parse_clause(clause.partition(pos['JJR'][1][0])[2]))
					return str(parse_clause(clause.partition('is')[0]))+'<'+str(parse_clause(clause.partition(pos['JJR'][0][0])[2]))
			return str(parse_clause(clause.partition('is')[0]))+'=='+str(parse_clause(clause.partition('is')[2]))
		if verb in ('equals','equates'):
			return str(parse_clause(clause.partition(verb)[0]))+'=='+str(parse_clause(clause.partition(verb)[2]))
	if pos.has_key('NN'):
		noun = pos['NN'][0][0]
		if noun in ('Sin','sin','Sine','sine'):
			return 'math.sin('+str(parse_clause(clause.partition(noun)[2]))+')'
		if noun in ('Cos','cos','Cosine','cosine'):
			return 'math.cos('+str(parse_clause(clause.partition(noun)[2]))+')'
		if noun in ('Tan','tan','Tangent','tangent'):
			return 'math.tan('+str(parse_clause(clause.partition(noun)[2]))+')'
		if noun in ('Square','square'):
			if len(pos['NN'])>1 and pos['NN'][1][0] == 'root':
				return 'math.sqrt('+str(parse_clause(clause.partition('root')[2]))+')'
			return 'math.pow('+str(parse_clause(clause.partition(noun)[2]))+',2)'
		if noun in ('Cube','cube'):
			if len(pos['NN'])>1 and pos['NN'][1][0] == 'root':
				return 'math.pow('+str(parse_clause(clause.partition('root')[2]))+',1.0/3)'
			return 'math.pow('+str(parse_clause(clause.partition(noun)[2]))+',3)'
		if noun in ('Log','log','Logarithm','logarithm'):
			return 'math.log('+str(parse_clause(clause.partition(noun)[2]))+')'
		if noun == 'pi':
			return 'math.pi'
		if noun == 'e':
			return 'math.e'
		return pos['NN'][0][0]
	return False

def parse_clause(clause,clause_type='expression'):							#recursively analyze a clause and extract meaning
	global first_sentence
	pos=tag(clause)	
	print pos															#just here for debugging purposes
	
	'''if pos.has_key('NN') and first_sentence==True:						#parsing for object declaration begins here
		pos
	if pos.has_key('TO') and first_sentence==True:						#parsing for function definitions begins here
		if pos.has_key('VB') and pos['VB'][0][1]>pos['TO'][0][1]:
			return define_function(pos)'''
	if clause_type=='first':
		if parse_object_definitions(pos):return parse_object_definitions(pos)
		if parse_function_definitions(pos):return parse_function_definitions(pos)
	if parse_conditionals(pos,clause):return parse_conditionals(pos,clause)
	if parse_functions(pos,clause,clause_type):return parse_functions(pos,clause,clause_type)
	if parse_expressions(pos,clause):return parse_expressions(pos,clause)
	return False														#if the sentence is meaningless, don't return anything

def parse_text_array():													#parses text_paragraphs_sentences_clauses by passing individual clauses to parse_clause()
	global parsed_file, text_paragraphs_sentences_clauses, indent
	for paragraph in text_paragraphs_sentences_clauses:
		first_sentence=True
		for sentence in paragraph:
			for clause in sentence:	
				for x in range(1,indent):
					parsed_file.writelines('	')
				if indent>0:indent-=1
				if first_sentence==True:
					parsed_file.writelines(str(parse_clause(clause,'first')))
				else:
					parsed_file.writelines(str(parse_clause(clause,'normal')))
				parsed_file.writelines('				#'+clause)
				parsed_file.writelines('\n')

def main():
	global filename, parsed_file, text_paragraphs_sentences_clauses
	try:
		if len(sys.argv) == 1:
			filename = raw_input('Enter program name: ')			#get name of desired ses file
		else:
			filename = sys.argv[1]
		if filename.endswith('.ses'):filename=filename.rpartition('.')[0]
		text = open(filename+'.ses')								#open the ses file
		parsed_file = open(filename+'.py','w')						#open what will be the parsed python file
	except IOError:
		print 'Oops!  That was not a valid file name.  Try again...'#if the ses file doesn't exist try again
		exit()
	text_string = text.read()											#a string of the entire ses file, basically unusable
	text.close()
	setup_parsed_file()
	
	text_paragraphs = text_string.split('\n')							#split text into paragraphs
	for paragraph in text_paragraphs:									#get data into the text_paragraphs_sentences_clauses array
		paragraph = paragraph+' '
		paragraph_sentences = paragraph.split('. ')						#local array for sentences cut from the paragraphs, still pretty much useless with all the punctuation
		paragraph_sentence_clauses = []									#local array for sentence arrays of clauses that will ultimately be translated into lines of code split along punctuation

		for sentence in paragraph_sentences:
		    paragraph_sentence_clauses.append(sentence.split(', '))		#array of sentence arrays of clauses to be plugged into text_paragraphs_sentences_clauses
		text_paragraphs_sentences_clauses.append(paragraph_sentence_clauses)
	
	sort_paragraphs()
	
	parse_text_array()
	
	parsed_file.close()													#close the parsed python file
	os.system('python '+filename+'.py')									#run the parsed python file. will deploy when I feel it works

if __name__ == '__main__':												#initialize the program
	main()
