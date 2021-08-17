#!/usr/bin/python3

# ns.png.py - Script to convert NS data to rss
# 2020 sep 23  v1  Maarten Pennings  Copied from rss4
version = "v1"


# To merge Python into Apache on Ubuntu:
#   sudo apt install apache2 libapache2-mod-wsgi-py3  # for python3

# Create a python script (e.g. ns.png.py) and assign rights
#   sudo chown maarten:www-data ns.png.py
#   sudo chmod 755 ns.png.py

# Map python script 'ns.png.py' to url 'rss/ns.png'
#   Edit configuration file    
#     sudo vi /etc/apache2/sites-available/000-default.conf
#   and add the line in the section <VirtualHost *:80>
#     WSGIScriptAlias /rss/ns.png /var/www/html/rss/ns.png.py

# Then, enable mod-wsgi configuration and restart Apache service with the following command:
#   sudo a2enconf wsgi
#   sudo systemctl restart apache2

# To check errors in script look at the log
#   less /var/log/apache2/error.log


import os
import io
import requests
import json
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 


# Drawing settings
div_color_amsgrey1=( 70, 85, 95)      # color code for ams dark grey
div_color_amsgrey2=(125,136,143)      # color code for ams medium grey 
div_color_amsgrey3=(172,178,183)      # color code for ams light grey
div_color_amsgreen=( 65,171,  2)      # color code for ams green
div_color_amsblue=(  0,117,176)       # color code for ams blue
                                                                       
div_bgcol= 0                          # background color of picture (0=transparant, also eg "white")
                                      
div_txt_fontsize=40                   # font size for labels
div_txt_fontname="ARIAL.TTF"          # font name for labels
div_txt_fgcolor= div_color_amsgrey1   # foreground color
div_txt_bgcolor= div_color_amsgrey3   # foreground color
div_txt_olcolor= div_color_amsgrey2   # outline color

div_Y0=50                             # top and bottom margin
div_X0=50                             # left and right margin
div_dY=70                             # cell height
div_sY=30                             # cell separation
div_mX=30                             # x-margin for text
div_mY=15                             # y-margin for text

# Adds the path of this script to fonts\`filename` to make it an absolute path    
def getFontPath(filename):
  folder = os.path.dirname(os.path.realpath(__file__))
  path = os.path.join(folder, os.path.join('fonts',filename))
  return path             


# Extract the interesting fields
def dict2dict(indeps):
    outdeps=[]
    for indep in indeps :
        dest = indep["direction"]
        time = indep["plannedDateTime"][11:16]
        track= indep["plannedTrack"]
        cat  = indep["product"]["longCategoryName"]
        stats= ""
        for stat in indep["routeStations"] :
            if stats!="" : stats+=", "
            stats+= stat["mediumName"]
        outdep={'dest':dest, 'time':time, 'track':track, 'cat':cat, 'stats':stats}    
        outdeps.append(dict(outdep))
    return outdeps


def dict2img(deps) :
    # Loop over all departures to determine column width
    img = Image.new('RGBA', (10,10), div_bgcol ) # temp
    draw = ImageDraw.Draw(img) # temp
    font_txt = ImageFont.truetype(getFontPath(div_txt_fontname), div_txt_fontsize) # temp
    dest_width_max=0
    time_width_max=0
    trackcat_width_max=0
    stats_width_max=0
    for ix,dep in enumerate(deps):
        # width of "dest"
        lbl= dep["dest"]
        sizex,sizey= draw.textsize( lbl, font=font_txt)
        dest_width_max= max(dest_width_max,sizex)
        # width of "time"
        lbl= dep["time"]
        sizex,sizey= draw.textsize( lbl, font=font_txt)
        time_width_max= max(time_width_max,sizex)
        # width of "track" and "cat"
        lbl= "track "+dep["track"]+" "+dep["cat"]
        sizex,sizey= draw.textsize( lbl, font=font_txt)
        trackcat_width_max= max(trackcat_width_max,sizex)
        # width of "stats
        lbl= "via "+dep["stats"]
        sizex,sizey= draw.textsize( lbl, font=font_txt)
        stats_width_max= max(stats_width_max,sizex)
    # determine image width
    dX= div_mX+dest_width_max+div_mX + div_mX+time_width_max+div_mX + div_mX+trackcat_width_max+div_mX + div_mX+stats_width_max+div_mX
    width = div_X0 + dX + div_X0
    height= div_Y0 + div_dY*len(deps) + div_sY*(len(deps)-1) + div_Y0
    # Prepare drawing sheet
    img = Image.new('RGBA', (width,height), div_bgcol )
    draw = ImageDraw.Draw(img)
    font_txt = ImageFont.truetype(getFontPath(div_txt_fontname), div_txt_fontsize)
    # Loop over all departures
    for ix,dep in enumerate(deps):
        # draw box for departure ix/dep
        draw.rectangle([div_X0,div_Y0+(div_dY+div_sY)*ix , div_X0+dX,div_Y0+(div_dY+div_sY)*ix+div_dY],fill=div_txt_bgcolor,outline=div_txt_olcolor)
        # print "dest"
        lbl= dep["dest"]
        x= div_X0 + div_mX
        y= div_Y0+(div_dY+div_sY)*ix+div_mY
        draw.text( (x,y), lbl, div_txt_fgcolor, font=font_txt)
        # print "time"
        lbl= dep["time"]
        x= div_X0 + div_mX+dest_width_max+div_mX + div_mX
        y= div_Y0+(div_dY+div_sY)*ix+div_mY
        draw.text( (x,y), lbl, div_color_amsblue, font=font_txt)
        # print "track" and "cat"
        lbl= "track "+dep["track"]+" "+dep["cat"]
        x= div_X0 + div_mX+dest_width_max+div_mX + div_mX+time_width_max+div_mX + div_mX
        y= div_Y0+(div_dY+div_sY)*ix+div_mY
        draw.text( (x,y), lbl, div_txt_fgcolor, font=font_txt)
        # print "stats
        lbl= "via "+dep["stats"]
        x= div_X0 + div_mX+dest_width_max+div_mX + div_mX+time_width_max+div_mX + div_mX+trackcat_width_max+div_mX + div_mX
        y= div_Y0+(div_dY+div_sY)*ix+div_mY
        draw.text( (x,y), lbl, div_txt_fgcolor, font=font_txt)
    return img

   
def application(environ, start_response):
  log= 'SYNTAX : ns.png\r\n\r\n'
  try:
    # Contact info
    url='https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/departures?station=EHV&maxJourneys=8'
    headers= { 'Ocp-Apim-Subscription-Key': 'a27b9a201fcd4ea2bdfd2971245cc92b'} # Maarten's private key
    # Load remote rss feed
    resp= requests.get(url, headers=headers)
    data= resp.text
    log+=  f'data   : {data [0:200]}...\r\n'
    # Parse NS data
    dict= json.loads(data)
    departures= dict["payload"]["departures"]
    log+=  f'dict   : "{departures[0]["direction"]}" ...\r\n'
    # Extract/normalize departures
    departures2= dict2dict(departures)
    for i,d in enumerate(departures2):
      log+=  f'dep[{i}] : {d["dest"]} {d["time"]} track {d["track"]} {d["cat"]} via {d["stats"]}\r\n'
    # Convert to image with table
    image= dict2img(departures2)
    log+= 'image  : created\r\n'
    # Send image to web client
    with io.BytesIO() as memfile:
      image.save(memfile, format="png")
      bytes= memfile.getvalue()
    log+= 'bytes  : created\r\n'
    #raise Exception('Aborted for testing') # Uncomment for testing
    start_response('200 OK',[('Content-type','image/png')])
    return [bytes]
  except Exception as x:
    log+='\r\nERROR  : %s\r\n' % str(x)
    start_response('404 ERROR',[('Content-type','text/plain')])
    return [ log.encode('utf-8') ]


