#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import apina
import argparse

from pprint import pprint


parser = argparse.ArgumentParser(description='Optional app description')

parser.add_argument('-o', type=str,
                    help='Tulostettavan tiedoston nimi.')

parser.add_argument('--output', type=str,
                    help='Tulostettavan tiedoston nimi.')

args = parser.parse_args()

filename = args.output or args.o

if __name__ == "__main__":
    api = apina.Apina("https://fi.wiktionary.org/w/api.php")
    #api = apina.Apina("https://en.wikipedia.org/w/api.php")
    #api = apina.Apina("https://fi.wikisource.org/w/api.php")

    query = { 
        'action'        : 'query', 
        'list'          : 'usercontribs', 
        'ucuser'        : 'HunsBot',
        'ucnamespace'   : "0",
        #'ucdir'         : dir                  and dir, 
        'uclimit'       : 50,
        'ucstart'       : "2019-04-21T17:29:20",#"20190421170128",#2019-04-22T00:00:00",
        'ucend'         : "2019-04-21T17:01:28",#"20190421172920",#"2019-04-21T00:00:00",
        #'ucprop'       : "|",
        'uccontinue'    : None,
        #'rawcontinue' : '',
    }

    if not filename:
        print(f'Käyttö: {sys.argv[0]} --output <tiedosto>')
        exit(1)

    with open(filename, 'a') as the_file:
        for list_ in api.general_query(query, "uccontinue"):
            for line in list_:
                the_file.write(line['title'])
                the_file.write('\n')

            eka = list_[0]
            vika = list_[len(list_)-1]
            print(f"Kirjoitettiin {len(list_)} riviä ('{eka}' – '{vika}'")

            


        
