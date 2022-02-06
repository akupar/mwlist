#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import argparse

import mwapi

def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def fix_endpoint(endpoint):
    if endpoint.startswith("http://"):
        endpoint = endpoint.replace("http://", "https://")
        
    if not endpoint.startswith("https://"):
        endpoint = "https://" + endpoint
    
    if not endpoint.endswith("/w/api.php"):
        endpoint = endpoint + "/w/api.php"

    return endpoint


def get(category, output, api):
    query['cmtitle'] = 'Category:' + category
    print_err("Fetching:", query['cmtitle'])

    query_handler = api.general_list_query(query, "cmcontinue")

    page_list = []
    continued = False
    for partial_list in query_handler.next():
        page_list = page_list + partial_list
        if query_handler.continues():
            sys.stderr.write('.')
            time.sleep(5)
            continued = True

    if continued:
        sys.stderr.write('\n')
        
    for line in page_list:
        output.write(line['title'])
        output.write(';')
        output.write(category)                
        output.write('\n')

    print_err(f"Wrote: {len(page_list)}")

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Lists category members of a mediawiki wiki')
    
    parser.add_argument('--output', '-o', type=str,
                        help='Output file name')
    
    parser.add_argument('--category', '-c', type=str,
                        help='Category to fetch')
    
    parser.add_argument('-e', '--endpoint', type=str,
                        help='API url eg. en.wiktionary.org/w/api.php',
                        required=True)
    
    try:
        args = parser.parse_args()
    except:
        exit(1)
        
    
    filename = args.output
    category = args.category
    endpoint = args.endpoint

    endpoint_fixed = fix_endpoint(endpoint)
    if endpoint_fixed != endpoint:
        endpoint = endpoint_fixed
        print_err(f"Endpoint: {endpoint}")
    
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

    api = mwapi.MWApi(endpoint)

    if filename or filename == '-':
        output = sys.stdout
    else:
        output = open(filename, 'a') 
    
    if category:
        get(category, output, api)
    else:
        print_err("Enter category names:")
        while True:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if line == '':
                break
            
            get(line, output, api)

            


        
