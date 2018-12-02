from os import listdir
from os.path import isfile, join
import sys
import re
import heapq
import math
from string import digits
from itertools import chain

# Path to unsorted indexed blocks and path where merged blocks to be saved
blocks_folder = sys.argv[1]
merged_folder = sys.argv[2]


# Required to remove digits from document field
remove_digits = str.maketrans('', '', digits)

# Names of all the indexed block files to be merged
block_names = [f for f in listdir(blocks_folder)]
block_names.remove('stats.txt')

# Returns keys on which lines should be sorted
def find_key(line):
    return line.split(':')[0]

# Creates merged index blocks 
def write_merged_block(merged_index, block_count, first_key, last_key):
    f = open(merged_folder + str(block_count) + ' ' + first_key + ' ' + last_key, 'w')
    f.write(merged_index)
    f.close()

    
merged_index = ''
block_count = 0
RAM_limit = 200e6  # 200mb untill it gets written 
first = True
debug_counter = 0

for i in heapq.merge(*[open(blocks_folder + str(f),'r') for f in block_names], key = find_key):
    i = i.split(':')
    current_key = i[0]
    current_line = i[1]
    
    if first:
        first_key = current_key
        prev_key = current_key
        prev_line = current_line  
        first = False
    else:
        if current_key == prev_key:
            # Merge both postings
            prev_line = prev_line[:-2] + current_line[1:]
        else:
            merged_index += prev_key + ':' + prev_line[1:-2] + '\n' 

            last_key = prev_key
            prev_line = current_line
            prev_key = current_key

            if len(merged_index) > RAM_limit:
                first = True
                write_merged_block(merged_index, block_count, first_key, last_key)
                block_count += 1
                merged_index = ''

            # Printing out just to see if everything is working
            debug_counter += 1
            if debug_counter%1000000 == 0:
                print('Added to index: ' + str(debug_counter) + ' terms, size: ' +str(len(merged_index)))

# Final write for block which didnt reach limit
last_key = current_key
merged_index += prev_key + ':' + prev_line  
write_merged_block(merged_index, block_count, first_key, last_key) 
