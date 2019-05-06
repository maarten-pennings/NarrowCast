#!/usr/bin/python3
# sp.py - Script to bridge to a sharepoint site (which requires login)
#         e.g. http://192.168.1.1/sp?http://sharepoint.company.com/pictures/banner.jpg
# 2019 may 06  v2  Maarten Pennings  Moved cfg.py
# 2019 may 03  v1  Maarten Pennings  Created


import requests
import requests_ntlm


# Import cfg.username, cfg.password, cfg.hostname, cfg.hostip
import sys; sys.path.append( "/var/www" ); import cfg


def application(environ, start_response):
  log= 'SYNTAX : sp?<url>\r\nexample: http://192.168.1.1/sp?http://sharepoint.company.com/pictures/banner.jpg\r\n\r\n'
  try:
    arg= environ.get('QUERY_STRING')
    log+= 'arg    : "%s"\r\n' % arg
    if arg=='': raise Exception('&<url> argument missing')
    url= arg.replace(cfg.hostname,cfg.hostip) # Hack because DNS is not working
    log+= 'url    : "%s"\r\n' % url
    session = requests.Session() 
    response = session.get(url, auth=requests_ntlm.HttpNtlmAuth(cfg.username,cfg.password), headers={'Host':cfg.hostname} ) # Hack because DNS is not working
    if response.status_code!=200: raise Exception('Remote site failed with status %d' % response.status_code)
    log+= 'status : "%d"\r\n' % response.status_code
    mime= response.headers['Content-Type']
    log+= 'mime   : "%s"\r\n' % mime
    if False: raise Exception('Aborted for testing') # Change False to True for testing
    start_response('200 OK',[('Content-type',mime)])
    return [ response.content ]
  except Exception as x:
    log+='\r\nERROR  : %s\r\n' % str(x)
    start_response('404 ERROR',[('Content-type','text/plain')])
    return [ log.encode('utf-8') ]

