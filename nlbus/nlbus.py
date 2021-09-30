#!/usr/bin/python3


# nlbus.png.py - Script creating a timetable for bus stops (in the Netherlands)
# 2021 sep 29  v1  Maarten Pennings  Created
version = "v1"


# You need some modules
#   sudo python3 -m pip install pillow requests

# To merge Python into Apache on Ubuntu:
#   sudo apt install apache2 libapache2-mod-wsgi-py3  # for python3

# Create a python script (e.g. nlbus.png.py) and assign rights
#   sudo chown maarten:www-data nlbus.png.py
#   sudo chmod 755 nlbus.png.py

# Map python script 'nlbus.png.py' to url 'rss/nlbus.png'
#   Edit configuration file
#     sudo vi /etc/apache2/sites-available/000-default.conf
#   and add the line in the section <VirtualHost *:80>
#     WSGIScriptAlias /rss/nlbus.png /var/www/html/rss/nlbus.png.py

# Then, enable mod-wsgi configuration and restart Apache service with the following command:
#   sudo a2enconf wsgi
#   sudo systemctl restart apache2

# To check errors in script look at the log
#   less /var/log/apache2/error.log


import os
import io
import requests
import json
import urllib
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from datetime import datetime


# URL source (also see https://drgl.nl/)
const_url="https://v0.ovapi.nl"

# Standard colors (typically don't change, but add new names)
const_color_amsgrey1=( 70, 85, 95)        # color code for ams dark grey
const_color_amsgrey2=(125,136,143)        # color code for ams medium grey
const_color_amsgrey3=(172,178,183)        # color code for ams light grey
const_color_amsgreen=( 65,171,  2)        # color code for ams green
const_color_amsblue =(  0,117,176)        # color code for ams blue
const_color_red     =(255,  0,  0)        # color code for plain red




# Diversity settings: Vertical spacing
#
#   div_y_mar  |
#              +----------------------------------+
#   div_y_head |Eindhoven, HTC/Berkenbos          |
#              +----------------------------------+
#   div_y_seph |
#              +-----+ +---+ +--------------------+
#   div_y_row  |15:48| |407| |Eindhoven Station   |
#              +-----+ +---+ +--------------------+
#   div_y_sepc |
#              +-----+ +---+ +--------------------+
#   div_y_row  |16:18| |407| |Eindhoven Station   |
#              +-----+ +---+ +--------------------+
#   div_y_sepc |
#              +-----+ +---+ +--------------------+
#   div_y_row  |16:48| |407| |Eindhoven Station   |
#              +-----+ +---+ +--------------------+
#   div_y_sepm |
#              +-------------+
#   map.height |MAP          |
#              +-------------+
#   div_y_mar  |

div_y_mar = 25                            # top and bottom vertical margin
div_y_seph = 20                           # vertical space between head cell and (first) plain cell
div_y_sepc = 15                           # vertical space between plain cells
div_y_sepm = 20                           # vertical space between plain cells and map

div_y_head = 78                           # height of the head cell
div_y_row = 60                            # height of the plain cells


# Diversity settings: Horizontal spacing
#
#   div_x_mar div_x_head                                                    div_x_seph                                 div_x_mar
#   ---------+-------------------------------------------------------------+----------+-------------------------------+---------
#            |Eindhoven, HTC/Berkenbos                                     |          |Eindhoven, HTC/Dommeldal       |
#            +----------+----------+----------+----------+-----------------+----------+-----+-+---+-+-----------------+
#            |  15:48   |          |    407   |          |Eindhoven Station|          |15:46| |407| |Eindhoven Station|
#            +----------+----------+----------+----------+-----------------+----------+-----+-+---+-+-----------------+
#             div_x_time div_x_sepc div_x_line div_x_sepc     div_x_dest

div_x_mar = 45                            # top and bottom horizontal margin
div_x_seph = 45                           # horizontal space between head cells
div_x_sepc = 15                           # horizontal space between plain cells

div_x_time = 200                          # width for the departure time field
div_x_line = 120                          # width for the bus line number field
div_x_dest = 600                          # width for the bus destination field
div_x_head = div_x_time + div_x_sepc + div_x_line + div_x_sepc + div_x_dest


# Diversity settings: Background color for generated image
div_bgcol= 0                              # background color of generated image (0=transparent, also eg "white")


# Diversity settings: Font and colors for heading
div_head_fontname="ARIALBD.TTF"           # font name for head cells
div_head_fontsize=44                      # font size for within head cells
div_head_bgcolor= const_color_amsgrey2    # background color for within head cells
div_head_fgcolor= const_color_amsgrey1    # foreground color for within head cells
div_head_ytxt = 16                        # vertical offset for text in head cells
div_head_xtxt = 20                        # horizontal offset for text in head cells


# Diversity settings: Font and colors for plain cells
div_cell_fontname="ARIAL.TTF"             # font name for plain cells
div_cell_fontsize=36                      # font size for within plain cells
div_cell_bgcolor= const_color_amsgrey3    # background color for within plain cells
div_cell_fgcolor_lo= const_color_amsgrey1 # foreground color (low light) for within plain cells
div_cell_fgcolor_hi= const_color_amsblue  # foreground color (high light) for within plain cells
div_cell_fgcolor_delay= const_color_red   # foreground color for delays
div_cell_ytxt = 10                        # vertical offset for text in plain cells
div_cell_xtxt = 20                        # horizontal offset for text in plain cells


# Diversity settings: Font for server "now" time stamp
div_now_fontname="ARIAL.TTF"              # font name for server "now" time stamp
div_now_fontsize=16                       # font size for server "now" time stamp
div_now_fgcolor=const_color_amsgrey1      # foreground color for server "now" time stamp


# Prepend the path of this script to fonts\filename to make it an absolute path
def getFontPath(filename):
  global log
  folder = os.path.dirname(os.path.realpath(__file__))
  path = os.path.join(folder, os.path.join("fonts",filename))
  log+= f"font   : {path}\r\n"
  return path


# Looks up the departures for bus stops and returns a dictionary of departure tables.
#
# `stops` is a string of comma separated "stopareacode"s, e.g. "ehvhbb,ehvhts". Find yours in https://v0.ovapi.nl/stopareacode
# Each stopareacode is a key into the returned dictionary, giving the departure table for that stop.
# The departure table is also a dictionary with `name`, `code` and a dictionary of `deps` (departures):
#   'ehvhts': {
#     'name': 'Eindhoven, HTC/The Strip',
#     'code': '64121390',
#     'deps': {
#       '13:42': { 'dest':'Best Station via Airport', 'line':'20', 'time':'2021-09-29T13:42:00', 'delay':  0 },
#       '14:42': { 'dest':'Best Station via Airport', 'line':'20', 'time':'2021-09-29T14:42:00', 'delay':120 }
#     }
#   }
def stops2tables(stops) :
  global log
  # Load json data
  url = f"{const_url}/stopareacode/{stops}"
  log+= f"request: {url}\r\n"
  resp= requests.get(url)
  data_json= resp.text
  log+= f"data   : {data_json[:150]}...\r\n"
  # Convert data to json
  data_dict = json.loads(data_json)
  # log+= f"dict   : {str(data_dict)[:150]}...\r\n"
  
  # data_dict has this structure, pick the relevant fields
  #
  # {
  #     "ehvhbb": {
  #         "64121290": {
  #             "Stop": {
  #                 "TimingPointName": "Eindhoven, HTC/Berkenbos",
  #                 ...
  #             },
  #     ...
  # }
  tables = {}
  for stop in stops.split(",") :
    stopdata_dict = data_dict[stop]
    # Get stop name and code
    TimingPointCode = list(stopdata_dict.keys())[0] # TimingPointCode is only key of a stop
    TimingPointName = stopdata_dict[TimingPointCode]["Stop"]["TimingPointName"]
    table = { "name": TimingPointName, "code":TimingPointCode }
    log+= f"{stop} : {TimingPointName}\r\n"
    # Get busses that pass at this stop
    departures = {}
    passes_dict = stopdata_dict[TimingPointCode]["Passes"]
    for key in passes_dict :
      pass_dict = passes_dict[key]
      DestinationName50 = pass_dict["DestinationName50"]
      LinePublicNumber = pass_dict["LinePublicNumber"]
      TargetArrivalTime = pass_dict["TargetArrivalTime"]
      ExpectedArrivalTime = pass_dict["ExpectedArrivalTime"]
      delay = datetime.strptime(ExpectedArrivalTime,'%Y-%m-%dT%H:%M:%S') - datetime.strptime(TargetArrivalTime,'%Y-%m-%dT%H:%M:%S') 
      delay = int(delay.total_seconds())
      log+= f"           {TargetArrivalTime} +{delay}s {LinePublicNumber} {DestinationName50}\r\n"
      time = TargetArrivalTime[11:19]# "2021-09-29T00:41:33+0200"
      departures[time]= {"dest":DestinationName50, "line":LinePublicNumber, "time":TargetArrivalTime, "delay":delay }
    table["deps"] = dict(sorted(departures.items())) # Sort on time, this is the order in the UI
    tables[stop] = table
  return tables


# Converts departure tables to graphical matrix, and return that image.
# Matrix dimensions and colors are governed by the diversity settings (e.g. by div_xxx).
# If the destination of a departure contains `lowlight`, that destination is rendered in lowlight, else in highlight.
# Reason: low light bus stops to the area where we already are (High Tech Campus)
# If `mapname` is not None, it should be a path to a image that will be added.
def tables2image(tables,lowlight,mapname) :
  global log
  # Find longest table
  maxdeps = 1 # at least "no (more) busses"
  numstops = 0
  for skey in tables :
    stop = tables[skey]
    maxdeps = max(maxdeps,len(stop["deps"]))
    numstops += 1
  log+= f"draw   : tables {numstops}, rows {maxdeps}\r\n"
  # Compute size
  width = div_x_mar + div_x_head*numstops + div_x_seph*(numstops-1) + div_x_mar
  height = div_y_mar + div_y_head + div_y_seph + div_y_row*maxdeps + div_y_sepc*(maxdeps-1) + div_y_mar
  # Get map image
  if mapname!= None :
    mapimg = Image.open(mapname)
    height += div_y_sepm + mapimg.height
  # Create image
  img = Image.new("RGBA", (width,height), div_bgcol )
  draw = ImageDraw.Draw(img)
  head_font = ImageFont.truetype(getFontPath(div_head_fontname), div_head_fontsize)
  cell_font = ImageFont.truetype(getFontPath(div_cell_fontname), div_cell_fontsize)
  now_font = ImageFont.truetype(getFontPath(div_now_fontname), div_now_fontsize)
  log+= f"size   : {width}*{height}\r\n"
  # Create a column per stop
  x0 = div_x_mar
  for skey in tables :
    stop = tables[skey]
    # Draw head
    y0 = div_y_mar
    draw.rectangle([x0,y0,x0+div_x_head,y0+div_y_head],fill=div_head_bgcolor,outline=div_head_bgcolor)
    draw.text( (x0+div_head_xtxt,y0+div_head_ytxt), stop["name"], div_head_fgcolor, font=head_font)
    # Draw departure rows
    y0 += div_y_head + div_y_seph
    for dkey in stop["deps"] :
      dep = stop["deps"][dkey]
      #  - time
      x = x0
      txt = dep["time"][11:16]
      if dep["delay"]>=60 :
        txt += f' +{dep["delay"]//60}'
      draw.rectangle([x,y0,x+div_x_time,y0+div_y_row],fill=div_cell_bgcolor,outline=div_cell_bgcolor)
      sizex,sizey= draw.textsize( txt, font=cell_font)
      dx = (div_x_time-div_cell_xtxt-div_cell_xtxt-sizex)//2
      draw.text( (x+div_cell_xtxt+dx,y0+div_cell_ytxt), txt, div_cell_fgcolor_delay if dep["delay"]>=60 else div_cell_fgcolor_lo, font=cell_font)
      #  - line
      x += div_x_time + div_x_sepc
      txt = dep["line"]
      draw.rectangle([x,y0,x+div_x_line,y0+div_y_row],fill=div_cell_bgcolor,outline=div_cell_bgcolor)
      sizex,sizey= draw.textsize( txt, font=cell_font)
      dx = (div_x_line-div_cell_xtxt-div_cell_xtxt-sizex)//2
      draw.text( (x+div_cell_xtxt+dx,y0+div_cell_ytxt), txt , div_cell_fgcolor_lo, font=cell_font)
      #  - dest
      x += div_x_line + div_x_sepc
      txt = dep["dest"]
      draw.rectangle([x,y0,x+div_x_dest,y0+div_y_row],fill=div_cell_bgcolor,outline=div_cell_bgcolor)
      draw.text( (x+div_cell_xtxt,y0+div_cell_ytxt), txt, div_cell_fgcolor_lo if lowlight in txt else div_cell_fgcolor_hi, font=cell_font)
      # Move x0 to new column
      y0 += div_y_row + div_y_sepc
    # Was there a stop, or no more busses because too late?
    if len(stop["deps"])==0 :
      draw.rectangle([x0,y0,x0+div_x_head,y0+div_y_row],fill=div_cell_bgcolor,outline=div_cell_bgcolor)
      txt = "no (more) busses"
      draw.text( (x0+div_cell_xtxt,y0+div_cell_ytxt), txt, div_cell_fgcolor_lo, font=cell_font)
    # Move x0 to new column
    x0 += div_x_head + div_x_seph

  # Add map
  if mapname!= None :
    img.paste( mapimg, ( (width-mapimg.width)//2, height-mapimg.height-div_y_mar ) )
  # Add server url and time stamp
  txt = datetime.now().strftime("%H:%M:%S")
  sizex,sizey= draw.textsize( txt, font=now_font)
  draw.text( (width-sizex-div_x_mar,height-sizey-div_now_fontsize//2), txt, div_now_fgcolor, font=now_font)
  txt = const_url
  sizex,sizey= draw.textsize( txt, font=now_font)
  draw.text( (div_x_mar,height-sizey-div_now_fontsize//2), txt, div_now_fgcolor, font=now_font)
  return img


# Converts an image to a buffer of raw bytes (to be send by http)
def image2bytes(image) :
  global log
  # Send image to web client
  with io.BytesIO() as memfile:
    image.save(memfile, format="png")
    buffer= memfile.getvalue()
  log+= f"buffer : {len(buffer)} bytes\r\n"
  return buffer


# Sequence of conversion steps, with a log to more easily finding errors
# `stops` is a string of comma separated "stopareacode"s, e.g. "ehvhbb,ehvhts". Find yours in https://v0.ovapi.nl/stopareacode
# If the destination of a departure contains `lowlight`, that destination is drawn in lowlight, else in highlight.
# If mapname is not none, it should be a path to a image that will be added.
# Returns the final image buffer but also the intermediate results: tables, image, buffer.
def main(stops,lowlight,mapname) :
  global log
  log = ""
  log += f"NL Bus creates a timetable for bus stops (in the Netherlands) - {version}\r\n"
  log += "SYNTAX : nlbus.png?stops=ehvhbb,ehvhts&lowlight=Campus&mapname=htc.png\r\n"
  log += "         Find stops on https://v0.ovapi.nl/stopareacode, lowlight and mapname are optional\r\n\r\n"
  # Create table with departures for every bus stop in `stops`
  tables = stops2tables(stops)
  # Convert table to image grid (low lighting all destinations that contain `lowlight`)
  image = tables2image(tables,lowlight,mapname)
  # Convert image to bytes array
  buffer = image2bytes(image)
  return tables,image,buffer


# The entry point for the webserver
def application(environ, start_response):
  global log
  try:
    # Get parameters from URL
    params = urllib.parse.parse_qs(environ['QUERY_STRING'])
    stops = params.get('stops', ["ehvhts"])[0]
    lowlight = params.get('lowlight', [""])[0]
    mapname = params.get('mapname', [None])[0]
    # Load actual bus data from server and convert to image
    tables,image,buffer = main(stops,lowlight,mapname)
    # raise Exception("Aborted for testing") # Uncomment for testing
    start_response("200 OK",[("Content-type","image/png")])
    return [buffer]
  except Exception as x:
    log+= f"\r\nERROR  : {x}\r\n"
    start_response("404 ERROR",[("Content-type","text/plain")])
    return [ log.encode("utf-8") ]


# The entry point for command line test
if __name__ == "__main__":
  global log
  try:
    stops="ehvhbb,ehvhts"
    lowlight="High Tech Campus"
    stops = "aalvbl,aalmts"
    lowlight=""
    mapname="htc.png"
    tables,image,buffer = main(stops,lowlight,mapname)
    filename = "trial.png"
    image.save(filename)
    log+= f"png    : saved '{filename}'\r\n"
    print(log)
  except Exception as x:
    log+= f"\r\nERROR  : {x}\r\n"
    print(log)
