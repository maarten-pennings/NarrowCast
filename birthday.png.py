#!/usr/bin/python3

# sudo pip install pillow
# sudo pip install xlrd
# make sure fonts are copied to the web server - see getPath() for location

import os
import datetime
import random
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
from collections import OrderedDict
import io
import xlrd


div_Y0=50                            # top and bottom margin
div_X0=50                            # left and right margin
div_dY=100                           # row step
div_dRY=div_dY-40                    # height of the rectangles
div_dX=500                           # column step
div_dRX=div_dX-80                    # width of the date+name rectangles
div_dRX2=50                          # width of the date area
div_fontsize_cell=35                 # font size for plain cells
div_fontname_cell="ARIAL.TTF"        # font name for plain cells
div_fgcolor_cell=(0,0,0,255)         # foreground color for plain cells
div_fgcolor_cellhi=(0,100,0,255)     # foreground color for plain cells highlighted (birthday now)
div_bgcolor_cell=(200,200,200,255)   # background color for plain cells
div_bgcolor_cellhi=(150,250,150,255) # background color for plain cells highlighted (birthday now)
div_fontsize_head=40                 # font size for header cells
div_fontname_head="ARIALBD.TTF"      # font name for header cells
div_fgcolor_head=(0,50,250,255)      # foreground color for header cells
div_bgcolor_head=(200,200,255,255)   # background color for header cells
div_fontsize_dbg=16                  # font size for plain cells
div_fontname_dbg="ARIAL.TTF"         # font name for plain cells
div_fgcolor_dbg=(220,220,220,255)    # foreground color for plain cells

div_monthnames = ['Zero','January','February','March','April','May','June','July','August','September','October','November','December']
div_bgcolors = [ (168,100,253,255), (41,205,255,255), (120,255,68,255), (255,113,141,255), (253,255,106,255) ]

# Converts a name,date list to a dictionary. 
# The dictionary maps a month/date to a list of person that has birthday that date.
# The returned object has a (month,day) as key and a list of name,date tuples as value
def convert(name_date_list):
    md_namedates_dict={}
    for name,date in name_date_list:
        md=(date.month,date.day)
        if md not in md_namedates_dict:
            md_namedates_dict[md]=[(name,date)]
        else:
            md_namedates_dict[md].append((name,date))
    return md_namedates_dict

# Adds the path of this script to 'filename' to make it an asbolute path    
def getPath(filename):
    folder = os.path.dirname(os.path.realpath(__file__))
    filePath = os.path.join(folder, os.path.join('fonts',filename))
    return filePath             

def getPath2(filename):
    folder = os.path.dirname(os.path.realpath(__file__))
    filePath = os.path.join(folder, filename)
    return filePath             

def table2Img(md_namedates_dict, dbg):
    # The table is generated taken current time 'now' into account
    now= datetime.datetime.now()
    # The columns is the (month,year) we want to draw
    columns=[]
    month=now.month
    year=now.year
    for i in range(3):
        columns.append( (month,year) ) 
        month=month+1
        if( month==13 ): month=1; year=year+1
    # Compute Bounding box
    width=div_X0
    height=0
    for month,year in columns:
        Y= div_Y0
        for day in range(1,32):
            if (month,day) not in md_namedates_dict: continue;
            for name,date in md_namedates_dict[(month,day)]:
                Y=Y+div_dY
                if Y>height: height=Y
        width= width+div_dX
    width=width-(div_dX-div_dRX)+div_X0
    height=height+div_dY-div_dRY+div_Y0
    # Start drawing on image
    newImage = Image.new('RGBA', (width,height), "white" )
    draw = ImageDraw.Draw(newImage)
    font_cell = ImageFont.truetype(getPath(div_fontname_cell), div_fontsize_cell)
    font_head = ImageFont.truetype(getPath(div_fontname_head), div_fontsize_head)
    font_dbg = ImageFont.truetype(getPath(div_fontname_dbg), div_fontsize_dbg)
    # Draw confetti
    for ix in range(1, 150+random.randint(0,150)):
        X= random.randint(0, width)
        Y= random.randint(0, height)
        radius= random.randint( int(div_dY/8), int(div_dY/4))
        colix= random.randint(0,len(div_bgcolors)-1)
        color= div_bgcolors[colix]
        draw.ellipse((X, Y, X+radius, Y+radius), fill=color, outline=color)
    # Draw columns
    X=div_X0
    for month,year in columns:
        Y= div_Y0
        # Draw header
        draw.rectangle([X-8,Y-8,X+div_dRX-8,Y+div_dRY-8],fill=div_bgcolor_head,outline=div_bgcolor_head)
        draw.text((X,Y),div_monthnames[month]+' '+str(year),div_fgcolor_head,font=font_head)
        Y=Y+div_dY
        cursordrawn= False
        for day in range(1,32):
            if (month,day) not in md_namedates_dict: continue;
            if (now.month==month) and (now.day<day) and not cursordrawn:
                dy= int(div_dY/2)
                draw.polygon( [(X,Y+int(div_dRY/2)-8-dy),(X-30,Y-8-dy),(X-30,Y+div_dRY-8-dy)], fill=div_bgcolor_cellhi, outline=div_fgcolor_cellhi) # draw cursor
                cursordrawn= True
            for name,date in md_namedates_dict[(month,day)]:
                fgcolor= div_fgcolor_cell
                bgcolor= div_bgcolor_cell
                if (now.month==month) and (now.day==day) :
                    fgcolor=div_fgcolor_cellhi
                    bgcolor=div_bgcolor_cellhi
                    draw.polygon( [(X,Y+int(div_dRY/2)-8),(X-30,Y-8),(X-30,Y+div_dRY-8)], fill=div_bgcolor_cellhi, outline=div_fgcolor_cellhi) # draw cursor
                    cursordrawn= True
                draw.rectangle([X-8,Y-8,X+div_dRX-8,Y+div_dRY-8],fill=bgcolor,outline=bgcolor)
                draw.text((X,Y),'{:2d}'.format(day),fgcolor,font=font_cell)
                draw.text((X+div_dRX2,Y),str(name),fgcolor,font=font_cell)
                Y=Y+div_dY
        if (now.month==month) and not cursordrawn:
            dy= int(div_dY/2)
            draw.polygon( [(X,Y+int(div_dRY/2)-8-dy),(X-30,Y-8-dy),(X-30,Y+div_dRY-8-dy)], fill=div_bgcolor_cellhi, outline=div_fgcolor_cellhi) # draw cursor
            cursordrawn= True
        X= X+div_dX
    # Draw dbg
    draw.text((div_X0,height-div_fontsize_dbg-8),dbg+" "+now.strftime('%Y%m%d %H:%M'),div_fgcolor_dbg,font=font_dbg)
    return newImage

# Reads an xls file from local path `xlsname`    
# The first sheet of the workbook should have in Column A the last name, in Column B the first name and in Column C the date of birth
# If the third columns does not have valid date, the person is skipped. This automatically skips white lines and the header.
# Returns [[str,date]],log -- a series of name and date and a parse log
def readXLSX(xlsname): 
    try:
        name_date_list= []
        workbook= xlrd.open_workbook( getPath2(xlsname) )
        worksheet= workbook.sheet_by_index(0)
        rejects= 0
        for i in range(0,worksheet.nrows):
            try:
                a1= worksheet.cell_value(rowx=i, colx=2) # col2 is date of birth
                date= datetime.datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                name= worksheet.cell_value(rowx=i, colx=1)+" "+ worksheet.cell_value(rowx=i, colx=0)
                name_date_list.append( (name,date) )
            except:
                if len(name_date_list)>0: rejects= rejects+1
                pass
        log= str(len(name_date_list))+" ok, "+str(rejects)+" rejected"
    except:
        name_date_list.append( ("Error",datetime.datetime.now()) )
        log= "Failed to open '"+xlsname+"'" if len(xlsname)>0 else "Missing calender, append ?ehv-birthdays.xlsx to URL" 
    return (name_date_list,log)

def application(environ, start_response):
    xlsname= environ.get('QUERY_STRING')
    pos= xlsname.find("&")
    if pos>=0: xlsname= xlsname[:pos]
    name_date_list,log= readXLSX(xlsname)
    md_namedates_dict= convert(name_date_list)
    image= table2Img(md_namedates_dict,log)
    with io.BytesIO() as memfile:
        image.save(memfile, format="png")
        bytes= memfile.getvalue()
    status= '200 OK'
    response_header= [('Content-type','image/png')]
    start_response(status,response_header)
    return [bytes]
   
if __name__ == "__main__":
    name_date_list,rejects= readXLSX(r"ehv-birthdays.xlsx")
    md_namedates_dict= convert(name_date_list)
    image= table2Img(md_namedates_dict,log)
    with io.BytesIO() as memfile:
        image.save(memfile, format="png")
        bytes= memfile.getvalue()
    #print( bytes )
    








