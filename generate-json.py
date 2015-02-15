#!/usr/bin/env python
# coding=utf-8

# Import useful libraries.
import os
import re
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from urllib import urlencode

## Settings
# Path to the input file:
databaseDump = sys.argv[1] #'enwikivoyage-20130101-pages-articles.xml'
print 'Using data from ' + databaseDump
outputDirectory = 'articles'
minimization = True

def urlencode_string(target):
    return urlencode({'':target})[1:]

re_redirect = re.compile('#REDIRECT', re.I) # Regular expression to detect REDIRECT
def is_redirect(wikicode):
    #print wikicode
    #print bool(re_redirect.match(wikicode))
    return re_redirect.match(wikicode)

# Some operating systems don't like 20000 files in the same directory, or filenames with exotic characters.
# This method builds a file path for this article that looks like '38/16720965.json'
# That means files will be distributed between 100 directories.
# Even though overall collision probability is 1/500k, a future enhancement could be to check for collisions.
def hashName(articleName):
    hashvalue = '%d' % abs(hash(articleName))
    directory = hashvalue[:2]
    file = hashvalue[2:]
    if not os.path.isdir('%s/%s' % (outputDirectory, directory)):
        os.mkdir('%s/%s' % (outputDirectory, directory))
    return directory + '/' + file + '.json'

# This class represents a Wikitravel article, parses it and processes its content.
class Article(object):
    def __init__ (self, wikicode, articleName):
        self.wikicode = wikicode
        self.articleName = articleName

    # Parse the wikicode and write this article as an json object.
    def saveJson(self):
        print articleName
        outputFile = open('%s/%s' % (outputDirectory,hashName(self.articleName)), 'w')
        outputFile.write('{ "title":"%s"' % self.articleName)

        # Breadcrumb
        cursor = articleName
        breadcrumb = []
        while(cursor in isPartOfs):
            isPartOf = isPartOfs[cursor]
            breadcrumb.append(isPartOf)
            if len(breadcrumb) > 100:
                print "IsPartOf circular reference detected: " + '←'.join(breadcrumb)
                break
            cursor = isPartOf
        if len(breadcrumb) > 0:
            outputFile.write(', "isPartOf":[')
            buffer = "{}"
            for cursor in breadcrumb:
                # print 'buffer: ' + buffer
                # print 'hash:' + hashName(cursor)
                # print 'cur: ' + cursor
                buffer = '{ "id":"' + hashName(cursor) + '", "name":"' + cursor + '" },' + buffer
            outputFile.write(buffer)
            outputFile.write('], ')

        body = ""
        menuItems = [] # Contains internal links to History, See, Eat, etc

        lastLineWasBlank = True
        restOfWikicode = self.wikicode
        while 1:
            # Read one line from the article.
            if len(restOfWikicode)==0: break
            split = restOfWikicode.partition('\n')
            line = '" + split[0] + '"'
            restOfWikicode = split[2]

            # Image and interwiki links (ignored).
            if re.compile('^\[\[[^\]]*:').match(line):
                continue

            # Region template (only display region wikilink and description).
            if re.compile('^\s*region[0-9]*color.*\|\s*$').match(line): #Ignore region color
                continue
            if re.compile('^\s*region[0-9]*items.*\|\s*$').match(line): #Ignore region items
                continue
            if re.compile('^\s*region[0-9]*name=\[\[[^\]]*\]\]\s*\|\s*$').match(line): # Leave only the wikilink, which will be processed afterwards.
                line = re.compile('^\s*region[0-9]*name=').sub('', line)
                line = re.compile('\s*\|\s*$').sub('', line)
            if re.compile('^\s*region[0-9]*description.*\|\s*$').match(line): # Leave only description.
                line = re.compile('^\s*region[0-9]*description=').sub(' ', line)
                line = re.compile(' \|').sub('', line)

            # Template (just print lines content).
            if re.compile('^\{\{').match(line):
                continue
            if re.compile('^\|').match(line):
                line=re.compile('^\|[^=]*=').sub('',line)
            if re.compile('^\}\}').match(line):
                continue

            # Comment (ignored)
            line = re.compile('<![^<>]*>').sub('', line) # does not seem to work
            if re.compile('^<!--').match(line): # does not seem to work
                continue

            # Blank line.
            if re.compile('^\s*$').match(line):
               if lastLineWasBlank:
                   continue
               else:
                   #end of section
                   line = '],'
                   lastLineWasBlank = True
            else:
               lastLineWasBlank = False

            # Header.
            #h5
            if re.compile('^\s*=====.*=====\s*$').match(line):
                line = re.compile('^(\s*=====\s*)').sub('"',line)
                line = re.compile('(\s*=====\s*)$').sub('":[',line)
            #h4
            if re.compile('^\s*====.*====\s*$').match(line):
                line = re.compile('^(\s*====\s*)').sub('"',line)
                line = re.compile('(\s*====\s*)$').sub('":[',line)
            #h3
            if re.compile('^\s*===.*===\s*$').match(line):
                line = re.compile('^(\s*===\s*)').sub('"',line)
                line = re.compile('(\s*===\s*)$').sub('":[',line)
            #h2
            if re.compile('^\s*==.*==\s*$').match(line):
                line = re.compile('^(\s*==\s*)').sub('"',line)
                line = re.compile('(\s*==\s*)$').sub('":[',line)

            # List item.
            if re.compile('^\*').match(line):
                line = re.compile('^(\*)').sub('"* ',line)
                line = line+'",'

            # Wikilinks.
            if re.compile('.*\]\].*').match(line):
                # Contains at least one wikilink. Let's split the line and process one wikilink at a time.
                restOfLine = line
                line = ""
                while 1:
                    # Split one portion from the line.
                    if len(restOfLine)==0: break
                    split = restOfLine.partition(']]')
                    portion = split[0]
                    restOfLine = split[2]
                    # Process this portion
                    #print "parsing, portion:"+portion
                    split = portion.partition('[[')
                    text = split[0]
                    wikilink = split[2]
                    line = line+text
                    # Parse the inside of the wikilink
                    target = wikilink
                    label = wikilink
                    if '|' in wikilink:
                        split = wikilink.partition("|")
                        target = split[0].strip()
                        label = split[2].strip()
                    # Create link only if the article exists.
                    target = redirects.get(target, target) # Redirected target, or if inexistent the target itself
                    
                    if label: # Ignore if label is empty
                        if target in articleNames:
                            line += '{"id":"' + hashName(target) + '", "label":"' + label + '"},'
                        else:
                            # Don't create a link, because it would be a broken link.
                            line += '"' + label + '",'

            # External links.
            # TODO
            if re.compile('.*\].*').match(line):
                # Contains at least one wikilink. Let's split the line and process one wikilink at a time.
                restOfLine = line
                line = ""
                while 1:
                    # Split one portion from the line.
                    if len(restOfLine)==0: break
                    split = restOfLine.partition(']')
                    portion = split[0]
                    restOfLine = split[2]
                    # Process this portion
                    split = portion.partition('[')
                    text = split[0]
                    extlink = split[2]
                    line = line+text
                    # Parse the inside of the wikilink
                    target = extlink
                    label = ""
                    if " " in extlink:
                        split = extlink.partition(" ")
                        target = split[0].strip()
                        label = split[2].strip()
                    if extlink:
                        line += '{"id":"' + target + '", "label":"' + label + '"},'

            # Old-style listing.
            if re.compile('^<li>\s*(<|&lt;)(see|do|buy|eat|drink|sleep).*(<|&gt;)/.*').match(line):
                # Opening tag containing interesting attributes.
                line = re.compile('^<li>\s*(<|&lt;)(see|do|buy|eat|drink|sleep)[^\s]* [^\s]*="').sub('<li>',line)
                line = re.compile('" [^\s]*="[^"]').sub('. ', line)
                line = re.compile('" [^\s]*="').sub('', line)
                line = re.compile('"\s*(>|&gt;)').sub('. ', line)
                # Closing tag.
                line = re.compile('</.*>').sub('', line)
                line = re.compile('&lt;/.*&gt;').sub('', line)

            # New-style listing.
            # Coordinates
            if re.compile('.*lat=[-0-9][^ ]* \\| long=[-0-9].*').match(line):
                coords = re.search('.*lat=([^ ]*) \\| long=([^ ]*).*', line, re.I | re.U)
                lat = coords.group(1)
                lon = coords.group(2)
                line = line + '{ "geo":[' + lat + ',' + lon + ']}'
                
            # TODO: Rest of new listing. Difficult because multi-line

            # Bold: remove.
            line=re.compile("'''").sub("", line)

            # Italic: remove.
            line=re.compile("''").sub("", line)

            if minimization:
                line = re.compile('\s+').sub(' ', line)
            body += line + ', \n'
            # if not minimization:
            #     body += '\n'


        outputFile.write(body)
        outputFile.write('}')
# End of Article class

# Main


# Create the directory where HTML files will be written.
if not os.path.isdir(outputDirectory):
    os.mkdir(outputDirectory)

print "### Build list of articles and map of redirects"
redirects = {}
articleNames = []
isPartOfs = {}
redirect = 0
isPartOf = 0
for line in open(databaseDump):
    if line.startswith("    <title>"):
        articleName = line.partition('>')[2].partition('<')[0]
    if line.startswith("    <redirect"):
        redirect = 1
        target = line.partition('"')[2].partition('"')[0].partition('#')[0]
    if line.startswith("{{IsPartOf|") or line.startswith("{{isPartOf|"):
        isPartOf = line[11:].partition('}')[0]
        isPartOf = isPartOf.replace("_", " ")
    if line.startswith("{{IsIn|") or line.startswith("{{isIn|"):
        isPartOf = line[7:].partition('}')[0]
        isPartOf = isPartOf.replace("_", " ")
    if line.startswith("  </page>"):
        if(redirect):
            #print "New redirect: " + articleName + " to " + target
            redirects[articleName] = target
        else:
            #print "New article: " + articleName
            articleNames.append(articleName)
        if(isPartOf != 0):
            isPartOfs[articleName] = isPartOf
        redirect = 0
        isPartOf = 0

print str(len(redirects)) + " redirects"
print str(len(articleNames)) + " articles"
print str(len(isPartOfs)) + " articles with breadcrumb"

#    if is_redirect_line(line):
#        # Get the wikilink of the REDIRECT
#        target = line.partition('[[')[2].partition(']]')[0].partition('#')[0]
#        # Substitute underscores with spaces
#        target = re.compile('_').sub(' ', target)
#        #print "Redirect from " + articleName + " to " + target
#        # Add to dictionary
#        redirects[articleName] = target
#    else:
#        articleNames.append(articleName)
#    if line.startswith("    <title>"):
#        articleName = line.partition('>')[2].partition('<')[0]

print "### Check for double-redirects"
for (name,target) in redirects.items():
    if target in redirects:
        print "# Double redirect detected, please fix: [[" + name + "]] > [[" + target + "]] > [[" + redirects[target] + "]]"

print "### Generate articles"
flag=0;skip=0
for line in open(databaseDump):
    if line.startswith("    <title>"):
        if "/Gpx" in line or ":" in line: # Skip GPS traces and articles such as Template: Title: Wikivoyage:
            skip=1
        else:
            articleName = re.compile('    <title>').sub('', line)
            articleName = re.compile('</title>.*', re.DOTALL).sub('', articleName)
    if line.startswith("  </page>"):
        flag=0
        if skip:
            skip=0
        else:
            wikicode = re.compile('.*preserve">', re.DOTALL).sub('', page)
            if not is_redirect(wikicode):
                wikicode = re.compile('      <sha1>.*', re.DOTALL).sub('', wikicode)
                article = Article(wikicode, articleName);
                article.saveJson();
    if line.startswith("  <page>"):
        flag=1
        page=""
    if flag and not line.startswith("  <page>"):
        page += line

