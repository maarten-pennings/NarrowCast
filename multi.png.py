#!/usr/bin/python3
# multi.py - Script to combine multiple images to one. For the moment hard wired to 3 knmi pictures
# 2019 jun 18  v1  Maarten Pennings  Created


import io
import requests
from PIL import Image


url1="https://cdn.knmi.nl/knmi/map/page/weer/actueel-weer/temperatuur.png"
url2="https://cdn.knmi.nl/knmi/map/page/weer/actueel-weer/windsnelheid.png" # 569x622
url3="https://cdn.knmi.nl/knmi/map/page/weer/actueel-weer/relvocht.png"


# Converts a list of urls to a list of images (raises exception when url get fails)
def load( urls ) :
  imgs= []
  for url in urls:
    resp= requests.get(url)
    if resp.status_code!=200: raise Exception('Image %s failed with status %d' % (url,resp.status_code) )
    img = Image.open(io.BytesIO(resp.content))
    imgs.append(img)
  return imgs


# Converts a list images to a single image (all horizontally with some spacing)
def combine(imgs):
  # Layout constants
  xmar= 32 # margin on both sides (horizontally)
  xsep= 32 # spacing between images (horizontally)
  ymar= 32 # margin on both sides (vertically)
  # Get sizes
  width= 0
  height= 0
  for img in imgs:
    height= max(height,img.height)
    if width>0: width+=xsep
    width+= img.width
  width= xmar+width+xmar
  height= ymar+height+ymar
  # Start drawing on image
  image = Image.new('RGBA', (width,height), 0x00FFFFFF ) # 100%transparent + white
  # Loop
  x= xmar
  y= ymar
  for img in imgs:
    image.paste(img,(x,y))
    x= x+img.width+xsep
  return image


def application(environ, start_response):
  log= 'SYNTAX : multi.png\r\nexample: http://192.168.1.1/multi.png\r\n\r\n'
  try:
    urls= [url1,url2,url3]
    log+= 'urls   : %s\r\n' % ' '.join(urls)
    imgs= load( urls )
    log+= 'images : %s\r\n' % 'loaded'
    image= combine( imgs )
    log+= 'images : %s\r\n' % 'combined'
    with io.BytesIO() as memfile:
      image.save(memfile, format="png")
      bytes= memfile.getvalue()
    log+= 'binary : %s\r\n' % 'done'
    if False: raise Exception('Aborted for testing') # Change False to True for testing
    start_response( '200 OK', [('Content-type','image/png')] )
    return [bytes]
  except Exception as x:
    log+='\r\nERROR  : %s\r\n' % str(x)
    start_response('404 ERROR',[('Content-type','text/plain')])
    return [ log.encode('utf-8') ]


