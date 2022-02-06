#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import apina
import argparse
import json

from pprint import pprint


parser = argparse.ArgumentParser(description='Optional app description')

parser.add_argument('-o', '--output', type=str,
                    help='Tulostettavan tiedoston nimi.')

parser.add_argument('-u', '--user', type=str,
                    help='Haettava käyttäjä')

parser.add_argument('-a', '--api-url', type=str,
                    help='APIn URL')

args = parser.parse_args()

filename = args.output
user = args.user
apiurl = args.api_url or "https://fi.wiktionary.org/w/api.php"

print("API:", apiurl)
if __name__ == "__main__":
    api = apina.Apina(apiurl)

    query = { 
        'action'        : 'query', 
        'list'          : 'usercontribs', 
        'ucuser'        : user,
        'ucprop'        : 'title|comment',
        'uclimit'       : 500,
        'uccontinue'    : None,
    }

    if not filename:
        print(f'Käyttö: {sys.argv[0]} --output <tiedosto> --user <käyttäjä> --api-url <apin url>')
        exit(1)

    with open(filename, 'a') as the_file:
        for list_ in api.general_query(query, "uccontinue"):
            for line in list_:
                the_file.write(line['title'])
                the_file.write(';')
                #the_file.write(line['timestamp'])
                #the_file.write(';')
                the_file.write(line['comment'])
                the_file.write('\n')

            eka = list_[0]
            vika = list_[len(list_)-1]
            print(f"Kirjoitettiin {len(list_)} riviä ('{eka}' – '{vika}'")

            


        
