#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import mwapi
import argparse

from pprint import pprint




def get(category, the_file, api):
    query['cmtitle'] = 'Category:' + category
    print("Fetching:", query['cmtitle'])

    query_ = api.general_list_query(query, "cmcontinue")

    lst = query_.list

    while query_.continues():
        query['cmcontinue'] = query_.ticket
        query_ = api.general_query(query, "cmcontinue")
        lst = lst + query_.list
        if query_.continues():
            time.sleep(5)
        
    for line in lst:
        the_file.write(line['title'])
        the_file.write(';')
        the_file.write(category)                
        the_file.write('\n')

    print(f"Wrote: {len(lst)}")

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Lists category members of a mediawiki wiki')
    
    parser.add_argument('--output', '-o', type=str,
                        help='Output file name',
                        required=True)
    
    parser.add_argument('--category', '-c', type=str,
                        help='Category to fetch',
                        required=True)
    
    parser.add_argument('-a', '--api-url', type=str,
                        help='API url eg. en.wiktionary.org/w/api.php',
                        required=True)
    
    try:
        args = parser.parse_args()
    except:
        exit(1)
        
    
    filename = args.output or args.o
    category = args.category or args.c
    apiurl = args.api_url
    
    if not apiurl.startswith("http"):
        apiurl = "https://" + apiurl
    
    if not apiurl.endswith("/w/api.php"):
        apiurl = apiurl + "/w/api.php"
    
    
    if not filename or not category:
        print("Missing file name (-o)")
        exit(1)
    
    if not category:
        print("Missing category (-c)")
        exit(1)
    
    if not apiurl:
        print("Missing api url (-a)")
        exit(1)
        
        
    query = { 
        'action'        : 'query', 
        'list'          : 'categorymembers', 
        'cmtitle'       : 'Category:' + category,
        'cmnamespace'   : "*",
        #'cmdir'         : dir                  and dir, 
            'cmlimit'       : 500,
        #'cmprop'       : "|",
            'cmcontinue'    : None,
        #'rawcontinue' : '',
    }

    api = mwapi.MWApi(apiurl)

    with open(filename, 'a') as the_file:

        get(category, the_file, api)

            


        
