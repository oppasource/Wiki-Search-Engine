# Wiki-Search-Engine

## Getting the output

- Make three empty folders for indexed_blocks, merged_blocks and id2title

1. First run indexer.py with following arguments. 
			First argument:- /path/to/xml/dump
			Second argument:- /path/to/folder/of/indexed_blocks/
	It will create index blocks of a particular maximum size with file name format "<block number> <first word of index> <last word of index>.txt"

	example usage:- python3 indexer.py /path/to/xml/dump /path/to/folder/of/indexed_blocks/




2. Second run merger.py with following arguments. 
			First argument:- /path/to/folder/of/indexed_blocks/
			Second argument:- /path/to/folder/of/merged_blocks/
	It will create merged blocks of a particular maximum size with same file name format as before.

	example usage:- python3 merger.py /path/to/folder/of/indexed_blocks/ /path/to/folder/of/merged_blocks/ 




3. Third run id2title.py with following arguments. 
			First argument:- /path/to/xml/dump
			Second argument:- /path/to/folder/of/docid2title/

	example usage:- python3 id2title.py /path/to/xml/dump /path/to/folder/of/docid2title dict/




4. Last run search.py with following arguments:
			First argument:- /path/to/folder/of/indexed_blocks/
			Second argument:- /path/to/folder/of/docid2title dict/
			Third argument:- /path/to/folder/of/merged_blocks/
	
	example usage:- python3 search.py /path/to/folder/of/indexed_blocks/ /path/to/folder/of/docid2title dict/ /path/to/folder/of/merged_blocks/
