# -*- coding: utf-8 -*-
"""
Created on Sat Feb 23 16:21:29 2019

@author: georg
"""

import re
import nltk
import spacy


nlp = spacy.load('en')

   
class Ingredient:
    def __init__(self, qty, unit, item, comments = None, qty_option = None):
        self.qty = qty
        self.qty_option = qty_option
        self.unit = unit
        self.item = item
        self.comments = comments
    
    def i_print(self):
        print('qty: ',self.qty,
              '\nqty_opt: ',self.qty_option,
              '\nunit: ',self.unit,
              '\nitem: ',self.item,
              '\ncomment: ',self.comments, '\n\n')
        

ingred = ['18 medium taco shells','2 pounds lean ground beef','1 (14 ounce) bottle ketchup','1 (8 ounce) package shredded Cheese','1 large tomato, diced','1 cup iceberg lettuce, shredded']

UNITWORDS = set(['can','jar','pound','ounce','cup','packet','bottle','pinch'])

def cut_s(string):
    s = string
    if s.endswith('s'): s = s[:-1]
    return(s)

def str_to_frac(string):
    t = string.split('/')
    return int(t[0])/int(t[1])

paren_pat = re.compile(r'\((.*?)\)')
def parse_ingred(ingreds):
    parsed_ingreds = []
    
    for line in ingreds:
        # all the vars we need for Ingredient class
        qty = 0
        qty_opt = ''
        unit = ''
        item = ''
        comments = ''
        
        # look for parentheses, take them out, place whats in them in the qty_option
        if re.search(paren_pat,line):
            qty_opt = re.search(paren_pat,line).group(0)
            qty_opt = qty_opt[1:len(qty_opt)-1]
            line = re.sub(r'\((.*?)\)', '', line)
            
            
        # look for numbers, put them in qty
        number = re.search('\d*\s*[^A-Za-z]*', line).group(0)
        for num in number.split():
            if '/' in num:
                num = str_to_frac(num)
            else: 
                num = int(num)
            qty = qty + num
        
        line = re.sub('[0-9]+\s*[^A-Za-z]*', '', line)

        # look for unit words
        if cut_s(line.split()[0]) in UNITWORDS:
            unit = line.split()[0]
            line = ' '.join(line.split()[1:])
        
        # split string on ',' for item and comment
        line = line.split(',')
        item = line[0]
        try:
            comments = line[1]
        except: pass
        
        parsed_ingreds.append(Ingredient(qty,unit,item,comments,qty_opt))
                
    return(parsed_ingreds)


recipe = ['Preheat oven to 375 degrees F (190 degrees C).',
          'Warm taco shells for 5 minutes on the center rack in the preheated oven.',
          'In a medium skillet over medium high heat, brown the beef. Halfway through browning, pour in ketchup. Stir well and let simmer for 5 minutes.',
          'Spoon the meat mixture into the warm taco shells and top with Cheddar cheese. Return the filled taco shells to the preheated oven and bake until cheese is melted. Top each taco with a little tomato and lettuce.']
INGREDS = parse_ingred(ingred)
METHODS = ['top','stir','simmer','mix','spoon','warm','preheat','bake','brown','pour','return', 'pour in']
sortedmethods = sorted(set([i for i in METHODS]), key=len, reverse = True)
ingred_list = sorted(set([i.item for i in INGREDS]), key=len)

def pwords(doc):
    for token in doc:
        print(token.text, token.pos_, token.dep_)
def pchunk(doc):
    for chunk in doc.noun_chunks:
        print(chunk.text, chunk.root.text, chunk.root.dep_,
              chunk.root.head.text)
def pdep(doc):
    for token in doc:
        print(token.text, token.dep_, token.head.text, token.head.pos_, token.pos_,
          [child for child in token.children])


# recipe assumptions: they all start with a verb OR they start with a prep phrase in which case, verb appears after the comma
# and commas only exist if the sentence starts with a prep phrase
def find_ingred(line):
    wordoverlaps = [None] * len(line.split())
    index = 0
    for word in line.split():
        num_overlap = [len(set([word]).intersection(set(i.split()))) for i in ingred_list]
        if max(num_overlap) > 0:  #if we're able to match more than one word
            wordoverlaps[index] = ingred_list[num_overlap.index(max(num_overlap))]  #grab the first (and thus shortest) award name that matches max(num_overlap) times
        else:
            wordoverlaps[index] = None
        index += 1
    ans = []
    inds = []
    for i in range(len(wordoverlaps)):
        if wordoverlaps[i] != None:
            ans.append(wordoverlaps[i])
            inds.append(i)
    return ans, inds
        
def find_method(line):
    linecopy = line
    for verb in sortedmethods:
        line = linecopy
        span = len(verb.split())
        while len(line) > 0:
            tmp = line.split()[0:span]
            test = ' '.join(tmp).lower()
            if test == verb:
                return verb
            line = ' '.join(line.split()[1:])
    return None
            

class Step:
    def __init__(self, ingreds = None, tools=None, time=None, method=None, method_opt= None):
        self.ingreds= ingreds
        self.tools = tools
        self.time = time
        self.method=method
        self.method_opt = method_opt

def parse_recipe(recipe):
    sentences = []
    for i in recipe:
        j = (i.split('.'))
        for y in j:
            if y == '': pass
            else: 
                if y[0] == ' ':
                    y = y[1:]
                sentences.append(y)
            
    sent2 = []
    for i in sentences:
        j = i.split('and')
        for z in range(len(j)):
            y = j[z]
            if y == '': pass
            else:
                if y[0] == ' ':
                    y = y[1:]
                indicator = 0
                for word in y.split():
                    if word.lower() in set(METHODS):
                        indicator = 1
                        break               
                if indicator == 1:
                    sent2.append(y)
                else:
                    if z == 0:
                        sent2.append(y)
                    else:
                        tmp = sent2[-1]
                        sent2 = sent2[:-1]
                        sent2.append(tmp + 'and ' + y)
    sentences = sent2            

    splits = []
    for line in sentences:
        g = line.split(',')
        split = []
        for j in g:
            prev = 0
            doc = nlp(j)
            for i in range(len(doc)):
                word = doc[i]
                if word.pos_ == 'ADP':
                    if i > 0 and doc[i-1].pos_ == 'VERB': pass
                    elif word.text.lower() != 'through':         
                        tmp = doc[prev:i]
                        if len(tmp) > 0:
                            split.append(doc[prev:i])
                        prev = i
            split.append(doc[prev:])
        splits.append(split)


    verb = ''
    verbs = []
    ingredlist = []
    for i in range(len(splits)):
        verb = ''
        split = splits[i]
        for j in range(len(split)):
            s = split[j]
            if s[0].pos_ == 'ADP' :pass
            else:    
                a = find_method(s.text)
                if a:
                    verb = a
                    ingred, inds = find_ingred(s.text)
                    splits[i][j] = nlp(s.text.lower().replace(a, ' ').lstrip())
                    for ind in inds:
                        tmpword = s[ind].text
                        #splits[i][j] = nlp(s.text.lower().replace(tmpword, ' ').lstrip())
                    verbs.append(verb)
                    ingredlist.append(ingred)

        # identify the verb (in case we didnt catch it with KB)
    for verb in verbs:
        if verb == '':
            ingred = []
            for s in splits:
                ingred = []
                if s[0].pos_ == 'ADP': pass
                else: 
                    for j in s:
                        if j.pos_ == 'VERB':
                            ingred = find_ingred(s.text)
                            verb = j
                            break
                        else: pass
            if str(verb) == '':
                for s in splits:
                    if s[0].pos_ == 'ADP': pass
                    else: 
                        verb = s[0]
                        ingred = find_ingred(s.text)
            verbs = [verb]
            stack = [child for child in verb.children ]
            while stack != []:
                for child in stack:
                    stack.remove(child)
                    if child.pos_ == 'VERB':
                        index = 0
                        for s in splits:
                            if child.text in s.text: index = splits.index(s)                        
                        if splits[index][0].pos_ == 'ADP': pass
                        else: 
                            verbs.append(child)
                        for i in child.children:
                            stack.append(i)
            print(line,'-----', verbs, ingred)
        
    #cleaning up        
    splits2 = []
    for i in splits:
        prev = 0
        newsplit = []
        for j in i:
            if j:
                for k in range(len(j)):
                    if j[k].pos_ == 'ADP':
                        newsplit.append(j[prev:k])
                        prev = k
                newsplit.append(j[prev:])
                print(prev)
            else:
                pass
        splits2.append(newsplit)
        
        for i in splits2:
            for j in i:
                if not j:
                    i.remove(j)
    
    #work on method_opts
    methodopts = [None] * len(splits2)
    for i in range(len(splits2)):
        tmplist = []
        split = splits2[i]
        for j in split:
            for k in j:
                if k.pos_ == 'ADP':
                    tmplist.append(j)
        methodopts[i] = tmplist
    
    steps = []
    for i in range(len(splits2)):
        tmpstep = Step(ingredlist[i], method = verbs[i], method_opt = methodopts[i])
        steps.append(tmpstep)
    
def __init__(self, ingreds = None, tools=None, time=None, method=None, method_opt= None)    


doc = nlp(u'Apple is looking at buying U.K. startup for $1 billion')
for token in doc:
    print(token.text, token.pos_, token.dep_)    

class Parsed_Recipe:
    def __init__(self, ingred_string, recipe_string):
        self.ingredients = parse_ingred(ingred_string)
        self.recipe = parse_recipe(recipe_string)
