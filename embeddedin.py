#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import mwapi
import argparse
from pprint import pprint


parser = argparse.ArgumentParser(description='Optional app description')

parser.add_argument('-o', '--output', type=str,
                    help='Tulostettavan tiedoston nimi.')

parser.add_argument('-t', '--template', type=str,
                    help='Haettava malline')

parser.add_argument('-a', '--api-url', type=str,
                    help='APIn URL')

args = parser.parse_args()

filename = args.output
template = args.template
apiurl = args.api_url or "https://fi.wiktionary.org/w/api.php"

if not template.startswith("Template:"):
    template = "Template:" + template
    

if not filename:
    print("Tiedosto puuttuu")
    exit(1)

if not template:
    print(f"Puuttuu parametri template")
    exit(1)


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
    #'rawcontinue' : '',
}

    

def get(template_name, the_file, api):
    query['eititle'] = template_name
    print("haetaan:", query['eititle'])


    
    has_more = True
    
    query_ = api.general_query(query, "eicontinue")

    lst = query_.list

    print("list 1: ", query_.list)
    
    while query_.continues():
        query['eicontinue'] = query_.ticket
        query_ = api.general_query(query, "eicontinue")
        print("list n: ", query_.list)
        lst = lst + query_.list
        
    for line in lst:
        the_file.write(line['title'])
        the_file.write(';')
        the_file.write(template_name)                
        the_file.write('\n')

    print(f"Kirjoitetttiin: {len(lst)}")
    
if __name__ == "__main__":
    api = mwapi.MWApi(apiurl)


    if not filename:
        print(f'Käyttö: {sys.argv[0]} --output <tiedosto>')
        exit(1)

    with open(filename, 'a') as the_file:

        get(template, the_file, api)


        
