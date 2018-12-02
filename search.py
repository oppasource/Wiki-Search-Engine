import time
import sys
import multiprocessing
import re
from Stemmer import Stemmer
from os import listdir
from os.path import isfile, join
import math
from string import digits
import operator
import pickle
import itertools
import signal

print("\nPlease Wait!\n")

class TimeoutError (RuntimeError):
    pass

def alarm_handler(signum, frame):
    raise TimeoutError()

# Number of documents indexed for idf
with open((sys.argv[1]) + 'stats.txt', 'r', encoding = 'utf-8') as input_file:
    N = input_file.read()
    N = int(N.split()[-1])

stemmer = Stemmer("english")
timeout = 10  # timeout untill query processes

# Following code is to load dictionary to map from document id to document title
doc2title = dict()
mypath = sys.argv[2]
index_files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
for i in index_files:
    with open(mypath + i, 'rb') as handle:
        b = pickle.load(handle)
        doc2title.update(b)
        del b

# Required to remove digits from document field
remove_digits = str.maketrans('', '', digits)

# path of merged index to look up 
mypath = sys.argv[3]
index_files = [f for f in listdir(mypath) if isfile(join(mypath, f))]


# Stopwords to be removed
with open("./nltkstopwords.txt", 'r', encoding = 'utf-8') as input_file:
    STOPWORDS = input_file.read().rstrip().split('\n')
STOPWORDS = list(set(STOPWORDS))


# Calculates tf-idf score for each doc given doc info(body, title, etc content)
def cal_tf_idf(field, num_docs, idf):
    
    tf_d = re.split(r'[blicrt]',field)[1:]
    tf_d = math.log(1 + sum(list(map(int, tf_d))))
    tf_idf = tf_d * idf
    
    return tf_idf


# Funtion returns top 10 docs given a query (Query should not specify fields e.g. title, category, etc)
def non_field_query(inp):
    # doc_score to keep all the retrieved documents with score (tf-idf)
    doc_score = dict()
    
    # Preprocessing (case folding, tokenization, etc on query)
    t = re.sub(r'[{[\],|\'#@\)+^\\%$~\.\(=};<>!–:"&*`\?\/_-]', ' ', inp, flags=re.MULTILINE)
    t = [stemmer.stemWord(i) for i in t.lower().split() if (i not in STOPWORDS) ]

    for w in t:
        index_file = None
        for j in index_files:
            ranges = j.split()
            if (ranges[1] <= w) and (ranges[2] >= w):
                index_file = j
                break

        if index_file is not None:
            with open(mypath + index_file) as fileobject:
                for line in fileobject:
                    if w +':' in line and re.match(r'^'+re.escape(w)+':', line):

                        posting = line.split(':')[1]
                        l = re.findall(r'\w+',posting)

                        num_docs = len(l)/2
                        idf = math.log(N/num_docs)

                        for i in range(0,len(l)-1,2):
                            # l[i] -> docid
                            # l[i-1] -> field
                            tf_idf = cal_tf_idf(l[i+1], num_docs, idf)
                            # Keep adding the scores for documents in the dictionary
                            doc_score[l[i]] = doc_score.get(l[i], 0) + tf_idf
                        break

    # Sort the documents by score 
    sorted_x = sorted(doc_score.items(), key = operator.itemgetter(1), reverse = True)
    
    sorted_x = [k for k, v in sorted_x[:60]]
    return sorted_x


# Funtion returns top 10 docs given a query (Query should specify fields e.g. title, category, etc)
def field_query(inp):
    # doc_attendence to keep all the retrieved documents with attendence (Number of occurrances)
    doc_attendence = dict()
    
    l = re.split('(\w:)', inp)[1:]
    
    # Make dict of above list with first and next element as key value pairs
    # d = {docid : 'fieldinfo'} 
    d = dict(itertools.zip_longest(*[iter(l)] * 2, fillvalue=""))
    
    for k, v in d.items():
        # Preprocessing (case folding, tokenization, etc on query)
        t = re.sub(r'[{[\],|\'#@\)+^\\%$~\.\(=};<>!–:"&*`\?\/_-]', ' ', v, flags=re.MULTILINE)
        t = [stemmer.stemWord(i) for i in t.lower().split() if (i not in STOPWORDS) ]
        
        for w in t:
            index_file = None
            for j in index_files:
                ranges = j.split()
                if (ranges[1] <= w) and (ranges[2] >= w):
                    index_file = j
                    break
            
            if index_file is not None:
                with open(mypath + index_file) as fileobject:
                    for line in fileobject:
                        if w +':' in line and re.match(r'^'+re.escape(w)+':', line):

                            posting = line.split(':')[1]
                            l = re.findall(r'\w+',posting)
                            
                            for i in range(1,len(l),2):
                                # l[i] -> field
                                # l[i-1] -> docid
                                if k[0] in l[i]:
                                    # Keep adding the scores for documents in the dictionary
                                    doc_attendence[l[i-1]] = doc_attendence.get(l[i-1], 0) + 1
                            break
    
    # Sort the documents by score
    sorted_x = sorted(doc_attendence.items(), key = operator.itemgetter(1), reverse = True)
    sorted_x = [k for k, v in sorted_x[:60]]
    return sorted_x
    
    
# Function is used to print all the results given document ids as input
def print_beautifully(l):
    count = 0
    
    for i in range(len(l)):
        try:
            title = doc2title[l[i]]
            if count<10:
                if ('Wikipedia:' not in title) and ('File:' not in title) and ('List of' not in title):
                    print('{:<3s}'.format(str(count+1)+')') + '{:<10s}'.format(l[i]) + ': \t' + doc2title[l[i]]  + '\n')
                    count += 1
            else:
                return
        except:
            pass
        
    if count == 0:
        print("Sorry, try adding some more keywords")
    
    
###################### Input ########################

while True:
    inp = input('PLease enter your query: ')
    print('\n')

    start_time = time.time()
    # set signal handler for time out
    signal.signal(signal.SIGALRM, alarm_handler)
     
    try:
        signal.alarm(timeout)
        if re.match(r'[bitlcr]:', inp):
            l = field_query(inp)
            if not l:
                print_beautifully(non_field_query(inp))
            else:
                print_beautifully(l)
        else:
            print_beautifully(non_field_query(inp))
        signal.alarm(0)
        print("\n\nQuery took \"%s\" seconds \n" % (time.time() - start_time))
    except TimeoutError:
        print('Sorry, Time out\n')
