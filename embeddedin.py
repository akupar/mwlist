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


def get(template, output, api):
    query['eititle'] = 'Template:' + template
    print_err("Fetching:", query['eititle'])

    query_handler = api.general_list_query(query, "eicontinue")

    page_list = []
    for partial_list in query_handler.next():
        page_list = page_list + partial_list
        if query_handler.continues():
            sys.stdout.write('.')
            time.sleep(5)

    if partial_list:
        sys.stdout.write('\n')
        
    for line in page_list:
        output.write(line['title'])
        output.write(';')
        output.write(template)                
        output.write('\n')

    print_err(f"Wrote: {len(page_list)}")

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Lists pages a template is embedded in in a mediawiki wiki')
    
    parser.add_argument('--output', '-o', type=str,
                        help='Output file name')
    
    parser.add_argument('--template', '-t', type=str,
                        help='Template')
    
    parser.add_argument('-e', '--endpoint', type=str,
                        help='API url eg. en.wiktionary.org/w/api.php',
                        required=True)
    
    try:
        args = parser.parse_args()
    except:
        exit(1)
        
    
    filename = args.output
    template = args.template
    endpoint = args.endpoint

    endpoint_fixed = fix_endpoint(endpoint)
    if endpoint_fixed != endpoint:
        print_err(f"Endpoint: {endpoint}")
        endpoint = endpoint_fixed

    query = { 
        'action'        : 'query',
        'format'        : 'json',
        'list'          : 'embeddedin', 
        'eititle'       : None,
        #'einamespace'   : "0",
        #'eidir'         : dir                  and dir, 
        'eilimit'       : 500,
        #'eiprop'       : "|",
        'eicontinue'    : None,
    }
        

    api = mwapi.MWApi(endpoint)

    if not filename or filename == '-':
        output = sys.stdout
    else:
        output = open(filename, 'a') 
    
    if template:
        get(template, output, api)
    else:
        print_err("Enter template names:")
        while True:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if line == '':
                break
            
            get(line, output, api)

            

