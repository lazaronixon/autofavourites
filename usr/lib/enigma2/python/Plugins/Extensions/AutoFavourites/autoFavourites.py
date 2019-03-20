#!/usr/bin/python

import os
import sys
import glob
import re
import unicodedata
import urllib

#---------------------------------------------
lamedb = '/etc/enigma2/lamedb'
outdir = '/etc/enigma2'
rules  = '/etc/bouquetRules.cfg'
#---------------------------------------------

def removeoldfiles():
    userbouquets = glob.glob(outdir + '/userbouquet.*')
    for userbouquet in userbouquets:
        os.remove(userbouquet)

    bouquetindexes = glob.glob(outdir + '/bouquets.*')
    for bouquetindex in bouquetindexes:
        os.remove(bouquetindex)

def reload():
    f = urllib.urlopen('http://127.0.0.1/web/servicelistreload?mode=2')
    s = f.read()
    f.close()

def mkfavfilename(s):
    s = unicode(s.replace(' ', '').lower(), 'UTF-8')
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return 'userbouquet.' + s + '.tv'

def extractchannel(serviceid):
    servicesplit = serviceid.split(':')
    channel = {
        'channelname':   line,
        'channelcode':   servicesplit[0],
        'tpcode':        servicesplit[1],
        'code2':         servicesplit[2],
        'code3':         servicesplit[3],
        'channeltype':   servicesplit[4]
    }

    channel['channeltype'] = re.sub('^0+','',channel['channeltype']).upper()
    channel['channelcode'] = re.sub('^0+','',channel['channelcode']).upper()
    channel['code2'] = re.sub('^0+','',channel['code2']).upper()
    channel['tpcode'] = re.sub('^0+','',channel['tpcode']).upper()

    if (channel['channeltype'] == '25'):
        channel['channeltype'] = '19'

    return channel

def extractrule(rule):
    return rule.strip().split(':')

def genfavindex():
    favindexfile = open(outdir + '/bouquets.tv', 'w')
    favindexfile.write('#NAME User - bouquets (TV)\n')

    filerules = open(rules)
    for rule in filerules:
        favname, channellist = extractrule(rule)
        favfilename = mkfavfilename(favname)
        favindexfile.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet\n' % favfilename)

    favindexfile.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet\n')
    favindexfile.close()

    radioindexfile = open(outdir + '/bouquets.radio', 'w')
    radioindexfile.write('#NAME User - bouquets (RADIO)\n')
    radioindexfile.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.radio" ORDER BY bouquet\n')
    radioindexfile.close()

def writechannels(channels, favfile):
    channels = sorted(channels, key=lambda channel: channel['channelname'].lower())
    for channel in channels:
        favfile.write('#SERVICE 1:0:%(channeltype)s:%(channelcode)s:%(code2)s:1:%(tpcode)s:0:0:0:\n' % channel)

def isepgchannel(channel, tpcodes):
    istvchannel = channel['channeltype'] in ('1', '19')
    isuniquetp  = (not (channel['tpcode'] in tpcodes))
    return (istvchannel and isuniquetp)

def genfav():
    filerules = open(rules)
    for rule in filerules:
        favname, channellist = extractrule(rule)
        favfilename = mkfavfilename(favname)
        favfile = open(outdir + '/' + favfilename, 'w')
        favfile.write('#NAME %s\n' % favname)

        channels, tpcodes = [], []
        serviceid, servicesreading = None, False
        regexchannel = re.compile(channellist, re.IGNORECASE)
        regexid = re.compile('^.{4}:.{8}:.{4}')
        filelamedb = open(lamedb)

        for line in filelamedb:
            line = line.strip()

            if line == 'services':
                servicesreading = True
                continue
            if servicesreading and line == 'end':
                servicesreading = False
                continue
            if servicesreading:
                if line.startswith('p:'):
                    continue
                if regexid.match(line):
                    serviceid = line
                    continue
                if regexchannel.search(line):
                    channel = extractchannel(serviceid)
                    if (favname.lower() == 'epgrefresh'):
                        if isepgchannel(channel, tpcodes):
                            tpcodes.append(channel['tpcode'])
                            channels.append(channel)
                    else:
                        channels.append(channel)

        filelamedb.close()

        writechannels(channels, favfile)
        favfile.close()

def gendefaultfav():
    favtvallfile = open(outdir + '/userbouquet.favourites.tv', 'w')
    favtvallfile.write('#NAME Favourites (TV)\n')
    favtvallfile.close()

    favradioallfile = open(outdir + '/userbouquet.favourites.radio', 'w')
    favradioallfile.write('#NAME Favourites (Radio)\n')
    favradioallfile.close()

def log(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()

def main():
    log('Removing old files...\n')
    removeoldfiles()
    log('Generating favourites index...\n')
    genfavindex()
    log('Generating default favourites...\n')
    gendefaultfav()
    log('Generating favourites...\n')
    genfav()
    log('Reloading...\n')
    reload()

main()
