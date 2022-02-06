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

def poista_falset(dict1):
    """
    Poistaa dict-oliosta avaimet, joiden arvo on False tai None.
    """
    dict2 = {}
    for d in dict1:
        if dict1[d] != None and dict1[d] != False: dict2[d] = dict1[d]
    return dict2


class ApiException(Exception):
    """
    Apin palauttamat virheet.
    """
    def __init__(self, errstr):
        self.errstr = errstr

    def __str__(self):
        return self.errstr


class ApiList(object):
    """
    Apin palauttama lista, jonka lataamista voi jatkaa.
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
            raise Exception("ApiList:merge: listat eri tyyppiä")


        
class MWApi(object):
    def __init__(self, apiurl = None):
        self.apiurl = apiurl
        ua = mw.build_user_agent("mediawiki-list", "0.10", "github.com/akupar/mediawiki-list")
        self.wiki = mw.MediaWiki(apiurl, user_agent=ua)

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
        logging.debug(u"get_namespaces: query-return: %s", r)

    def get_n_for_query(self, query, x, whattxt, limittxt, continuetxt):
        """
        Jos x = 0, palauttaa kaikki
              > 0, palattaa (korkeintaan) x tulosta;
              < 0, käyttää oletusta (joka on 10??)
        """
        # Huom. jos x > maksimimäärä, palauttaa vain osan
        if x > 0: query[limittxt] = x
        elif x == 0: query[limittxt] = 50  # suurin sallittu, boteille 500
        elif limittxt in query: del query[limittxt]

        logging.debug(u"Query: %s", query)
        l = []
        r = self.wiki.call(query)
        logging.debug(u"Return: %s", r)
        try:
            count = 0
            l = r['query'][whattxt]
            # jatkotiedot, jotka annetaan uudelle querylle
            while (x == 0 or len(l) < x) and 'query-continue' in r:
                count = count + 1
                next = r['query-continue'][whattxt][continuetxt]
                query[continuetxt] = next
                r = self.wiki.call(query)
                l = l + r['query'][whattxt]
                if 'query-continue' in r: time.sleep(0.5)
            logging.debug(u"Yhteensä %d hakua.", count)
        except KeyError as e:
            if not self.print_error(r):
                print(f"Tuntematon vika, r: {r}")
        return l


    def get_backlinks_for_title(self, title, n = 0, namespace = None):
        """
        Palauttaa sivut, jotka linkittävät sivuun title. 

        Huom. ei palauta mallineiden sisällyttämistä, mutta niiden linkittämisen kyllä.
        """
        # bltitle, blpagbld, blnamespace, bldir, blfilterredir
        query = { 'action' : 'query', 'list' : 'backlinks', 'bltitle' : title }
        if namespace: query['blnamespace'] = namespace.to_num()

        return self.get_n_for_query(query, n, 'backlinks', 'bllimit', 'blcontinue')


    def get_embeddedin_for_title(self, title, n = 0, namespace = None):
        """
        Palauttaa sivut, joille title on sisällytetty.

        Title voi olla malline tai muu sivu.
        """
        # eititle, eipageid, einamespace, eidir, eifilterredir
        query = { 'action' : 'query', 'list' : 'embeddedin', 'eititle' : title }
        if namespace: query['einamespace'] = namespace.to_num()
        
        return self.get_n_for_query(query, n, 'embeddedin', 'eilimit', 'eicontinue')

    def get_members_of_category(self, title, n = 0, namespace = None):

        """
        Palauttaa sivut, jotka kuuluvat annettuun luokkaan.
        """
        query = { 'action' : 'query', 'list' : 'categorymembers', 'cmtitle' : title }
        if namespace: query['cmnamespace'] = namespace.to_num()

        return self.get_n_for_query(query, n, 'categorymembers', 'cmlimit', 'cmcontinue')

    def get_contribs_of_user(self, user, n = 0, namespace = None):
        """
        Palauttaa annetun käyttäjän muokkaukset.
        """
        # eititle, eipageid, einamespace, eidir, eifilterredir
        query = { 'action' : 'query', 'list' : 'usercontribs', 'ucuser' : user }
        if namespace: query['ucnamespace'] = namespace.to_num()
        
        return self.get_n_for_query(query, n, 'usercontribs', 'uclimit', 'uccontinue')


    def get_info(self, title):
        i = self.wiki.call({ 'action' : 'query', 'prop' : 'info', 'titles' : title })
        if 'query' not in r: 
            if not self.print_error(r):
                print(u"Virhe: paluuarvo: " + str(r))
            return None
        return i['query']['pages'].values()[0]




    def query_revision(self, revids, namespaces=[], diffto=None, props=[]):
        """
        Palauttaa tietyn revision

        @p user     voi olla sivun title tai pageid
        """
        query = { 
            'action'        : 'query', 
            'prop'          : 'revisions', 
            'revids'        : "|".join(map(lambda r: str(r), revids)), 
            'rvprop'        : (props != [])        and "|".join(props), 
            'rvdiffto'      : diffto,
            }

        qr = self.wiki.call(query)
        return qr['query']['pages']


    def get_wikitext(self, titles=[], revids=[]):
        """Palauttaa sivuille `titles` tai `revids` niiden nykyisen revision wikitekstin.

        https://www.mediawiki.org/wiki/API:Revisions
        
        @p titles  [str]  lista sivuotsikoita
        @return    [str]  lista sivujen nykyisiä wikitekstejä
        """

        # Palauttaa esim:
        # {
        #     "batchcomplete": "",
        #     "query": {
        #         "pages": {
        #             "55332": {
        #                 "pageid": 55332,
        #                 "ns": 0,
        #                 "title": "API",
        #                 "revisions": [
        #                     {
        #                         "revid": 2539883,
        #                         "parentid": 2539881,
        #                         "user": "Mainframe98",
        #                         "timestamp": "2017-08-19T18:23:42Z",
        #                         "slots": {
        #                             "main": {
        #                                 "contentmodel": "wikitext",
        #                                 "contentformat": "text/x-wiki",
        #                                 "*": "#REDIRECT [[API:Main page]]<!-- Don't delete, linked from old MediaWiki releases.-->"
        #                             }
        #                         }
        #                     }
        #                 ]
        #             },
        #             "1423": {
        #                 "pageid": 1423,
        #                 "ns": 0,
        #                 "title": "Main Page",
        #                 "revisions": [
        #                     {
        #                         "revid": 5875,
        #                         "parentid": 5860,
        #                         "user": "Bdk",
        #                         "timestamp": "2005-09-16T01:14:43Z",
        #                         "slots": {
        #                             "main": {
        #                                 "contentmodel": "wikitext",
        #                                 "contentformat": "text/x-wiki",
        #                                 "*": "#redirect [[MediaWiki]]"
        #                             }
        #                         }
        #                     }
        #                 ]
        #             }
        #         }
        #     }
        # }

        if revids != []:
            qr = self.wiki.call({
                'action' : 'query',
                'prop' : 'revisions',
                'rvprop' : 'content|timestamp|ids|user',
                'revids' : "|".join(map(lambda r: str(r), revids)) })
            
        elif titles != []:
            qr = self.wiki.call({
                'action' : 'query',
                'prop' : 'revisions',
                'rvprop' : 'content|timestamp|ids|user',
                'titles' : "|".join(titles) })
        else:
            raise Exception("Parameter `revids` or `titles` required")
            
#        logging.debug(u"get_wikitext: query-return: %s", qr)
        if not qr:
            raise Exception("What?")
        elif 'error' in qr: 
            raise ApiException(self.get_error(qr))
        elif 'warnings' in qr:
            self.print_warning(qr)
        elif 'query' not in qr:
            print("OUTO TULOS:\n" + str(qr) + "\n")

            
        return qr['query']['pages']


    def get_preview(self, wikitext, title = None):
        qr = self.wiki.call({ 'action' : 'parse', 'text' : wikitext, 'title' : title })
        logging.debug(u"get_preview: query-return: \n%s\n", qr)
        if 'error' in qr:
            raise ApiException(self.get_error(qr))
        if 'parse' not in qr:
            print(u"Virhe: paluuarvo: " + str(qr))
            return None
        return qr['parse']['text']['*']

    def get_rendered_page(self, title):
        qr = self.wiki.call({ 'action' : 'parse', 'page' : title })
        logging.debug(u"get_rendered_page: query-return: \n%s\n", qr)
        if 'error' in qr:
            raise ApiException(self.get_error(qr))
        if 'parse' not in qr:
            print(u"Virhe: paluuarvo: " + str(qr))
            return None
        return qr['parse']['text']['*']

    def get_rendered_text(self, title, text):
        qr = self.wiki.call({ 'action' : 'parse', 'title' : title, 'text' : text, 'contentmodel' : 'wikitext' })
        logging.debug(u"get_rendered_text: query-return: \n%s\n", qr)
        if 'error' in qr:
            raise ApiException(self.get_error(qr))
        if 'parse' not in qr:
            print(u"Virhe: paluuarvo: " + str(qr))
            return None
        return qr['parse']['text']['*']


    def _get_delete_token(self, title):
        return self._get_edit_token(title)

    def _get_move_token(self, title):
        """
        Hakee movetokenin, jota tarvitaan siirtojen tekemiseen. Tallentaa sen `self.edittokeniin`.

        Huom. titleillä ei ole väliä tässä, sillä edittoken säilyy samana koko istunnon ajan.
        
        @p title [str]  artikkeliotsikko
        """
        qr = self.wiki.call({ 'action' : 'query', 'prop' : 'info', 'intoken' : 'move', 'titles' : title })
        logging.debug(u"get_move_Token: get token: query-return: %s", qr)
        if 'error' in qr:
            raise ApiException(self.get_error(qr))
        else:
            if 'warnings' in qr:
                self.print_warning(qr)
                                
            pageid = list(lqr['query']['pages'])[0]
            page = qr['query']['pages'][pageid]

            self.movetoken = page['movetoken']


    def _get_edit_token(self, title):
        """
        Hakee edittokenin, jota tarvitaan editointien ja undojen tekemiseen. Tallentaa sen `self.edittokeniin`.

        Huom. titleillä ei ole väliä tässä, sillä edittoken säilyy samana koko istunnon ajan.
        
        @p title [str]  artikkeliotsikko
        """
        qr = self.wiki.call({ 'action' : 'query', 'prop' : 'info', 'intoken' : 'edit', 'titles' : title })
        logging.debug(u"get_edit_token: get token: query-return: %s", qr)
        if 'error' in qr:
            raise ApiException(self.get_error(qr))
        else:
            if 'warnings' in qr:
                self.print_warning(qr)

            pageid = list(qr['query']['pages'])[0]
            page = qr['query']['pages'][pageid]

            self.edittoken = page['edittoken']


    
    
    def _hoida_captcha(self, qr, cb):
        """
        Palauttaa `qr`:n arvon, jos captchaa ei ole. Jos on, kutsuu `cb`:tä kunnes se
        palauttaa oikean avaimen tai None.

        @p qr   edellisen editointipyynnön palauttama vastaus, joka voi sisältää captchan tai ei
        @p cb   funktio muotoa bool (id, url), jossa url on captchakuvan osoite
        @return (bool, dict)  TODO  sisältääkö dict aina edit-osan??
        """

        # loopataan kunnes käyttäjä antaa oikean captchan tai peruuttaa.
        while True:
            if 'edit' in qr:
                page = qr['edit']
            elif 'delete' in qr:
                page = qr['delete']
            elif 'move' in qr:
                page = qr['move']
            else:
                page = {}
                
            if 'result' in page and page['result'] == 'Success':
                return (True, page)
            if 'captcha' in page:
                cid = page['captcha']['id']
                curl = self.host + page['captcha']['url']
                print("Captcha: id: {0}, url: {1}".format(cid, curl))
                avain = cb(cid, curl)
                if avain == None:
                    return (False, None)
                else:
                    q['captchaid'] = cid
                    q['captchaword'] = avain.strip()
                    qr = self.wiki.call(q)
                    logging.debug(u"_hoida_captcha:  query-return: %s", qr)
                    
                    if 'error' in qr: 
                        raise ApiException(self.get_error(qr))
            else:
                return (True, page)


    def edit_page(self, title, text, timestamp, comm, captcha_cb, minor=False):

        # Get token if we don't already have one.
        if self.edittoken == None:
            #self._get_edit_token(title)
            self._get_csrf_token()

        if self.edittoken:
            q = { 
                'action' : 'edit', 
                'title' : title, 
                'basetimestamp' : timestamp, 
                'text' : text, 
                'summary' : comm, 
                'bot' : True, 
                'token' : self.edittoken 
            }
            if minor: q['minor'] = True
            qr = self.wiki.call(q)
            logging.debug(u"edit_page: edit: query-return: %s", qr)

            if 'error' in qr: 
                raise ApiException(self.get_error(qr))
            else:
                return self._hoida_captcha(qr, captcha_cb)
        else:
            print("VIRHE: ei tokenia")
        return (False, None)


    def undo_edit(self, title, revid, timestamp, comm, captcha_cb, minor=False):
        """
        Peruuttaa muutoksen `revid`.
        """

        # Get token if we don't already have one.
        if self.edittoken == None:
            #self._get_edit_token(title)
            self._get_csrf_token()

        if self.edittoken:
            q = { 
                'action' : 'edit', 
                'title' : title, 
                'basetimestamp' : timestamp, 
                'summary' : comm, 
                'undo' : revid,
                'bot' : True, 
                'token' : self.edittoken 
            }
            if minor: q['minor'] = True
            qr = self.wiki.call(q)
            logging.debug(u"undolast:     : query-return: %s", qr)

            if 'error' in qr: 
                raise ApiException(self.get_error(qr))
            else:
                return self._hoida_captcha(qr, title)
        else:
            print("VIRHE: ei tokenia")
        return False


        # Vastaus esim.
        # {
        #   'batchcomplete': u'',
        #   'query': {
        #      'pages': {
        #         '356965': {
        #             'lastrevid': 2167048,
        #             'pagelanguagedir': 'ltr',
        #             'pageid': 356965,
        #             'title': 'Eukalyptus',
        #             'starttimestamp': '2016-08-10T03:00:37Z',
        #             'pagelanguagehtmlcode': 'fi',
        #             'length': 283,
        #             'contentmodel': 'wikitext',
        #             'pagelanguage': 'fi',
        #             'touched': '2016-06-30T20:20:46Z',
        #             'edittoken': '641cb5fea831a5f784424cc1dc904f6357aa98d5+\\',
        #             'ns': 0 } } },
        #   'warnings': {
        #         'info': {
        #           '*': 'The intoken parameter has been deprecated.' } } }

    

    def move_page(self, from_, to_title, reason, captcha_cb):
        """
        Siitää sivun `from` nimelle `to_title`.

        https://www.mediawiki.org/wiki/API:Move
        @p from (str/int) sivun, joka uudelleen nimetään, title tai id 
        @p to_title (str) uusi otsikko
        @p reason (str)   syy
        @p captcha_cb         captchaa kysyvä funktio
        """

        # Get token if we don't already have one.
        if self.edittoken == None:
            #self._get_edit_token(title)
            self._get_csrf_token()
        
        if self.edittoken:
            q = {
                'action' : 'move', 
                'reason' : reason,
                'from' : None,
                'to' : to_title,
                'movetalk' : True,
                'movesubpages' : True,
                'noredirect' : True,
                'bot' : True,   # toimiiko??
                'token' : self.edittoken 
            }
            if self.is_id(from_): q['fromid'] = from_
            else: q['from'] = from_

            logging.debug(u"move_page: query: \n%s\n", q)
            qr = self.wiki.call(q)
            logging.debug(u"move_page: query-return: \n%s\n", qr)

            if 'error' in qr: 
                raise ApiException(self.get_error(qr))
            else:
                return self._hoida_captcha(qr, from_)
        else:
            print("VIRHE: ei tokenia")
            
        return (False, None)




    def delete_page(self, title_id, reason, captcha_cb):
        """
        Siitää sivun `from` nimelle `to_title`.

        https://www.mediawiki.org/wiki/API:Delete
        @p title_id (str/int) poistettavan sivun title tai id 
        @p reason (str)       syy
        @p captcha_cb (function)  captchaa kysyvä funktio
        """

        print(u"Deleting {0} ({1})".format(title_id, reason))

        # Get token if we don't already have one.
        if self.edittoken == None:
            self._get_delete_token(title_id)   # onko sama kuin edittoken???

        if self.edittoken:
            q = { 
                'action' : 'delete', 
                'reason' : reason, 
                'bot' : True,   # toimiiko??
                'token' : self.edittoken 
            }
            if self.is_id(title_id): q['page_id'] = title_id
            else: q['title'] = title_id

            logging.debug(u"delete_page: query: \n%s\n", q)
            qr = self.wiki.call(q)
            logging.debug(u"delete_page: query-return: \n%s\n", qr)

            if 'error' in qr: 
                raise ApiException(self.get_error(qr))
            else:
                return self._hoida_captcha(qr, title_id)
        else:
            print("VIRHE: ei tokenia")
        return False



    def _get_rollback_token(self, titles):
        """
        Hakee rollbacktokenin, jota tarvitaan rollbackin tekemiseen.
        
        @p titles [str]  artikkeliotsikkoluettelo
        @return (token, timestamp) 
        """
        qr = self.wiki.call({ 'action' : 'query', 'prop' : 'revisions', 'rvtoken' : 'rollback', 'titles' : titles })
        if 'error' in qr:
            raise ApiException(self.get_error(qr))
        else:
            if 'warnings' in qr:
                self.print_warning(qr)

            token = None
            pageid = list(qr['query']['pages'])[0]
            page = qr['query']['pages'][pageid]
            rev = page['revisions'][0]
            if 'rollbacktoken' in rev:
                token = rev['rollbacktoken']

            timestamp = rev['timestamp']
            
            return token, timestamp


    def rollback_in_terror(self, titles):
        """
        Rolls back own edits on pages `titles`. TODO ei oikeuksia

        https://www.mediawiki.org/wiki/API:Rollback
        """
        #api.php?action=query&prop=revisions&rvtoken=rollback&titles=Main%20Page

        # Get rollback token.
        token, timestamp = self._get_rollback_token(titles)
        if token:
            q = { 
                'action' : 'rollback', 
                'title' : titles, 
                'user' : 'HunsBot',
                #                'summary' : "Peruutustesti",  # oletusviesti ehkä parempi
                'markbot' : True, 
                'token' : token 
            }

            qr = self.wiki.call(q)
            logging.debug(u"edit_page: rollback: query-return: \n%s\n", qr)


    def list_query(self, query, qtype, qcontinue):
        """
        @p query           varsinainen pyyntö
        @p qtype           esim. "embeddedin", "categorymembers"
        @p qcontinue       esim. "eicontinue", "cmcontinue"
        @return (ApiList)  sisältää apin vastauksen alkaen `qtypen` jälkeläisistä
        """

        logging.debug(qtype + ": query: \n%s\n", query)

        qr = self.wiki.call(poista_falset(query))
        logging.debug(qtype + ": query-return: \n%s\n", qr)
        
        if 'error' in qr: raise ApiException(self.get_error(qr))
        if 'warnings' in qr: self.print_warning(qr)

        cont = None
        # Vanhentunut?? -->
        if 'query-continue' in qr:
            cont = qr['query-continue'][qtype][qcontinue]
            # <--

        if 'continue' in qr:
            cont = qr['continue'][qcontinue]

        if 'query' in qr and qtype in qr['query']:
            list_ = qr['query'][qtype]
        else:
            list_ = None

        return ApiList(qtype, list_, cont)



    def category_members(self, category, namespaces=[], types=['page'], limit=None, props=['ids', 'title'], 
                         dir="asc", continu=None):
        """
        Palauttaa luokan sivut osina.

        https://www.mediawiki.org/wiki/API:Categorymembers
        """

        q = { 
            'action'      : 'query', 
            'list'        : 'categorymembers', 
            'cmtitle'     : (str(category) == category) and category, 
            'cmpageid'    : (str(category) != category) and category, 
            'cmnamespace' : (namespaces != [])           and "|".join(map(str, namespaces)), 
            'cmtype'      : (types != [])               and "|".join(types), 
            'cmprop'      : (props != [])               and "|".join(props), 
            'cmlimit'     : limit, 
            'cmcontinue'  : continu                    and continu, 
            'cmdir'       : dir                         and dir,
            'rawcontinue' : '',
        }

        return self.list_query(q, "categorymembers", "cmcontinue")


    def embedded_in(self, title, namespaces=[], filterredir=['all'], limit=10, continu=None):
        """
        Palauttaa sivut, joihin toinen sivu (malline tai muu) on sisällytettynä.

        https://www.mediawiki.org/wiki/API:Embeddedin
        """

        q = { 
            'action'        : 'query', 
            'list'          : 'embeddedin', 
            'eititle'       : title, 
            'einamespace'   : (namespaces != [])    and "|".join(map(str, namespaces)), 
            'eifilterredir' : (filterredir != [])  and "|".join(filterredir), 
            'eilimit'       : limit                and limit, 
            'eicontinue'    : continu              and continu,
            'rawcontinue' : '',
        }

        return self.list_query(q, "embeddedin", "eicontinue")

    # ei toimi -> eubadquery
    def ext_url_usage(self, url, protocol=None, namespaces=[], props=[], limit=None, continu=None):
        """
        Palauttaa ulosjohtavan linkin käytön. Protokolla tulee `protocol`-parametriin. Esim. "http"
        Muu osoite palvelimesta alkaen `url`-parametriin, esim. "runeberg.org". Palauttaa kaikki
        merkkijonolla alkavat osoitteet, esim. "runeberg.org" palauttaa sivut, joilla on linkit
        <http://runeberg.org/pieni/3/0057.html>, <//runeberg.org/pieni/4/>, jne. Apisivulla mainittua
        asteriksia ei voi käyttää.

        https://www.mediawiki.org/wiki/API:Exturlusage
        """

        q = { 
            'action'        : 'query', 
            'list'          : 'exturlusage', 
            'euquery'       : url, 
            'euprotocol'    : protocol, 
            'eunamespace'   : (namespaces != [])   and "|".join(map(str, map(str, namespaces))), 
            'euprop'        : (props != [])        and "|".join(props), 
            'eulimit'       : limit                and limit, 
            'euoffset'      : continu              and continu,
            'rawcontinue' : '',
        }


        return self.list_query(q, "exturlusage", "euoffset")

    @staticmethod
    def backlinks(page, namespaces=[], dir=None, filterredir=None, limit=None, continu=None):
        """
        Palauttaa sivut, jotka linkittävät annetulle sivulle.

        @p page     voi olla sivun title tai pageid

        https://www.mediawiki.org/wiki/API:Backlinks
        """
        query = { 
            'action'        : 'query', 
            'list'          : 'backlinks', 
            'bltitle'       : (str(page) == page)  and page, 
            'blpageid'      : (str(page) != page)  and page, 
            'blfilterredir' : filterredir          and filterredir, 
            'blnamespace'   : (namespaces != [])   and "|".join(map(str, map(str, namespaces))), 
            'bldir'         : dir                  and dir, 
            'bllimit'       : limit                and limit, 
            'blcontinue'    : continu              and continu,
            'rawcontinue' : '',
        }

        return self.list_query(q, "backlinks", "blcontinue")


    def user_contribs(self, user, namespaces=[], dir=None, limit=None, start=None, end=None, props=[], continu=None):
        """
        Palauttaa sivut, jotka linkittävät annetulle sivulle.

        @p user     voi olla sivun title tai pageid

        https://www.mediawiki.org/wiki/API:Backlinks
        """
        query = { 
            'action'        : 'query', 
            'list'          : 'usercontribs', 
            'ucuser'        : (str(user) == user)  and user, 
            'ucnamespace'   : (namespaces != [])   and "|".join(map(str, map(str, namespaces))), 
            'ucdir'         : dir                  and dir, 
            'uclimit'       : limit                and limit, 
            'ucstart'       : start                and start, 
            'ucend'         : end                  and end, 
            'ucprop'        : (props != [])        and "|".join(props), 
            'uccontinue'    : continu              and continu,
            'rawcontinue' : '',
        }

        return self.list_query(query, "usercontribs", "uccontinue")


    # UUDET YLEISET
    def list_query2(self, query, qtype, qcontinue):
        """
        @p query           varsinainen pyyntö
        @p qtype           esim. "embeddedin", "categorymembers"
        @p qcontinue       esim. "eicontinue", "cmcontinue"
        @return (ApiList)  sisältää apin vastauksen alkaen `qtypen` jälkeläisistä
        """

        #logging.debug(qtype + ": query: \n%s\n", query)

        qr = self.wiki.call(poista_falset(query))
        #logging.debug(qtype + ": query-return: \n%s\n", qr)
        
        if 'error' in qr: raise ApiException(self.get_error(qr))
        if 'warnings' in qr: self.print_warning(qr)

        cont = None
        if 'query-continue' in qr:
            cont = qr['query-continue'][qtype][qcontinue]

        if 'continue' in qr:
            cont = qr['continue'][qcontinue]

        if 'query' in qr and qtype in qr['query']:
            list_ = qr['query'][qtype]
        else:
            list_ = None


        print("QR:", qr)
        return ApiList(qtype, list_, cont)
    


    def general_query(self, query, cont):
        """

        """

        return self.list_query2(query, query['list'], cont)


    def general_query2(self, query, captcha_cb):

        if 'token' not in query or query['token'] == None:
            query['token'] = self.edittoken

        qr = self.wiki.call(query)
        logging.debug(u"edit_page: edit: query-return: %s", qr)

        print(qr)

        if 'error' in qr: 
            raise ApiException(self.get_error(qr))
        else:
            return self._hoida_captcha(qr, captcha_cb)

    def _get_csrf_token(self):
        """
        Hakee edittokenin, jota tarvitaan editointien ja undojen tekemiseen. Tallentaa sen `self.edittokeniin`.

        Huom. titleillä ei ole väliä tässä, sillä edittoken säilyy samana koko istunnon ajan.
        
        @p title [unicode]  artikkeliotsikko
        """
        qr = self.wiki.call({
            'format': 'json',
            'action' : 'query',
            'meta' : 'tokens'
        })
        print_err("{}".format(qr))
        
        if 'error' in qr:
            raise ApiException(self.get_error(qr))
        else:
            if 'warnings' in qr:
                self.print_warning(qr)

            tokens = qr['query']['tokens']

            for key in tokens:
                print_err("TOKEN %s: %s" % (key, tokens[key]))

            self.edittoken = tokens['csrftoken']

        

    def get_cache(self, fn):
        f = open(fn, "r")
        l = f.read()
        f.close()
        return json.loads(l)


    def save_cache(self, data, fn):
        f = open(fn, "w")
        f.write(json.dumps(data))
        f.close()

