#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Ce script archive des pages de discussion
"""
# Importation des modules
from __future__ import absolute_import, unicode_literals
import os
import sys
import time
import pywikibot
from pywikibot import *
# JackBot
dir_wt = os.path.dirname(__file__)
dir_src = os.path.dirname(dir_wt)
sys.path.append(dir_src)
sys.path.append(os.path.join(dir_src, 'lib'))
sys.path.append(os.path.join(dir_src, 'wiktionary'))
from lib import *
from wiktionary import *

# Global variables
debug_level = 0
debug_aliases = ['debug', 'd', '-d']
for debugAlias in debug_aliases:
    if debugAlias in sys.argv:
        debug_level = 1
        sys.argv.remove(debugAlias)

site_language, site_family, site = get_site_by_file_name(__file__)
username = config.usernames[site_family][site_language]

summary = 'Autoarchivage de [[Wiktionnaire:Bot/Requêtes]]'


'''
@param waitingTimeBeforeArchiving nombre de jours d'inactivité requis avant archivage
(utile pour permettre aux requêtes traitées d'être relues avant qu'elles soient enfouies
en page d'archive)
'''
def treat_page_by_name(page_name, waitingTimeBeforeArchiving=3):
    page = Page(site, page_name)

    # Ne pas archiver tout de suite si page très récemment modifiée
    # (Idéalement, la date des dernières interventions devrait être checkée...)
    latestRev = page.editTime()
    now = datetime.datetime.now()
    inactivityDuration = (now - latestRev).days
    if inactivityDuration < waitingTimeBeforeArchiving:
        return

    if page.exists():
        if page.namespace() != 4 and page.title() != 'User:JackBot/test':
            return
        else:
            try:
                page_content = page.get()
            except pywikibot.exceptions.NoPage:
                print("NoPage")
                return
            except pywikibot.exceptions.IsRedirectPage:
                print("Redirect page l 42")
                page_content = page.get(get_redirect=True)
                page2 = Page(site, page_content[page_content.find('[[')+2:page_content.find(']]')])
                try:
                    final_page_content2 = page2.get()
                except pywikibot.exceptions.NoPage:
                    print("NoPage")
                    return
                except pywikibot.exceptions.IsRedirectPage:
                    print("Redirect page l 51")
                    return
                except pywikibot.exceptions.LockedPage:
                    print("Locked/protected page")
                    return
                if final_page_content2.find('{{NavigBOT') == -1:
                    final_page_content2 = '{{NavigBOT|' + page2.title()[len(page2.title())-4:len(page2.title())] + '}}\n' + final_page_content2
                    save_page(page2, final_page_content2, summary)
                return
            except pywikibot.exceptions.LockedPage:
                print("Locked/protected page")
                return
    else:
        return

    final_page_content = ''
    annee = time.strftime('%Y')
    regex = '\n==[ ]*{{[rR]equête [fait|refus|refusée|sans suite]+}}.*==[ \t]*\n'
    while re.compile(regex).search(page_content):
        DebutParagraphe = re.search(regex,page_content).end()
        if re.search(r'\n==[^=]',page_content[DebutParagraphe:]):
            FinParagraphe = re.search(r'\n==[^=]',page_content[DebutParagraphe:]).start()
        else:
            FinParagraphe = len(page_content[DebutParagraphe:])
        if debug_level > 0:
            input(page_content[DebutParagraphe:][:FinParagraphe])
            print('-------------------------------------')
        if page_content[DebutParagraphe:].find('\n==') == -1:
            # Dernier paragraphe
            final_page_content = final_page_content + page_content[:DebutParagraphe][page_content[:DebutParagraphe].rfind('\n=='):] + page_content[DebutParagraphe:]
            page_content = page_content[:DebutParagraphe][:page_content[:DebutParagraphe].rfind('\n==')]
        else:
            final_page_content = final_page_content + page_content[:DebutParagraphe][page_content[:DebutParagraphe].rfind('\n=='):] + page_content[DebutParagraphe:][:FinParagraphe]
            page_content = page_content[:DebutParagraphe][:page_content[:DebutParagraphe].rfind('\n==')] + page_content[DebutParagraphe:][FinParagraphe:]


    # Sauvegardes
    if page_content != page.get():
        page2 = Page(site,page_name + '/Archives/' + annee)
        final_page_content2 = ''
        if page2.exists():
            try:
                final_page_content2 = page2.get()
            except pywikibot.exceptions.NoPage:
                print("NoPage")
                return
            except pywikibot.exceptions.IsRedirectPage:
                print("Redirect page")
                return
            except pywikibot.exceptions.LockedPage:
                print("Locked/protected page")
                return
        if final_page_content2.find('{{NavigBOT') == -1: final_page_content2 = '{{NavigBOT|' + page2.title()[len(page2.title())-4:len(page2.title())] + '}}\n' + final_page_content2
        save_page(page2, final_page_content2 + final_page_content, summary)
        save_page(page, page_content, summary)

treat_page_by_name('Wiktionnaire:Bots/Requêtes')