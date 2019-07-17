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
    :param year: numerical value representing a year
    :param month: number value of a month in the year (i.e. 1 is january)
    :param day: day of month
    :return: integer timestamp of time since epoch in seconds
    """
    return (datetime.datetime(int(year), int(month), int(day)) - datetime.datetime(1970,1,1)).total_seconds()


# def to_title(event_string):  # NOTE: Never used
#     """
#     Use when displaying results (not during data collection)
#     :param event_string: String abbreviation of an event name.
#     :return: Full human-readable event name
#     """
#     #
#     gender_map = {"M": "Men", "F": "Women", "X": "Mixed"}
#     stroke_map = {"1": "Freestyle", "2": "Backstroke", "3": "Breaststroke", "4": "Butterfly", "5": "IM",
#                   "M": "Medley Relay: ", "F": "Free Relay: ", "L": "Leadoff"}
#
#     gender = event_string[0]
#     stroke = event_string[1]
#     if event_string[2] in "MF":
#         relay_tag = stroke_map[event_string[2]]
#         distance = event_string[3:-1]
#     else:
#         relay_tag = ""
#         distance = event_string[2:-1]
#
#     return "{}'s {} Yard {}".format(gender_map[gender], distance, relay_tag + stroke_map[stroke])


def to_event_title(event_string):
    """
    This can be used during data collection. Converts abbreviated event name to format used on collegeswimming.com
    :param event_string: String abbreviation of an event name.
    :return: Full human-readable event name from collegeswimming
    """
    # break event_string into its component parts
    gender = event_string[0]  # can be M, F, or X
    stroke = event_string[1]  # can be 1, 2, 3, 4, 5, M, or F
    distance = event_string[2:-1]  # the distance of the event. can be a lot of values

    gender_map = {"M": "Men", "F": "Women", "X": "Mixed"}
    stroke_map = {"1": "Free", "2": "Back", "3": "Breast", "4": "Fly", "5": "IM",
                  "M": "Medley Relay", "F": "Free Relay"}
    return "{} {} {} ".format(distance, stroke_map[stroke], gender_map[gender])


def normalize_name(name):
    """
    Note: this assumes there are 1 or 0 apostrophes in the name
    :param name: string that is meant to be the name of something/someone (e.g. Brad beacham)
    :return name: Now properly formatted according to english grammar rules. (e.g. Brad Beacham)
    """
    name_parts = name.split()
    name = " ".join([part.lower().capitalize() for part in name_parts])
    # if there is an apostrophe in the name, capitalize the first letter after it
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
    :param name: a string. should be someones name
    :return name: same string with one extra apostrophe, if there was one (1) there before. otherwise just same.
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

