#!/usr/bin/python3
# This script draws a piechart from an excel table.
# It is assumed the table has many entries.
# The table is shuffled and drawn, and a random 'div_numrays' pieslieces are highlighted
# 2020 02 08 Maarten Pennings


# sudo pip install pillow
# sudo pip install xlrd
#
# make sure fonts are copied to the web server - see getFontPath() for location


# To merge Python into Apache on Ubuntu:
#   sudo apt install apache2 libapache2-mod-wsgi-py3  # for python3
#
# Create a python scipt (e.g. piechart.png.py) and assign rights
#   sudo chown maarten:www-data piechart.png.py
#   sudo chmod 775 piechart.png.py
#
# Map python script 'piechart.png.py' to url 'rss/piechart.png'
#   Edit configuration file    
#     sudo vi /etc/apache2/sites-available/000-default.conf
#   and add the line in the section <VirtualHost *:80>
#     WSGIScriptAlias /rss/piechart.png /var/www/html/rss/piechart.png.py
#
# Then, enable mod-wsgi configuration and restart Apache service with the following command:
#   sudo a2enconf wsgi
#   sudo systemctl restart apache2
#
# To check errors in script look at the log
#   less /var/log/apache2/error.log


import os
import random
import datetime
import platform
import math
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import io
import xlrd

div_color_amsgrey1=( 70, 85, 95)     # color code for ams dark grey
div_color_amsgrey2=(125,136,143)     # color code for ams medium grey 
div_color_amsgrey3=(172,178,183)     # color code for ams light grey
div_color_amsgreen=( 65,171,  2)     # color code for ams green
div_color_amsblue=(  0,117,176)      # color code for ams blue

div_width= 1920                      # Width of image
div_height= 1026                     # Height of image
div_bgcol="white"                    # background color of picture
div_centerx= div_width/2             # Center of circle
div_centery= div_height/2            # Center of circle

div_label_fontsize=20                # font size for labels
div_label_fontname="ARIAL.TTF"       # font name for labels

div_head_fontsize=32                 # font size for debug message (lower left corner)
div_head_fontname="ARIAL.TTF"        # font name for debug message (lower left corner)
div_head_fgcolor= div_color_amsgrey1 # foreground color for debug message (lower left corner)

div_dbg_fontsize=16                  # font size for debug message (lower left corner)
div_dbg_fontname="ARIAL.TTF"         # font name for debug message (lower left corner)
div_dbg_fgcolor=(220,220,220,255)    # foreground color for debug message (lower left corner)

div_numtoprank= 10                   # Number of people in the top
div_numrays= 30                      # Number of rays out of the ring

div_radius=400                       # Radius of the circle
div_innerradius=250                  # Radius of the white inner circle
div_ray0radius= 410                  # Radius of start of ray
div_ray1radius= 450                  # Radius of end of ray

# Returns the the unix time stamp for file `path_to_file`
def creation_date(path_to_file):
  """
  Try to get the date that a file was created, falling back to when it was
  last modified if that isn't possible.
  See http://stackoverflow.com/a/39501288/1709587 for explanation.
  """
  if platform.system() == 'Windows':
    return os.path.getctime(path_to_file)
  else:
    stat = os.stat(path_to_file)
    try:
      return stat.st_birthtime
    except AttributeError:
      # We're probably on Linux. No easy way to get creation dates here,
      # so we'll settle for when its content was last modified.
      return stat.st_mtime
        
# Adds the path of this script to `filename` to make it an absolute path    
def getScriptPath(filename):
  folder = os.path.dirname(os.path.realpath(__file__))
  filePath = os.path.join(folder, filename)
  return filePath             
# Adds the path of this script to fonts\`filename` to make it an absolute path    
def getFontPath(filename):
  folder = os.path.dirname(os.path.realpath(__file__))
  filePath = os.path.join(folder, os.path.join('fonts',filename))
  return filePath             

# Reads an xls file from local path `xlsname`    
# The first sheet of the workbook should have in Column A the first name, in Column B the last name, in Column C the count, and in column E a 'y' when the record should be included
# Returns [(firstname,lastname,count)],log -- a series of name with count and a parse log
def readXLSX(xlsname): 
    try:
        list= []
        workbook= xlrd.open_workbook( getScriptPath(xlsname) )
        worksheet= workbook.sheet_by_index(0)
        rejects= 0
        for i in range(0,worksheet.nrows):
            # 0       1        2 3    4 5
            # Maarten Pennings 1 mpen y y
            try:
                firstname= worksheet.cell_value(rowx=i, colx=0)
                lastname= worksheet.cell_value(rowx=i, colx=1)
                count= int(float( worksheet.cell_value(rowx=i, colx=2) ))
                show= worksheet.cell_value(rowx=i, colx=4)
                #print(firstname, lastname, count, show=="y")
                if show=="y": list.append( (firstname,lastname,count) )
            except:
                if len(list)>0: rejects= rejects+1 # do not count header rows as an error
                pass
        log= str(len(list))+" ok, "+str(rejects)+" errors"
    except:
        list.append( ("Error",datetime.datetime.now()) )
        log= "Failed to open '"+xlsname+"'" if len(xlsname)>0 else "Missing counts sheet, append ?counts.xlsx to URL" 
    return (list,log)

# The `list3` of the form [(firstname,lastname,count)] is converted to [(firstname,lastname,count,rank)]
# The rank is the index of that record when the table is sorted on `count` (rank 1 has highest count)
# The returned list is shuffled
def add_rank(list3):
  # Sort on count
  list3.sort( key=lambda t:-t[2] )
  rank= 1
  list4= []
  for firstname,lastname,count in list3:
    list4.append( (firstname,lastname,count,rank) )
    rank+= 1
  random.shuffle(list4) 
  return list4

# Draws a piechart, where each record in `list4` has a slice.
# Some random records are highlighted by pulling them out: and extra ray with a label
def table2Img(list4, publishdate, dbg):
  # Compute angle scale (degrees per count) and rayangle (degrees per ray)
  total=0
  for firstname,lastname,count,rank in list4: total+= count
  anglescale= 360.0/total
  rayangle= 360 / div_numrays
  # Create drawing objects
  newImage = Image.new('RGBA', (div_width,div_height), div_bgcol )
  draw = ImageDraw.Draw(newImage)
  font_label = ImageFont.truetype(getFontPath(div_label_fontname), div_label_fontsize)
  font_head = ImageFont.truetype(getFontPath(div_head_fontname), div_head_fontsize)
  font_dbg = ImageFont.truetype(getFontPath(div_dbg_fontname), div_dbg_fontsize)
  # Draw the piechart
  index= 0
  angle= 0.0
  lastray = 0
  for firstname,lastname,count,rank in list4:
    # Determine color for record
    col= div_color_amsgrey2 if index%2==0 else div_color_amsgrey3
    if rank<=div_numtoprank: col= div_color_amsblue
    # Draw the pieslice for the record
    angle2= angle + count*anglescale
    draw.pieslice( [div_centerx-div_radius,div_centery-div_radius,div_centerx+div_radius,div_centery+div_radius], angle, angle2, col)
    # Does this record encompass a ray
    ray= math.floor(angle2/rayangle)*rayangle
    if ray>lastray:
      # Yes draw a ray: draw ray on center of record (angle `a`)
      a= (angle+angle2)/2
      # Compute ray coordinates (x0,y0)-(x1,y1)
      sin= math.sin(a*math.pi/180)
      cos= math.cos(a*math.pi/180)
      x0= div_centerx+div_ray0radius*cos
      y0= div_centery+div_ray0radius*sin
      x1= div_centerx+div_ray1radius*cos
      y1= div_centery+div_ray1radius*sin
      # Draw the ray line
      draw.line( [ x0,y0,x1,y1 ], col, 3 )
      # Compose string for the text label, and determine label size
      lbl= " "+firstname+" "+lastname+" ("+str(count)+") "
      sizex,sizey=draw.textsize(lbl, font=font_label)
      # Determine anchor point (tx,ty) for text label, depending on the angle of the pieslice
      tx,ty= (0,0)
      if a<0+30: tx,ty= x1,y1-sizey//2
      elif a<90-12: tx,ty= x1,y1
      elif a<90: tx,ty= x1-2*div_label_fontsize,y1+0.75*div_label_fontsize
      elif a<90+12: tx,ty= x1-sizex+2*div_label_fontsize,y1+0.75*div_label_fontsize
      elif a<180-30: tx,ty= x1-sizex,y1
      elif a<180+30: tx,ty= x1-sizex,y1-sizey//2
      elif a<270-12: tx,ty= x1-sizex,y1-sizey
      elif a<270: tx,ty= x1-sizex+2*div_label_fontsize,y1-sizey-0.75*div_label_fontsize
      elif a<270+12: tx,ty= x1-2*div_label_fontsize,y1-sizey-0.75*div_label_fontsize
      elif a<360-30: tx,ty= x1,y1-sizey
      else: tx,ty= x1,y1-sizey//2
      # Draw text label
      #draw.rectangle( [tx,ty,tx+sizex,ty+sizey], outline=col)
      draw.text( (tx,ty), lbl, col, font=font_label)
      lastray= ray
    index+= 1
    angle= angle2
  # At some text inside piechart
  draw.pieslice( [div_centerx-div_innerradius,div_centery-div_innerradius,div_centerx+div_innerradius,div_centery+div_innerradius], 0, 360, div_bgcol)
  lbl= "ams Circle of Inventors"
  sizex,sizey=draw.textsize(lbl, font=font_head)
  draw.text( (div_width//2-sizex//2,div_height/2-div_head_fontsize*2), lbl, div_head_fgcolor, font=font_head)
  lbl= "based on patent families"
  sizex,sizey=draw.textsize(lbl, font=font_label)
  draw.text( (div_width//2-sizex//2,div_height/2), lbl, div_head_fgcolor, font=font_label)
  lbl= "as of " + publishdate.strftime('%B %Y')
  sizex,sizey=draw.textsize(lbl, font=font_label)
  draw.text( (div_width//2-sizex//2,div_height/2+div_label_fontsize*2), lbl, div_head_fgcolor, font=font_label)
  # Draw dbg
  now= datetime.datetime.now()
  draw.text( (8,div_height-div_dbg_fontsize-8),dbg+" "+now.strftime('%Y-%m-%d %H:%M'),div_dbg_fgcolor,font=font_dbg)
  return newImage

# Main function: opens xls file `xlsname` and converts that to a piechart image, which is returned
def xls2img(xlsname):
  publishdate= datetime.datetime.utcfromtimestamp((creation_date(getScriptPath(xlsname)))) 
  list3,log= readXLSX(xlsname)
  list4= add_rank(list3)
  image= table2Img(list4,publishdate,log)
  return image

# Entry point for webserver
def application(environ, start_response):
  log= 'SYNTAX : piechart.png?<url-to-xls>\r\n'
  try:
    # Get name
    xlsname= environ.get('QUERY_STRING')
    log+= 'arg    : "%s"\r\n' % xlsname
    pos= xlsname.find("&")
    if pos>=0: xlsname= xlsname[:pos]
    log+= 'xlsname: "%s"\r\n' % xlsname
    # Load xls and convert to image
    if xlsname=='': raise Exception('&<url-to-xls> argument missing')
    image= xls2img(xlsname)
    log+= 'image  : created\r\n'
    # Send image to web client
    with io.BytesIO() as memfile:
      image.save(memfile, format="png")
      bytes= memfile.getvalue()
    log+= 'bytes  : created\r\n'
    status= '200 OK'
    response_header= [('Content-type','image/png')]
    if False: raise Exception('Aborted for testing') # Change False to True for testing
    start_response(status,response_header)
    return [bytes]
  except Exception as x:
    log+='\r\nERROR  : %s\r\n' % str(x)
    start_response('404 ERROR',[('Content-type','text/plain')])
    return [ log.encode('utf-8') ]

# Entry point for testing
if __name__ == "__main__":
  print("Local test mode")
  image= xls2img(r"ams_rank.xlsx")
  image.save("ams_rank.png","PNG")
  print("done")

    








