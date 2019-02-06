# NarrowCast
A simple html/javascript/css based narrow cast player that can run on e.g. a Raspberry Pi.

To view it in a web browser, click [here](https://maarten-pennings.github.io/NarrowCast/narrowcast.html).

The actual sources can be found in the github
[web project](https://github.com/maarten-pennings/maarten-pennings.github.io/tree/master/NarrowCast).

# Setup
The `narrowcast.html` is the player.
It has a playlist of channels. Each channel is an xml file linking to images.
Unfortunately, due to security (CORS or Cross-Origin Resource Sharing), 
browsers will not let an html file load xml files from sites other than the "origin".
The "origin" being the site that served the html. Browsers will even refuse to load xml 
files using `file://`.

What this means is
 - you can not test `narrwocast.html` from a file system
 - `narrowcast.html` (and `logo.png`) must be on an http server.
 - the channel (xml) files must either be on the same server
 - or the xml files must be on a server that declares that is contents are "public"
 
For the latter, assuming you use apache on Ubuntu
 - goto directory `/etc/apache2/sites-available`
 - edit file `000-default.conf`
 - add the fragment `<Directory /var/www/html/rss>Header set Access-Control-Allow-Origin *</Directory>`
   assuming the xmls files are in `/var/www/html/rss`

   
