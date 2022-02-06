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



def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

    
parser = argparse.ArgumentParser(description='Hakee annettujen sivujen tiedot.')

parser.add_argument('-o', type=str,
                    help='Tulostettavan tiedoston nimi.')

parser.add_argument('--output', type=str,
                    help='Tulostettavan tiedoston nimi.')

parser.add_argument('-p', action='store_true',
                    help='Syötteenä annetut tiedot ovat sivujen page id:eitä.')

parser.add_argument('--page-ids', action='store_true',
                    help='Syötteenä annetut tiedot ovat sivujen page id:eitä.')

parser.add_argument('-t', action='store_true',
                    help='Syötteenä annetut tiedot ovat sivujen nimiä (oletus).')

parser.add_argument('--titles', action='store_true',
                    help='Syötteenä annetut tiedot ovat sivujen nimiä (oletus).')

args = parser.parse_args()

filename = args.output or args.o
titles = args.titles or args.t
pageids = args.page_ids or args.p

if not titles and not pageids:
    titles = True
    
if titles and pageids:
    eprint("Virheelliset parametrit. Anna joko --titles tai --page-ids")
    exit(1)


if not filename:
    eprint("Tiedosto puuttuu (--output)")
    exit(1)
    
if __name__ == "__main__":
    #api = mwapi.MWApi("https://commons.wikimedia.org/w/api.php")
    #api = mwapi.MWApi("https://fi.wiktionary.org/w/api.php")
    #api = mwapi.MWApi("https://sv.wikipedia.org/w/api.php")
    api = mwapi.MWApi("https://fi.wikipedia.org/w/api.php")
    #api = mwapi.MWApi("https://en.wikipedia.org/w/api.php")
    #api = mwapi.MWApi("https://fi.wikisource.org/w/api.php")

    input_items = []

    line = True
    while line:
        line = sys.stdin.readline()
        if line and line != "":
            input_items.append(line.strip().replace("|", "%7C"))

    eprint(f"{len(input_items)} sivua")

    input_chunks = list(chunk(input_items, 50))

    query = { 
        'action'        : 'query', 
        'prop'          : 'pageprops', 
        #'pprop'         : ,
        'ppcontinue'    : None,
    }


    with open(filename, 'w') as the_file:    
        for items in input_chunks:

            string = "|".join(items),
            if pageids:
                query['pageids'] = string[0]
            else:
                query['titles'] = string[0]
    
            result = api.simple_query(query)
            if not 'query' in result:
                eprint("Ei 'queryä' tuloksessa: ")
                pprint(result)
                exit(1)
            
            if not 'pages' in result['query']:
                eprint("Ei 'pagesiä' tuloksessa: ")
                pprint(result)
                exit(1)

            pages = result['query']['pages']
            for pageid in pages.keys():
                if pageid == "-1":
                    continue
                page = pages[pageid]
                if 'missing' in page:
                    continue
                the_file.write(page['title'])
                the_file.write(';')
                the_file.write(str(page['pageid']))
                the_file.write(';')
                if 'pageprops' in page:
                    the_file.write(json.dumps(page['pageprops']))
                the_file.write('\n')

            if len(pages.keys()) > 0:
                print(f"Kirjoitettiin {len(pages.keys())}")
            else:
                print("Ei kirjoitettu mitään")
            


        
