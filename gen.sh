#!/bin/bash

# Download the latest dump from the Wikivoyage server and transform it to an HTML guide.

wget http://dumps.wikimedia.org/enwikivoyage/ -O ./dump-dates.txt
LAST_DUMP_LINE=`cat ./dump-dates.txt | grep -v latest | grep href | tail -n 1`
LAST_DUMP_DATE=`echo $LAST_DUMP_LINE | sed -e "s/\/<\/a>.*//g" -e "s/.*>//g"`
echo "Last dump date: $LAST_DUMP_DATE"

# Check if already downloaded
if [ -f enwikivoyage-$LAST_DUMP_DATE-pages-articles.xml ];
then
   echo "Already present. Continue with generation."
else
   echo "Not present yet. Downloading."
   wget http://dumps.wikimedia.org/enwikivoyage/$LAST_DUMP_DATE/enwikivoyage-$LAST_DUMP_DATE-pages-articles.xml.bz2
   bunzip2 enwikivoyage-$LAST_DUMP_DATE-pages-articles.xml.bz2
fi


rm -rf articles

mkdir articles

./generate-json.py enwikivoyage-$LAST_DUMP_DATE-pages-articles.xml

PRETTY_DATE=`echo $LAST_DUMP_DATE | sed 's/^\(.\{4\}\)/\1-/' | sed 's/^\(.\{7\}\)/\1-/'`
rm -rf wikivoyage-dump_$PRETTY_DATE
mkdir wikivoyage-dump_$PRETTY_DATE
mv articles wikivoyage-dump_$PRETTY_DATE/
ZIPNAME="wikivoyage-dump_$PRETTY_DATE.zip"
zip -r $ZIPNAME wikivoyage-dump_$PRETTY_DATE/

echo "Done: $ZIPNAME"
