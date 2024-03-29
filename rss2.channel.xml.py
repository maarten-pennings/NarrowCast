#!/usr/bin/python3

# rss2.channel.xml.py - Script to bridge an rss feed (eg https://www.nrc.nl/rss) - it is just a copy to work around CORS
# 2019 may 27  v2  Maarten Pennings  Improved xml_text
# 2019 may 23  v1  Maarten Pennings  Redesign of older variant (rss.channel.xml.py)
version = "v2"


# To merge Python into Apache on Ubuntu:
#   sudo apt install apache2 libapache2-mod-wsgi-py3  # for python3

# Create a python scipt (e.g. rss2.channel.xml.py) and assign rights
#   sudo chown maarten:www-data rss2.channel.xml.py
#   sudo chmod 755 rss2.channel.xml.py

# Map python script 'rss2.channel.xml.py' to url 'rss/rss2.channel.xml'
#   Edit configuration file    
#     sudo vi /etc/apache2/sites-available/000-default.conf
#   and add the line in the section <VirtualHost *:80>
#     WSGIScriptAlias /rss/rss2.channel.xml /var/www/html/rss/rss2.channel.xml.py

# Then, enable mod-wsgi configuration and restart Apache service with the following command:
#   sudo a2enconf wsgi
#   sudo systemctl restart apache2

# To check errors in script look at the log
#   less /var/log/apache2/error.log


import sys
import ntpath
import requests
import xml.dom.minidom
from xml.sax.saxutils import escape


# Get the text string from a DOM element (safely)
def xml_text(node):
    if node==None: return ""
    result= ""
    if hasattr(node, 'tagName') and node.tagName=="description" and len(node.childNodes)==1 and hasattr(node.childNodes[0], 'tagName') and node.childNodes[0].tagName=="p": node= node.childNodes[0] # Telegraaf adds <p> around description
    for child in node.childNodes:
      if not hasattr(child, 'data'): continue
      s= child.data.strip() # Get rid of pre or post whitespace
      if s[:3]=='<p>' and s[-4:]=='</p>':  s= s.replace('<p>','').replace('</p>','') # Some site surround description with <p>..</p>. Remove it. 
      if result!="" and s!="": s+= " " # If multiple non-empty children, add separating space
      result+= escape(s) # escape xml char (& -> &amp;)
    return result


def parse(rssin):
    global log
    # Step 1: Parse meta part (from the header)
    # Convert string to xml dom
    dom= xml.dom.minidom.parseString(rssin)
    # Get root tag <rss>
    rss= dom.getElementsByTagName('rss')
    if len(rss)!=1: raise Exception('xml file does not have <rss> as root')
    # Get rss child tag <channel>
    channels= rss[0].getElementsByTagName('channel')
    if len(channels)!=1: raise Exception('xml file does not have <channel> in <rss>')
    # Get channel child tag <title> 
    titles= channels[0].getElementsByTagName('title')
    if len(titles)<1 or titles[0].parentNode!=channels[0]: raise Exception('xml file does not have <title> in <channel> in <rss>')
    # Set meta
    chtitle= xml_text(titles[0])
    chtitle=  chtitle[0].upper() + chtitle[1:] # enforce inital cap - should we do that?
    meta= ( chtitle, 'other meta vars could go here' )
    # Step 2: Parse items
    # Init triples
    triples= []
    # Get <item> tags from <channel>
    items= channels[0].getElementsByTagName('item')
    if len(items)<1: raise Exception('xml file does not have <item>s in <channel> in <rss>')
    ix = 0
    for item in items:
      # Get <title> from <item>
      itemtitle= item.getElementsByTagName('title')
      if len(itemtitle)!=1: raise Exception('xml file: <item> '+str(ix)+' should have 1 title')
      log+= f'item{ix}: "{xml_text(itemtitle[0])}"\r\n'
      # Get <description> from <item>
      itemdescription= item.getElementsByTagName('description')
      if len(itemdescription)!=1: raise Exception('xml file: <item> '+str(ix)+' should have 1 description')
      # Get <enclosure> or <media:content> (and item url) from <item>
      itemenclosure= item.getElementsByTagName('enclosure')
      if len(itemenclosure)==0: itemenclosure= item.getElementsByTagName('media:content')
      if len(itemenclosure)!=1: continue
      itemurl= itemenclosure[0].getAttribute('url')
      itemurl= itemurl.replace('%25','%')
      if itemurl.endswith('.mp4'): continue
      # NU.nl trick to have better pictures (enlarged)
      pos= itemurl.find('media.nu.nl')
      if pos>=0: pos= itemurl.find('sqr256.jpg') 
      if pos>=0: itemurl= itemurl[:pos] + 'sqr512.jpg' + itemurl[pos+10:]
      # Append triple
      triples.append( (xml_text(itemtitle[0]), xml_text(itemdescription[0]), escape(itemurl) ) )
      ix= ix+1
    # Step 3: Return results
    return (meta,triples)


def unparse(meta,triples):
  s1= '<?xml version="1.0" encoding="utf-8"?>\r\n'\
      '<rss>\r\n'\
      '  <channel>\r\n'\
      '    <title>%s</title>\r\n'\
      '    <editor>Generated by %s %s</editor>\r\n'\
      '\r\n' % (meta[0], ntpath.basename(__file__), version)
  s2= ''
  for triple in triples:
    s2+='    <item>\r\n'\
        '      <title>%s</title>\r\n'\
        '      <description>%s</description>\r\n'\
        '      <enclosure url="%s"/>\r\n'\
        '    </item>\r\n'\
        '\r\n' % triple
  s3= '  </channel>\r\n'\
      '</rss>\r\n'
  return s1+s2+s3
    
    
def application(environ, start_response):
  global log
  log= 'SYNTAX : rss2.channel.xml?<url>\r\nexample: http://192.168.1.1/rss2.channel.xml?https://www.nrc.nl/rss\r\n\r\n'
  try:
    # Get the arguments
    args= environ.get('QUERY_STRING')
    log+= 'arg    : "%s"\r\n' % args
    if args=='': raise Exception('&<url> argument missing')
    # Get first arg only, it is the url
    url= args+'&'
    pos= url.find('&')
    url= url[:pos] 
    log+= 'url    : "%s"\r\n' % url
    # Load remote rss feed
    resp= requests.get(url)
    resp.encoding = resp.apparent_encoding
    rssin= resp.text
    log+= 'rssin  : "%s" ...\r\n' % rssin[0:500]
    # Parse rss feed
    (meta,triples)= parse(rssin)
    log+= 'meta   : "%s"\r\n' % meta[0] 
    log+= 'triple0: "%s", "%s", "%s"\r\n' % triples[0] 
    # Create rss to output
    rssout= unparse(meta,triples)
    log+= 'rssout : "%s" ...\r\n' % rssout[0:1000]
    # Send to webserver
    if False: raise Exception('Aborted for testing') # Change False to True for testing
    start_response('200 OK',[('Content-type','text/xml')])
    return [ rssout.encode() ]
  except Exception as x:
    log+='\r\nERROR  : %s\r\n' % str(x)
    start_response('404 ERROR',[('Content-type','text/plain')])
    return [ log.encode('utf-8') ]


