#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import apina
import argparse
from itertools import islice
import re

from pprint import pprint


parser = argparse.ArgumentParser(description='Hakee annetun luettelon sivujen sisällön')

parser.add_argument('-i', '--input-list', type=str,
                    help='Tiedosto, jossa on lueteltu haettavat sivut')

parser.add_argument('-o', '--output', type=str,
                    help='Tiedosto, johon tulokset tallennetaan')

parser.add_argument('-a', '--api-url', type=str,
                    help='APIn URL')

args = parser.parse_args()

infilename = args.input_list
outfilename = args.output
apiurl = args.api_url or "https://fi.wiktionary.org/w/api.php"

def get_n_lines(the_file, n):
    lines = []
    for line in the_file.readlines():
        line = line.strip()
        lines.append(line)
        if len(lines) == n:
            yield lines
            lines = []
    yield lines

def write_line(outfile, line):
    outfile.write(line)
    outfile.write('\n')

def handle_lines(query, outfile):
    result = api.simple_query(query)
    print(result)
    if not "query" in result or not "pages" in result["query"]:
        return

    pages = result["query"]["pages"]
    for page_id, page in pages.items():
        print("TITLE:", page["title"])

        if not "revisions" in page:
            continue
        
        content = page["revisions"][0]["slots"]["main"]["*"]

        m = re.search("\{\{R:TLFi\}\}", content)
        if m:
            write_line(outfile, page["title"])
            
        m = re.search("\{\{R:TLFi\|([^}]*)\}\}", content)
        # jos ekaa parametria ei ole
        if m and (m.group(1).startswith("alt=") or m.group(1).startswith("etym=") or m.group(1).startswith("nodot=")):
            write_line(outfile, page["title"])
            
        

if __name__ == "__main__":
    api = apina.Apina(apiurl)

    query = { 
        'action'        : 'query', 
        'prop'          : 'revisions', 
        'titles'        : [],
        'rvprop'        : 'content',
        'rvslots'       : 'main',
        'rvcontinue'    : None,
    }

    if not outfilename or not infilename:
        print(f'Käyttö: {sys.argv[0]} --output <tiedosto> --input <tiedosto>')
        exit(1)


        
    with open(infilename, 'r') as infile:
        with open(outfilename, 'a') as outfile:

            for lines in get_n_lines(infile, 50):
                print(lines[0], "—", lines[1])            
                query["titles"] = "|".join(lines)

                handle_lines(query, outfile)

                #x = input("Paina nappia")
                time.sleep(5)

        
    # for list_ in api.general_query(query, "rvcontinue"):
    #     for line in list_:
    #         the_file.write(line['title'])
    #         the_file.write('\n')
            
    #         eka = list_[0]
    #         vika = list_[len(list_)-1]
    #         print(f"Kirjoitettiin {len(list_)} riviä ('{eka}' – '{vika}'")

            


        
