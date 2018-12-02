import sys
import time
import xml.sax
import re
from html import unescape
from Stemmer import Stemmer
import collections

stemmer = Stemmer("english")

index = dict()
total_documents = 0
check_RAM = 0
block_number = 0
document_interval = 2000
max_index_size = 100e6    # 100MB each block
max_index_size = 2*max_index_size

# Path to xml dump and path to index blocks to be saved
full_xml_path = sys.argv[1]
index_path = sys.argv[2]


# Creating a list of stop words
with open("./nltkstopwords.txt", 'r', encoding = 'utf-8') as input_file:
    STOPWORDS = input_file.read().rstrip().split('\n')
STOPWORDS = list(set(STOPWORDS))

    
class Indexer():
    
    # This method is used to update the global index 
    def updateIndex(docid, title, body, infobox, category, link, reference):
        global index
        
        structured_data = {'t':title, 'b':body,'i':infobox,'c':category,'l':link,'r':reference}
        
        for k,v in structured_data.items():
            for w in v:  
                try:
                    index[w][docid][k] +=1
                except:
                    try:
                        index[w][docid].update({k:1})
                    except:
                        try:
                            index[w].update({docid:{k:1}})
                        except:
                            index.update({w:{docid:{k:1}}})  
    
    # Helper function to replace multiple chars in string
    def replace_all(text, dic):
        for i, j in dic.items():
            text = text.replace(i, j)
        return text
    
    # This method is used to write the fully updated index to the file
    def write_index(block_num):
        global index
        index_string = ''
        
        index = collections.OrderedDict(sorted(index.items()))
        
        # Name of block indexes is of format (<block number> <start word of index> <last word of index> )
        file_name = str(block_num)+ ' ' + str(list(index.items())[0][0]) + ' ' + str(list(index.items())[-1][0])
        
        for word, docs in index.items():
            d = {'"':'','\'':'',',':'',' ':'',':':''}
            index_string += word+':' + Indexer.replace_all(str(docs),d) + '\n'
        
        f = open(index_path + file_name,'w', encoding = 'utf-8')
        f.write(str(index_string))
        f.close()
                    
# Class contains methods for processing text like case folding, tokenization, stemming, etc
class TextProcessor(): 
   
    # Function removes all unwanted strings, performs tokenization, stop word removal, stemming
    # Returns list of processed words
    def processText(text):
        global STOPWORDS
        global ps

        # '(<\/?[\w" -=]+\/?>)'                                                xml tags
        # '(\w+=(?!=)|\w+ =(?!=))'                                             attribute keys
        # '(https?:\/\/[#+&,\w\./%?=-]+|:?\/?\/?www.[#+&,\w\./%?=-]+)'         urls
        # '(\[\[category:)'                                                    category 
        # '[{[\],|\'#@\)+^\\%$~\.\(=};<>!–:"&*`\?\/_-]'                        all the punctuations
        # '([A-z0-9]+)'                                                        only alphabets 

        #text = ' '.join(text)
        text = re.sub(r'(<\/?[\w" -=]+\/?>)'    
                      '|(\w+=(?!=)|\w+ =(?!=))'
                      '|(https?:\/\/[#+&,\w\./%?=-]+'
                      '|:?\/?\/?www.[#+&,\w\./%?=-]+)'
                      '|(\[\[category:)'
                      '|\{\{defaultsort:', '', text, flags=re.MULTILINE)
        
        # Removing "cite" as it dose not charaterize document for searching
        text = re.sub(r'(\{\{cite[\',\w =]+\|)', '', text, flags=re.MULTILINE)
        
        # Removing all the puntuations and replacing it with space
        text = re.sub(r'[{[\],|\'#@\)+^\\%$~\.\(=};<>!–:"&*`\?\/_-]', ' ', text, flags=re.MULTILINE)
        
        # Removing all the non-english words and Stop Words, also performs Stemming
        text = [stemmer.stemWord(i) for i in text.split() if (i == i.encode("ascii", errors="ignore").decode()) and (i not in STOPWORDS)]
        
        return text
        
    # This function takes in text field and separates out 
    # infobox, category, references, external links, body present in that text field
    def separateOut(data):
        data = unescape(data)
        data = data.lower()
        lines = data.split('\n')
        
        info_bracket = 0
        category_flag = 0
        ref_flag = 0
        link_flag = 0
        
        category = ''
        infobox = ''
        reference = ''
        body = ''
        link = ''
        
        if len(lines) >= 1:
            for line in lines:

                if '{{infobox' in line or '{{taxobox' in line:
                    info_bracket += 1
                    #infobox.append(line)
                elif '{{' in line and '}}' not in line and info_bracket:
                    info_bracket += 1
                    infobox += line + ' '
                elif '}}' in line and '{{' not in line and info_bracket:
                    info_bracket -= 1
                    infobox += line + ' '
                elif info_bracket:
                    infobox += line + ' '
                elif '== reference' in line or '==reference' in line:
                    ref_flag = 1
                elif ('== external' in line or '==external' in line):
                    ref_flag = 0
                    link_flag = 1
                elif ('==' in line or '[[category' in line) and (ref_flag or link_flag):
                    ref_flag = 0
                    link_flag = 0
                    if '[[category:' in line:
                        category += line + ' '
                elif ref_flag:
                    if '{{reflist' not in line:
                        reference += line + ' '
                elif link_flag:
                    link += line + ' '
                elif '[[category:' in line:
                    category += line + ' '
                else:
                    if '{{link' not in line:
                        body += line + ' '
                        
        category = TextProcessor.processText(category) 
        infobox = TextProcessor.processText(infobox)
        reference = TextProcessor.processText(reference)
        body = TextProcessor.processText(body)
        link = TextProcessor.processText(link)
        
        return category, infobox, reference, body, link
    
    def processTitle(t):
        t = t.lower()
        # For punctuations
        t = re.sub(r'[{[\],|\'#@\)+^\\%$~\.\(=};<>!–:"&*`\?\/_-]', ' ', t, flags=re.MULTILINE)
        t = [stemmer.stemWord(i) for i in t.split() if ((i == i.encode("ascii", errors="ignore").decode()) and (i not in STOPWORDS) )]
        return t

class XMLHandler(xml.sax.ContentHandler):
    
    def __init__(self):
        self.is_page_id = False
        self.isId = False
        self.isTitle = False
        self.isText = False
        self.isRedirect = False
        
        self.textBuffer = ""
        self.idBuffer = ""
        self.titleBuffer = ""
        
    def startElement(self, name, attrs):
        if name == 'page':
            self.is_page_id = True 
        elif name == 'title':
            self.isTitle = True
            self.titleBuffer = ""
        elif name == 'redirect':
            self.isRedirect = True
        elif name == 'text':
            self.isText = True
            self.textBuffer = ""
        # Checking if id is page id
        elif name == 'id' and self.is_page_id:
            self.is_page_id = False
            self.isId = True
            self.idBuffer = ""
            
            
    def characters(self, content):
        if self.isId:
            self.idBuffer += content
        elif self.isTitle:
            self.titleBuffer += content  
        elif self.isText:
            self.textBuffer += content
           
    
    def endElement(self, name):
        global index
        global total_documents
        global check_RAM
        global block_number
        global document_interval
        global max_index_size
        
        if name == 'id':
            self.isId = False
            
        elif name == 'title':
            self.isTitle = False
            
        elif name == 'text':
            self.isText = False
            total_documents += 1
            check_RAM += 1
            
            if not self.isRedirect:
                title = TextProcessor.processTitle(self.titleBuffer)
                category, infobox, reference, body, link = TextProcessor.separateOut(self.textBuffer)
                Indexer.updateIndex(self.idBuffer, title, body, infobox, category, link, reference)
                
                # After every certain number of documents we check if index can still fit in memory 
                # Else make a block file and empty the index
                if (check_RAM % document_interval) == 0:
                    if (len(str(index)) >= max_index_size):
                        print('writing file! ' + str(total_documents))
                        Indexer.write_index(block_number)
                        block_number += 1
                        index = dict()
                        check_RAM = 0
                        
            self.isRedirect = False


start_time = time.time()

parser = xml.sax.make_parser()
parser.setContentHandler(XMLHandler())
parser.parse(open(full_xml_path, "r", encoding = 'utf-8'))

# Adding remaining index
Indexer.write_index(block_number)

f = open(index_path + 'stats.txt', 'w', encoding = 'utf-8')
f.write("Number of Documents: " + str(total_documents))
f.close()


# Printing seconds passed since start time
print("--- %s seconds ---" % (time.time() - start_time))
