import sqlite3
import sys
import datetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# College Swimming Summer Break Project 2019                                Brad Beacham #
#                                                      Adapted from code by Kevin Wylder #
# This file builds a database from data collected off collegeswimming.com                #
# for more detail on the structure of the database, the global variables in this file,   #
# or the collegeswimming.com website structure, see the README                           #
#                                                                                        #
# From here on out, 90 character width isn't guarenteed                                  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def convertToTime(year, month, day):
    """
    Input integer values for year, month, and day of month
    Output total number of seconds since epoch
    """
    return (datetime.datetime(int(year), int(month), int(day)) - datetime.datetime(1970,1,1)).total_seconds()

def toTitle(eventString):
    """
    Input string eventString
    Output human readable event title
    """
    gender = eventString[0]
    stroke = eventString[1]
    distance = eventString[2:-1]
    genderMap = {"M":"Men", "F":"Women"}
    strokeMap = {"1":"Freestyle", "2":"Backstroke", "3":"Breaststroke", "4":"Butterfly", "5":"IM"}
    return "{}'s {} Yard {}".format(genderMap[gender], distance, strokeMap[stroke])

def normalizeName(name):
    """
    Input a string name.
    Output a string where the first letter of every word is capitalized.
    Note: this assumes there are 1 or 0 apostrophes in the name
    Makes sure every name is properly formatted according to english grammar rules.
    Input "Brad o'hara" Output "Brad O'Hara"
    """
    nameParts = name.split()
    name = " ".join([part.lower().capitalize() for part in nameParts])
    n = name.find("'")
    if n > -1:
        name = name[:n+1] + name[n+1:].capitalize()
    return name

def sqlsafe(name):
    """
    Input some string corresponding to a name
    Output edited string where apostrophes are doubled.
    Note: this assumes there are 1 or 0 apostrophes in the name
    Input " ' " output " '' "
    """
    n = name.find("'")
    if n > -1:
        name = name[:n+1] + "'" + name[n+1:]
    return name

def showLoadingBar(percent):
    """
    Input some value between 0 and 1
    Print a string of "#" and " " characters ending with a floating point percent value
    """
    chars = int(percent * 50)
    print("\n" + ("#" * chars) + (" " * (50 - chars)) + " {:10.2f}%\r".format(100 * percent))
    sys.stdout.flush()

