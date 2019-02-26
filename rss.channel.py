# Script to bridge an rss feed (eg https://www.nu.nl/rss.html) - it is just a copy to work around CORS
# 2019 feb 20  v1  Maarten Pennings  Created


# To merge Python into Apache on Ubuntu:
#   https://www.howtoforge.com/tutorial/how-to-run-python-scripts-with-apache-and-mod_wsgi-on-ubuntu-18-04/

# Create a python scipt (e.g. rss.channel.py) and assign rights
#   sudo chown maarten:www-data rss.channel.py
#   sudo chmod 755 rss.channel.py

# Map python script 'rss.channel.py' to url 'rss/rss.channel.xml'
#   Edit configuration file    
#     sudo vi /etc/apache2/conf-available/wsgi.conf
#   Add the mapping by adding:
#     WSGIScriptAlias /rss/rss.channel.xml /var/www/html/rss/rss.channel.py

# Then, enable mod-wsgi configuration and restart Apache service with the following command:
#   sudo a2enconf wsgi
#   sudo systemctl restart apache2


import sys
import urllib2
import xml.dom.minidom
import urlparse


# Download a file, given its URL, and return it as a DOM (xml tree)
def xml_get(url):
    req= urllib2.Request(url)
    resp= urllib2.urlopen(req)
    data= resp.read()
    return xml.dom.minidom.parseString(data)


# Get the text string from a DOM element (safely)
def xml_text(node):
    if node==None: return ""
    child= node.firstChild
    if child==None: return ""
    val= child.data
    if val==None: return ""
    return val


# Helper to create a DOM node for an rss <item>
def xml_createitem(xml,simg,stitle,sdescription):
    item= xml.createElement('item'); item.appendChild(xml.createTextNode('\r\n'))
    enclosure= xml.createElement('enclosure'); item.appendChild(enclosure); item.appendChild(xml.createTextNode('\r\n'))
    enclosure.setAttribute( 'url', simg )
    title= xml.createElement('title'); item.appendChild(title); item.appendChild(xml.createTextNode('\r\n'))
    title.appendChild( xml.createTextNode(stitle) )
    description= xml.createElement('description'); item.appendChild(description); item.appendChild(xml.createTextNode('\r\n'))
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
    channel_out.appendChild(xml_out.createTextNode('\r\n\r\n')); 
    # Create one item
    item_out= xml_createitem(xml_out, '', 'Error', error ); channel_out.appendChild(item_out)
    channel_out.appendChild(xml_out.createTextNode('\r\n'))
    channel_out.appendChild(xml_out.createTextNode('\r\n'))
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
    channel_out.appendChild(xml_out.createTextNode('\r\n\r\n')); 
    # Copy: all items    
    items_in= xml_getChildrenByTagName(channel_in[0],'item')
    if len(items_in)<1: item_out= xml_createitem(xml_out,'','Error','xml file does not have <item>s in <channel> in <rss>'); channel_out.appendChild(item_out); return xml_out
    ix = 0
    for item_in in items_in:
        channel_out.appendChild(xml_out.createComment(str(ix))); channel_out.appendChild(xml_out.createTextNode('\r\n'))
        itemenclosure_in= xml_getChildrenByTagName(item_in,'enclosure')
        if len(itemenclosure_in)!=1: item_out= xml_createitem(xml_out,'','Error','xml file: <item> '+str(ix)+' should have 1 enclosure'); channel_out.appendChild(item_out); return xml_out
        itemtitle_in= xml_getChildrenByTagName(item_in,'title')
        if len(itemtitle_in)!=1: item_out= xml_createitem(xml_out,'','Error','xml file: <item> '+str(ix)+' should have 1 title'); channel_out.appendChild(item_out); return xml_out
        itemdescription_in= xml_getChildrenByTagName(item_in,'description')
        if len(itemdescription_in)!=1: item_out= xml_createitem(xml_out,'','Error','xml file: <item> '+str(ix)+' should have 1 description'); channel_out.appendChild(item_out); return xml_out
        item_out= xml_createitem(xml_out,itemenclosure_in[0].getAttribute('url'), xml_text(itemtitle_in[0]), xml_text(itemdescription_in[0]) ); channel_out.appendChild(item_out)
        channel_out.appendChild(xml_out.createTextNode('\r\n'))
        channel_out.appendChild(xml_out.createTextNode('\r\n'))
        ix= ix+1
    return xml_out


# Returns tuple (error,src), where src is parsed from the URL
#     ?src=http://www.nu.nl/rss/Algemeen
# If all ok, error==None, otherwise error is a string describing what is wrong
def url_parse(environ):
    query_parms= urlparse.parse_qs( environ.get('QUERY_STRING') )
    # Get 'src' param
    src= query_parms.get('src')
    if src==None: return ('Add src= to URL, e.g    ?src=http://www.nu.nl/rss/Algemeen%26limit=4',None,None)
    s_src=src[0]
    return (None,s_src)

        
def application(environ, start_response):
    (error,src)= url_parse(environ)
    if error==None: 
        xml_in= xml_get( src )
        xml_out= xml_convert(xml_in)
    else:
        xml_out= xml_error(error)
    status = '200 OK'
    start_response('200 OK',[('Content-type','text/xml')])
    return [ xml_out.toxml().encode('utf-8') ]


if __name__ == "__main__":
    # Test - execute only if run as a script
    xml_in= xml_get('http://www.nu.nl/rss/Algemeen')
    xml_out= xml_convert(xml_in)
    a= xml_out.toxml()
    print( a.encode('utf-8') )
    
