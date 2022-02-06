#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import mwapi
import argparse
import json
import re

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

def get(user, startdate, enddate, output, api, props):
    if not props or props == []:
        props = ["title", "timestamp", "comment"]
        
    query = { 
        'action'        : 'query', 
        'list'          : 'usercontribs', 
        'ucuser'        : user,
        'ucprop'        : "|".join(props),
        'uclimit'       : 500,
        'ucstart'       : startdate,
        'ucend'         : enddate,
        'uccontinue'    : None,
    }

    query_handler = api.general_list_query(query, 'uccontinue')
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
        for prop in props:
            output.write(line[prop])
            if prop != props[-1]:
                output.write(';')
                
        output.write('\n');

    print_err(f"Wrote {len(page_list)}")
        


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Optional app description')

    parser.add_argument('-o', '--output', type=str,
                        help='Output file, or - for stdout')
    
    parser.add_argument('-u', '--user', type=str,
                        help='User name (without User:)')
    
    parser.add_argument('-e', '--endpoint', type=str,
                        help='Endpoint URL')

    parser.add_argument('-f', '--from', type=str, dest="from_",
                        help='Start time in ISO-8601 format (YYYY-MM-DDTHH:mm:ss)')
    
    parser.add_argument('-t', '--to', type=str,
                        help='End time in ISO-8601 format')

    parser.add_argument('-p', '--props', type=str,
                        help='Props to return (title, timestamp, comment)')
    
    try:
        args = parser.parse_args()
    except:
        exit(1)
    
    filename = args.output
    user = args.user
    endpoint = args.endpoint
    startdate = args.from_
    enddate = args.to
    props = args.props

    if props:
        props = re.split(r"[^a-z]", props)

    endpoint_fixed = fix_endpoint(endpoint)
    if endpoint_fixed != endpoint:
        endpoint = endpoint_fixed
        print_err(f"Endpoint: {endpoint}")
    
    api = mwapi.MWApi(endpoint)

    if filename or filename == '-':
        output = sys.stdout
    else:
        output = open(filename, 'a')


    get(user, startdate, enddate, output, api, props)

        
