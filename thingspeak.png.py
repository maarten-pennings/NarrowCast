# sudo pip install matplotlib
# sudo apt-get install python-tk

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import json 
import requests
import os, sys, io
from datetime import datetime,timedelta
from dateutil import tz

def application(environ, start_response):
    info_plot = [["249563","2","#ffd43b","600"], #ENS210.H [may be changed]                 
                 ["616372","2","#e74c3c", "300"], #CCS811.eTVOC [may be changed]  
                 ["381884","1","#34495e", "300"], #iAQcore.CO2 [may be changed]
                 ["249563","1","#ffd43b","600"], #ENS210.T [may be changed]
                 ["616372","4","#e74c3c", "300"], #CCS811.R [may be changed]
                 ["320672","1","#2ecc71","600"]] #ENS220.P [may be changed]
                 
    
    data = []
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    for idata in range(len(info_plot)):          
        url= "https://thingspeak.com/channels/"+info_plot[idata][0]+"/field/"+info_plot[idata][1]+".json?results="+info_plot[idata][3]
        resp= requests.get(url)
        text= resp.text
        data.append(json.loads(text))

    plt.ioff()
    fig = plt.figure(figsize=[19.2*0.8,10*0.8])
   
    for idata in range(len(info_plot)):
        data_feeds = data[idata]["feeds"]
        dtime = []
        plotdata = []
        plotname = data[idata]["channel"]["field%s" %info_plot[idata][1]]
        for idx in range(len(data_feeds)):
            utc = datetime.strptime(data_feeds[idx]['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            utc = utc.replace(tzinfo = from_zone)
            central = utc.astimezone(to_zone)
            dtime.append(central)
            plotdata.append(float(data_feeds[idx]["field%s" %info_plot[idata][1]])) 
            
        plt.subplot(int("23"+str(idata+1)))
        plt.plot(dtime, plotdata,'.-', color = info_plot[idata][2])
        plt.xlabel('Date')
        plt.ylabel(plotname)
        plt.title(data[idata]["channel"]["name"]) 
        
        ax = plt.gca()
        ax.get_yaxis().get_major_formatter().set_useOffset(False)
        
    plt.tight_layout()

    with io.BytesIO() as memfile:
        plt.savefig(memfile, format="png")
        bytes = memfile.getvalue()
    plt.close(fig)
    
    status = '200 OK'
    response_header = [('Content-type','image/png')]
    start_response(status,response_header)
    return [bytes]

if __name__ == "__main__":
     application({},{})


# { u'feeds': [
#   {u'created_at': u'2019-02-27T08:00:56Z', u'field1': u'23.053125', u'entry_id': 1835901}, 
#   {u'created_at': u'2019-02-27T08:01:27Z', u'field1': u'23.037500', u'entry_id': 1835902}, 
#   {u'created_at': u'2019-02-27T08:01:58Z', u'field1': u'23.006250', u'entry_id': 1835903}, 
#   ...
#   {u'created_at': u'2019-02-27T08:48:42Z', u'field1': u'22.975000', u'entry_id': 1835993}, 
#   {u'created_at': u'2019-02-27T08:49:13Z', u'field1': u'22.959375', u'entry_id': 1835994}, 
#   {u'created_at': u'2019-02-27T08:49:45Z', u'field1': u'22.959375', u'entry_id': 1835995}, 
#   {u'created_at': u'2019-02-27T08:50:16Z', u'field1': u'23.006250', u'entry_id': 1835996}, 
#   {u'created_at': u'2019-02-27T08:50:47Z', u'field1': u'23.006250', u'entry_id': 1835997}, 
#   {u'created_at': u'2019-02-27T08:51:18Z', u'field1': u'22.990625', u'entry_id': 1835998}, 
#   {u'created_at': u'2019-02-27T08:51:49Z', u'field1': u'22.975000', u'entry_id': 1835999}, 
#   {u'created_at': u'2019-02-27T08:52:20Z', u'field1': u'23.006250', u'entry_id': 1836000}
#   ]
# , u'channel': {
#   u'description': u'ENS210 relative humidity and temperature sensor by ams', 
#   u'updated_at': u'2018-10-18T15:08:33Z', 
#   u'longitude': u'5.4601', 
#   u'last_entry_id': 1836000, 
#   u'id': 249563, 
#   u'name': u'ENS210 @ HTC', 
#   u'field2': u'Humidity (in %RH)', 
#   u'field3': u'TStatus', 
#   u'created_at': u'2017-03-28T18:46:17Z', 
#   u'field1': u'Temperature (in \xb0C)', 
#   u'field4': u'HStatus', 
#   u'latitude': u'51.4109'
#   }
# }
#      
