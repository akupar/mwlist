#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import mwapi
import argparse

from pprint import pprint


parser = argparse.ArgumentParser(description='Optional app description')

parser.add_argument('--output', '-o', type=str,
                    help='Tulostettavan tiedoston nimi.')

args = parser.parse_args()

filename = args.output

if not filename:
    print("Tiedosto puuttuu")
    exit(1)


query = { 
    'action'        : 'query', 
    'list'          : 'categorymembers', 
    'cmtitle'       : None,
    'cmnamespace'   : "*",
    #'cmdir'         : dir                  and dir, 
    'cmlimit'       : 500,
    #'cmprop'       : "|",
    'cmcontinue'    : None,
    #'rawcontinue' : '',
}


def get(category, the_file, api):
    query['cmtitle'] = 'Category:' + category
    print("haetaan:", query['cmtitle'])


    query_ = api.general_query(query, "cmcontinue")
    print("list::", query_.list)
    for line in query_.list:
        the_file.write(line['title'])
        the_file.write(';')
        the_file.write(category)                
        the_file.write('\n')

            
    
    
if __name__ == "__main__":
    #api = mwapi.MWApi("https://commons.wikimedia.org/w/api.php")
    api = mwapi.MWApi("https://fi.wiktionary.org/w/api.php")
    #api = mwapi.MWApi("https://en.wikipedia.org/w/api.php")
    #api = mwapi.MWApi("https://fi.wikisource.org/w/api.php")



    if not filename:
        print(f'Käyttö: {sys.argv[0]} --output <tiedosto>')
        exit(1)

    print("Avattu:", filename)
    with open(filename, 'a') as the_file:
        
        print("Anna syöte:")

        line = sys.stdin.readline()
        while line:
            line = line.strip()

            if line:
                get(line, the_file, api)

            time.sleep(5)                
            line = sys.stdin.readline()

            the_file.flush()
        

        
