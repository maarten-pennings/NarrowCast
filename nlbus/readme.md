# nlbus.png
Script creating a timetable for bus stops (in the Netherlands).

## Getting started
First test this on your PC.

 - Take a PC that has Python 3.8 or up
 - Download the whole directory `nlbus`, anywhere you want.
 - Start a `cmd.exe` in that directory.
 - Run `steup.bat`, this creates a virtual env (downloads python packages only for this project).
 - Generate a table with `run`
 
This should generate an image like this. Not exactly like this, because the table is generated based on live data :-)

![Bus table](trial.png)
 
## Configure
This script uses the server [https://v0.ovapi.nl](https://v0.ovapi.nl).
I believe the website [drpl](https://drgl.nl/) is a demo.

A parameter of nlbus is a list of `stops`, e.g. `ehvhbb,ehvhts`.
To find those stops, get the list of all stops from the [server](https://v0.ovapi.nl/stopareacode).

My script is intended for guests of the High Tech Campus in Eindhoven (HTC).
So the script has an option to pass a map (`mapname`).

Finally, busses make several stops on the High Tech Campus.
I added a `lowlight` feature so that guests would be (hopefully) 
less confused to see the High Tech Campus as destination on the High Tech Campus.

feel free to play around with these parameters
in `if __name__ == "__main__" :` on line ~350.

## Diversity settings
All options starting with `div_` govern how the tables will look like.
It determines horizontal and vertical spacing, background and foreground colors,
and some highlighting aspects. See line ~60 and further.

## Webserver
This module is intended to be a WSGI script in a web server, generating an image.
That has not yet been tested.

Line ~10 and further gives some web install instructions.


(end)


