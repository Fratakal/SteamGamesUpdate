#!/usr/bin/python3

#---------------------------------------------------------------------------
#Basic Configuration
#---------------------------------------------------------------------------
SERVER_NAME = "Arma001"

STEAM_PATH = "D:\Steam\\"
#If the steam user or the password are empty it will be replaced by anonimous user, some games download doen't support it
#So make sure to enter both, you also have to disable *SteamGuard*, with is not recomended, always prefer anon user !
STEAM_USER = ""
STEAM_PASS = ""
#Max retry for steam to download mods and game
MAX_RETRY = 10

SERVER_DIR = "D:\Arma001\\"

#Steam game ID
GAME_SERVER_ID = "233780"
#Steam Game workshop ID
WORKSHOP_GAME_ID = "107410"

#Used as a reference to update steam mods file
#Keep it empty if you don't care, you still should be fine... i hope...
SMALLEST_WORKSHOP_ITEM_ID = "639837898"

ADDONSDIR = "addons"

#---------------------------------------------------------------------------
#end - Basic Configuration
#---------------------------------------------------------------------------

#===========================================================================

#---------------------------------------------------------------------------
#Advanced Configuration
#---------------------------------------------------------------------------

#Do you get the message : "Assertion Failed: !m_bIsFinalized"
#if yes set at True if not set False
ASSERFAIL = True

# Copy a specific list of files form all workshop path into a specific directory 
# if no files are set it just copy the directory content for each directory found
COPYCONTENT = { 
            "keys": ["*.bikey","*.key"],
            "userconfig": [""]
       }

#Exclude links 
#Edit this to delete directory links made during install process
EXCLUDEDLINKS = [
        "battleye",
        "missions",
        "mpmissions",
        "keys"
    ]

#Mods
#Workshop Mods to download and install
#The mod name is for convignance, it will be use mostly for you to know what mod you have installed
#        "ModName": "ModId"
MODS = {
        "@cba_a3":                      "450814997",
        "@cup_terrains_core":           "583496184"
}

#Manual mod path
MANUAL_MODS_PATH = {
        "BattleEye":        "battleye",
        "Missions":         "mpmissions",
        "Keys":             "keys"
    }
#---------------------------------------------------------------------------
#end - Advanced Configuration
#---------------------------------------------------------------------------



#region Functions
#---------------------------------------------------------------------------
# /!\ Do not edit below this point except if you know what you are doing /!\
#---------------------------------------------------------------------------
import os
import os.path
import re
import shutil
import argparse
import time
import platform
from datetime import datetime, timedelta
from urllib import request
from steamfiles import acf
from steamfiles import appinfo
from steamfiles import manifest
from collections import OrderedDict
from lxml import html

SYSTEM = platform.system()

if SYSTEM != 'Linux':
    STEAM_CMD = os.path.join(STEAM_PATH, "steamcmd.exe")
else:
    STEAM_CMD = os.path.join(STEAM_PATH, "steamcmd.sh")
WORKSHOP_DIR = os.path.join(os.path.join(STEAM_PATH, "steamapps"), "workshop")
GAME_WORKSHOP_MODS_DIR = os.path.join(os.path.join(WORKSHOP_DIR, "content"), WORKSHOP_GAME_ID)
GAME_MODS_DIR = os.path.join(SERVER_DIR, ADDONSDIR)

parser = argparse.ArgumentParser()
parser.add_argument('-f', help='Force update Mods', action='store_true')
parser.add_argument('-d', help='Force update special directory content', action='store_true')
parser.add_argument('-p', help='Enable pause message', action='store_true')
parser.add_argument('-v', help='Verbose', action='store_true')
args = parser.parse_args()
FORCEMODUPDATE = args.f
FORCEDIRUPDATE = args.d
ForceLogDisplay = args.v
PAUSEMESSAGE = args.p

start_time = time.time()

def log(msg):
    if ForceLogDisplay:
        print("")
        print("{{0:=<{}}}".format(len(msg)).format(""))
        printMsg(msg);
        print("{{0:=<{}}}".format(len(msg)).format(""))

def sysCmd(cmd):
    if not ForceLogDisplay:
        if SYSTEM != 'Linux':
            cmd = cmd + "> NUL"
        else:
            cmd = cmd + ">/dev/null 2>&1"
    os.system(cmd)
        
def printMsg(msg):
    if ForceLogDisplay:
        print(msg)

def call_steamcmd(params):
    sysCmd("{} {}".format(STEAM_CMD, params))    

def update_server():
    log("Updating server {} ({})".format(SERVER_NAME, GAME_SERVER_ID))

    if not STEAM_USER or not STEAM_PASS:
        steam_cmd_params = " +login anonymous"
    else:
        steam_cmd_params = " +login '{}' '{}'".format(STEAM_USER, STEAM_PASS)
    # steam_cmd_params += " +force_install_dir {}".format(SERVER_DIR)
    steam_cmd_params += " +app_update {} validate".format(GAME_SERVER_ID)
    steam_cmd_params += " +quit"

    call_steamcmd(steam_cmd_params)

def checkForWorkshopUpdate(id_workshop):
    url = "https://steamcommunity.com/sharedfiles/filedetails/?l=english&id={}".format(id_workshop)
    response = request.urlopen(url)
    
    page_source = response.read()
    tree = html.fromstring(page_source)
    data = tree.xpath('//div[@class="detailsStatRight"]/text()')
    try:
        date_update = data[2]
        datetime_object = datetime.strptime(date_update, '%d %b @ %I:%M%p')
        datetime_object = datetime_object.replace(year=datetime.now().year)
    except ValueError:
        date_update = data[2]
        datetime_object = datetime.strptime(date_update, '%d %b, %Y @ %I:%M%p')
    except IndexError:
        try:
            date_update = data[1]
            datetime_object = datetime.strptime(date_update, '%d %b, %Y @ %I:%M%p')
        except ValueError:
            date_update = data[1]
            datetime_object = datetime.strptime(date_update, '%d %b @ %I:%M%p')
            datetime_object = datetime_object.replace(year=datetime.now().year)
    return time.mktime(datetime_object.timetuple())

def isModNeedUpdate(data, idToUpdate):
    for IdAppWorkshop, Item in data['AppWorkshop']['WorkshopItemDetails'].items():
        if IdAppWorkshop == idToUpdate:
            return (float(Item['timetouched']) <= checkForWorkshopUpdate(idToUpdate))
    return True

def mod_needs_update(mod_id):
    with open(os.path.join(WORKSHOP_DIR, 'appworkshop_{}.acf'.format(WORKSHOP_GAME_ID)), 'r+') as f:
        data = acf.load(f, wrapper=OrderedDict)
        return isModNeedUpdate(data, mod_id)
    return True

def update_mods():
    log("Updating mods")

    if not SMALLEST_WORKSHOP_ITEM_ID:
        log("No mod reference updating")
    else:
        log("Updating mod reference file for mod {}".format(WORKSHOP_GAME_ID))
        if not STEAM_USER or not STEAM_PASS:
            steam_cmd_params  = " +login anonymous"
        else:
            steam_cmd_params  = " +login '{}' '{}'".format(STEAM_USER, STEAM_PASS)
        steam_cmd_params += " +workshop_download_item {} {} validate +workshop_status {}".format(
            WORKSHOP_GAME_ID,
            SMALLEST_WORKSHOP_ITEM_ID,
            WORKSHOP_GAME_ID
        )
        steam_cmd_params += " +quit"
        
        call_steamcmd(steam_cmd_params)

    for mod_name, mod_id in MODS.items():
        path = "{}\{}".format(GAME_WORKSHOP_MODS_DIR, mod_id)
        # Check if mod needs to be updated
        if os.path.isdir(path):
            if FORCEMODUPDATE:
               shutil.rmtree(path)
            elif mod_needs_update(mod_id):
                # Delete existing folder so that we can verify whether the
                # download succeeded
                shutil.rmtree(path)
            else:
                if ForceLogDisplay:
                    printMsg("No update required for \"{}\" ({})... SKIPPING".format(mod_name, mod_id))
                continue

        # Keep trying until the download actually succeeded
        tries = 0
        while os.path.isdir(path) == False and tries < MAX_RETRY:
            log("Updating \"{}\" ({}) | {}".format(mod_name, mod_id, tries + 1))

            if not STEAM_USER or not STEAM_PASS:
                steam_cmd_params  = " +login anonymous"
            else:
                steam_cmd_params  = " +login {} {}".format(STEAM_USER, STEAM_PASS)
            steam_cmd_params += " +workshop_download_item {} {} validate".format(
                WORKSHOP_GAME_ID,
                mod_id
            )
            steam_cmd_params += " +quit"
            
            call_steamcmd(steam_cmd_params)

            # Sleep for a bit so that we can kill the script if needed
            time.sleep(5)
            tries = tries + 1

        if tries >= MAX_RETRY:
            log("!! Updating {} failed after {} tries !!".format(mod_name, tries))

def lowercase_workshop_dir():
    if SYSTEM != 'Linux':
        log("Windows => No Lowercase convertion...")
    else:
        log("Converting uppercase files/folders to lowercase...")
        sysCmd("(cd {} && find . -depth -exec rename -v 's/(.*)\/([^\/]*)/$1\/\L$2/' {{}} \;)".format(GAME_WORKSHOP_MODS_DIR))
        
        for path_name, path in MANUAL_MODS_PATH.items():
            sysCmd("(cd {}{} && find . -depth -exec rename -v 's/(.*)\/([^\/]*)/$1\/\L$2/' {{}} \;)".format(SERVER_DIR, path))

def create_mod_symlinks():
    log("Creating symlinks...")

    for mod_name, mod_id in MODS.items():
        link_path = os.path.join(GAME_MODS_DIR, mod_name)
        real_path = os.path.join(GAME_WORKSHOP_MODS_DIR, mod_id)

        if os.path.isdir(real_path):
            if not os.path.islink(link_path):
                os.symlink(real_path, link_path)
                log("Creating symlink '{}'...".format(link_path))
        else:
            if ForceLogDisplay:
                printMsg("Mod '{}' does not exist! ({})".format(mod_name, real_path))

def get_game_name():
    with open(os.path.join(os.path.join(STEAM_PATH, 'steamapps'), 'appmanifest_{}.acf'.format(GAME_SERVER_ID)), 'r+') as f:
        data = acf.load(f, wrapper=OrderedDict)
        return data['AppState']['name']

def create_symlinks_from_game_dir():
    #create link based on the new app installed
    game_path = os.path.join(os.path.join(os.path.join(STEAM_PATH, "steamapps"), "common"), get_game_name())
    for x in os.listdir(game_path):
        source = os.path.join(game_path, x)
        target = os.path.join(SERVER_DIR, x)
        if not os.path.islink(source):
            if any(x in s for s in EXCLUDEDLINKS) and os.path.isdir(source):
                if not os.path.exists(target):
                    shutil.copytree(source, target)
            else:
                if not os.path.exists(target):
                    os.symlink(source, target)

def copy_files():
    for dir in COPYCONTENT:
        log("Copy files...")
        for file in COPYCONTENT[dir]:
            if file:
                if SYSTEM != 'Linux':
                    sysCmd('FORFILES /P {} /M {} /S /C "cmd /c xcopy @file {} /y"'.format(GAME_WORKSHOP_MODS_DIR, file, os.path.join(SERVER_DIR, dir)))
                else:
                    sysCmd('find {}/* -type f -name "{}" -exec cp -rfv'.format(GAME_WORKSHOP_MODS_DIR, file) + ' {} ' + '{} \\;'.format(os.path.join(SERVER_DIR, dir)))
            else:
                if SYSTEM != 'Linux':
                    sysCmd('FORFILES /P {} /M {} /S /C "cmd /c xcopy @path {} /S /Q /Y /F /I"'.format(GAME_WORKSHOP_MODS_DIR, dir, os.path.join(SERVER_DIR, dir)))
                else:
                    sysCmd('find {}/ -name "{}" -exec cp -rfv'.format(GAME_WORKSHOP_MODS_DIR, dir) + ' {} ' + '{} \\;'.format(SERVER_DIR))


def start_message():
    printMsg("For help with params add -h or --help.")
    if SYSTEM != 'Linux':
        printMsg("Make sure to run as Administrator to create links.")
    if not PAUSEMESSAGE and not os.path.exists(os.path.join(os.path.dirname(__file__), "ver_{}.txt".format(SERVER_NAME))):
        input("Press Enter to continue... or Ctrl+C to quit")
    if FORCEMODUPDATE:
        printMsg("Force mods update is set on {}".format(FORCEMODUPDATE))
#endregion

start_message()
update_server()
create_symlinks_from_game_dir()

update_mods()
lowercase_workshop_dir()
create_mod_symlinks()
copy_files()


elapsed = time.time() - start_time
print("Update/Install over, take {} seconds".format(str(timedelta(seconds=elapsed))))
