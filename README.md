# SteamGamesUpdate

Python script to Download/Update any games and workshop mods

Windows and Unix ready

/!\ Untested on MacOS /!\

============================================================


Dependencies :

  pip3
  
  python-protobuf
  
  python3-lxml
  
  steamfiles (https://pypi.org/project/steamfiles/) [use pip3 to install]
  


============================================================

Warning : You should disable TwoFactor Auth if need to get logged or the script will pause for code.

============================================================


Usage: 

Windows:

	x:\SteamDownload-Update.py [-h] [-f] [-d] [-p] [-v]

Unix:

	./SteamDownload-Update.py [-h] [-f] [-d] [-p] [-v]



optional arguments:

	  -h, --help  show this help message and exit
  
	  -f          Force update Mods
  
	  -d          Force update special directory content
  
	  -p          Enable pause message
  
	  -v          Verbose
  
