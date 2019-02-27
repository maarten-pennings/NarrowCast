# xkcd.channel.xml.py - Script to convert XKCD rss feed to NarrowCast rss feed (with only one item)
# 2019 feb 19  v1  Maarten Pennings  Created


# To merge Python into Apache on Ubuntu:
#   https://www.howtoforge.com/tutorial/how-to-run-python-scripts-with-apache-and-mod_wsgi-on-ubuntu-18-04/

# Create a python scipt (e.g. xkcd.channel.py) and assign rights
#   sudo chown maarten:www-data xkcd.channel.xml.py
#   sudo chmod 755 xkcd.channel.xml.py

# Map python script 'xkcd.channel.xml.py' to url 'rss/xkcd.channel.xml'
#   Edit configuration file    
#     sudo vi /etc/apache2/conf-available/wsgi.conf
#   and add the mapping by adding:
#     WSGIScriptAlias /rss/xkcd.channel.xml /var/www/html/rss/xkcd.channel.xml.py

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


# Parse the XKCD rss feed and return the first item in a tuple (title, desc, src)
# Returns None on parsing error
def parse(page):
    # Parse the page to get the first item
    dom1= minidom.parseString(page)
    items= dom1.getElementsByTagName('item')
    if len(items)<1: return None
    # Get title and description
    titles= items[0].getElementsByTagName('title')
    if len(titles)<1: return None
    title= text(titles[0])
    descriptions= items[0].getElementsByTagName('description')
    if len(descriptions)<1: return None
    description= text(descriptions[0])
    # Switch to parsing the html in description
    if description[0]!="<": return None
    if description[-1]!=">": return None
    dom2= minidom.parseString(description)
    imgs= dom2.getElementsByTagName("img")
    if len(imgs)<1: return None
    src= imgs[0].getAttribute("src")
    desc= imgs[0].getAttribute("title")
    return (title, desc, src)

def application(environ, start_response):
    # input
    url= 'https://xkcd.com/rss.xml'
    req= urllib2.Request(url)
    resp= urllib2.urlopen(req)
    page= resp.read()
    # processing
    result= parse(page)
    if result==None: result=('Error',url, 'https://imgs.xkcd.com/comics/not_available.png')
    # output
    status = '200 OK'
    xml=  '<?xml version="1.0" encoding="utf-8"?>\r\n'\
          '<rss>\r\n'\
          '  <channel>\r\n'\
          '    <title>xkcd</title>\r\n'\
          '    <item>\r\n'\
          '      <enclosure url="{2}"/>\r\n'\
          '      <title>{0}</title>\r\n'\
          '      <description>{1}</description>\r\n'\
          '    </item>\r\n'\
          '  </channel>\r\n'\
          '</rss>\r\n'.format(result[0],result[1],result[2])
    response_header = [('Content-type','text/xml')]
    start_response(status,response_header)
    return [xml]

 
