# -*- coding: utf-8 -*-

# render http://en.wikipedia.org/w/index.php?action=render&title=Sobekhotep%20I


import time
import simplemediawiki as mw
import simplejson as json
import logging
import fileinput
import functools
from sys import stderr

def print_err(*args, **kwargs):
    print(*args, file=stderr, **kwargs)

def remove_empty(dict1):
    """
    Removes elements that are None.
    """
    dict2 = {}
    for d in dict1:
        if dict1[d] != None:
            dict2[d] = dict1[d]
    return dict2


class MWApiException(Exception):
    """
    MWApin palauttamat virheet.
    """
    def __init__(self, errstr):
        self.errstr = errstr

    def __str__(self):
        return self.errstr


continue_keywords = {
    "embeddedin": "eicontinue",
    "categorymembers": "cmcontinue",
    "pageprops": "ppcontinue",
    "usercontribs": "uccontinue",
}


            
        

class QueryResult():
    def __init__(self, query, query_result_json):
        self.query = query
        self.result = query_result_json

        if 'list' in query:
            self.qtype = query['list']
        elif 'prop' in query:
            self.qtype = query['prop']

        self.qcontinue = continue_keywords.get(self.qtype)
        if not self.qcontinue:
            raise Exception("Not implemented: continue " + self.qtype)

    def has_error(self):
        return ('error' in self.result)

    def get_error(self):
        if 'error' in self.result:
            return self.result['error']['code'] + ": " + self.result['error']['info']
        else:
            return None

    def has_warnings(self):
        return ('warnings' in self.result)

    def continues(self):
        return self.get_continue_id()
        
    def get_continue_id(self):
        if 'query-continue' in self.result:
            return self.result['query-continue'][self.qtype][self.qcontinue]
        if 'continue' in self.result:
            return self.result['continue'][self.qcontinue]
        
        return None

    @property
    def data(self):
        if 'query' not in self.result:
            return None

        if self.qtype in self.result['query']:
            return self.result['query'][self.qtype]
        elif 'pages' in self.result['query']:
            return self.result['query']['pages']
        

class QueryHandler(object):
    """
    MWApin palauttama lista, jonka lataamista voi jatkaa.
    """
    def __init__(self, api, query, qcontinue = None):
        """
        @p type_    queryn tyyppi
        @p list_    apin palauttama list
        @p ticket   queryn jatkamiseen käytetty koodi
        """
        self.api = api
        self.query = query
        if 'list' in query:
            self.qtype = query['list']
        elif 'prop' in query:
            self.qtype = query['prop']
        else:
            raise Exception("Not implemented")
        self.qcontinue = qcontinue or continue_keyword[self.qtype]
        self._continues = False

    def __str__(self):
        return self.type + str(self.list)

    def __getitem__(self, i):
        return self.list[i]

    def __len__(self):
        return len(self.list)

    def continues(self):
        return self._continues

    def next(self):
        api = self.api
        qtype = self.qtype
        query = self.query
        qcontinue = self.qcontinue
        
        while True:
            qr = api.list_query(query)
            if qr.has_error():
                raise MWApiException(qr.get_error())
        
            if qr.has_warnings():
                self.api.print_warnings(qr.result)

            print("YIELDING:", json.dumps(qr.data))
            yield qr.data

            if not qr.continues():
                self._continues = False                
                break
            
            query['cmcontinue'] = qr.get_continue_id()
        self._continues = True
            
        return None

    
class MWApi(object):
    def __init__(self, apiurl = None):
        self.apiurl = apiurl
        ua = mw.build_user_agent("mediawiki-list", "0.10", "https://github.com/akupar/mwlist")
        self.wiki = mw.MediaWiki(apiurl, user_agent=ua)

    def login(self, name, passwd):
        if self.wiki.login(name, passwd):
            self.login_name = name
        return self.login_name

    def logout(self):
        return self.wiki.logout()

    def get_namespaces(self):
        r = self.wiki.namespaces()
        logging.debug("get_namespaces: query-return: %s", r)

    def list_query(self, query):
        """
        @return (QueryResult)  
        """

        qrjson = self.wiki.call(remove_empty(query))
        qr = QueryResult(query, qrjson)
        
        return qr
    


    def general_list_query(self, query, cont):
        """
        Makes a list query that generates results.

        @return (QueryHandler)  
        """

        return QueryHandler(self, query, cont)


    def general_query(self, query):
        qrjson = self.wiki.call(query)
        qr = QueryResult(query, qrjson)

        if qr.has_error(): 
            raise MWApiException(qr.get_error())

        return qr

    def _get_csrf_token(self):
        """
        Gets csrf token (needed for editing) and saves it in `self.csrftoken`.
        """
        qr = self.wiki.call({
            'format': 'json',
            'action' : 'query',
            'meta' : 'tokens'
        })
        print_err("{}".format(qr))
        
        if 'error' in qr:
            raise MWApiException(self.get_error(qr))
        else:
            if 'warnings' in qr:
                self.print_warning(qr)

            tokens = qr['query']['tokens']

            for key in tokens:
                print_err("TOKEN %s: %s" % (key, tokens[key]))

            self.csrftoken = tokens['csrftoken']

        

    def print_warnings(self, qr):
        for warning in qr['warnings']:
            print_err(warning)
            
