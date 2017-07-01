#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, unicode_literals
import os, re, sys, traceback
import json as simplejson
#sys.path.append(os.environ['HOME'] + '/pywikipedia')
from xml.dom.minidom import parseString as minidom_parseString
from xml.dom import Node
import pywikibot
from pywikibot import *
mynick = "JackBot"
debug = True
 
MONTHS = [u'January',u'February',u'March',u'April',u'May',u'June',u'July',u'August',u'September',u'October',u'November',u'December',
    u'Janvier',u'Février',u'Mars',u'Avril',u'Mai',u'Juin',u'Juillet',u'Août',u'Septembre',u'Octobre',u'Novembre',u'Décembre'] #TODO: srsly...
date_rx = re.compile(r'(\d+) (%s) (\d\d\d\d)' % ('|'.join(MONTHS),), re.IGNORECASE)
 
 
def parseNews(page):
    pywikibot.output(page.aslink())
    try:
        site = page.site()
    except TypeError:
        print 'TypeError'
        site = pywikibot.Site(code = lang, fam = 'wikipedia')
    '''try:
        response, data = site.postForm('/w/api.php', {'action':'parse','format':'json','page':page.title()})
    except ValueError: #too many values to unpack
        raw_input('Erreur systématique')'''
    predata = { #ex : https://fr.wikipedia.org/w/api.php?action=parse&format=jsonfm&page=Portail:Canada/Actualit%C3%A9s/Wikinews
       'action': 'parse',
       'format': 'json',
       'page': page.title().encode('utf-8')
    }
    data = site.postForm(site.apipath(), predata) # WARNING: Http response status 405
    if debug == True: raw_input(data)
    text = simplejson.loads(data)['parse']['text']['*'] # ValueError: No JSON object could be decode
    if debug == True: raw_input(text)
 
    #doc = minidom_parseString(u'<html><body>' + text.encode('utf-8') + u'</body></html>')
    doc = minidom_parseString((u'<html><body>' + text + u'</body></html>').encode('utf-8'))
 
    ul = doc.getElementsByTagName('ul')
    if ul:
        for li in ul[0].getElementsByTagName('li'):
            if li.firstChild.nodeType == Node.TEXT_NODE:
                prefix = li.firstChild.nodeValue
                if site.lang == 'en':
                    prefix = date_rx.sub(r'[[\2 \1]]',prefix)
                elif site.lang == 'fr':
                    prefix = date_rx.sub(r'{{date|\1|\2|\3}}',prefix)
            else:
                prefix = ''
            yield prefix, Page(site, li.getElementsByTagName('a')[0].getAttribute('title'))

def parseNews2(page):
    if debug == True: page.title()
    try:
        pageContent = page.get()
    except pywikibot.exceptions.NoPage:
        print u'NoPage l 1383'
        return
    except pywikibot.exceptions.IsRedirectPage: 
        #PageBegin = page.get(get_redirect=True)
        print u'IsRedirect l 1393'
        return
    if debug == True: raw_input(pageContent.encode(config.console_encoding, 'replace'))
    return pageContent.split("\n")

def doOnePage(tpl, page, site_src):
    pywikibot.output(page.aslink())
    txt = page.get().replace('_', ' ')
    rx = re.search(r'{{(%s\|.*?)}}' % (tpl.title()), txt)
    if not rx:
        return
 
    config = {
            'page' : (None, False),
            'indent' : (u'*', False),
            }
 
    raw_config = rx.group(1).split('|')[1:]
    for x in raw_config:
        var, val = x.split('=',1)
        var, val = var.strip(), val.strip()
        config[var] = (val, True)
 
    if not config['page'][0]:
        pywikibot.output(u'No target page specified!')

    newsPage = Page(site_src, config['page'][0])    # ex : Page:Canada/Wikipedia
    if debug == True: print newsPage                # ex : <DynamicPageList>
    text = u'\n'.join(
        [u'%(indent)s %(prefix)s[[wikinews:%(lang)s:%(article_page)s|%(article_title)s]]' % {
                'article_page' : re.sub(r'[\s\xa0]', ' ', news.title()),
                'article_title' : news.title(),
                'prefix' : prefix,
                'indent' : config['indent'][0],
                'lang' : site_src.lang
            }
            #for prefix, news in parseNews(newsPage)]
            for prefix, news in parseNews2(newsPage)
        ]
    )
    if debug == True: raw_input(text.encode(config.console_encoding, 'replace'))

    #Check for old content
    oldtext = page.get()
    #Ignore lead (timestamp etc.)
    rx = re.compile('^(.*)<noinclude>.*', re.DOTALL)
    oldtext = rx.sub(r'\1', oldtext).strip()
 
    if text != oldtext:
        raw_config = '|'.join(u'%s = %s' % (v,k[0]) for v,k in config.items() if k[1])
        text = u'%(text)s<noinclude>\n{{%(tpl)s|%(config)s}}\nRetrieved by ~~~ from [[wikinews:%(lang)s:%(page)s|]] on ~~~~~\n</noinclude>' % {
                'text' : text,
                'tpl' : tpl.title(),
                'config' : raw_config,
                'page' : config['page'][0],
                'lang' : site_src.lang,
                }
        #pywikibot.output(text)
        result = 'ok'
        if debug == True:
			print text #.encode(config.console_encoding, 'replace')
			result = raw_input("Sauvegarder ? (o/n) ")
        if result != "n" and result != "no" and result != "non":
			page.put(text, comment=u'Updating from [[n:%s|%s]]' % (newsPage.title(),newsPage.title(),))

    try:
        site = page.site()
    except TypeError:
        print 'TypeError'
        site = pywikibot.Site(code = lang, fam = 'wikipedia')

    return {
        'src' : newsPage.title(),
        'ns'  : site.namespace(page.namespace()),
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
 
    audit_txt = u''
    for ns in sorted(pages_maintained.keys()):
        audit_txt += '\n\n== %s: ==\n\n' % ns
        items = sorted(pages_maintained[ns], key=lambda x: x['dst'])
        audit_txt += '\n'.join('# [[%(dst)s]] &larr; [[n:%(src)s|%(src)s]]' % item for item in items)
    audit_txt = audit_txt.strip()
 
    audit_page = Page(site_dest,'User:' + mynick + u'/List')
    oldtext = audit_page.get()
    rx = re.compile('^.*?(?=\n== )', re.DOTALL)
    oldtext = rx.sub('', oldtext).strip()
    #pywikibot.showDiff(oldtext, audit_txt)
    if oldtext != audit_txt:
        result = 'ok'
        if debug == True:
			print audit_page #.encode(config.console_encoding, 'replace')
			result = raw_input("Sauvegarder ? (o/n) ")
        if result != "n" and result != "no" and result != "non":
			audit_page.put(
            u'List of pages maintained by {{user|' + mynick + u'}} by namespace. Last updated: ~~~~~\n\n' + audit_txt,
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