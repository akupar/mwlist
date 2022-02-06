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
    "categorymembers" : "cmcontinue",
}

class QueryHandler(object):
    """
    MWApin palauttama lista, jonka lataamista voi jatkaa.
    """
    def __init__(self, type_, list_, ticket=None):
        """
        @p type_    queryn tyyppi
        @p list_    apin palauttama list
        @p ticket   queryn jatkamiseen käytetty koodi
        """
        self.type = type_
        self.list = list_
        self.ticket = ticket

    def __str__(self):
        return self.type + str(self.list)

    def __getitem__(self, i):
        return self.list[i]

    def __len__(self):
        return len(self.list)

    def next(self):
        return self.list.next()

    def __iter__(self):
        return self.list.__iter__()

    def continues(self):
        return self.ticket != None

    def merge(self, another):
        if another.type == self.type:
            self.list = self.list + another.list
            self.ticket = another.ticket
        else:
            raise Exception("QueryHandler:merge: listat eri tyyppiä")


        
class MWApi(object):
    def __init__(self, apiurl = None):
        self.apiurl = apiurl
        ua = mw.build_user_agent("mediawiki-list", "0.10", "github.com/akupar/mediawiki-list")
        self.wiki = mw.MediaWiki(apiurl, user_agent=ua)

    def has_error(self, result):
        return ('error' in result)
    
    def get_error(self, result):
        if 'error' in result:
            return result['error']['code'] + ": " + result['error']['info']
        else:
            return None

    def login(self, name, passwd):
        if self.wiki.login(name, passwd):
            self.login_name = name
        return self.login_name

    def logout(self):
        return self.wiki.logout()

    def get_namespaces(self):
        r = self.wiki.namespaces()
        logging.debug("get_namespaces: query-return: %s", r)

    def list_query(self, query, qtype, qcontinue):
        """
        @p query           varsinainen pyyntö
        @p qtype           esim. "embeddedin", "categorymembers"
        @p qcontinue       esim. "eicontinue", "cmcontinue"
        @return (QueryHandler)  sisältää apin vastauksen alkaen `qtypen` jälkeläisistä
        """

        if not qcontinue:
            qcontinue = continue_keywords[qtype]

        if not qcontinue:
            raise Exception("Missing parameter qcontinue")

        qr = self.wiki.call(remove_empty(query))
        
        if has_errors(qr):
            raise MWApiException(get_error(qr))
        
        if has_warnings(qr):
            self.print_warnings(qr)

        cont = None
        if 'query-continue' in qr:
            cont = qr['query-continue'][qtype][qcontinue]

        if 'continue' in qr:
            cont = qr['continue'][qcontinue]

        if 'query' in qr and qtype in qr['query']:
            page_list = qr['query'][qtype]
        else:
            page_list = None


        return QueryHandler(qtype, page_list, cont)
    


    def general_list_query(self, query, cont):
        """

        """

        return self.list_query(query, query['list'], cont)


    def general_query2(self, query, captcha_cb):

        if 'token' not in query or query['token'] == None:
            query['token'] = self.csrftoken

        qr = self.wiki.call(query)
        logging.debug("edit_page: edit: query-return: %s", qr)

        print(qr)

        if 'error' in qr: 
            raise MWApiException(self.get_error(qr))

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

        

