#!/usr/bin/python3

# thinwordofday.png.py - Script to display a nice word in nice font
# 2021 sep 9  v1  Cas van der Avoort  Copied from thinwords.png.py, credits to Maarten Pennings
version = "v1"


# To merge Python into Apache on Ubuntu:
#   sudo apt install apache2 libapache2-mod-wsgi-py3  # for python3

# Create a python script (e.g. wordsmith.png.py) and assign rights
#   sudo chown maarten:www-data wordsmith.png.py
#   sudo chmod 755 wordsmith.png.py

# Map python script 'wordsmith.png.py' to url 'rss/wordsmith.png'
#   Edit configuration file
#     sudo vi /etc/apache2/sites-available/000-default.conf
#   and add the line in the section <VirtualHost *:80>
#     WSGIScriptAlias /rss/wordsmith.png /var/www/html/rss/wordsmith.png.py

# Then, enable mod-wsgi configuration and restart Apache service with the following command:
#   sudo a2enconf wsgi
#   sudo systemctl restart apache2

# To check errors in script look at the log
#   less /var/log/apache2/error.log

# sudo python3 -m pip install xmltodict

import os
import io
import requests
import xmltodict
import json
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

# Drawing settings
div_color_amsgrey1=( 70, 85, 95)      # color code for ams dark grey
div_color_amsgrey2=(125,136,143)      # color code for ams medium grey
div_color_amsgrey3=(172,178,183)      # color code for ams light grey
div_color_amsgreen=( 65,171,  2)      # color code for ams green
div_color_amsblue =(  0,117,176)      # color code for ams blue

div_bgcol= 0                          # background color of picture (0=transparent, also eg "white")

div_txt_fontsize=240                  # font size for labels
div_txt_fontname="Kiona-Light.ttf"    # font name for labels
div_txt_fgcolor= div_color_amsgrey1   # foreground color white, preview on white troublesome

div_Y0=150                            # top margin
div_Y1=250                            # bottom margin
div_X0=50                             # left and right margin
div_sY= 0                             # line1/line2 extra spacing

div_url="https://wordsmith.org/awad/rss1.xml"


# Adds the path of this script to fonts\`filename` to make it an absolute path
def getFontPath(filename):
  global log
  folder = os.path.dirname(os.path.realpath(__file__))
  path = os.path.join(folder, os.path.join("fonts",filename))
  log+= f"font   : {path}\r\n"
  return path


# Converts
def generateimg(text1,text2) :
  global log
  # Render temp image to determine size
  img = Image.new("RGBA", (10,10), div_bgcol )
  draw = ImageDraw.Draw(img)
  font_text1 = ImageFont.truetype(getFontPath(div_txt_fontname), div_txt_fontsize)
  size1x,size1y= draw.textsize( text1, font=font_text1)
  size2x,size2y= draw.textsize( text2, font=font_text1)
  log+= f"size   : {size1x}x{size1y} and {size2x}x{size2y}\r\n"
  # String text2 is set in same font as text1, now scale to make same width as text1
  font_text2 = ImageFont.truetype(getFontPath(div_txt_fontname), int(div_txt_fontsize*size1x/size2x))
  size2y = int( size2y * size1x/size2x )
  size2x = int( size2x * size1x/size2x )
  # Determine image size
  width = div_X0 + size1x + div_X0
  height= div_Y0 + size1y + div_sY + size2y + div_Y1
  # Prepare drawing sheet
  img = Image.new("RGBA", (width,height), div_bgcol )
  draw = ImageDraw.Draw(img)
  # Print the two texts
  # draw.rectangle( [div_X0,div_Y0,div_X0+size2x,div_Y0+size1y],outline=div_color_amsgreen)
  draw.text( (div_X0,div_Y0), text1, div_txt_fgcolor, font=font_text1)
  # draw.rectangle( [div_X0,div_Y0+size1y+div_sY,div_X0+size2x,div_Y0+size1y+div_sY+size2y],outline=div_color_amsgreen)
  draw.text( (div_X0,div_Y0+size1y+div_sY), text2, div_txt_fgcolor, font=font_text2)
  return img


def indent(s) :
  return s.replace("\n","\n         ")


# Fixed URL to tuple of image and image bytes
def url2img(url) :
  global log
  log= "SYNTAX : wordsmith.png\r\n\r\n"
  # Load remote rss feed
  log+= f"request: {url}\r\n"
  resp= requests.get(url)
  data= resp.text
  log+= f"data   : {indent(data)}\r\n"
  # Convert rss string to dict and extract item
  dict = xmltodict.parse(data)
  log+= f"parsed : dict ok\r\n"
  item = dict["rss"]["channel"]["item"]
  log+= f"item   : {item}\r\n"
  title = item["title"]
  log+= f"  title: {title}\r\n"
  description = item["description"]
  log+= f"  desc : {description}\r\n\r\n"
  # Convert to image
  image = generateimg(title,description)
  log+= f"image  : created {image.width}x{image.height}\r\n"
  # Send image to web client
  with io.BytesIO() as memfile:
    image.save(memfile, format="png")
    bytes= memfile.getvalue()
  log+= f"bytes  : created {len(bytes)}\r\n"
  return image,bytes


# The entry point of the webserver
def application(environ, start_response):
  global log
  log = ""
  try:
    image,bytes = url2img(div_url)
    # raise Exception("Aborted for testing") # Uncomment for testing
    start_response("200 OK",[("Content-type","image/png")])
    return [bytes]
  except Exception as x:
    log+= f"\r\nERROR  : {x}\r\n"
    start_response("404 ERROR",[("Content-type","text/plain")])
    return [ log.encode("utf-8") ]


# The entry point for commandline test
if __name__ == "__main__":
  global log
  log = ""
  try:
    image,bytes = url2img(div_url)
    name = "trial.png"
    image.save(name)
    log+= f"png    : saved {name}\r\n"
    print(log)
  except Exception as x:
    log+= f"\r\nERROR  : {x}\r\n"
    print(log)



