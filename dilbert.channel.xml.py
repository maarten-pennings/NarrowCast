# dilbert.channel.xml.py - Script to convert dilbert webpage to a NarrowCast rss feed (with only one item)
# 2019 apr 15  v1  Maarten Pennings  Created (copied from xkcd.channel.xml.py)


# To merge Python into Apache on Ubuntu:
#   https://www.howtoforge.com/tutorial/how-to-run-python-scripts-with-apache-and-mod_wsgi-on-ubuntu-18-04/

# Create a python scipt (e.g. dilbert.channel.xml.py) and assign rights
#   sudo chown maarten:www-data dilbert.channel.xml.py
#   sudo chmod 755 dilbert.channel.xml.py

# Map python script 'dilbert.channel.xml.py' to url 'rss/dilbert.channel.xml'
#   Edit configuration file    
#     sudo vi /etc/apache2/conf-available/wsgi.conf
#   and add the mapping by adding:
#     WSGIScriptAlias /rss/dilbert.channel.xml /var/www/html/rss/dilbert.channel.xml.py

# Then, enable mod-wsgi configuration and restart Apache service with the following command:
#   sudo a2enconf wsgi
#   sudo systemctl restart apache2


import urllib2
from xml.dom import minidom
import sys


# Get the text string from an element
def text(elm):
    if elm==None: return ""
    child= elm.firstChild
    if child==None: return ""
    val= child.data
    if val==None: return ""
    return val


# Parse the dilbert rss feed and return the first item in a tuple (title, desc, imgurl).
# Returns None on parsing error.
def parse(page):
    title='Dilbert'
    # find the line with the image tag
    pos1= page.find('"img-responsive img-comic"')
    if pos1<0: return None
    pos2= page.find('>',pos1)
    if pos2<0: return None
    line= page[pos1:pos2]
    # Cut out the 'alt' -> 'desc'
    pos1= line.find('alt="')
    if pos1<0: return None
    pos2= line.find(' - Dilbert by Scott Adams"',pos1)
    if pos2<0: return None
    desc= line[pos1+5:pos2]
    # Cut out the 'src' -> 'imgurl'
    pos1= line.find('src="')
    if pos1<0: return None
    pos2= line.find('"',pos1+5)
    if pos2<0: return None
    imgurl= 'https:'+line[pos1+5:pos2]    
    return (title, desc, imgurl)

# Loads the dilbert rss feed, parses it and returns a triple (title, desc, imgurl).
# In case of errors, an "error triple" is returned.
def loadtriple():
    try:
        url= 'https://dilbert.com'
        req= urllib2.Request(url)
        resp= urllib2.urlopen(req)
        page= resp.read()
        triple= parse(page)
        if triple==None: triple=('Parse error',url, 'https://assets.amuniversal.com/583d3560af230132cfe8005056a9545d')
    except Exception as error:
        # print(error)
        triple=('Load error ',url, 'https://assets.amuniversal.com/583d3560af230132cfe8005056a9545d')
    return triple

# Converts a triple (title, desc, imgurl) to an rss (xml) string
def rss(triple):
    return '<?xml version="1.0" encoding="utf-8"?>\r\n'\
           '<rss>\r\n'\
           '  <channel>\r\n'\
           '    <title>dilbert</title>\r\n'\
           '    <item>\r\n'\
           '      <enclosure url="{2}"/>\r\n'\
           '      <title>{0}</title>\r\n'\
           '      <description>{1}</description>\r\n'\
           '    </item>\r\n'\
           '  </channel>\r\n'\
           '</rss>\r\n'.format(triple[0],triple[1],triple[2])
    
# The entry point of the webserver
def application(environ, start_response):
    status = '200 OK'
    xml= rss(loadtriple())
    response_header = [('Content-type','text/xml')]
    start_response(status,response_header)
    return [xml]

if __name__ == "__main__":
    print( rss(loadtriple()) )
 
