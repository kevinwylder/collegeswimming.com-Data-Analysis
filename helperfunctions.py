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


def convert_to_time(year, month, day):
    """
    Input integer values for year, month, and day of month
    Output total number of seconds since epoch
    """
    return (datetime.datetime(int(year), int(month), int(day)) - datetime.datetime(1970,1,1)).total_seconds()


def to_title(event_string):
    """
    Use when displaying results (not during data collection)
    :param event_string: String abbreviation of an event name.
    :return: Full human-readable event name
    """
    gender_map = {"M": "Men", "F": "Women", "X": "Mixed"}
    stroke_map = {"1": "Freestyle", "2": "Backstroke", "3": "Breaststroke", "4": "Butterfly", "5": "IM",
                  "M": "Medley Relay: ", "F": "Free Relay: ", "L": "Leadoff"}

    gender = event_string[0]
    stroke = event_string[1]
    if event_string[2] in "MF":
        relay_tag = stroke_map[event_string[2]]
        distance = event_string[3:-1]
    else:
        relay_tag = ""
        distance = event_string[2:-1]

    return "{}'s {} Yard {}".format(gender_map[gender], distance, relay_tag + stroke_map[stroke])


def to_event_title(event_string):
    """
    This can be used during data collection. Converts abbreviated event name to format used on collegeswimming.com
    :param event_string: String abbreviation of an event name.
    :return: Full human-readable event name from collegeswimming
    """
    gender = event_string[0]
    stroke = event_string[1]
    distance = event_string[2:-1]
    gender_map = {"M": "Men", "F": "Women", "X": "Mixed"}
    stroke_map = {"1": "Free", "2": "Back", "3": "Breast", "4": "Fly", "5": "IM",
                  "M": "Medley Relay", "F": "Free Relay"}
    return "{} {} {} ".format(distance, stroke_map[stroke], gender_map[gender])


def normalize_name(name):
    """
    Input a string name.
    Output a string where the first letter of every word is capitalized.
    Note: this assumes there are 1 or 0 apostrophes in the name
    Makes sure every name is properly formatted according to english grammar rules.
    Input "Brad o'hara" Output "Brad O'Hara"
    """
    name_parts = name.split()
    name = " ".join([part.lower().capitalize() for part in name_parts])
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


def show_loading_bar(percent):
    """
    Input some value between 0 and 1
    Print a string of "#" and " " characters ending with a floating point percent value
    """
    chars = int(percent * 50)
    print("\n" + ("#" * chars) + (" " * (50 - chars)) + " {:10.2f}%\r".format(100 * percent))
    sys.stdout.flush()

