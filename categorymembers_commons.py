#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import mwapi
import argparse

from pprint import pprint


parser = argparse.ArgumentParser(description='Optional app description')

parser.add_argument('-o', type=str,
                    help='Tulostettavan tiedoston nimi.')

parser.add_argument('--output', type=str,
                    help='Tulostettavan tiedoston nimi.')

parser.add_argument('-c', type=str, nargs='+',
                    help='Haettava Commons-luokka')

parser.add_argument('--category', type=str, nargs='+',
                    help='Haettava Commons-luokka')

args = parser.parse_args()

filename = args.output or args.o
category = " ".join(args.category or args.c)
    
if __name__ == "__main__":
    api = mwapi.MWApi("https://commons.wikimedia.org/w/api.php")
    #api = mwapi.MWApi("https://fi.wiktionary.org/w/api.php")
    #api = mwapi.MWApi("https://en.wikipedia.org/w/api.php")
    #api = mwapi.MWApi("https://fi.wikisource.org/w/api.php")

    query = { 
        'action'        : 'query', 
        'list'          : 'categorymembers', 
        'cmtitle'       : 'Category:' + category,
        'cmnamespace'   : "*",
        #'cmdir'         : dir                  and dir, 
        'cmlimit'       : 50,
        #'cmprop'       : "|",
        'cmcontinue'    : None,
        #'rawcontinue' : '',
    }

    if not filename:
        print(f'Käyttö: {sys.argv[0]} --output <tiedosto> --category <hakemisto>')
        exit(1)

    filename = filename.replace("~", "/home/antti/")
        
    if os.path.exists(filename):
        append_write = 'a'
    else:
        append_write = 'w'
        
    with open(filename, append_write) as the_file:
        for list_ in api.general_query(query, "cmcontinue"):
            for line in list_:
                the_file.write(line['title'])
                the_file.write('\n')

            if len(list_) > 0:
                eka = list_[0]
                vika = list_[len(list_)-1]
                print(f"Kirjoitettiin {len(list_)} riviä ('{eka}' – '{vika}'")
            else:
                print("Ei kirjoitettu mitään")
            


        
