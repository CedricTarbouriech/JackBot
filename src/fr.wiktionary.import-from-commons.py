#!/usr/bin/env python
# coding: utf-8
# Ce script importe les sons de Commons dans le Wiktionnaire

from __future__ import absolute_import, unicode_literals
import re, sys
from lib import *
import pywikibot
from pywikibot import *

debugLevel = 0
debugAliases = ['-debug', '-d']
for debugAlias in debugAliases:
    if debugAlias in sys.argv:
        debugLevel= 1
        sys.argv.remove(debugAlias)

fileName = __file__
if debugLevel > 0: print fileName
if fileName.rfind('/') != -1: fileName = fileName[fileName.rfind('/')+1:]
siteLanguage = fileName[:2]
if debugLevel > 1: print siteLanguage
siteFamily = fileName[3:]
siteFamily = siteFamily[:siteFamily.find('.')]
if debugLevel > 1: print siteFamily
siteDest = pywikibot.Site(siteLanguage, siteFamily)
username = config.usernames[siteFamily][siteLanguage]

site = pywikibot.Site(u'commons', u'commons')
summary = u'Ajout du son depuis [[commons:Category:Pronunciation]]'


def treatPageByName(pageName):
    print(pageName.encode(config.console_encoding, 'replace'))
    if pageName[-4:] != u'.ogg' and pageName[-4:] != u'.oga' and pageName[-4:] != u'.wav':
        if debugLevel > 0: print u' No supported file format found'
        return

    fileName = pageName[len(u'File:'):-4]
    if fileName.find(u'-') == -1:
        if debugLevel > 0: print u' No language code found'
        return

    languageCode = fileName[:fileName.find(u'-')]
    if languageCode == 'LL':
        if debugLevel > 0: print u' Lingua Libre formats'
        # LL-<Qid de la langue> (<code iso 693-3>)-<Username>-<transcription> (<précision>).wav

        if fileName.count('-') > 3:
            if debugLevel > 0: print u' Compound word'
            word = fileName
            for i in range(3):
                word = word[word.find(u'-')+1:]
        else:
            word = fileName[fileName.rfind(u'-')+1:]

        s = re.search(ur'\(([^\)]+)\)', fileName)
        if s:
            languageCode = s.group(1)[:2]
        else:
            if debugLevel > 0: print u' No parenthesis found'
            s = re.search(ur'\-([^\-]+)\-[^\-]+$', fileName)
            if not s:
                if debugLevel > 0: print u' No language code found'
                return
            languageCode = s.group(1)[:2]

    else:
        languageCode = languageCode.lower()
        if languageCode == u'qc': languageCode = u'fr'
        word = fileName[fileName.find(u'-')+1:]
        word = word.replace(u'-',' ')
        word = word.replace(u'_',' ')
        word = word.replace(u'\'',u'’')

    if debugLevel > 0:
        print u' Language code: ' + languageCode
        print u' Word: ' + word

    region = u''
    page1 = Page(siteDest, word)
    try:
        PageBegin = page1.get()
    except pywikibot.exceptions.NoPage:
        # Retrait d'un éventuel article ou une région dans le nom du fichier
        word1 = word

        if languageCode == u'de':
            if word[0:4] == u'der ' or word[0:4] == u'die ' or word[0:4] == u'das ' or word[0:4] == u'den ':
                word = word[word.find(u' ')+1:]
            if word[0:3] == u'at ':
                region = u'{{' + word[0:2].upper() + u'|nocat=1}}'
                word = word[word.find(u' ')+1:]
                
        elif languageCode == u'en':
            if word[0:4] == u'the ' or word[0:2] == u'a ':
                word = word[word.find(u' ')+1:]
            if word[0:3] == u'au ' or word[0:3] == u'gb ' or word[0:3] == u'ca ' or word[0:3] == u'uk ' or word[0:3] == u'us ':
                region = u'{{' + word[0:2].upper() + u'|nocat=1}}'
                word = word[word.find(u' ')+1:]
            
        elif languageCode == u'es':
            if word[0:3] == u'el ' or word[0:3] == u'lo ' or word[0:3] == u'la ' or word[0:3] == u'un ' or word[0:4] == u'uno ' or word[0:4] == u'una ' or word[0:5] == u'unos ' or word[0:5] == u'unas ' or word[0:4] == u'los ':
                word = word[word.find(u' ')+1:]
            if word[0:3] == u'mx ' or word[0:3] == u'ar ':
                region = u'{{' + word[0:2].upper() + u'|nocat=1}}'
                word = word[word.find(u' ')+1:]
            if word[0:7] == u'am lat ':
                region = u'{{AM|nocat=1}}'
                word = word[word.find(u' ')+1:]
                word = word[word.find(u' ')+1:]
                
        elif languageCode == u'fr':
            if word[:3] == u'le ' or word[:3] == u'la ' or word[:4] == u'les ' or word[:3] == u'un ' or word[:3] == u'une ' or word[:4] == u'des ':
                word = word[word.find(u' ')+1:]
            if word[:3] == u'ca ' or word[:3] == u'be ':
                region = u'{{' + word[:2].upper() + u'|nocat=1}}'
                word = word[word.find(u' ')+1:]
            if word[:6] == u'Paris ':
                region = u'Paris (France)'
                word = word[word.find(u' ')+1:]
                
        elif languageCode == u'it':
            if word[0:3] == u"l'" or word[0:3] == u'la ' or word[0:3] == u'le ' or word[0:3] == u'lo ' or word[0:4] == u'gli ' or word[0:3] == u'un ' or word[0:4] == u'uno ' or word[0:4] == u'una ':
                word = word[word.find(u' ')+1:]
        
        elif languageCode == u'nl':
            if word[0:3] == u'de ' or word[0:4] == u'een ' or word[0:4] == u'het ':
                word = word[word.find(u' ')+1:]
                            
        elif languageCode == u'pt':
            if word[0:2] == u'a ' or word[0:2] == u'o ' or word[0:3] == u'as ' or word[0:3] == u'os ':
                word = word[word.find(u' ')+1:]
            if word[0:3] == u'br ' or word[0:3] == u'pt ':
                region = u'{{' + word[0:2].upper() + u'|nocat=1}}'

        elif languageCode == u'sv':
            if word[0:3] == u'en ' or word[0:4] == u'ett ':
                word = word[word.find(u' ')+1:]                
        
        if debugLevel > 1: print u' Mot potentiel : ' + word.encode(config.console_encoding, 'replace')
        # Deuxième tentative de recherche sur le Wiktionnaire    
        if word != word1:
            page1 = Page(siteDest, word)
            try:
                PageBegin = page1.get()
            except pywikibot.exceptions.NoPage:
                if debugLevel > 0: print u' Page introuvable 1'
                return
            except pywikibot.exceptions.IsRedirectPage:
                PageBegin = page1.get(get_redirect=True)
        else:
            if debugLevel > 0: print u' Page introuvable 2'
            return
    except pywikibot.exceptions.IsRedirectPage:
        PageBegin = page1.get(get_redirect=True)
    # à faire : 3e tentative en retirant les suffixes numériques (ex : File:De-aber2.ogg)

    regex = ur'{{pron\|[^\}|]*\|' + languageCode + u'}}'
    if re.compile(regex).search(PageBegin):
        prononciation = PageBegin[re.search(regex,PageBegin).start()+len(u'{{pron|'):re.search(regex,PageBegin).end()-len(u'|'+languageCode+u'}}')]
    else:
        prononciation = u''
    if debugLevel > 1: print prononciation.encode(config.console_encoding, 'replace')
    
    if debugLevel > 1: print u' Mot du Wiktionnaire : ' + word.encode(config.console_encoding, 'replace')
    Son = pageName[len(u'File:'):]
    if PageBegin.find(Son) != -1 or PageBegin.find(Son[:1].lower() + Son[1:]) != -1 or PageBegin.find(Son.replace(u' ', u'_')) != -1 or PageBegin.find((Son[:1].lower() + Son[1:]).replace(u' ', u'_')) != -1:
        if debugLevel > 0: print u' Son déjà présent'
        return
    if PageBegin.find(u'{{langue|' + languageCode) == -1:
        if debugLevel > 0: print u' Paragraphe absent'
        return
    PageTemp = PageBegin

    PageEnd = addPronunciation(PageTemp, languageCode, u'prononciation', u'* {{écouter|' + region + u'|' + prononciation + u'|lang=' + languageCode + u'|audio=' + Son + u'}}')

    # Sauvegarde
    if PageEnd != PageBegin: savePage(page1, PageEnd, summary)


p = PageProvider(treatPageByName, site, debugLevel)
setGlobals(debugLevel, site, username)
setGlobalsWiktionary(debugLevel, site, username)
def main(*args):
    if len(sys.argv) > 1:
        if debugLevel > 1: print sys.argv
        if sys.argv[1] == u'-test':
            treatPageByName(u'User:' + username + u'/test')
        elif sys.argv[1] == u'-test2':
            treatPageByName(u'User:' + username + u'/test2')
        elif sys.argv[1] == u'-page' or sys.argv[1] == u'-p':
            treatPageByName(u'File:LL-Q150 (fra)-Guilhelma-celui-là.wav')
        elif sys.argv[1] == u'-file' or sys.argv[1] == u'-txt':
            p.pagesByFile(u'src/lists/articles_' + siteLanguage + u'_' + siteFamily + u'.txt')
        elif sys.argv[1] == u'-dump' or sys.argv[1] == u'-xml':
            regex = u''
            if len(sys.argv) > 2: regex = sys.argv[2]
            p.pagesByXML(siteLanguage + siteFamily + '\-.*xml', regex)
        elif sys.argv[1] == u'-u':
            p.pagesByUser(u'User:' + username)
        elif sys.argv[1] == u'-search' or sys.argv[1] == u'-s' or sys.argv[1] == u'-r':
            if len(sys.argv) > 2:
                p.pagesBySearch(sys.argv[2])
            else:
                p.pagesBySearch(u'chinois')
        elif sys.argv[1] == u'-link' or sys.argv[1] == u'-l' or sys.argv[1] == u'-template' or sys.argv[1] == u'-m':
            p.pagesByLink(u'Template:autres projets')
        elif sys.argv[1] == u'-category' or sys.argv[1] == u'-cat' or sys.argv[1] == u'-c':
            afterPage = u''
            if len(sys.argv) > 2: afterPage = sys.argv[2]
            p.pagesByCat(u'Lingua Libre pronounciation-fra', afterPage = afterPage, recursive = True, namespaces = None)
        elif sys.argv[1] == u'-redirects':
            p.pagesByRedirects()
        elif sys.argv[1] == u'-all':
           p.pagesByAll()
        elif sys.argv[1] == u'-RC':
            while 1:
                p.pagesByRCLastDay()
        elif sys.argv[1] == u'-nocat':
            p.pagesBySpecialNotCategorized()
        elif sys.argv[1] == u'-lint':
            p.pagesBySpecialLint()
        else:
            treatPageByName(sys.argv[1])
    else:
        p.pagesByCat(u'Category:Pronunciation', recursive = True, notCatNames = ['spoken ', 'Wikipedia', 'Wikinews'])

if __name__ == "__main__":
    main(sys.argv)
