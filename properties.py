#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import mwapi
import argparse

from pprint import pprint
import simplejson as json

from itertools import islice

def chunk(it, size):
    """Split list into fixed size chunks.

    Usage: list(chunk(range(14), 3)
      ->   [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9, 10, 11), (12, 13)]
    """
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())

def fix_endpoint(endpoint):
    if endpoint.startswith("http://"):
        endpoint = endpoint.replace("http://", "https://")
        
    if not endpoint.startswith("https://"):
        endpoint = "https://" + endpoint
    
    if not endpoint.endswith("/w/api.php"):
        endpoint = endpoint + "/w/api.php"

    return endpoint



def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get(items, output, api):
    string = "|".join(items),
    if pageids:
        query['pageids'] = string[0]
    else:
        query['titles'] = string[0]


    query_handler = api.general_list_query(query, 'ppcontinue')
    pages = {}
    continued = False
    for partial_dict in query_handler.next():
        for key in partial_dict.keys():
            pages[key] = partial_dict[key]
        if query_handler.continues():
            sys.stdout.write('.')
            time.sleep(5)
            continued = True            

    if continued:
        sys.stdout.write('\n')
        
    for pageid in pages.keys():
        if pageid == "-1":
            continue
        page = pages[pageid]
        if 'missing' in page:
            continue
        output.write(page['title'])
        output.write(';')
        output.write(str(page['pageid']))
        output.write(';')
        if 'pageprops' in page:
            output.write(json.dumps(page['pageprops']))
        output.write('\n')

    print_err(f"Wrote {len(pages.keys())}")
        

    
if __name__ == "__main__":    
    parser = argparse.ArgumentParser(description='Hakee annettujen sivujen tiedot.')

    parser.add_argument('--output', '-o', type=str,
                        help='Tulostettavan tiedoston nimi.')
    

    parser.add_argument('-e', '--endpoint', type=str,
                        help='API url eg. en.wiktionary.org/w/api.php',
                        required=True)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--page-ids', '-p', action='store_true',
                        help='Syötteenä annetut tiedot ovat sivujen page id:eitä.')
    
    group.add_argument('--titles', '-t', action='store_true',
                        help='Syötteenä annetut tiedot ovat sivujen nimiä (oletus).')
    
    try:
        args = parser.parse_args()
    except:
        exit(1)
    
    filename = args.output
    titles = args.titles
    pageids = args.page_ids
    endpoint = args.endpoint

    endpoint_fixed = fix_endpoint(endpoint)
    if endpoint_fixed != endpoint:
        endpoint = endpoint_fixed
        print_err(f"Endpoint: {endpoint}")

        
    input_items = []
    line = True
    while line:
        line = sys.stdin.readline()
        if line and line != "":
            input_items.append(line.strip().replace("|", "%7C"))

    print_err(f"Total: {len(input_items)}")

    
    input_chunks = list(chunk(input_items, 50))

    query = { 
        'action'        : 'query', 
        'prop'          : 'pageprops', 
        'ppcontinue'    : None,
    }

    if filename or filename == '-':
        output = sys.stdout
    else:
        output = open(filename, 'a') 

    api = mwapi.MWApi(endpoint)        
    for items in input_chunks:

        get(items, output, api)
        
         


        
