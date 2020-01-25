#!/usr/bin/env python
# coding: utf-8
'''
Ce script vérifie toutes les URL des articles :
    1) de la forme http://, https:// et [//
    2) incluses dans certains modèles (pas tous étant donnée leur complexité, car certains incluent des {{{1}}} et {{{2}}} dans leurs URL)
    3) il traduit les noms et paramètres de ces modèles en français (ex : {{cite web|title=}} par {{lien web|titre=}}) cf http://www.tradino.org/
'''

from __future__ import absolute_import, unicode_literals
import os.path
import pywikibot
from pywikibot import *
import codecs, urllib, urllib2, httplib, json, pprint, urlparse, datetime, re, webbrowser, cookielib, socket, time, ssl
import requests
from lib import *

debugLevel = 0
username = 'JackBot'
site = pywikibot.Site('fr', 'wiktionary')

#*** General functions ***
def setGlobalsHL(myDebugLevel, mySite, myUsername):
    global debugLevel
    global site
    global username
    debugLevel  = myDebugLevel
    site        = mySite
    username    = myUsername 

# Preferences
semiauto = False
retablirNonBrise = False    # Reteste les liens brisés
checkURL = False

brokenDomains = []
#brokenDomains.append('marianne2.fr')    # Site remplacé par marianne.net en mai 2017

blockedDomains = [] # à cause des popovers ou Node.js ?
blockedDomains.append(u'bbc.co.uk')
blockedDomains.append(u'biodiversitylibrary.org')
blockedDomains.append(u'charts.fi')
blockedDomains.append(u'cia.gov')
blockedDomains.append(u'finnishcharts.com')
blockedDomains.append(u'history.navy.mil') # IP Free bloquée en lecture
blockedDomains.append(u'itunes.apple.com')
blockedDomains.append(u'nytimes.com')
blockedDomains.append(u'psaworldtour.com')
blockedDomains.append(u'rottentomatoes.com')
blockedDomains.append(u'soundcloud.com')
blockedDomains.append(u'twitter.com')
blockedDomains.append(u'w-siberia.ru')

authorizedFiles = []
authorizedFiles.append(u'.pdf')

# Modèles qui incluent des URL dans leurs pages
ligne = 4
colonne = 2
TabModeles = [[0] * (colonne+1) for _ in range(ligne+1)]
TabModeles[1][1] = u'Import:DAF8'
TabModeles[1][2] = u'http://www.cnrtl.fr/definition/academie8/'
TabModeles[2][1] = u'R:DAF8'
TabModeles[2][2] = u'http://www.cnrtl.fr/definition/academie8/'
TabModeles[3][1] = u'Import:Littré'
TabModeles[3][2] = u'http://artflx.uchicago.edu/cgi-bin/dicos/pubdico1look.pl?strippedhw='
TabModeles[4][1] = u'R:Littré'
TabModeles[4][2] = u'http://artflx.uchicago.edu/cgi-bin/dicos/pubdico1look.pl?strippedhw='

# Modèles qui incluent des URL dans leurs paramètres
oldTemplate = []
newTemplate = []
oldTemplate.append(u'cite web')
newTemplate.append(u'lien web')
oldTemplate.append(u'citeweb')
newTemplate.append(u'lien web')
oldTemplate.append(u'cite news')
newTemplate.append(u'article')
oldTemplate.append(u'cite journal')
newTemplate.append(u'article')
oldTemplate.append(u'cite magazine')
newTemplate.append(u'article')
oldTemplate.append(u'lien news')
newTemplate.append(u'article')
oldTemplate.append(u'cite video')
newTemplate.append(u'lien vidéo')
oldTemplate.append(u'cite episode')
newTemplate.append(u'citation épisode')
oldTemplate.append(u'cite arXiv')
newTemplate.append(u'lien arXiv')
oldTemplate.append(u'cite press release')
newTemplate.append(u'lien web')
oldTemplate.append(u'cite press_release')
newTemplate.append(u'lien web')
oldTemplate.append(u'cite conference')
newTemplate.append(u'lien conférence')
oldTemplate.append(u'docu')
newTemplate.append(u'lien vidéo')
oldTemplate.append(u'cite book')
newTemplate.append(u'ouvrage')
#oldTemplate.append(u'cite')
#newTemplate.append(u'ouvrage')
# it
oldTemplate.append(u'cita pubblicazione')
newTemplate.append(u'article')
# sv
oldTemplate.append(u'webbref')
newTemplate.append(u'lien web')
limiteL = len(newTemplate)    # Limite de la liste des modèles traduis de l'anglais (langue=en)

# Modèle avec alias français
oldTemplate.append(u'deadlink')
newTemplate.append(u'lien brisé')
#oldTemplate.append(u'dead link') TODO: if previous template is {{lien brisé}} then remove else replace 
#newTemplate.append(u'lien brisé')
oldTemplate.append(u'webarchive')
newTemplate.append(u'lien brisé')
oldTemplate.append(u'lien brise')
newTemplate.append(u'lien brisé')
oldTemplate.append(u'lien cassé')
newTemplate.append(u'lien brisé')
oldTemplate.append(u'lien mort')
newTemplate.append(u'lien brisé')
oldTemplate.append(u'lien web brisé')
newTemplate.append(u'lien brisé')
oldTemplate.append(u'lien Web')
newTemplate.append(u'lien web')
oldTemplate.append(u'cita web')
newTemplate.append(u'lien web')
oldTemplate.append(u'cita noticia')
newTemplate.append(u'lien news')
oldTemplate.append(u'web site')
newTemplate.append(u'lien web')
oldTemplate.append(u'site web')
newTemplate.append(u'lien web')
oldTemplate.append(u'périodique')
newTemplate.append(u'article')
oldTemplate.append(u'quote')
newTemplate.append(u'citation bloc')

# Modèles pour traduire leurs paramètres uniquement
oldTemplate.append(u'lire en ligne')
newTemplate.append(u'lire en ligne')
oldTemplate.append(u'dts')
newTemplate.append(u'dts')
oldTemplate.append(u'Chapitre')
newTemplate.append(u'Chapitre')
limiteM = len(newTemplate)

# Paramètres à remplacer
oldParam = []
newParam = []
oldParam.append(u'author')
newParam.append(u'auteur')
oldParam.append(u'authorlink1')
newParam.append(u'lien auteur1')
oldParam.append(u'title')
newParam.append(u'titre')
oldParam.append(u'publisher')
newParam.append(u'éditeur')
oldParam.append(u'work')    # paramètre de {{lien web}} différent pour {{article}}
newParam.append(u'périodique')
oldParam.append(u'newspaper')
newParam.append(u'journal')
oldParam.append(u'day')
newParam.append(u'jour')
oldParam.append(u'month')
newParam.append(u'mois')
oldParam.append(u'year')
newParam.append(u'année')
oldParam.append(u'accessdate')
newParam.append(u'consulté le')
oldParam.append(u'access-date')
newParam.append(u'consulté le')
oldParam.append(u'language')
newParam.append(u'langue')
oldParam.append(u'lang')
newParam.append(u'langue')
oldParam.append(u'quote')
newParam.append(u'extrait')
oldParam.append(u'titre vo')
newParam.append(u'titre original')
oldParam.append(u'first')
newParam.append(u'prénom')
oldParam.append(u'surname')
newParam.append(u'nom')
oldParam.append(u'last')
newParam.append(u'nom')
for p in range(1, 100):
    oldParam.append(u'first'+str(p))
    newParam.append(u'prénom'+str(p))
    oldParam.append(u'given'+str(p))
    newParam.append(u'prénom'+str(p))
    oldParam.append(u'last'+str(p))
    newParam.append(u'nom'+str(p))
    oldParam.append(u'surname'+str(p))
    newParam.append(u'nom'+str(p))
    oldParam.append(u'author'+str(p))
    newParam.append(u'auteur'+str(p))
oldParam.append(u'issue')
newParam.append(u'numéro')
oldParam.append(u'authorlink')
newParam.append(u'lien auteur')
oldParam.append(u'author-link')
newParam.append(u'lien auteur')
for p in range(1, 100):
    oldParam.append(u'authorlink'+str(p))
    newParam.append(u'lien auteur'+str(p))
    oldParam.append(u'author'+str(p)+u'link')
    newParam.append(u'lien auteur'+str(p))
oldParam.append(u'coauthorlink')
newParam.append(u'lien coauteur')
oldParam.append(u'coauthor-link')
newParam.append(u'lien coauteur')
oldParam.append(u'surname1')
newParam.append(u'nom1')
oldParam.append(u'coauthors')
newParam.append(u'coauteurs')
oldParam.append(u'co-auteurs')
newParam.append(u'coauteurs')
oldParam.append(u'co-auteur')
newParam.append(u'coauteur')
oldParam.append(u'given')
newParam.append(u'prénom')
oldParam.append(u'trad')
newParam.append(u'traducteur')
oldParam.append(u'at')
newParam.append(u'passage')
oldParam.append(u'origyear')
newParam.append(u'année première édition') # "année première impression" sur les projets frères
oldParam.append(u'année première impression')
newParam.append(u'année première édition')
oldParam.append(u'location')
newParam.append(u'lieu')
oldParam.append(u'place')
newParam.append(u'lieu')
oldParam.append(u'publication-date')
newParam.append(u'année')
oldParam.append(u'writers')
newParam.append(u'scénario')
oldParam.append(u'episodelink')
newParam.append(u'lien épisode')
oldParam.append(u'serieslink')
newParam.append(u'lien série')
oldParam.append(u'titlelink')
newParam.append(u'lien titre')
oldParam.append(u'credits')
newParam.append(u'crédits')
oldParam.append(u'network')
newParam.append(u'réseau')
oldParam.append(u'station')
newParam.append(u'chaîne')
oldParam.append(u'city')
newParam.append(u'ville')
oldParam.append(u'began')
newParam.append(u'début')
oldParam.append(u'ended')
newParam.append(u'fin')
oldParam.append(u'diffusion')
newParam.append(u'airdate')
oldParam.append(u'number')
newParam.append(u'numéro')
oldParam.append(u'season')
newParam.append(u'saison')
oldParam.append(u'year2')
newParam.append(u'année2')
oldParam.append(u'month2')
newParam.append(u'mois2')
oldParam.append(u'time')
newParam.append(u'temps')
oldParam.append(u'accessyear')
newParam.append(u'année accès')
oldParam.append(u'accessmonth')
newParam.append(u'mois accès')
oldParam.append(u'conference')
newParam.append(u'conférence')
oldParam.append(u'conferenceurl')
newParam.append(u'urlconférence')
oldParam.append(u'booktitle')
newParam.append(u'titre livre')
oldParam.append(u'others')
newParam.append(u'champ libre')
# Fix
oldParam.append(u'en ligne le')
newParam.append(u'archivedate')
oldParam.append(u'autres')
newParam.append(u'champ libre')
oldParam.append(u'Auteur')
newParam.append(u'auteur')
oldParam.append(u'auteur-')
newParam.append(u'auteur')
oldParam.append(u'editor')
newParam.append(u'éditeur')

# espagnol
oldParam.append(u'autor')
newParam.append(u'auteur')
oldParam.append(u'título')
newParam.append(u'titre')
oldParam.append(u'fechaacceso')
newParam.append(u'consulté le')
oldParam.append(u'fecha')
newParam.append(u'date')
oldParam.append(u'obra')
newParam.append(u'série')
oldParam.append(u'idioma')
newParam.append(u'langue')
oldParam.append(u'publicació')
newParam.append(u'éditeur')
oldParam.append(u'editorial')
newParam.append(u'journal')
oldParam.append(u'series')
newParam.append(u'collection')
oldParam.append(u'agency')
newParam.append(u'auteur institutionnel') # ou "périodique" si absent
oldParam.append(u'magazine')
newParam.append(u'périodique')

# italien
oldParam.append(u'autore')
newParam.append(u'auteur')
oldParam.append(u'titolo')
newParam.append(u'titre')
oldParam.append(u'accesso')
newParam.append(u'consulté le')
oldParam.append(u'data')
newParam.append(u'date')
oldParam.append(u'nome')
newParam.append(u'prénom')
oldParam.append(u'cognome')
newParam.append(u'nom')
oldParam.append(u'linkautore')
newParam.append(u'lien auteur')
oldParam.append(u'coautori')
newParam.append(u'coauteurs')
oldParam.append(u'rivista')
newParam.append(u'journal')
oldParam.append(u'giorno')
newParam.append(u'jour')
oldParam.append(u'mese')
newParam.append(u'mois')
oldParam.append(u'anno')
newParam.append(u'année')
oldParam.append(u'pagine')
newParam.append(u'page')

# suédois
oldParam.append(u'författar')
newParam.append(u'auteur')
oldParam.append(u'titel')
newParam.append(u'titre')
oldParam.append(u'hämtdatum')
newParam.append(u'consulté le')
oldParam.append(u'datum')
newParam.append(u'date')
oldParam.append(u'förnamn')
newParam.append(u'prénom')
oldParam.append(u'efternamn')
newParam.append(u'nom')
oldParam.append(u'författarlänk')
newParam.append(u'lien auteur')
oldParam.append(u'utgivare')
newParam.append(u'éditeur')
oldParam.append(u'månad')
newParam.append(u'mois')
oldParam.append(u'år')
newParam.append(u'année')
oldParam.append(u'sida')
newParam.append(u'page')
oldParam.append(u'verk')
newParam.append(u'périodique')

limiteP = len(oldParam)
if limiteP != len(newParam):
    raw_input(u'Erreur l 227')
    
# URL à remplacer
limiteU = 3
URLDeplace = range(1, limiteU +1)
URLDeplace[1] = u'athena.unige.ch/athena'
URLDeplace[2] = u'un2sg4.unige.ch/athena'

# Caractères délimitant la fin des URL
# http://tools.ietf.org/html/rfc3986
# http://fr.wiktionary.org/wiki/Annexe:Titres_non_pris_en_charge
UrlLimit = 14
UrlEnd = range(1, UrlLimit +1)
UrlEnd[1] = u' '
UrlEnd[2] = u'\n'
UrlEnd[3] = u'['
UrlEnd[4] = u']'
UrlEnd[5] = u'{'
UrlEnd[6] = u'}'
UrlEnd[7] = u'<'
UrlEnd[8] = u'>'    
UrlEnd[9] = u'|'
UrlEnd[10] = u'^'
UrlEnd[11] = u'\\'
UrlEnd[12] = u'`'
UrlEnd[13] = u'"'
#UrlEnd.append(u'~'    # dans 1ère RFC seulement
# Caractères qui ne peuvent pas être en dernière position d'une URL :
UrlLimit2 = 7
UrlEnd2 = range(1, UrlLimit +1)
UrlEnd2[1] = u'.'
UrlEnd2[2] = u','
UrlEnd2[3] = u';'
UrlEnd2[4] = u'!'
UrlEnd2[5] = u'?'
UrlEnd2[6] = u')' # mais pas ( ou ) simple
UrlEnd2[7] = u"'"

ligneB = 6
colonneB = 2
noTag = [[0] * (colonneB+1) for _ in range(ligneB+1)]
noTag[1][1] = u'<pre>'
noTag[1][2] = u'</pre>'
noTag[2][1] = u'<nowiki>'
noTag[2][2] = u'</nowiki>'
noTag[3][1] = u'<ref name='
noTag[3][2] = u'>'
noTag[4][1] = u'<rdf'
noTag[4][2] = u'>'
noTag[5][1] = u'<source'
noTag[5][2] = u'</source' + u'>'
noTag[6][1] = u'\n '
noTag[6][2] = u'\n'
'''
    ligneB = ligneB + 1
    noTag[ligneB-1][1] = u'<!--'
    noTag[ligneB-1][2] = u'-->'
'''
noTemplates = []
if not retablirNonBrise: noTemplates.append('lien brisé')

limiteE = 20
Erreur = []
Erreur.append("403 Forbidden")
Erreur.append("404 – File not found")
Erreur.append("404 error")
Erreur.append("404 Not Found")
Erreur.append("404. That’s an error.")
Erreur.append("Error 404 - Not found")
Erreur.append("Error 404 (Not Found)")
Erreur.append("Error 503 (Server Error)")
Erreur.append("Page not found")    # bug avec http://www.ifpi.org/content/section_news/plat2000.html et http://www.edinburgh.gov.uk/trams/include/uploads/story_so_far/Tram_Factsheets_2.pdf
Erreur.append("Runtime Error")
Erreur.append("server timedout")
Erreur.append("Sorry, no matching records for query")
Erreur.append("The page you requested cannot be found")
Erreur.append("this page can't be found")
Erreur.append("The service you requested is not available at this time")
Erreur.append("There is currently no text in this page.") # wiki
Erreur.append("500 Internal Server Error")
# En français
Erreur.append("Cette forme est introuvable !")
Erreur.append("Soit vous avez mal &#233;crit le titre")
Erreur.append(u'Soit vous avez mal écrit le titre')
Erreur.append(u'Terme introuvable')
Erreur.append(u"nom de domaine demandé n'est plus actif")
Erreur.append("Il n'y a pour l'instant aucun texte sur cette page.")
    
# Média trop volumineux    
limiteF = 52
Format = range(1, limiteF +1)
# Audio
Format[1] = u'RIFF'
Format[2] = u'WAV'
Format[3] = u'BWF'
Format[4] = u'Ogg'
Format[5] = u'AIFF'
Format[6] = u'CAF'
Format[7] = u'PCM'
Format[8] = u'RAW'
Format[9] = u'CDA'
Format[10] = u'FLAC'
Format[11] = u'ALAC'
Format[12] = u'AC3'
Format[13] = u'MP3'
Format[14] = u'mp3PRO'
Format[15] = u'Ogg Vorbis'
Format[16] = u'VQF'
Format[17] = u'TwinVQ'
Format[18] = u'WMA'
Format[19] = u'AU'
Format[20] = u'ASF'
Format[21] = u'AA'
Format[22] = u'AAC'
Format[23] = u'MPEG-2 AAC'
Format[24] = u'ATRAC'
Format[25] = u'iKlax'
Format[26] = u'U-MYX'
Format[27] = u'MXP4'
# Vidéo
Format[28] = u'avi'
Format[29] = u'mpg'
Format[30] = u'mpeg'
Format[31] = u'mkv'
Format[32] = u'mka'
Format[33] = u'mks'
Format[34] = u'asf'
Format[35] = u'wmv'
Format[36] = u'wma'
Format[37] = u'mov'
Format[38] = u'ogv'
Format[39] = u'oga'
Format[40] = u'ogx'
Format[41] = u'ogm'
Format[42] = u'3gp'
Format[43] = u'3g2'
Format[44] = u'webm'
Format[45] = u'weba'
Format[46] = u'nut'
Format[47] = u'rm'
Format[48] = u'mxf'
Format[49] = u'asx'
Format[50] = u'ts'
Format[51] = u'flv'

# Traduction des mois
monthLine = 12
monthColumn = 2
TradM = [[0] * (monthColumn + 1) for _ in range(monthLine + 1)]
TradM[1][1] = u'January'
TradM[1][2] = u'janvier'
TradM[2][1] = u'February'
TradM[2][2] = u'février'
TradM[3][1] = u'March'
TradM[3][2] = u'mars'
TradM[4][1] = u'April'
TradM[4][2] = u'avril'
TradM[5][1] = u'May'
TradM[5][2] = u'mai'
TradM[6][1] = u'June'
TradM[6][2] = u'juin'
TradM[7][1] = u'July'
TradM[7][2] = u'juillet'
TradM[8][1] = u'August'
TradM[8][2] = u'août'
TradM[9][1] = u'September'
TradM[9][2] = u'septembre'
TradM[10][1] = u'October'
TradM[10][2] = u'octobre'
TradM[11][1] = u'November'
TradM[11][2] = u'novembre'
TradM[12][1] = u'December'
TradM[12][2] = u'décembre'

# Traduction des langues
ligneL = 17
colonneL = 2
TradL = [[0] * (colonneL+1) for _ in range(ligneL+1)]
TradL[1][1] = u'French'
TradL[1][2] = u'fr'
TradL[2][1] = u'English'
TradL[2][2] = u'en'
TradL[3][1] = u'German'
TradL[3][2] = u'de'
TradL[4][1] = u'Spanish'
TradL[4][2] = u'es'
TradL[5][1] = u'Italian'
TradL[5][2] = u'it'
TradL[6][1] = u'Portuguese'
TradL[6][2] = u'pt'
TradL[7][1] = u'Dutch'
TradL[7][2] = u'nl'
TradL[8][1] = u'Russian'
TradL[8][2] = u'ru'
TradL[9][1] = u'Chinese'
TradL[9][2] = u'zh'
TradL[10][1] = u'Japanese'
TradL[10][2] = u'ja'
TradL[11][1] = u'Polish'
TradL[11][2] = u'pl'
TradL[12][1] = u'Norwegian'
TradL[12][2] = u'no'
TradL[13][1] = u'Swedish'
TradL[13][2] = u'sv'
TradL[14][1] = u'Finnish'
TradL[14][2] = u'fi'
TradL[15][1] = u'Indonesian'
TradL[15][2] = u'id'
TradL[16][1] = u'Hindi'
TradL[16][2] = u'hi'
TradL[17][1] = u'Arabic'
TradL[17][2] = u'ar'

def hyperlynx(currentPage):
    if debugLevel > 0:
        print u'------------------------------------'
        #print time.strftime('%d-%m-%Y %H:%m:%S')
    summary = u'Vérification des URL'
    htmlSource = ''
    url = u''
    currentPage = currentPage.replace(u'[//https://', u'[https://')
    currentPage = currentPage.replace(u'[//http://', u'[http://')
    currentPage = currentPage.replace(u'http://http://', u'http://')
    currentPage = currentPage.replace(u'https://https://', u'https://')
    currentPage = currentPage.replace(u'<ref>{{en}}} ', u'<ref>{{en}} ')
    currentPage = currentPage.replace(u'<ref>{{{en}} ', u'<ref>{{en}} ')
    currentPage = currentPage.replace(u'<ref>{{{en}}} ', u'<ref>{{en}} ')
    currentPage = re.sub(u'[C|c]ita(tion)? *\n* *(\|[^}{]*title *=)', ur'ouvrage\2', currentPage)
    currentPage = translateLinkTemplates(currentPage)
    currentPage = translateDates(currentPage)
    currentPage = translateLanguages(currentPage)

    if debugLevel > 1:
        print u'Fin des traductions :'
        raw_input(currentPage.encode(config.console_encoding, 'replace'))

    # Recherche de chaque hyperlien en clair ------------------------------------------------------------------------------------------------------------------------------------
    finalPage = u''
    while currentPage.find(u'//') != -1:
        if debugLevel > 0: print u'-----------------------------------------------------------------'
        url = u''
        DebutURL = u''
        CharFinURL = u''
        titre = u''
        templateEndPosition = 0
        isBrokenLink = False
        # Avant l'URL
        PageDebut = currentPage[:currentPage.find(u'//')]
        while currentPage.find(u'//') > currentPage.find(u'}}') and currentPage.find(u'}}') != -1:
            if debugLevel > 0: print u'URL après un modèle'
            finalPage = finalPage + currentPage[:currentPage.find(u'}}')+2]
            currentPage = currentPage[currentPage.find(u'}}')+2:]

        # noTags interdisant la modification de l'URL
        ignoredLink = False
        for b in range(1, ligneB):
            if PageDebut.rfind(noTag[b][1]) != -1 and PageDebut.rfind(noTag[b][1]) > PageDebut.rfind(noTag[b][2]):
                ignoredLink = True
                if debugLevel > 0: print u'URL non traitée, car dans ' + noTag[b][1]
                break
            if finalPage.rfind(noTag[b][1]) != -1 and finalPage.rfind(noTag[b][1]) > finalPage.rfind(noTag[b][2]):
                ignoredLink = True
                if debugLevel > 0: print u'URL non traitée, car dans ' + noTag[b][1]
                break
        for noTemplate in noTemplates:
            if PageDebut.rfind(u'{{' + noTemplate + u'|') != -1 and PageDebut.rfind(u'{{' + noTemplate + u'|') > PageDebut.rfind(u'}}'):
                ignoredLink = True
                if debugLevel > 0: print u'URL non traitée, car dans ' + noTemplate
                break
            if PageDebut.rfind(u'{{' + noTemplate[:1].upper() + noTemplate[1:] + u'|') != -1 and \
                PageDebut.rfind(u'{{' + noTemplate[:1].upper() + noTemplate[1:] + u'|') > PageDebut.rfind(u'}}'):
                ignoredLink = True
                if debugLevel > 0: print u'URL non traitée, car dans ' + noTemplate
                break
            if finalPage.rfind(u'{{' + noTemplate + u'|') != -1 and finalPage.rfind(u'{{' + noTemplate + u'|') > finalPage.rfind(u'}}'):
                ignoredLink = True
                if debugLevel > 0: print u'URL non traitée, car dans ' + noTemplate
                break
            if finalPage.rfind(u'{{' + noTemplate[:1].upper() + noTemplate[1:] + u'|') != -1 and \
                finalPage.rfind(u'{{' + noTemplate[:1].upper() + noTemplate[1:] + u'|') > finalPage.rfind(u'}}'):
                ignoredLink = True
                if debugLevel > 0: print u'URL non traitée, car dans ' + noTemplate
                break

        if ignoredLink == False:
            # titre=
            if PageDebut.rfind(u'titre=') != -1 and PageDebut.rfind(u'titre=') > PageDebut.rfind(u'{{') and PageDebut.rfind(u'titre=') > PageDebut.rfind(u'}}'):
                currentPage3 = PageDebut[PageDebut.rfind(u'titre=')+len(u'titre='):]
                if currentPage3.find(u'|') != -1 and (currentPage3.find(u'|') < currentPage3.find(u'}}') or currentPage3.rfind(u'}}') == -1):
                    titre = currentPage3[:currentPage3.find(u'|')]
                else:
                    titre = currentPage3
                if debugLevel > 0: print u'Titre= avant URL : ' + titre
            elif PageDebut.rfind(u'titre =') != -1 and PageDebut.rfind(u'titre =') > PageDebut.rfind(u'{{') and PageDebut.rfind(u'titre =') > PageDebut.rfind(u'}}'):
                currentPage3 = PageDebut[PageDebut.rfind(u'titre =')+len(u'titre ='):]
                if currentPage3.find(u'|') != -1 and (currentPage3.find(u'|') < currentPage3.find(u'}}') or currentPage3.rfind(u'}}') == -1):
                    titre = currentPage3[:currentPage3.find(u'|')]
                else:
                    titre = currentPage3
                if debugLevel > 0: print u'Titre = avant URL : ' + titre
        
            # url=
            if PageDebut[-1:] == u'[':
                if debugLevel > 0: print u'URL entre crochets sans protocole'
                DebutURL = 1
            elif PageDebut[-5:] == u'http:':
                if debugLevel > 0: print u'URL http'
                DebutURL = 5
            elif PageDebut[-6:] == u'https:':
                if debugLevel > 0: print u'URL https'
                DebutURL = 6
            elif PageDebut[-2:] == u'{{':
                if debugLevel > 0: print u"URL d'un modèle"
                break
            else:
                if debugLevel > 0: print u'URL sans http ni crochet'
                DebutURL = 0
            if DebutURL != 0:
                # Après l'URL
                FinPageURL = currentPage[currentPage.find(u'//'):]
                # url=    
                CharFinURL = u' '
                for l in range(1, UrlLimit):
                    if FinPageURL.find(CharFinURL) == -1 or (FinPageURL.find(UrlEnd[l]) != -1 and FinPageURL.find(UrlEnd[l]) < FinPageURL.find(CharFinURL)):
                        CharFinURL = UrlEnd[l]
                if debugLevel > 0: print u'*Caractère de fin URL : ' + CharFinURL
                
                if DebutURL == 1:
                    url = u'http:' + currentPage[currentPage.find(u'//'):currentPage.find(u'//')+FinPageURL.find(CharFinURL)]
                    if titre == u'':
                        titre = currentPage[currentPage.find(u'//')+FinPageURL.find(CharFinURL):]
                        titre = trim(titre[:titre.find(u']')])
                else:
                    url = currentPage[currentPage.find(u'//')-DebutURL:currentPage.find(u'//')+FinPageURL.find(CharFinURL)]
                if len(url) <= 10:
                    url = u''
                    htmlSource = u''
                    isBrokenLink = False
                else:
                    for u in range(1,UrlLimit2):
                        while url[len(url)-1:] == UrlEnd2[u]:
                            url = url[:len(url)-1]
                            if debugLevel > 0: print u'Réduction de l\'URL de ' + UrlEnd2[u]
                    
                    Media = False
                    for f in range(1,limiteF):
                        if url[len(url)-len(Format[f])-1:].lower() == u'.' + Format[f].lower():
                            if debugLevel > 0:
                                print url.encode(config.console_encoding, 'replace')
                                print u'Média détecté (memory error potentielle)'
                            Media = True
                    if Media == False:
                        if debugLevel > 0: print(u'Recherche de la page distante : ' + url)
                        htmlSource = testURL(url, debugLevel)
                        if debugLevel > 0: print(u'Recherche dans son contenu')
                        isBrokenLink = testURLPage(htmlSource, url)
                
                # Site réputé HS, mais invisible car ses sous-pages ont toutes été déplacées, et renvoient vers l'accueil
                for u in range(1,limiteU):
                    if url.find(URLDeplace[u]) != -1 and len(url) > len(URLDeplace[u]) + 8:    #http://.../
                        isBrokenLink = True
                
                # Confirmation manuelle
                if semiauto == True:
                    webbrowser.open_new_tab(url)
                    if isBrokenLink:
                        result = raw_input("Lien brisé ? (o/n) ")
                    else:
                        result = raw_input("Lien fonctionnel ? (o/n) ")
                    if result != "n" and result != "no" and result != "non":
                        isBrokenLink = True
                    else:
                        isBrokenLink = False
                        
                if debugLevel > 0:
                    # Compte-rendu des URL détectées
                    try:
                        print u'*URL : ' + url.encode(config.console_encoding, 'replace')
                        print u'*Titre : ' + titre.encode(config.console_encoding, 'replace')
                        print u'*HS : ' + str(isBrokenLink)
                    except UnicodeDecodeError:
                        print u'*HS : ' + str(isBrokenLink)
                        print "UnicodeDecodeError l 466"
                if debugLevel > 1: raw_input (htmlSource[:7000])
                
                # Modification du wiki en conséquence    
                DebutPage = currentPage[0:currentPage.find(u'//')+2]
                DebutURL = max(DebutPage.find(u'http://'),DebutPage.find(u'https://'),DebutPage.find(u'[//'))
                
                # Saut des modèles inclus dans un modèle de lien
                while DebutPage.rfind(u'{{') != -1 and DebutPage.rfind(u'{{') < DebutPage.rfind(u'}}'):
                    # pb des multiples crochets fermants sautés : {{ ({{ }} }})
                    currentPage2 = DebutPage[DebutPage.rfind(u'{{'):]
                    if currentPage2.rfind(u'}}') == currentPage2.rfind(u'{{'):
                        DebutPage = DebutPage[:DebutPage.rfind(u'{{')]
                    else:
                        DebutPage = u''
                        break
                    if debugLevel > 1: raw_input(DebutPage[-100:].encode(config.console_encoding, 'replace'))
                    
                
                # Détection si l'hyperlien est dans un modèle (si aucun modèle n'est fermé avant eux)
                if (DebutPage.rfind(u'{{') != -1 and DebutPage.rfind(u'{{') > DebutPage.rfind(u'}}')) or \
                    (DebutPage.rfind(u'url=') != -1 and DebutPage.rfind(u'url=') > DebutPage.rfind(u'}}')) or \
                    (DebutPage.rfind(u'url =') != -1 and DebutPage.rfind(u'url =') > DebutPage.rfind(u'}}')):
                    DebutModele = DebutPage.rfind(u'{{')
                    DebutPage = DebutPage[DebutPage.rfind(u'{{'):len(DebutPage)]
                    AncienModele = u''
                    # Lien dans un modèle connu (consensus en cours pour les autres, atention aux infobox)
                    '''for m in range(1,limiteM):
                        regex = u'{{ *[' + newTemplate[m][0:1] + ur'|' + newTemplate[m][0:1].upper() + ur']' + newTemplate[m][1:len(newTemplate[m])] + ur' *[\||\n]'
                    ''' 
                    if re.search(u'{{ *[L|l]ien web *[\||\n]', DebutPage):
                        AncienModele = u'lien web'
                        if debugLevel > 0: print u'Détection de ' + AncienModele
                    elif re.search('{{ *[L|l]ire en ligne *[\||\n]', DebutPage):
                        AncienModele = u'lire en ligne'
                        if debugLevel > 0: print u'Détection de ' + AncienModele
                    elif retablirNonBrise == True and re.search(u'{{ *[L|l]ien brisé *[\||\n]', DebutPage):
                        AncienModele = u'lien brisé'
                        if debugLevel > 0: print u'Détection de ' + AncienModele
                        
                    #if DebutPage[0:2] == u'{{': AncienModele = trim(DebutPage[2:DebutPage.find(u'|')])
                    
                    templateEndPosition = currentPage.find(u'//')+2
                    FinPageModele = currentPage[templateEndPosition:len(currentPage)]
                    # Calcul des modèles inclus dans le modèle de lien
                    while FinPageModele.find(u'}}') != -1 and FinPageModele.find(u'}}') > FinPageModele.find(u'{{') and FinPageModele.find(u'{{') != -1:
                        templateEndPosition = templateEndPosition + FinPageModele.find(u'}}')+2
                        FinPageModele = FinPageModele[FinPageModele.find(u'}}')+2:len(FinPageModele)]
                    templateEndPosition = templateEndPosition + FinPageModele.find(u'}}')+2
                    currentTemplate = currentPage[DebutModele:templateEndPosition]
                    #if debugLevel > 0: print "*Modele : " + currentTemplate[:100].encode(config.console_encoding, 'replace')
                    
                    if AncienModele != u'':
                        if debugLevel > 0: print u'Ancien modèle à traiter : ' + AncienModele
                        if isBrokenLink:
                            try:
                                currentPage = currentPage[:DebutModele] + u'{{lien brisé' + currentPage[re.search(u'{{ *[' + AncienModele[:1] + u'|' + AncienModele[:1].upper() + u']' + AncienModele[1:] + u' *[\||\n]', currentPage).end()-1:]
                            except AttributeError:
                                raise "Regex introuvable ligne 811"
                                
                        elif AncienModele == u'lien brisé':
                            if debugLevel > 0: print u'Rétablissement d\'un ancien lien brisé'
                            currentPage = currentPage[:currentPage.find(AncienModele)] + u'lien web' + currentPage[currentPage.find(AncienModele)+len(AncienModele):]
                        '''
                        # titre=
                        if re.search(u'\| *titre *=', FinPageURL):
                            if debugLevel > 0: print u'Titre après URL'
                            if titre == u'' and re.search(u'\| *titre *=', FinPageURL).end() != -1 and re.search(u'\| *titre *=', FinPageURL).end() < FinPageURL.find(u'\n') and re.search(u'\| *titre *=', FinPageURL).end() < FinPageURL.find(u'}}'):
                                currentPage3 = FinPageURL[re.search(u'\| *titre *=', FinPageURL).end():]
                                # Modèles inclus dans les titres
                                while currentPage3.find(u'{{') != -1 and currentPage3.find(u'{{') < currentPage3.find(u'}}') and currentPage3.find(u'{{') < currentPage3.find(u'|'):
                                    titre = titre + currentPage3[:currentPage3.find(u'}}')+2]
                                    currentPage3 = currentPage3[currentPage3.find(u'}}')+2:]
                                if currentPage3.find(u'|') != -1 and (currentPage3.find(u'|') < currentPage3.find(u'}}') or currentPage3.find(u'}}') == -1):
                                    titre = titre + currentPage3[0:currentPage3.find(u'|')]
                                else:
                                    titre = titre + currentPage3[0:currentPage3.find(u'}}')]
                        elif FinPageURL.find(u']') != -1 and (currentPage.find(u'//') == currentPage.find(u'[//')+1 or currentPage.find(u'//') == currentPage.find(u'[http://')+6 or currentPage.find(u'//') == currentPage.find(u'[https://')+7):
                            titre = FinPageURL[FinPageURL.find(CharFinURL)+len(CharFinURL):FinPageURL.find(u']')]
                        if debugLevel > 1: raw_input(FinPageURL.encode(config.console_encoding, 'replace'))    
                        
                        # En cas de modèles inclus le titre a pu ne pas être détecté précédemment
                        if titre == u'' and re.search(u'\| *titre *=', currentTemplate):
                            currentPage3 = currentTemplate[re.search(u'\| *titre *=', currentTemplate).end():]
                            # Modèles inclus dans les titres
                            while currentPage3.find(u'{{') != -1 and currentPage3.find(u'{{') < currentPage3.find(u'}}') and currentPage3.find(u'{{') < currentPage3.find(u'|'):
                                titre = titre + currentPage3[:currentPage3.find(u'}}')+2]
                                currentPage3 = currentPage3[currentPage3.find(u'}}')+2:]
                            titre = titre + currentPage3[:re.search(u'[^\|}\n]*', currentPage3).end()]
                            if debugLevel > 0:
                                print u'*Titre2 : '
                                print titre.encode(config.console_encoding, 'replace')
                            
                        if isBrokenLink == True and AncienModele != u'lien brisé' and AncienModele != u'Lien brisé':
                            summary = summary + u', remplacement de ' + AncienModele + u' par {{lien brisé}}'
                            if debugLevel > 0: print u', remplacement de ' + AncienModele + u' par {{lien brisé}}'
                            if titre == u'':
                                currentPage = currentPage[0:DebutModele] + u'{{lien brisé|consulté le=' + time.strftime('%Y-%m-%d') + u'|url=' + url + u'}}' + currentPage[templateEndPosition:len(currentPage)]
                            else:
                                currentPage = currentPage[0:DebutModele] + u'{{lien brisé|consulté le=' + time.strftime('%Y-%m-%d') + u'|url=' + url + u'|titre=' + titre + u'}}' + currentPage[templateEndPosition:len(currentPage)]
                        elif isBrokenLink == False and (AncienModele == u'lien brisé' or AncienModele == u'Lien brisé'):
                            summary = summary + u', Retrait de {{lien brisé}}'
                            currentPage = currentPage[0:DebutModele] + u'{{lien web' + currentPage[DebutModele+len(u'lien brisé')+2:len(currentPage)]
                        '''
                            
                        '''elif isBrokenLink:
                        summary = summary + u', ajout de {{lien brisé}}'
                        if DebutURL == 1:
                            if debugLevel > 0: print u'Ajout de lien brisé entre crochets 1'
                            # Lien entre crochets
                            currentPage = currentPage[0:DebutURL] + u'{{lien brisé|consulté le=' + time.strftime('%Y-%m-%d') + u'|url=' + url + u'|titre=' + titre + u'}}' + currentPage[currentPage.find(u'//')+FinPageURL.find(u']')+1:len(currentPage)]
                        else:
                            if debugLevel > 0: print u'Ajout de lien brisé 1'
                            if currentPage[DebutURL-1:DebutURL] == u'[' and currentPage[DebutURL-2:DebutURL] != u'[[': DebutURL = DebutURL -1
                            if CharFinURL == u' ' and FinPageURL.find(u']') != -1 and (FinPageURL.find(u'[') == -1 or FinPageURL.find(u']') < FinPageURL.find(u'[')): 
                                # Présence d'un titre
                                currentPage = currentPage[0:DebutURL] + u'{{lien brisé|consulté le=' + time.strftime('%Y-%m-%d') + u'|url=' + url + u'|titre=' + currentPage[currentPage.find(u'//')+FinPageURL.find(CharFinURL)+1:currentPage.find(u'//')+FinPageURL.find(u']')]  + u'}}' + currentPage[currentPage.find(u'//')+FinPageURL.find(u']')+1:len(currentPage)]
                            elif CharFinURL == u']':
                                currentPage = currentPage[0:DebutURL] + u'{{lien brisé|consulté le=' + time.strftime('%Y-%m-%d') + u'|url=' + url + u'}}' + currentPage[currentPage.find(u'//')+FinPageURL.find(CharFinURL):len(currentPage)]
                            else:
                                currentPage = currentPage[0:DebutURL] + u'{{lien brisé|consulté le=' + time.strftime('%Y-%m-%d') + u'|url=' + url + u'}}' + currentPage[currentPage.find(u'//')+FinPageURL.find(CharFinURL):len(currentPage)]
                        '''
                    else:
                        if debugLevel > 0: print url.encode(config.console_encoding, 'replace') + " dans modèle non géré"
                    
                else:
                    if debugLevel > 0: print u'URL hors modèle'
                    if isBrokenLink:
                        summary = summary + u', ajout de {{lien brisé}}'
                        if DebutURL == 1:
                            if debugLevel > 0: print u'Ajout de lien brisé entre crochets sans protocole'
                            if titre != u'':
                                currentPage = currentPage[:DebutURL] + u'{{lien brisé|consulté le=' + time.strftime('%Y-%m-%d') + u'|url=' + url + u'|titre=' + titre + u'}}' + currentPage[currentPage.find(u'//')+FinPageURL.find(CharFinURL):]
                            else:
                                currentPage = currentPage[:DebutURL] + u'{{lien brisé|consulté le=' + time.strftime('%Y-%m-%d') + u'|url=' + url + u'}}' + currentPage[currentPage.find(u'//')+FinPageURL.find(CharFinURL):]
                            #if debugLevel > 0: raw_input(currentPage.encode(config.console_encoding, 'replace'))
                        else:
                            if debugLevel > 0: print u'Ajout de lien brisé 2'
                            if currentPage[DebutURL-1:DebutURL] == u'[' and currentPage[DebutURL-2:DebutURL] != u'[[':
                                if debugLevel > 0: print u'entre crochet'
                                DebutURL = DebutURL -1
                                if titre == u'' :
                                    if debugLevel > 0: "Titre vide"
                                    # Prise en compte des crochets inclus dans un titre
                                    currentPage2 = currentPage[currentPage.find(u'//')+FinPageURL.find(CharFinURL):]
                                    #if debugLevel > 0: raw_input(currentPage2.encode(config.console_encoding, 'replace'))
                                    if currentPage2.find(u']]') != -1 and currentPage2.find(u']]') < currentPage2.find(u']'):
                                        while currentPage2.find(u']]') != -1 and currentPage2.find(u'[[') != -1 and currentPage2.find(u'[[') < currentPage2.find(u']]'):
                                            titre = titre + currentPage2[:currentPage2.find(u']]')+1]
                                            currentPage2 = currentPage2[currentPage2.find(u']]')+1:]
                                        titre = trim(titre + currentPage2[:currentPage2.find(u']]')])
                                        currentPage2 = currentPage2[currentPage2.find(u']]'):]
                                    while currentPage2.find(u']') != -1 and currentPage2.find(u'[') != -1 and currentPage2.find(u'[') < currentPage2.find(u']'):
                                        titre = titre + currentPage2[:currentPage2.find(u']')+1]
                                        currentPage2 = currentPage2[currentPage2.find(u']')+1:]
                                    titre = trim(titre + currentPage2[:currentPage2.find(u']')])
                                    currentPage2 = currentPage2[currentPage2.find(u']'):]
                                if titre != u'':
                                    if debugLevel > 0: "Ajout avec titre"
                                    currentPage = currentPage[:DebutURL] + u'{{lien brisé|consulté le=' + time.strftime('%Y-%m-%d') + u'|url=' + url + u'|titre=' + titre + u'}}' + currentPage[len(currentPage)-len(currentPage2)+1:len(currentPage)]
                                else:
                                    if debugLevel > 0: "Ajout sans titre"
                                    currentPage = currentPage[:DebutURL] + u'{{lien brisé|consulté le=' + time.strftime('%Y-%m-%d') + u'|url=' + url + u'}}' + currentPage[currentPage.find(u'//')+FinPageURL.find(u']')+1:len(currentPage)]
                            else:    
                                if titre != u'': 
                                    # Présence d'un titre
                                    if debugLevel > 0: print u'URL nue avec titre'
                                    currentPage = currentPage[:DebutURL] + u'{{lien brisé|consulté le=' + time.strftime('%Y-%m-%d') + u'|url=' + url + u'|titre=' + currentPage[currentPage.find(u'//')+FinPageURL.find(CharFinURL)+1:currentPage.find(u'//')+FinPageURL.find(u']')]  + u'}}' + currentPage[currentPage.find(u'//')+FinPageURL.find(u']')+1:len(currentPage)]
                                else:
                                    if debugLevel > 0: print u'URL nue sans titre'
                                    currentPage = currentPage[:DebutURL] + u'{{lien brisé|consulté le=' + time.strftime('%Y-%m-%d') + u'|url=' + url + u'}} ' + currentPage[currentPage.find(u'//')+FinPageURL.find(CharFinURL):len(currentPage)]
                        
                    else:
                        if debugLevel > 0: print u'Aucun changement sur l\'URL http'
            else:
                if debugLevel > 0: print u'Aucun changement sur l\'URL non http'    
        else:
            if debugLevel > 1: print u'URL entre balises sautée'

        # Lien suivant, en sautant les URL incluses dans l'actuelle, et celles avec d'autres protocoles que http(s)
        if templateEndPosition == 0 and isBrokenLink == False:
            FinPageURL = currentPage[currentPage.find(u'//')+2:len(currentPage)]
            CharFinURL = u' '
            for l in range(1,UrlLimit):
                if FinPageURL.find(UrlEnd[l]) != -1 and FinPageURL.find(UrlEnd[l]) < FinPageURL.find(CharFinURL):
                    CharFinURL = UrlEnd[l]
            if debugLevel > 0: print u'Saut après "' + CharFinURL + u'"'
            finalPage = finalPage + currentPage[:currentPage.find(u'//')+2+FinPageURL.find(CharFinURL)]
            currentPage = currentPage[currentPage.find(u'//')+2+FinPageURL.find(CharFinURL):]
        else:
            # Saut du reste du modèle courant (contenant parfois d'autres URL à laisser)
            if debugLevel > 0: print u'Saut après "}}"'
            finalPage = finalPage + currentPage[:templateEndPosition]
            currentPage = currentPage[templateEndPosition:]
        if debugLevel > 1: raw_input(finalPage.encode(config.console_encoding, 'replace'))

    if finalPage.find(u'|langue=None') != -1:
        if isBrokenLink == False:
            URLlanguage = getURLsiteLanguage(htmlSource)
            if URLlanguage != 'None':
                try:
                    finalPage = finalPage.replace(u'|langue=None', u'|langue=' + URLlanguage)
                except UnicodeDecodeError:
                    if debugLevel > 0: print u'UnicodeEncodeError l 1038'

    currentPage = finalPage + currentPage
    finalPage = u''    
    if debugLevel > 0: print ("Fin des tests URL")

    # Recherche de chaque hyperlien de modèles ------------------------------------------------------------------------------------------------------------------------------------
    if currentPage.find(u'{{langue') != -1: # du Wiktionnaire
        if debugLevel > 0: print("Modèles Wiktionnaire")
        for m in range(1,ligne):
            finalPage = u''
            while currentPage.find(u'{{' + TabModeles[m][1] + u'|') != -1:
                finalPage =  finalPage + currentPage[:currentPage.find(u'{{' + TabModeles[m][1] + u'|')+len(u'{{' + TabModeles[m][1] + u'|')]
                currentPage =  currentPage[currentPage.find(u'{{' + TabModeles[m][1] + u'|')+len(u'{{' + TabModeles[m][1] + u'|'):len(currentPage)]
                if currentPage[0:currentPage.find(u'}}')].find(u'|') != -1:
                    Param1Encode = currentPage[:currentPage.find(u'|')].replace(u' ',u'_')
                else:
                    Param1Encode = currentPage[:currentPage.find(u'}}')].replace(u' ',u'_')
                htmlSource = testURL(TabModeles[m][2] + Param1Encode, debugLevel)
                isBrokenLink = testURLPage(htmlSource, url)
                if isBrokenLink: finalPage = finalPage[:finalPage.rfind(u'{{' + TabModeles[m][1] + u'|')] + u'{{lien brisé|consulté le=' + time.strftime('%Y-%m-%d') + u'|url=' + TabModeles[m][2]
            currentPage = finalPage + currentPage
            finalPage = u''
        currentPage = finalPage + currentPage
        finalPage = u''
    if debugLevel > 0: print (u'Fin des tests modèle')

    # Paramètres inutiles
    currentPage = re.sub(ur'{{ *Références *\| *colonnes *= *}}', ur'{{Références}}', currentPage)
    # Dans {{article}}, "éditeur" vide bloque "périodique", "journal" ou "revue"
    currentPage = re.sub(ur'{{ *(a|A)rticle *((?:\||\n)[^}]*)\| *éditeur *= *([\||}|\n]+)', ur'{{\1rticle\2\3', currentPage)
    # Dans {{ouvrage}}, "lire en ligne" vide bloque "url"
    currentPage = re.sub(ur'{{ *(o|O)uvrage *((?:\||\n)[^}]*)\| *lire en ligne *= *([\||}|\n]+)', ur'{{\1uvrage\2\3', currentPage)
    # https://fr.wikipedia.org/w/index.php?title=Discussion_utilisateur:JackPotte&oldid=prev&diff=165491794#Suggestion_pour_JackBot_:_Signalement_param%C3%A8tre_obligatoire_manquant_+_Lien_web_vs_Article
    currentPage = re.sub(ur'{{ *(o|O)uvrage *((?:\||\n)[^}]*)\| *(?:ref|référence|référence simplifiée) *= *harv *([\|}\n]+)', ur'{{\1uvrage\2\3', currentPage)
    # https://fr.wikipedia.org/wiki/Wikip%C3%A9dia:Bot/Requ%C3%AAtes/2020/01#Remplacement_automatique_d%27un_message_d%27erreur_du_mod%C3%A8le_%7B%7BOuvrage%7D%7D
    currentPage = re.sub(ur'{{ *(o|O)uvrage *((?:\||\n)[^}]*)\| *display\-authors *= *etal *([\|}\n]+)', ur'{{\1uvrage\2|et al.=oui\3', currentPage)
    currentPage = re.sub(ur'{{ *(o|O)uvrage *((?:\||\n)[^}]*)\| *display\-authors *= *[0-9]* *([\|}\n]+)', ur'{{\1uvrage\2\3', currentPage)
    currentPage = re.sub(ur'{{ *(o|O)uvrage *((?:\||\n)[^}]*)\| *df *= *(?:mdy\-all|dmy\-all)* *([\|}\n]+)', ur'{{\1uvrage\2\3', currentPage)
    # Empty 1=
    currentPage = re.sub(ur'{{ *(a|A)rticle *((?:\||\n)[^}]*)\| *([\|}\n]+)', ur'{{\1rticle\2\3', currentPage)
    currentPage = re.sub(ur'{{ *(l|L)ien web *((?:\||\n)[^}]*)\| *([\|}\n]+)', ur'{{\1ien web\2\3', currentPage)
    #currentPage = re.sub(ur'{{ *(o|O)uvrage *((?:\||\n)[^}]*)\| *([\|}\n]+)', ur'{{\1uvrage\2\3', currentPage)
    ''' TODO : à vérifier
    while currentPage.find(u'|deadurl=no|') != -1:
        currentPage = currentPage[:currentPage.find(u'|deadurl=no|')+1] + currentPage[currentPage.find(u'|deadurl=no|')+len(u'|deadurl=no|'):]
    '''

    finalPage = finalPage + currentPage

    # TODO: avoid these fixes when: oldTemplate.append(u'lien mort')
    finalPage = finalPage.replace(u'<ref></ref>',u'')
    finalPage = finalPage.replace(u'{{lien mortarchive',u'{{lien mort archive')
    finalPage = finalPage.replace(u'|langue=None', u'')
    finalPage = finalPage.replace(u'|langue=en|langue=en', u'|langue=en')
    if debugLevel > 0: print(u'Fin hyperlynx.py')

    return finalPage


def getURLsiteLanguage(htmlSource, debugLevel = 0):
    if debugLevel > 0: print u'getURLsiteLanguage() Code langue à remplacer une fois trouvé sur la page distante...'
    URLlanguage = u'None'
    try:
        regex = u'<html [^>]*lang *= *"?\'?([a-zA-Z\-]+)'
        result = re.search(regex, htmlSource)
        if result:
            URLlanguage = result.group(1)
            if debugLevel > 0: print u' Langue trouvée sur le site'
            if (len(URLlanguage)) > 6: URLlanguage = u'None'
    except UnicodeDecodeError:
        if debugLevel > 0: print u'UnicodeEncodeError l 1032'
    if debugLevel > 0: print u' Langue retenue : ' + URLlanguage
    return URLlanguage

def testURL(url, debugLevel = 0):
    # Renvoie la page web d'une URL dès qu'il arrive à la lire.
    if checkURL == False: return 'ok'
    if debugLevel > 0: print u'--------'

    for blacklisted in brokenDomains:
        if url.find(blacklisted) != -1:
            if debugLevel > 0: print(u' broken domain')
            return 'ko'
    for whitelisted in blockedDomains:
        if url.find(whitelisted) != -1:
            if debugLevel > 0: print(u' authorized domain')
            return 'ok'
    for whitelisted in authorizedFiles:
        if url[len(url)-len(whitelisted):] == whitelisted:
            if debugLevel > 0: print(u' authorized file')
            return 'ok'

    htmlSource = u''
    connectionMethod = u'Request'
    try:
        req = urllib2.Request(url)
        res = urllib2.urlopen(req) # If blocked here for hours, just whitelist the domain if the page isn't forbidden
        # TODO : ssl.CertificateError: hostname 'www.mediarodzina.com.pl' doesn't match either of 'mediarodzina.pl', 'www.mediarodzina.pl'
        # UnicodeWarning: Unicode unequal comparison failed to convert both arguments to Unicode
        htmlSource = res.read()
        if debugLevel > 0: print str(len(htmlSource))
        if htmlSource != str(''): return htmlSource
    except UnicodeEncodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
    except UnicodeDecodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
    except UnicodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeError'
    except httplib.BadStatusLine:
        if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
    except httplib.HTTPException:
        if debugLevel > 0: print connectionMethod + u' : HTTPException' # ex : got more than 100 headers
    except httplib.InvalidURL:
        if debugLevel > 0: print connectionMethod + u' : InvalidURL'
    except urllib2.URLError:
        if debugLevel > 0: print connectionMethod + u' : URLError'
    except httplib.IncompleteRead:
        if debugLevel > 0: print connectionMethod + u' : IncompleteRead'
    except urllib2.HTTPError, e:
        if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
        connectionMethod = u'opener'
        try:
            opener = urllib2.build_opener()
            response = opener.open(url)
            htmlSource = response.read()
            if debugLevel > 0: print str(len(htmlSource))
            if htmlSource != str(''): return htmlSource
        except UnicodeEncodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
        except UnicodeDecodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
        except UnicodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeError'
        except httplib.BadStatusLine:
            if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
        except httplib.HTTPException:
            if debugLevel > 0: print connectionMethod + u' : HTTPException'
        except httplib.InvalidURL:
            if debugLevel > 0: print connectionMethod + u' : InvalidURL'
        except urllib2.HTTPError, e:
            if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
        except IOError as e:
            if debugLevel > 0: print connectionMethod + u' : I/O error({0}): {1}'.format(e.errno, e.strerror)
        except urllib2.URLError:
            if debugLevel > 0: print connectionMethod + u' : URLError'
        except MemoryError:
            if debugLevel > 0: print connectionMethod + u' : MemoryError'
        except requests.exceptions.HTTPError:
            if debugLevel > 0: print connectionMethod + u' : HTTPError'
        except requests.exceptions.SSLError:
            if debugLevel > 0: print connectionMethod + u' : SSLError'
        except ssl.CertificateError:
            if debugLevel > 0: print connectionMethod + u' : CertificateError'
        # pb avec http://losangeles.broadwayworld.com/article/El_Capitan_Theatre_Presents_Disneys_Mars_Needs_Moms_311421_20110304 qui renvoie 301 car son suffixe est facultatif
    except IOError as e:
        if debugLevel > 0: print connectionMethod + u' : I/O error({0}): {1}'.format(e.errno, e.strerror)
    except MemoryError:
        if debugLevel > 0: print connectionMethod + u' : MemoryError'
    except requests.exceptions.HTTPError:
        if debugLevel > 0: print connectionMethod + u' : HTTPError'
    except ssl.CertificateError:
        if debugLevel > 0: print connectionMethod + u' : CertificateError'
    except requests.exceptions.SSLError:
        if debugLevel > 0: print connectionMethod + u' : ssl.CertificateError'
        # HS : https://fr.wikipedia.org/w/index.php?title=Herv%C3%A9_Moulin&type=revision&diff=135989688&oldid=135121040
        url = url.replace(u'https:', u'http:')
        try:
            response = opener.open(url)
            htmlSource = response.read()
            if debugLevel > 0: print str(len(htmlSource))
            if htmlSource != str(''): return htmlSource
        except UnicodeEncodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
        except UnicodeDecodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
        except UnicodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeError'
        except httplib.BadStatusLine:
            if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
        except httplib.HTTPException:
            if debugLevel > 0: print connectionMethod + u' : HTTPException'
        except httplib.InvalidURL:
            if debugLevel > 0: print connectionMethod + u' : InvalidURL'
        except urllib2.HTTPError, e:
            if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
        except IOError as e:
            if debugLevel > 0: print connectionMethod + u' : I/O error({0}): {1}'.format(e.errno, e.strerror)
        except urllib2.URLError:
            if debugLevel > 0: print connectionMethod + u' : URLError'
        except MemoryError:
            if debugLevel > 0: print connectionMethod + u' : MemoryError'
        except requests.exceptions.HTTPError:
            if debugLevel > 0: print connectionMethod + u' : HTTPError'
        except requests.exceptions.SSLError:
            if debugLevel > 0: print connectionMethod + u' : SSLError'
        except ssl.CertificateError:
            if debugLevel > 0: print connectionMethod + u' : CertificateError'

    connectionMethod = u"urllib2.urlopen(url.encode('utf8'))"
    try:
        htmlSource = urllib2.urlopen(url.encode('utf8')).read()
        if debugLevel > 0: print str(len(htmlSource))
        if htmlSource != str(''): return htmlSource
    except UnicodeEncodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
    except UnicodeDecodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
    except UnicodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeError'
    except httplib.BadStatusLine:
        if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
    except httplib.HTTPException:
        if debugLevel > 0: print connectionMethod + u' : HTTPException'
    except httplib.InvalidURL:
        if debugLevel > 0: print connectionMethod + u' : InvalidURL'
    except httplib.IncompleteRead:
        if debugLevel > 0: print connectionMethod + u' : IncompleteRead'
    except urllib2.HTTPError, e:
        if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
        connectionMethod = u'HTTPCookieProcessor'
        try:
            cj = cookielib.CookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
            urllib2.install_opener(opener)
            response = opener.open(url)
            htmlSource = response.read()
            if debugLevel > 0: print str(len(htmlSource))
            if htmlSource != str(''): return htmlSource
        except UnicodeEncodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
        except UnicodeDecodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
        except UnicodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeError'
        except httplib.BadStatusLine:
            if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
        except httplib.HTTPException:
            if debugLevel > 0: print connectionMethod + u' : HTTPException'
        except httplib.InvalidURL:
            if debugLevel > 0: print connectionMethod + u' : InvalidURL'
        except urllib2.HTTPError, e:
            if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
        except IOError as e:
            if debugLevel > 0: print connectionMethod + u' : I/O error({0}): {1}'.format(e.errno, e.strerror)
        except urllib2.URLError:
            if debugLevel > 0: print connectionMethod + u' : URLError'
        except MemoryError:
            if debugLevel > 0: print connectionMethod + u' : MemoryError'
        except requests.exceptions.HTTPError:
            if debugLevel > 0: print connectionMethod + u' : HTTPError'
        except requests.exceptions.SSLError:
            if debugLevel > 0: print connectionMethod + u' : SSLError'
        except ssl.CertificateError:
            if debugLevel > 0: print connectionMethod + u' : CertificateError'
    except IOError as e:
        if debugLevel > 0: print connectionMethod + u' : I/O error({0}): {1}'.format(e.errno, e.strerror)
    except urllib2.URLError:
        if debugLevel > 0: print connectionMethod + u' : URLError'
    except MemoryError:
        if debugLevel > 0: print connectionMethod + u' : MemoryError'
    except requests.exceptions.HTTPError:
        if debugLevel > 0: print connectionMethod + u' : HTTPError'
    except requests.exceptions.SSLError:
        if debugLevel > 0: print connectionMethod + u' : SSLError'
    except ssl.CertificateError:
        if debugLevel > 0: print connectionMethod + u' : CertificateError'
        
    connectionMethod = u'Request text/html'    
    try:
        req = urllib2.Request(url)
        req.add_header('Accept','text/html')
        res = urllib2.urlopen(req)
        htmlSource = res.read()
        if debugLevel > 0: print connectionMethod + u' : text/html ' + str(len(htmlSource))
        if htmlSource != str(''): return htmlSource
    except UnicodeEncodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
    except UnicodeDecodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
    except UnicodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeError'
    except httplib.BadStatusLine:
        if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
    except httplib.HTTPException:
        if debugLevel > 0: print connectionMethod + u' : HTTPException'
    except httplib.InvalidURL:
        if debugLevel > 0: print connectionMethod + u' : InvalidURL'
    except httplib.IncompleteRead:
        if debugLevel > 0: print connectionMethod + u' : IncompleteRead'
    except urllib2.HTTPError, e:
        if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
        connectionMethod = u'geturl()'
        try:
            resp = urllib2.urlopen(url)
            req = urllib2.Request(resp.geturl())
            res = urllib2.urlopen(req)
            htmlSource = res.read()
            if debugLevel > 0: print str(len(htmlSource))
            if htmlSource != str(''): return htmlSource
        except UnicodeEncodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
        except UnicodeDecodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
        except UnicodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeError'
        except httplib.BadStatusLine:
            if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
        except httplib.HTTPException:
            if debugLevel > 0: print connectionMethod + u' : HTTPException'
        except httplib.InvalidURL:
            if debugLevel > 0: print connectionMethod + u' : InvalidURL'
        except urllib2.HTTPError, e:
            if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
        except IOError as e:
            if debugLevel > 0: print connectionMethod + u' : I/O error({0}): {1}'.format(e.errno, e.strerror)
        except urllib2.URLError:
            if debugLevel > 0: print connectionMethod + u' : URLError'
        except MemoryError:
            if debugLevel > 0: print connectionMethod + u' : MemoryError'
        except requests.exceptions.HTTPError:
            if debugLevel > 0: print connectionMethod + u' : HTTPError'
        except requests.exceptions.SSLError:
            if debugLevel > 0: print connectionMethod + u' : SSLError'
        except ssl.CertificateError:
            if debugLevel > 0: print connectionMethod + u' : CertificateError'
    except IOError as e:
        if debugLevel > 0: print connectionMethod + u' : I/O error({0}): {1}'.format(e.errno, e.strerror)
    except urllib2.URLError:
        if debugLevel > 0: print connectionMethod + u' : URLError'
    except MemoryError:
        if debugLevel > 0: print connectionMethod + u' : MemoryError'
    except requests.exceptions.HTTPError:
        if debugLevel > 0: print connectionMethod + u' : HTTPError'
    except requests.exceptions.SSLError:
        if debugLevel > 0: print connectionMethod + u' : SSLError'
    except ssl.CertificateError:
        if debugLevel > 0: print connectionMethod + u' : CertificateError'

    connectionMethod = u'Request Mozilla/5.0'
    agent = 'Mozilla/5.0 (compatible; MSIE 5.5; Windows NT)'
    try:
        headers = { 'User-Agent' : agent }
        req = urllib2.Request(url, "", headers)
        req.add_header('Accept','text/html')
        res = urllib2.urlopen(req)
        htmlSource = res.read()
        if debugLevel > 0: print connectionMethod + u' : ' + agent + u' : ' + str(len(htmlSource))
        if htmlSource != str(''): return htmlSource
    except UnicodeEncodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
    except UnicodeDecodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
    except UnicodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeError'
    except httplib.BadStatusLine:
        if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
    except httplib.HTTPException:
        if debugLevel > 0: print connectionMethod + u' : HTTPException'
    except httplib.IncompleteRead:
        if debugLevel > 0: print connectionMethod + u' : IncompleteRead'
    except httplib.InvalidURL:
        if debugLevel > 0: print connectionMethod + u' : InvalidURL'
    except urllib2.HTTPError, e:
        if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
        if e.code == "404": return "404 error"
        if socket.gethostname() == u'PavilionDV6':
            connectionMethod = u'follow_all_redirects'    # fonctionne avec http://losangeles.broadwayworld.com/article/El_Capitan_Theatre_Presents_Disneys_Mars_Needs_Moms_311421_20110304
            try:
                r = requests.get(url)
                req = urllib2.Request(r.url)
                res = urllib2.urlopen(req)
                htmlSource = res.read()
                if debugLevel > 0: print str(len(htmlSource))
                if htmlSource != str(''): return htmlSource
            except UnicodeEncodeError:
                if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
            except UnicodeDecodeError:
                if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
            except UnicodeError:
                if debugLevel > 0: print connectionMethod + u' : UnicodeError'
                connectionMethod = u"Méthode url.encode('utf8')"
                try:
                    sock = urllib.urlopen(url.encode('utf8'))
                    htmlSource = sock.read()
                    sock.close()
                    if debugLevel > 0: print str(len(htmlSource))
                    if htmlSource != str(''): return htmlSource
                except UnicodeError:
                    if debugLevel > 0: print connectionMethod + u' : UnicodeError'
                except UnicodeEncodeError:
                    if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
                except UnicodeDecodeError:
                    if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
                except httplib.BadStatusLine:
                    if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
                except httplib.HTTPException:
                    if debugLevel > 0: print connectionMethod + u' : HTTPException'
                except httplib.InvalidURL:
                    if debugLevel > 0: print connectionMethod + u' : InvalidURL'
                except urllib2.HTTPError, e:
                    if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
                except IOError as e:
                    if debugLevel > 0: print connectionMethod + u' : I/O error({0}): {1}'.format(e.errno, e.strerror)
                except urllib2.URLError:
                    if debugLevel > 0: print connectionMethod + u' : URLError'
                except MemoryError:
                    if debugLevel > 0: print connectionMethod + u' : MemoryError'
                except requests.exceptions.HTTPError:
                    if debugLevel > 0: print connectionMethod + u' : HTTPError'
                except requests.exceptions.SSLError:
                    if debugLevel > 0: print connectionMethod + u' : SSLError'
                except ssl.CertificateError:
                    if debugLevel > 0: print connectionMethod + u' : CertificateError'
            except httplib.BadStatusLine:
                if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
            except httplib.HTTPException:
                if debugLevel > 0: print connectionMethod + u' : HTTPException'
            except httplib.InvalidURL:
                if debugLevel > 0: print connectionMethod + u' : InvalidURL'
            except urllib2.HTTPError, e:
                if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
            except urllib2.URLError:
                if debugLevel > 0: print connectionMethod + u' : URLError'    
            except requests.exceptions.TooManyRedirects:
                if debugLevel > 0: print connectionMethod + u' : TooManyRedirects'
            except IOError as e:
                if debugLevel > 0: print connectionMethod + u' : I/O error({0}): {1}'.format(e.errno, e.strerror)
            except requests.exceptions.ConnectionError:
                if debugLevel > 0: print connectionMethod + u' ConnectionError'
            except requests.exceptions.InvalidSchema:
                if debugLevel > 0: print connectionMethod + u' InvalidSchema'
            except MemoryError:
                if debugLevel > 0: print connectionMethod + u' : MemoryError'
            except requests.exceptions.HTTPError:
                if debugLevel > 0: print connectionMethod + u' : HTTPError'
            except requests.exceptions.SSLError:
                if debugLevel > 0: print connectionMethod + u' : SSLError'
            except ssl.CertificateError:
                if debugLevel > 0: print connectionMethod + u' : CertificateError'
    except IOError as e:
        if debugLevel > 0: print connectionMethod + u' : I/O error({0}): {1}'.format(e.errno, e.strerror)
    except urllib2.URLError:
        if debugLevel > 0: print connectionMethod + u' : URLError'
    except MemoryError:
        if debugLevel > 0: print connectionMethod + u' : MemoryError'
    except requests.exceptions.HTTPError:
        if debugLevel > 0: print connectionMethod + u' : HTTPError'
    except requests.exceptions.SSLError:
        if debugLevel > 0: print connectionMethod + u' : SSLError'
    except ssl.CertificateError:
        if debugLevel > 0: print connectionMethod + u' : CertificateError'

    connectionMethod = u'Request &_r=4&'
    agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    try:
        if url.find(u'_r=') == -1:
            if url.find(u'?') != -1:
                url = url + "&_r=4&"
            else:
                url = url + "?_r=4&"
        else:
            if url.find(u'?') != -1:
                url = url[0:url.find(u'_r=')-1] + "&_r=4&"
            else:
                url = url[0:url.find(u'_r=')-1] + "?_r=4&"
        headers = { 'User-Agent' : agent }
        req = urllib2.Request(url, "", headers)
        req.add_header('Accept','text/html')
        res = urllib2.urlopen(req)
        htmlSource = res.read()
        if debugLevel > 0: print str(len(htmlSource))
        if htmlSource != str(''): return htmlSource
    except UnicodeEncodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
    except UnicodeDecodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
    except UnicodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeError'
    except httplib.BadStatusLine:
        if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
    except httplib.HTTPException:
        if debugLevel > 0: print connectionMethod + u' : HTTPException'
    except httplib.InvalidURL:
        if debugLevel > 0: print connectionMethod + u' : InvalidURL'
    except httplib.IncompleteRead:
        if debugLevel > 0: print connectionMethod + u' : IncompleteRead'
    except urllib2.HTTPError, e:
        if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
        connectionMethod = u'HTTPRedirectHandler'
        try:
            opener = urllib2.build_opener(urllib2.HTTPRedirectHandler)
            request = opener.open(url)
            req = urllib2.Request(request.url)
            res = urllib2.urlopen(req)
            htmlSource = res.read()
            if debugLevel > 0: print str(len(htmlSource))
            if htmlSource != str(''): return htmlSource
        except UnicodeEncodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
        except UnicodeDecodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
        except UnicodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeError'
        except httplib.BadStatusLine:
            if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
        except httplib.HTTPException:
            if debugLevel > 0: print connectionMethod + u' : HTTPException'
        except httplib.InvalidURL:
            if debugLevel > 0: print connectionMethod + u' : InvalidURL'
        except urllib2.HTTPError, e:
            if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
        except IOError as e:
            if debugLevel > 0: print connectionMethod + u' : I/O error({0}): {1}'.format(e.errno, e.strerror)
        except urllib2.URLError:
            if debugLevel > 0: print connectionMethod + u' : URLError'
        except MemoryError:
            if debugLevel > 0: print connectionMethod + u' : MemoryError'
        except requests.exceptions.HTTPError:
            if debugLevel > 0: print connectionMethod + u' : HTTPError'
        except requests.exceptions.SSLError:
            if debugLevel > 0: print connectionMethod + u' : SSLError'
        except ssl.CertificateError:
            if debugLevel > 0: print connectionMethod + u' : CertificateError'        
    except IOError as e:
        if debugLevel > 0: print connectionMethod + u' : I/O error({0}): {1}'.format(e.errno, e.strerror)
    except urllib2.URLError:
        if debugLevel > 0: print connectionMethod + u' : URLError'
    except MemoryError:
        if debugLevel > 0: print connectionMethod + u' : MemoryError'
    except requests.exceptions.HTTPError:
        if debugLevel > 0: print connectionMethod + u' : HTTPError'
    except requests.exceptions.SSLError:
        if debugLevel > 0: print connectionMethod + u' : SSLError'
    except ssl.CertificateError:
        if debugLevel > 0: print connectionMethod + u' : CertificateError'

    connectionMethod = u'urlopen'    # fonctionne avec http://voxofilm.free.fr/vox_0/500_jours_ensemble.htm, et http://www.kurosawa-drawings.com/page/27
    try:
        res = urllib2.urlopen(url)
        htmlSource = res.read()
        if debugLevel > 0: print str(len(htmlSource))
        if htmlSource != str(''): return htmlSource
    except UnicodeEncodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
    except UnicodeDecodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
    except UnicodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeError'
    except httplib.BadStatusLine:
        if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
    except httplib.HTTPException:
        if debugLevel > 0: print connectionMethod + u' : HTTPException'
    except httplib.InvalidURL:
        if debugLevel > 0: print connectionMethod + u' : InvalidURL'
    except httplib.IncompleteRead:
        if debugLevel > 0: print connectionMethod + u' : IncompleteRead'
    except urllib2.HTTPError, e:
        if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
        if e.code == 401: return "ok"    # http://www.nature.com/nature/journal/v442/n7104/full/nature04945.html
    except IOError as e:
        if debugLevel > 0: print connectionMethod + u' : I/O error({0}): {1}'.format(e.errno, e.strerror)
    except urllib2.URLError:
        if debugLevel > 0: print connectionMethod + u' : URLError'
    except MemoryError:
        if debugLevel > 0: print connectionMethod + u' : MemoryError'
    except requests.exceptions.HTTPError:
        if debugLevel > 0: print connectionMethod + u' : HTTPError'
    except requests.exceptions.SSLError:
        if debugLevel > 0: print connectionMethod + u' : SSLError'
    except ssl.CertificateError:
        if debugLevel > 0: print connectionMethod + u' : CertificateError' 

    connectionMethod = u'urllib.urlopen'
    try:
        sock = urllib.urlopen(url)
        htmlSource = sock.read()
        sock.close()
        if debugLevel > 0: print str(len(htmlSource))
        if htmlSource != str(''): return htmlSource
    except httplib.BadStatusLine:
        if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
    except httplib.HTTPException:
        if debugLevel > 0: print connectionMethod + u' : HTTPException'
    except httplib.InvalidURL:
        if debugLevel > 0: print connectionMethod + u' : InvalidURL'
    except IOError as e:
        if debugLevel > 0: print connectionMethod + u' : I/O error'
    except urllib2.URLError, e:
        if debugLevel > 0: print connectionMethod + u' : URLError %s.' % e.code
    except urllib2.HTTPError, e:
        if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
    except UnicodeEncodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
    except UnicodeDecodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
    except httplib.IncompleteRead:
        if debugLevel > 0: print connectionMethod + u' : IncompleteRead'
    except MemoryError:
        if debugLevel > 0: print connectionMethod + u' : MemoryError'
    except requests.exceptions.HTTPError:
        if debugLevel > 0: print connectionMethod + u' : HTTPError'
    except requests.exceptions.SSLError:
        if debugLevel > 0: print connectionMethod + u' : SSLError'
    except ssl.CertificateError:
        if debugLevel > 0: print connectionMethod + u' : CertificateError'
    except UnicodeError:
        if debugLevel > 0: print connectionMethod + u' : UnicodeError'
        connectionMethod = u"Méthode url.encode('utf8')"
        try:
            sock = urllib.urlopen(url.encode('utf8'))
            htmlSource = sock.read()
            sock.close()
            if debugLevel > 0: print str(len(htmlSource))
            if htmlSource != str(''): return htmlSource
        except UnicodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeError'
        except UnicodeEncodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeEncodeError'
        except UnicodeDecodeError:
            if debugLevel > 0: print connectionMethod + u' : UnicodeDecodeError'
        except httplib.BadStatusLine:
            if debugLevel > 0: print connectionMethod + u' : BadStatusLine'
        except httplib.HTTPException:
            if debugLevel > 0: print connectionMethod + u' : HTTPException'
        except httplib.InvalidURL:
            if debugLevel > 0: print connectionMethod + u' : InvalidURL'
        except urllib2.HTTPError, e:
            if debugLevel > 0: print connectionMethod + u' : HTTPError %s.' % e.code
        except IOError as e:
            if debugLevel > 0: print connectionMethod + u' : I/O error({0}): {1}'.format(e.errno, e.strerror)
        except urllib2.URLError:
            if debugLevel > 0: print connectionMethod + u' : URLError'
        except MemoryError:
            if debugLevel > 0: print connectionMethod + u' : MemoryError'
        except requests.exceptions.HTTPError:
            if debugLevel > 0: print connectionMethod + u' : HTTPError'
        except requests.exceptions.SSLError:
            if debugLevel > 0: print connectionMethod + u' : SSLError'
        except ssl.CertificateError:
            if debugLevel > 0: print connectionMethod + u' : CertificateError'
    if debugLevel > 0: print connectionMethod + u' Fin du test d\'existance du site'
    return u''

def testURLPage(htmlSource, url, debugLevel = 0):
    isBrokenLink = False
    try:
        #if debugLevel > 1 and htmlSource != str('') and htmlSource is not None: raw_input (htmlSource[0:1000])
        if htmlSource is None:
            if debugLevel > 0: print url.encode(config.console_encoding, 'replace') + " none type"
            return True
        elif htmlSource == str('ok') or (htmlSource == str('') and (url.find(u'à') != -1 or url.find(u'é') != -1 or url.find(u'è') != -1 or url.find(u'ê') != -1 or url.find(u'ù') != -1)): # bug http://fr.wikipedia.org/w/index.php?title=Acad%C3%A9mie_fran%C3%A7aise&diff=prev&oldid=92572792
            return False
        elif htmlSource == str('ko') or htmlSource == str(''):
            if debugLevel > 0: print url.encode(config.console_encoding, 'replace') + " page vide"
            return True
        else:
            if debugLevel > 0: print u' Page non vide'
            # Recherche des erreurs
            for e in range(0,limiteE):
                if debugLevel > 1: print Erreur[e]
                if htmlSource.find(Erreur[e]) != -1 and not re.search("\n[^\n]*if[^\n]*" + Erreur[e], htmlSource):
                    if debugLevel > 1: print u'  Trouvé'
                    # Exceptions
                    if Erreur[e] == "404 Not Found" and url.find("audiofilemagazine.com") == -1:    # Exception avec popup formulaire en erreur
                        isBrokenLink = True
                        if debugLevel > 0: print url.encode(config.console_encoding, 'replace') + " : " + Erreur[e]
                        break
                    # Wikis : page vide à créer
                    if Erreur[e] == "Soit vous avez mal &#233;crit le titre" and url.find("wiki") != -1:
                        isBrokenLink = True
                        if debugLevel > 0: print url.encode(config.console_encoding, 'replace') + " : " + Erreur[e]
                        break
                    elif Erreur[e] == "Il n'y a pour l'instant aucun texte sur cette page." != -1 and htmlSource.find("wiki") != -1:
                        isBrokenLink = True
                        if debugLevel > 0: print url.encode(config.console_encoding, 'replace') + " : " + Erreur[e]
                        break
                    elif Erreur[e] == "There is currently no text in this page." != -1 and htmlSource.find("wiki") != -1:
                        isBrokenLink = True
                        if debugLevel > 0: print url.encode(config.console_encoding, 'replace') + " : " + Erreur[e]
                        break
                    # Sites particuliers
                    elif Erreur[e] == "The page you requested cannot be found" and url.find("restaurantnewsresource.com") == -1:    # bug avec http://www.restaurantnewsresource.com/article35143 (Landry_s_Restaurants_Opens_T_REX_Cafe_at_Downtown_Disney.html)
                        isBrokenLink = True
                        if debugLevel > 0: print url.encode(config.console_encoding, 'replace') + " : " + Erreur[e]
                        break
                    elif Erreur[e] == "Terme introuvable" != -1 and htmlSource.find("Site de l'ATILF") != -1:
                        isBrokenLink = True
                        if debugLevel > 0: print url.encode(config.console_encoding, 'replace') + " : " + Erreur[e]
                        break
                    elif Erreur[e] == "Cette forme est introuvable !" != -1 and htmlSource.find("Site de l'ATILF") != -1:
                        isBrokenLink = True
                        if debugLevel > 0: print url.encode(config.console_encoding, 'replace') + " : " + Erreur[e]
                        break
                    elif Erreur[e] == "Sorry, no matching records for query" != -1 and htmlSource.find("ATILF - CNRS") != -1:
                        isBrokenLink = True
                        if debugLevel > 0: print url.encode(config.console_encoding, 'replace') + " : " + Erreur[e]
                        break
                    else:
                        isBrokenLink = True
                        if debugLevel > 0: print url.encode(config.console_encoding, 'replace') + " : " + Erreur[e]
                        break

    except UnicodeError:
        if debugLevel > 0: print u'UnicodeError lors de la lecture'
        isBrokenLink = False
    except UnicodeEncodeError:
        if debugLevel > 0: print u'UnicodeEncodeError lors de la lecture'
        isBrokenLink = False
    except UnicodeDecodeError:
        if debugLevel > 0: print u'UnicodeDecodeError lors de la lecture'
        isBrokenLink = False
    except httplib.BadStatusLine:
        if debugLevel > 0: print u'BadStatusLine lors de la lecture'
    except httplib.HTTPException:
        if debugLevel > 0: print u'HTTPException'
        isBrokenLink = False
    except httplib.InvalidURL:
        if debugLevel > 0: print u'InvalidURL lors de la lecture'
        isBrokenLink = False
    except urllib2.HTTPError, e:
        if debugLevel > 0: print u'HTTPError %s.' % e.code +  u' lors de la lecture'
        isBrokenLink = False
    except IOError as e:
        if debugLevel > 0: print u'I/O error({0}): {1}'.format(e.errno, e.strerror) +  u' lors de la lecture'
        isBrokenLink = False
    except urllib2.URLError:
        if debugLevel > 0: print u'URLError lors de la lecture'
        isBrokenLink = False
    else:
        if debugLevel > 1: print u'Fin du test du contenu'
    return isBrokenLink


def getCurrentLinkTemplate(currentPage):
    # Extraction du modèle de lien en tenant compte des modèles inclus dedans
    currentPage2 = currentPage
    templateEndPosition = 0
    while currentPage2.find(u'{{') != -1 and currentPage2.find(u'{{') < currentPage2.find(u'}}'):
        templateEndPosition = templateEndPosition + currentPage.find(u'}}')+2
        currentPage2 = currentPage2[currentPage2.find(u'}}')+2:]
    templateEndPosition = templateEndPosition + currentPage2.find(u'}}')+2
    currentTemplate = currentPage[:templateEndPosition]

    if debugLevel > 1:
        print(u'  getCurrentLinkTemplate()')
        print(templateEndPosition)
        raw_input(currentTemplate.encode(config.console_encoding, 'replace'))

    return currentTemplate, templateEndPosition


def translateTemplateParameters(currentTemplate):
    for p in range(0, limiteP):
        # Faux-amis variables selon les modèles
        if debugLevel > 1: print oldParam[p].encode(config.console_encoding, 'replace')
        frName = newParam[p]

        if oldParam[p] == u'work':
            if (currentTemplate.find(u'rticle') != -1 and currentTemplate.find(u'rticle') < currentTemplate.find(u'|')) and currentTemplate.find(u'ériodique') == -1:
                frName = u'périodique'
            elif currentTemplate.find(u'ien web') != -1 and currentTemplate.find(u'ien web') < currentTemplate.find(u'|') and currentTemplate.find(u'|site=') == -1 and currentTemplate.find(u'|website=') == -1:
                frName = u'site'
            else:
                frName = u'série'
        elif oldParam[p] == u'publisher':
            if (currentTemplate.find(u'rticle') != -1 and currentTemplate.find(u'rticle') < currentTemplate.find(u'|')) and currentTemplate.find(u'ériodique') == -1 and currentTemplate.find(u'|work=') == -1:
                frName = u'périodique'
            else:
                frName = u'éditeur'
        elif oldParam[p] == u'agency':
            if (currentTemplate.find(u'rticle') != -1 and currentTemplate.find(u'rticle') < currentTemplate.find(u'|')) and currentTemplate.find(u'ériodique') == -1 and currentTemplate.find(u'|work=') == -1:
                frName = u'périodique'
            else:
                frName = u'auteur institutionnel'
        elif oldParam[p] == u'issue' and (currentTemplate.find(u'|numéro=') != -1 and currentTemplate.find(u'|numéro=') < currentTemplate.find(u'}}')):
            frName = u'date'
        elif oldParam[p] == u'en ligne le':
            if currentTemplate.find(u'archiveurl') == -1 and currentTemplate.find(u'archive url') == -1 and currentTemplate.find(u'archive-url') == -1:
                continue
            elif currentTemplate.find(u'archivedate') != -1 or currentTemplate.find(u'archive date') != -1 or currentTemplate.find(u'archive-date') != -1:
                continue
            elif debugLevel > 0: u' archiveurl ' + u' archivedate'

        regex = ur'(\| *)' + oldParam[p] + ur'( *=)'
        currentTemplate = re.sub(regex, ur'\1' + frName + ur'\2', currentTemplate)
        currentTemplate = currentTemplate.replace(u'|=',u'|')
        currentTemplate = currentTemplate.replace(u'| =',u'|')
        currentTemplate = currentTemplate.replace(u'|  =',u'|')
        currentTemplate = currentTemplate.replace(u'|}}',u'}}')
        currentTemplate = currentTemplate.replace(u'| }}',u'}}')
        if currentTemplate.find(u'{{') == -1:    # Sans modèle inclus
            currentTemplate = currentTemplate.replace(u'||',u'|')

    return currentTemplate


def translateLinkTemplates(currentPage):
    finalPage = u''
    for m in range(0, limiteL):
        # Formatage des anciens modèles
        currentPage = re.sub((u'(Modèle:)?[' + oldTemplate[m][:1] + ur'|' + oldTemplate[m][:1].upper() + ur']' + oldTemplate[m][1:]).replace(u' ', u'_') + ur' *\|', oldTemplate[m] + ur'|', currentPage)
        currentPage = re.sub((u'(Modèle:)?[' + oldTemplate[m][:1] + ur'|' + oldTemplate[m][:1].upper() + ur']' + oldTemplate[m][1:]).replace(u' ', u'  ') + ur' *\|', oldTemplate[m] + ur'|', currentPage)
        currentPage = re.sub((u'(Modèle:)?[' + oldTemplate[m][:1] + ur'|' + oldTemplate[m][:1].upper() + ur']' + oldTemplate[m][1:]) + ur' *\|', oldTemplate[m] + ur'|', currentPage)
        # Traitement de chaque modèle à traduire
        while re.search(u'{{[\n ]*' + oldTemplate[m] + u' *[\||\n]+', currentPage):
            if debugLevel > 1:
                print(u'Modèle n°' + str(m))
                print(currentPage[re.search(u'{{[\n ]*' + oldTemplate[m] + u' *[\||\n]', currentPage).end()-1:][:100].encode(config.console_encoding, 'replace'))
            finalPage = finalPage + currentPage[:re.search(u'{{[\n ]*' + oldTemplate[m] + u' *[\||\n]', currentPage).end()-1]
            currentPage = currentPage[re.search(u'{{[\n ]*' + oldTemplate[m] + u' *[\||\n]', currentPage).end()-1:]    
            # Identification du code langue existant dans le modèle
            languageCode = u''
            if finalPage.rfind(u'{{') != -1:
                PageDebut = finalPage[:finalPage.rfind(u'{{')]
                if PageDebut.rfind(u'{{') != -1 and PageDebut.rfind(u'}}') != -1 and (PageDebut[len(PageDebut)-2:] == u'}}' or PageDebut[len(PageDebut)-3:] == u'}} '):
                    languageCode = PageDebut[PageDebut.rfind(u'{{')+2:PageDebut.rfind(u'}}')]
                    if site.family in ['wikipedia', 'wiktionary']:
                        # Recherche de validité mais tous les codes ne sont pas encore sur les sites francophones
                        if languageCode.find('}}') != -1: languageCode = languageCode[:languageCode.find('}}')]
                        if debugLevel > 1: print u'Modèle:' + languageCode
                        page2 = Page(site, u'Modèle:' + languageCode)
                        try:
                            PageCode = page2.get()
                        except pywikibot.exceptions.NoPage:
                            print "NoPage l 425"
                            PageCode = u''
                        except pywikibot.exceptions.LockedPage: 
                            print "Locked l 428"
                            PageCode = u''
                        except pywikibot.exceptions.IsRedirectPage: 
                            PageCode = page2.get(get_redirect=True)
                        if debugLevel > 0: print(PageCode.encode(config.console_encoding, 'replace'))
                        if PageCode.find(u'Indication de langue') != -1:
                            if len(languageCode) == 2:    # or len(languageCode) == 3: if languageCode == u'pdf': |format=languageCode, absent de {{lien web}}
                                # Retrait du modèle de langue devenu inutile
                                finalPage = finalPage[:finalPage.rfind(u'{{' + languageCode + u'}}')] + finalPage[finalPage.rfind(u'{{' + languageCode + u'}}')+len(u'{{' + languageCode + u'}}'):]
            if languageCode == u'':
                if debugLevel > 0: print u' Code langue à remplacer une fois trouvé sur la page distante...'
                languageCode = 'None'
            # Ajout du code langue dans le modèle
            if debugLevel > 0: print u'Modèle préalable : ' + languageCode
            regex = ur'[^}]*lang(ue|uage)* *=[^}]*}}'
            if not re.search(regex, currentPage):
                currentPage = u'|langue=' + languageCode + currentPage
            elif re.search(regex, currentPage).end() > currentPage.find(u'}}')+2:
                currentPage = u'|langue=' + languageCode + currentPage
                
        currentPage = finalPage + currentPage
        finalPage = u''

    for m in range(0, limiteM):
        if debugLevel > 1: print(u' Traduction des noms du modèle ' + oldTemplate[m])
        currentPage = currentPage.replace(u'{{' + oldTemplate[m] + u' ', u'{{' + oldTemplate[m] + u'')
        currentPage = re.sub(ur'({{[\n ]*)[' + oldTemplate[m][:1] + ur'|' + oldTemplate[m][:1].upper() + ur']' + oldTemplate[m][1:len(oldTemplate[m])] + ur'( *[\||\n\t|}])', ur'\1' +  newTemplate[m] + ur'\2', currentPage)
        # Suppression des modèles vides
        regex = u'{{ *[' + newTemplate[m][:1] + ur'|' + newTemplate[m][:1].upper() + ur']' + newTemplate[m][1:len(newTemplate[m])] + ur' *}}'
        while re.search(regex, currentPage):
            currentPage = currentPage[:re.search(regex, currentPage).start()] + currentPage[re.search(regex, currentPage).end():]
        # Traduction des paramètres de chaque modèle de la page
        regex = u'{{ *[' + newTemplate[m][:1] + ur'|' + newTemplate[m][:1].upper() + ur']' + newTemplate[m][1:len(newTemplate[m])] + ur' *[\||\n]'
        while re.search(regex, currentPage):
            finalPage = finalPage + currentPage[:re.search(regex, currentPage).start()+2]
            currentPage = currentPage[re.search(regex, currentPage).start()+2:]
            currentTemplate, templateEndPosition = getCurrentLinkTemplate(currentPage)
            currentPage = translateTemplateParameters(currentTemplate) + currentPage[templateEndPosition:]

        currentPage = finalPage + currentPage
        finalPage = u''

    return currentPage


def translateDates(currentPage):
    if debugLevel > 1: print(u'  translateDates()')
    parametersLimit = 9
    ParamDate = range(1, parametersLimit +1)
    # Date parameters
    ParamDate[1] = u'date'
    ParamDate[2] = u'mois'
    ParamDate[3] = u'consulté le'
    ParamDate[4] = u'en ligne le'
    # Date templates
    ParamDate[5] = u'dts'
    ParamDate[6] = u'Dts'
    ParamDate[7] = u'date triable'
    ParamDate[8] = u'Date triable'

    for m in range(1, monthLine + 1):
        if debugLevel > 1:
            print u'Mois ' + str(m)
            print TradM[m][1]
        for p in range(1, parametersLimit):
            if debugLevel > 1: print u'Recherche de ' + ParamDate[p] + u' *=[ ,0-9]*' + TradM[m][1]
            if p > 4:
                currentPage = re.sub(ur'({{ *' + ParamDate[p] + ur'[^}]+)' + TradM[m][1] + ur'([^}]+}})', ur'\1' +  TradM[m][2] + ur'\2', currentPage)
                currentPage = re.sub(ur'({{ *' + ParamDate[p] + ur'[^}]+)(\|[ 0-9][ 0-9][ 0-9][ 0-9])\|' + TradM[m][2] + ur'(\|[ 0-9][ 0-9])}}', ur'\1\3|' +  TradM[m][2] + ur'\2}}', currentPage)
            else:
                currentPage = re.sub(ur'(\| *' + ParamDate[p] + ur' *=[ ,0-9]*)' + TradM[m][1] + ur'([ ,0-9]*\.? *[<|\||\n\t|}])', ur'\1' +  TradM[m][2] + ur'\2', currentPage)
                currentPage = re.sub(ur'(\| *' + ParamDate[p] + ur' *=[ ,0-9]*)' + TradM[m][1][:1].lower() + TradM[m][1][1:] + ur'([ ,0-9]*\.? *[<|\||\n\t|}])', ur'\1' +  TradM[m][2] + ur'\2', currentPage)
                
                # Ordre des dates : jj mois aaaa'
                if debugLevel > 1: print u'Recherche de ' + ParamDate[p] + u' *= *' + TradM[m][2] + u' *([0-9]+), '
                currentPage = re.sub(ur'(\| *' + ParamDate[p] + u' *= *)' + TradM[m][2] + ur' *([0-9]+), *([0-9]+)\.? *([<|\||\n\t|}])', ur'\1' + ur'\2' + ur' ' + TradM[m][2] + ur' ' + ur'\3' + ur'\4', currentPage)    # trim(u'\3') ne fonctionne pas
 
    return currentPage


def translateLanguages(currentPage):
    if debugLevel > 1: print(u'  translateLanguages()')
    for l in range(1, ligneL+1):
        if debugLevel > 1:
            print u'Langue ' + str(l)
            print TradL[l][1]
        currentPage = re.sub(ur'(\| *langue *= *)' + TradL[l][1] + ur'( *[<|\||\n\t|}])', ur'\1' +  TradL[l][2] + ur'\2', currentPage)

        # Rustine suite à un imprévu censé être réglé ci-dessus, mais qui touche presque 10 % des pages.
        currentPage = re.sub(ur'{{' + TradL[l][2] + ur'}}[ \n]*({{[Aa]rticle\|langue=' + TradL[l][2] + ur'\|)', ur'\1', currentPage)
        currentPage = re.sub(ur'{{' + TradL[l][2] + ur'}}[ \n]*({{[Ll]ien web\|langue=' + TradL[l][2] + ur'\|)', ur'\1', currentPage)
        currentPage = re.sub(ur'{{' + TradL[l][2] + ur'}}[ \n]*({{[Oo]uvrage\|langue=' + TradL[l][2] + ur'\|)', ur'\1', currentPage)
 
    return currentPage
