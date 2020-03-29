#!/usr/bin/env python
# coding: utf-8
"""
Ce script publie les articles de Wikinews sur Wikipédia
"""
from __future__ import absolute_import, unicode_literals
import json as simplejson
import re
import sys
import traceback
from xml.dom import Node
from xml.dom.minidom import parseString as minidom_parseString

import pywikibot
from pywikibot import *

# Global variables
debug_level = 0
if len(sys.argv) > 2:
    if sys.argv[2] == 'debug' or sys.argv[2] == 'd':
        debug_level= 1
file_name = __file__
if debug_level > 0: print(file_name)
if file_name.rfind('/') != -1: file_name = file_name[file_name.rfind('/')+1:]
site_language = file_name[:2]
if debug_level > 1: print(site_language)
site_family = file_name[3:]
site_family = site_family[:site_family.find('.')]
if debug_level > 1: print(site_family)
site = pywikibot.Site(site_language, site_family)
username = config.usernames[site_family][site_language]

MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December',
    'Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre']
date_rx = re.compile(r'(\d+) (%s) (\d\d\d\d)' % ('|'.join(MONTHS),), re.IGNORECASE)

def getNewsOld(page):
    pywikibot.output(page.aslink())
    site = page.site()
    '''try:
        response, data = site.postForm('/w/api.php', {'action':'parse','format':'json','page':page.title()})
    except ValueError: #too many values to unpack
        input('Erreur systématique')'''
    predata = { #ex : https://fr.wikipedia.org/w/api.php?action=parse&format=jsonfm&page=Portail:Canada/Actualit%C3%A9s/Wikinews
       'action': 'parse',
       'format': 'json',
       'page': page.title().encode('utf-8')
    }
    data = site.postForm(site.apipath(), predata) # WARNING: Http response status 405
    if debug_level > 0: input(data)
    text = simplejson.loads(data)['parse']['text']['*'] # ValueError: No JSON object could be decode
    if debug_level > 0: input(text)
    return parseNews(text)

def parseNews(text):
    #doc = minidom_parseString('<html><body>' + text.encode('utf-8') + '</body></html>')
    doc = minidom_parseString(('<html><body>' + text + '</body></html>').encode('utf-8'))
    ul = doc.getElementsByTagName('ul')
    if ul:
        for li in ul[0].getElementsByTagName('li'):
            if li.firstChild.nodeType == Node.TEXT_NODE:
                prefix = li.firstChild.nodeValue
                #if site.lang == 'en':
                #    prefix = date_rx.sub(r'[[\2 \1]]',prefix)
                #elif site.lang == 'fr':
                prefix = date_rx.sub(r'{{date|\1|\2|\3}}',prefix)
            else:
                prefix = ''
            yield prefix, Page(site, li.getElementsByTagName('a')[0].getAttribute('title'))

def getNews(page):
    text = page._get_parsed_page()  # TODO: APIError missing title when the WN page doesn't exist
    #input(parsed_text)
    return parseNews(text)

def doOnePage(tpl, page, site_src):
    pywikibot.output(page.aslink())
    txt = page.get().replace('_', ' ')
    # Recherche dans [[w:Portail:Canada/Actualités/Wikinews]] du pattern avec {{Utilisateur:Wikinews Importer Bot/config|...}}
    rx = re.search(r'{{(%s\|.*?)}}' % (tpl.title()), txt)
    if not rx:
        return

    config = {
            'page' : (None, False),
            'indent' : ('*', False),
            }
 
    raw_config = rx.group(1).split('|')[1:]
    for x in raw_config:
        if debug_level > 0: print(x)
        var, val = x.split('=',1)
        var, val = var.strip(), val.strip()
        config[var] = (val, True)
 
    if not config['page'][0]:
        pywikibot.output('No target page specified!')

    newsPage = Page(site_src, config['page'][0])    # ex: [[wikinews:fr:Page:Canada/Wikipedia]]
    if debug_level > 0:
        print(newsPage)  # ex: <DynamicPageList>...
    text = '\n'.join(
        [u'%(indent)s %(prefix)s[[wikinews:%(lang)s:%(article_page)s|%(article_title)s]]' % {
                'article_page' : re.sub(r'[\s\xa0]', ' ', news.title()),
                'article_title' : news.title(),
                'prefix' : prefix,
                'indent' : config['indent'][0],
                'lang' : site_src.lang
            }
            #for prefix, news in parseNews(newsPage)]
            for prefix, news in getNews(newsPage)
        ]
    )
    #if debug_level > 0: input(text)
    #UnicodeEncodeError: 'ascii' codec can't encode character '\xa0' in position 22: ordinal not in range(128)
    #AttributeError: 'dict' object has no attribute 'console_encoding'

    #Check for old content
    oldtext = page.get()
    #Ignore lead (timestamp etc.)
    rx = re.compile('^(.*)<noinclude>.*', re.DOTALL)
    oldtext = rx.sub(r'\1', oldtext).strip()

    if text != oldtext:
        raw_config = '|'.join('%s = %s' % (v,k[0]) for v,k in config.items() if k[1])
        text = '%(text)s<noinclude>\n{{%(tpl)s|%(config)s}}\nRetrieved by ~~~ from [[wikinews:%(lang)s:%(page)s|]] on ~~~~~\n</noinclude>' % {
                'text' : text,
                'tpl' : tpl.title(),
                'config' : raw_config,
                'page' : config['page'][0],
                'lang' : site_src.lang,
                }
        #pywikibot.output(text)
        result = 'ok'
        if debug_level > 0:
			print(text)
			result = input("Sauvegarder ? (o/n) ")
        if result != "n" and result != "no" and result != "non":
			page.put(text, comment='Updating from [[n:%s|%s]]' % (newsPage.title(),newsPage.title(),))

    WPsite = pywikibot.Site(code = lang, fam = 'wikipedia')
    return {
        'src' : newsPage.title(),
        'ns'  : WPsite.namespace(page.namespace()),
        'dst' : page.title(),
        }


def main(lang):
    pages_maintained = {}
    site_src = pywikibot.Site(code = lang, fam = 'wikinews')
    site_dest = pywikibot.Site(code = lang, fam = 'wikipedia')
    tpl = Page(site_dest, 'User:Wikinews Importer Bot/config')
    for page in tpl.getReferences(onlyTemplateInclusion=True):
        if page.title().endswith('/Wikinews') or page.title().startswith('Template:Wikinewshas/') or '/Wikinews/' in page.title():
            try:
                step = doOnePage(tpl, page, site_src)
                if step['ns'] not in pages_maintained:
                    pages_maintained[step['ns']] = []
                pages_maintained[step['ns']].append(step)
            except KeyboardInterrupt:
                break
            except:
                traceback.print_exc()
 
    audit_txt = ''
    for ns in sorted(pages_maintained.keys()):
        audit_txt += '\n\n== %s: ==\n\n' % ns
        items = sorted(pages_maintained[ns], key=lambda x: x['dst'])
        audit_txt += '\n'.join('# [[%(dst)s]] &larr; [[n:%(src)s|%(src)s]]' % item for item in items)
    audit_txt = audit_txt.strip()
 
    audit_page = Page(site_dest,'User:' + username + '/List')
    oldtext = audit_page.get()
    rx = re.compile('^.*?(?=\n== )', re.DOTALL)
    oldtext = rx.sub('', oldtext).strip()
    #pywikibot.showDiff(oldtext, audit_txt)
    if oldtext != audit_txt:
        result = 'ok'
        if debug_level > 0:
			print(audit_page)
			result = input("Sauvegarder ? (o/n) ")
        if result != "n" and result != "no" and result != "non":
			audit_page.put(
            'List of pages maintained by {{user|' + username + '}} by namespace. Last updated: ~~~~~\n\n' + audit_txt,
            comment='Updating list of maintained pages (%d items).' % sum(len(i) for i in pages_maintained.values()),
            )
 
if __name__ == '__main__':
    try:
        if len(sys.argv) == 1:
            lang = 'fr'
        else:
            lang = sys.argv[1]
        main(lang)
    finally:
        pywikibot.stopme()
