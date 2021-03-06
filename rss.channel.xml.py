#!/usr/bin/python3

# rss.channel.xml.py - Script to bridge an rss feed (eg https://www.nu.nl/rss.html) - it is just a copy to work around CORS
# 2019 may 21  v2  Maarten Pennings  Converted to Python3
# 2019 feb 20  v1  Maarten Pennings  Created
version = "v2"


# To merge Python into Apache on Ubuntu:
#   sudo apt install apache2 libapache2-mod-wsgi-py3  # for python3

# Create a python scipt (e.g. rss.channel.xml.py) and assign rights
#   sudo chown maarten:www-data rss.channel.xml.py
#   sudo chmod 755 rss.channel.xml.py

# Map python script 'rss.channel.xml.py' to url 'rss/rss.channel.xml'
#   Edit configuration file    
#     sudo vi /etc/apache2/sites-available/000-default.conf
#   and add the line in the section <VirtualHost *:80>
#     WSGIScriptAlias /rss/rss.channel.xml /var/www/html/rss/rss.channel.xml.py

# Then, enable mod-wsgi configuration and restart Apache service with the following command:
#   sudo a2enconf wsgi
#   sudo systemctl restart apache2

# To check errors in script look at the log
#   less /var/log/apache2/error.log


import sys
import ntpath
import requests
import xml.dom.minidom


# Download a file, given its URL, and return it as a DOM (xml tree)
def xml_get(url):
    resp= requests.get(url)
    return xml.dom.minidom.parseString(resp.text)


# Get the text string from a DOM element (safely)
def xml_text(node):
    if node==None: return ""
    child= node.firstChild
    if child==None: return ""
    val= child.data
    if val==None: return ""
    return val


# Helper to create a DOM node for an rss <item>
def xml_createitem(xml,ix,simg,stitle,sdescription):
    item= xml.createElement('item'); 
    # item.setAttribute( 'ix', str(ix+1) )
    item.appendChild(xml.createComment(str(ix+1))); 
    enclosure= xml.createElement('enclosure'); item.appendChild(enclosure); 
    enclosure.setAttribute( 'url', simg )
    title= xml.createElement('title'); item.appendChild(title); 
    title.appendChild( xml.createTextNode(stitle) )
    description= xml.createElement('description'); item.appendChild(description); 
    description.appendChild( xml.createTextNode(sdescription) )
    return item


# Helper to find all elements with a given tagname, but only direct children, not all descendants
def xml_getChildrenByTagName(parent,tagname):
    list= []
    for node in parent.getElementsByTagName(tagname):
        if node.parentNode==parent: list.append(node)
    return list


# Helper to create an "empty" rss feed when there is an error
def xml_error(error):
    # Create empty xml_out 
    xml_out= xml.dom.minidom.Document(); 
    rss_out= xml_out.createElement('rss'); xml_out.appendChild(rss_out); 
    channel_out= xml_out.createElement('channel'); rss_out.appendChild(channel_out)
    # Create title
    chtitle_out= xml_out.createElement('title'); channel_out.appendChild(chtitle_out)
    chtitle_out.appendChild( xml_out.createTextNode( 'Error' ) )
    # Create editor
    cheditor_out= xml_out.createElement('editor'); channel_out.appendChild(cheditor_out)
    cheditor_out.appendChild( xml_out.createTextNode( 'Generated by '+ntpath.basename(__file__)+' '+version ) )
    # Create one item
    item_out= xml_createitem(xml_out, 0, '', 'Error', error ); channel_out.appendChild(item_out)
    return xml_out


# Convert the DOM tree passed in (xml_in) to the same tree, and return that.
# Some attributes and tags are dropped (not needed for the NarrowCast interpreter).
# The only crucial feature at this moment is sub-setting the number of items.
def xml_convert(xml_in):
    # Create empty xml_out 
    xml_out= xml.dom.minidom.Document(); 
    rss_out= xml_out.createElement('rss'); xml_out.appendChild(rss_out); 
    channel_out= xml_out.createElement('channel'); rss_out.appendChild(channel_out)
    # Check xml_in
    rss_in= xml_in.getElementsByTagName('rss')
    if len(rss_in)!=1: item_out= xml_createitem(xml_out,'','Error','xml file does not have <rss> as root'); channel_out.appendChild(item_out); return xml_out
    channel_in= rss_in[0].getElementsByTagName('channel')
    if len(channel_in)!=1: item_out= xml_createitem(xml_out,'','Error','xml file does not have <channel> in <rss>'); channel_out.appendChild(item_out); return xml_out
    channeltitle_in= xml_getChildrenByTagName(channel_in[0],'title')
    if len(channeltitle_in)!=1: item_out= xml_createitem(xml_out,'','Error','xml file does not have <title> in <channel> in <rss>'); channel_out.appendChild(item_out); return xml_out
    # Copy: title
    chtitle_out= xml_out.createElement('title'); channel_out.appendChild(chtitle_out)
    chtitle_out.appendChild( xml_out.createTextNode( xml_text(channeltitle_in[0]) ) )
    # Create editor
    cheditor_out= xml_out.createElement('editor'); channel_out.appendChild(cheditor_out)
    cheditor_out.appendChild( xml_out.createTextNode( 'Generated by '+ntpath.basename(__file__)+' '+version ) )
    # Copy: all items    
    items_in= xml_getChildrenByTagName(channel_in[0],'item')
    if len(items_in)<1: item_out= xml_createitem(xml_out,'','Error','xml file does not have <item>s in <channel> in <rss>'); channel_out.appendChild(item_out); return xml_out
    ix = 0
    for item_in in items_in:
        itemenclosure_in= xml_getChildrenByTagName(item_in,'enclosure')
        if len(itemenclosure_in)!=1: item_out= xml_createitem(xml_out,'','Error','xml file: <item> '+str(ix)+' should have 1 enclosure'); channel_out.appendChild(item_out); return xml_out
        itemtitle_in= xml_getChildrenByTagName(item_in,'title')
        if len(itemtitle_in)!=1: item_out= xml_createitem(xml_out,'','Error','xml file: <item> '+str(ix)+' should have 1 title'); channel_out.appendChild(item_out); return xml_out
        itemdescription_in= xml_getChildrenByTagName(item_in,'description')
        if len(itemdescription_in)!=1: item_out= xml_createitem(xml_out,'','Error','xml file: <item> '+str(ix)+' should have 1 description'); channel_out.appendChild(item_out); return xml_out
        item_out= xml_createitem(xml_out, ix, itemenclosure_in[0].getAttribute('url'), xml_text(itemtitle_in[0]), xml_text(itemdescription_in[0]) ); channel_out.appendChild(item_out)
        ix= ix+1
    return xml_out


# Returns tuple (error,url), where url is parsed from the URL
#     ?http://www.nu.nl/rss/Algemeen
# If all ok, error==None, otherwise error is a string describing what is wrong
def url_parse(environ):
    url= environ.get('QUERY_STRING')
    if url==None or url=="": 
      return ('Add rss-url to URL, e.g append   ?http://www.nu.nl/rss/Algemeen',None)
    else:
      # The next two lines strip any extra arguments - this is a hack, narrowcast addes a nounce and nu.nl can't handle that
      pos= url.find('&')
      if pos>=0: url= url[:pos] 
    return (None,url)

        
def application(environ, start_response):
    (error,url)= url_parse(environ)
    if error==None: 
        xml_in= xml_get(url)
        xml_out= xml_convert(xml_in)
    else:
        xml_out= xml_error(error)
    start_response('200 OK',[('Content-type','text/xml')])
    xml= xml_out.toprettyxml(indent='  ', newl="\r\n", encoding='utf-8') 
    return [ xml ] 


if __name__ == "__main__":
    url= 'http://www.nu.nl/rss/Algemeen'
    xml_in= xml_get(url)
    xml_out= xml_convert(xml_in)
    xml= xml_out.toprettyxml(indent='  ', newl="\r\n", encoding='utf-8') 
    print( xml )
    
