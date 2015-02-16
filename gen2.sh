#!/bin/bash

# Download the latest dump from the Wikivoyage server and transform it to an HTML guide.

wget http://dumps.wikimedia.org/enwikivoyage/ -O ./dump-dates.txt
LAST_DUMP_LINE=`cat ./dump-dates.txt | grep -v latest | grep href | tail -n 1`
LAST_DUMP_DATE=`echo $LAST_DUMP_LINE | sed -e "s/\/<\/a>.*//g" -e "s/.*>//g"`
echo "Last dump date: $LAST_DUMP_DATE"

# Check if already downloaded
if [ -f enwikivoyage-$LAST_DUMP_DATE-pages-articles.xml.bz2 ];
then
   echo "Already present. Continue with generation."
else
   echo "Not present yet. Downloading."
   wget http://dumps.wikimedia.org/enwikivoyage/$LAST_DUMP_DATE/enwikivoyage-$LAST_DUMP_DATE-pages-articles.xml.bz2
  # bunzip2 enwikivoyage-$LAST_DUMP_DATE-pages-articles.xml.bz2
fi

java -cp jsonpedia-full-1.2-SNAPSHOT.jar \
  com.machinelinking.cli.loader \
  conf/default.properties \
  enwikivoyage-$LAST_DUMP_DATE-pages-articles.xml.bz2

#java -cp jsonpedia-full-1.2-SNAPSHOT.jar com.machinelinking.cli.exporter \
#    --prefix http://en.wikivoyage.org \
#    --in enwikivoyage-$LAST_DUMP_DATE-pages-articles.xml.bz2 \
#    --out out.json --threads 1


echo "Done"
