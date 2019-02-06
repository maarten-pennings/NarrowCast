# NarrowCast
A simple html/javascript/css based narrow cast player that can run on e.g. a Raspberry Pi.

# Introduction
This project is basically a single html file (with embedded javascript and css) that acts as a narrow cast player.
It needs a _list_ of channels. A _channel_ is an xml file listing _pages_.
A page is a (screen sized) images with a title and description.

The player loads all channel files, merges them into one list of pages, shuffles the list, and then shows each page for several seconds.
After a longer time, the channel files are reloaded, merged and shuffled again.

This project delivers the player `narrowcast.html`, and example channel files (`art` and `weather`).
You would copy `narrowcast.html` and write you own channel files.

# Demo
To view narrowcast in a web browser, click [here](https://maarten-pennings.github.io/NarrowCast/narrowcast.html).

It is suggested to open the browser in full-screen mode (F11).

# Sources
The actual sources of this project can be found in the github
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
