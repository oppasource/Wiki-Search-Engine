import sys
import time
import xml.sax
import re
import pickle
import collections

full_xml_path = sys.argv[1]
saving_path = sys.argv[2]

block = 0
limit = 10e6 # Write after 'limit' number of dict entries


docid2title = dict()

class XMLHandler(xml.sax.ContentHandler):
    
    def __init__(self):
        self.is_page_id = False
        self.isId = False
        self.isTitle = False
        self.isRedirect = False
        
        self.idBuffer = ""
        self.titleBuffer = ""
    
    def write(a):
        string = ''
        d = [(k, a[k]) for k in sorted(a, key=int)]
        
#         for i in d:
#             string += str(i) + '\n'
        # Name of block indexes is of format (<block number> <start word of index> <last word of index> )
        file_name = str(block)+ ' ' + str(d[0][0]) + ' ' + str(d[-1][0])
        file_name = saving_path + file_name
        with open(file_name +'.pickle', 'wb') as handle:
            pickle.dump(a, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
    def startElement(self, name, attrs):
        if name == 'page':
            self.is_page_id = True
            
        if name == 'title':
            self.isTitle = True
            self.titleBuffer = ""
            
        if name == 'redirect':
            self.isRedirect = True
          
        # Checking if id is page id
        if name == 'id' and self.is_page_id:
            self.isId = True
            self.idBuffer = ""    
            
    def characters(self, content):
        if self.isId:
            self.idBuffer += content
            
        if self.isTitle:
            self.titleBuffer += content
    
    def endElement(self, name):
        global block
        global docid2title
        
        if name == 'id' and self.isId:
            self.isId = False
            self.is_page_id = False
            
            docid2title[self.idBuffer] = self.titleBuffer
            
            if int(self.idBuffer)%10000 == 0:
                print(self.idBuffer + '  ' + str(len(docid2title)) )
                
                if (len(docid2title) > limit):
                    XMLHandler.write(docid2title)
                    block += 1
                    docid2title = dict()
                 
        elif name == 'title':
            self.isTitle = False
            

start_time = time.time()

parser = xml.sax.make_parser()
parser.setContentHandler(XMLHandler())
parser.parse(open(full_xml_path, "r", encoding = 'utf-8'))
    
XMLHandler.write(docid2title)

# Printing seconds passed since start time
print("--- %s seconds ---" % (time.time() - start_time))
