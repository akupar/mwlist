#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import mwapi
import argparse

from pprint import pprint




def get(category, output_file, api):
    query['cmtitle'] = 'Category:' + category
    print("Fetching:", query['cmtitle'])

    query_handler = api.general_list_query(query, "cmcontinue")

    page_list = []
    for partial_list in query_handler.next():
        sys.stdout.write('.')
        page_list = page_list + partial_list
        if query_handler.continues():
            time.sleep(5)
        
    for line in page_list:
        output_file.write(line['title'])
        output_file.write(';')
        output_file.write(category)                
        output_file.write('\n')

    print(f"Wrote: {len(page_list)}")

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Lists category members of a mediawiki wiki')
    
    parser.add_argument('--output', '-o', type=str,
                        help='Output file name',
                        required=True)
    
    parser.add_argument('--category', '-c', type=str,
                        help='Category to fetch')
    
    parser.add_argument('-a', '--api-url', type=str,
                        help='API url eg. en.wiktionary.org/w/api.php',
                        required=True)
    
    try:
        args = parser.parse_args()
    except:
        exit(1)
        
    
    filename = args.output
    category = args.category
    apiurl = args.api_url
    
    if not apiurl.startswith("http"):
        apiurl = "https://" + apiurl
    
    if not apiurl.endswith("/w/api.php"):
        apiurl = apiurl + "/w/api.php"
    
    query = { 
        'action'        : 'query', 
        'list'          : 'categorymembers', 
        'cmtitle'       : None,
        'cmnamespace'   : "*",
        #'cmdir'         : dir                  and dir, 
            'cmlimit'       : 30,
        #'cmprop'       : "|",
            'cmcontinue'    : None,
    }

    api = mwapi.MWApi(apiurl)

    if category:
        with open(filename, 'a') as output_file:        
            get(category, output_file, api)
    else:
        with open(filename, 'a') as output_file:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break

                line = line.strip()
                if line == '':
                    break
            
                get(line, output_file, api)

            


        
