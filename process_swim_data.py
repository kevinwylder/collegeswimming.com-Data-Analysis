import pandas as pd
import sqlite3
from constants import *
import re
import helperfunctions as hf
# This file is for processing the data


def get_data():
    """
    :return: swims, swimmers, teams, raw data from collegeswimming website.
    """
    connection = sqlite3.connect(DATABASE_FILE_NAME)
    swims = pd.read_sql_query("SELECT * FROM Swims", connection)
    swimmers = pd.read_sql_query("SELECT * FROM Swimmers", connection).rename({"name": "athlete_name"}, axis="columns")
    teams = pd.read_sql_query("SELECT * FROM Teams", connection).rename({"name": "team_name"}, axis="columns")
    swimmers.set_index("swimmer_id", inplace=True)
    teams.set_index("team_id", inplace=True)
    connection.close()

    event_list = list(swims["event"].unique())  # TODO: this should come from user input in the future
    # TODO: use this instead of swims as return value when you feel ready ^^
    return swims, swimmers, teams, event_list


def get_athlete_data(swims, swimmers, teams, event_list):
    """
    :param swims: dataframe containing data on individual swims
    :param swimmers: dataframe with names and IDs of swimmers
    :param event_list: list of events included in the dataset
    :return: team_data, a dataframe of all swimmers, as well as different measures of their performance
    """
    grouped_dataset = swims.groupby(["swimmer", "event"])
    team_data = []
    swimmer_event_pairs_used = grouped_dataset.groups.keys()

    for swimmer, swimmer_data in swimmers.iterrows():
        team = teams.loc[swimmer_data["team_id"]]["team_name"]
        for event in event_list:
            if (swimmer, event) not in swimmer_event_pairs_used:
                team_data.append({"swimmer_id": swimmer, "event": event, "team": team, "minimum_time": None,
                                  "average_time": None, "median_time": None})
            else:
                individual_event_data = grouped_dataset.get_group((swimmer, event))
                minimum_time = individual_event_data["time"].min()
                average_time = individual_event_data["time"].mean()
                median_time = individual_event_data["time"].median()
                team_data.append({"swimmer_id": swimmer, "event": event, "team": team,
                                  "minimum_time": minimum_time, "average_time": average_time, "median_time": median_time})

    team_data = pd.DataFrame(team_data, columns=["swimmer_id", "event", "team", "minimum_time", "average_time", "median_time"])
    # This will have every possible athlete-event pairing possible, even if an athlete hasn't done that event before
    return team_data


def filter_from_dataset(swims, swimmers, team=None, gender=None, start_year=None, end_year=None):  # Not in use
    """
    function for filtering raw data
    :param swims: the database of swims from which we begin to whittle down the group data
    :param team: an integer team id for the team whose data you may want to collect
    :param gender: character M or F representing gender whose swims you want to collect
    :param start_year: all data on the group must be after this year (a default month and start day are used)
    :param end_year: all data on the group must be before this year (a default month and start day are used)
    :return: filtered_data: dataset containing only data that you want
    """
    #NOTE: this might not be what is wanted, spend some time figuring out what is wrong with it, then make sure it is
    # what you are being asked for. If it can't separate the other parts then it is useless.
    filtered_data = swims.copy()
    if team:
        filtered_data = filtered_data[filtered_data["team"]==team]
    if gender:
        gender_swimmers = []
        for swimmer in swimmers.iterrows():
            if swimmer[1]["gender"] in gender:  # not sure why the 1 is needed but it works now
                gender_swimmers.append(swimmer[0])
        filtered_data = filtered_data[filtered_data["swimmer"].isin(gender_swimmers)]
    if start_year:
        start_timestamp = hf.convert_to_time(int(start_year), SEASON_LINE_MONTH, SEASON_LINE_DAY)
        filtered_data = filtered_data[filtered_data["date"] >= start_timestamp]
    if end_year:
        end_timestamp = hf.convert_to_time(int(end_year), SEASON_LINE_MONTH, SEASON_LINE_DAY)
        filtered_data = filtered_data[filtered_data["date"] <= end_timestamp]
    return filtered_data


def get_team_swims(swims, team):  # Not in use
    """
    :param swims: dataframe of raw swim data, including the team a swimmer who performed a swim was on
    :param team: integer corresponding to the team we want to keep swims for
    :return: team_swims: a table/pandas dataframe of swims performed by a given team
    """
    team_swims = swims[swims["team_id"] == team]
    return team_swims


def filter_by_team(id_matrix, swimmers, team):  # I should use a more descriptive name than id_matrix if possible
    """
    Filters a table based on the team that its players come from. the table must be indexed by player ID
    :param id_matrix: a pandas table indexed by swimmer ID
    :param swimmers: a pandas table of all swimmers in the database
    :param team: the team you wish to filter by
    :return: filtered_table: a table that only contains data on swimmers from the target team
    """
    filtered_swimmers = swimmers[swimmers["team_id"] == team]
    filtered_table = id_matrix[id_matrix.index.isin(filtered_swimmers.index.tolist())]
    return filtered_table


def get_predicted_performance_matrix(team_data, preference):
    """
    Inputs:
    1. team_data, a pandas data frame containing information on a group (or groups) of athletes.
    2. preference, a string indicating the information in team_data that you wish to use to find an optimal team lineup
    Outputs:
    athlete_prediction_dictionary, a dictionary of athletes and their predicted performances
    """
    # NOTE: In the future when we decide how this information is input, there should be a dictionary that converts
    #  different input types to be equal to these values (i.e. {"minimum : MIN,...}), or the reverse of this
    # NOTE: It also might be a good idea to use athlete ID instead of name somewhere in case two team members have the
    #  same name, but that is a problem for another time

    group_by_individual = team_data.groupby("swimmer_id")  # should uniquely identify every player

    athlete_prediction_dictionary = {}
    for athlete, athlete_data in group_by_individual:
        individual_data = athlete_data[["event",preference]].transpose()
        individual_data.columns = individual_data.iloc[0]
        individual_data.drop("event", inplace=True)
        athlete_prediction_dictionary[athlete] = individual_data.to_dict('records')[0]
    return pd.DataFrame.from_dict(athlete_prediction_dictionary, orient='index')


def get_team_lineup(swims, swimmers, teams, event_list, meet_id):
    """
    :param swims: raw data on individual swims in a dataframe.
    :param swimmers: dataframe of swimmer names and IDs
    :param event_list: the list of events that are included in the dataset
    :param meet_id: this is a numerical ID
    :return: meet_lineup, the lineup used by one team at a single meet. this is a dictionary with the format
    {swimmer_id: {"event1": (1 or 0), "event2": (1 or 0),...}} with 1 showing that an athlete participated in an event
    and 0 indicating that they did not

    The purpose of this function is to find a previous lineup used by a given team.
    """

    filter_by_meet = swims[swims["meet_id"] == meet_id].copy()  # works without copy() but will throw a warning
    filter_by_meet['time'] = filter_by_meet['time'].notna().astype(int)

    group_by_individual = filter_by_meet.groupby("swimmer")

    event_dict = {event: 0 for event in event_list}

    meet_lineup = {}
    # makes a nested dictionary containing all athletes and events. all values in event dicts are False (0)
    for swimmer, swimmer_data in swimmers.iterrows():
        meet_lineup[swimmer] = event_dict.copy()

    # updates the dictionary made above so that events an athlete participated in are True (1)
    for swimmer, swimmer_data in group_by_individual:
        print(swimmer_data[["event","time"]])
        individual_data = swimmer_data[["event","time"]].transpose()
        individual_data.columns = individual_data.iloc[0]
        individual_data.drop("event", inplace=True)
        meet_lineup[swimmer].update(individual_data.to_dict('records')[0])
    return pd.DataFrame.from_dict(meet_lineup, orient='index')


def score_event(results_a, results_b, places):
    """
    assigns points to groups based on who has the smallest score/time.
    :param results_a: list of recorded times for team a
    :param results_b: list of recorded times for team b
    :param places: list of point values awarded for first, second, etc place
    :return: scores of team a and b
    """
    score_a = score_b = 0
    for place in places:
        if len(results_a) > 0 and len(results_b) > 0:
            if min(results_a) < min(results_b):
                results_a.remove(min(results_a))
                score_a += place
            else:
                results_b.remove(min(results_b))
                score_b += place
        elif len(results_a) > 0:
            results_a.pop()
            score_a += place
        elif len(results_b) > 0:
            results_b.pop()
            score_b += place
        else:
            continue
    return score_a, score_b


def calculate_pred_score(perfA, lineA, perfB, lineB):
    """
    returns the predicted score of team A for a swimming meet
    :param perfA: Pandas dataframe of predicted performances for a given team A's swimmers
    :param lineA: Pandas Dataframe of a given lineup for a team A
    :param perfB: Pandas dataframe of predicted performances for a given team B's swimmers
    :param lineB: Pandas Dataframe of a given lineup for a team B
    :return: pred_score: Integer value of team A's predicted
    """
    # This is a predicted performance matrix that only contains values for swimmers in the lineup
    lineup_scores_a = perfA[lineA==1]
    lineup_scores_b = perfB[lineB==1]
    # Team scores are integer values
    score_a = score_b = 0
    # Find times for all relay events and put them together in one dictionary
    event_list = lineup_scores_a.columns.tolist()
    r = re.compile(".L[MF].+")  # look for relay events
    relay_list = list(filter(r.match, event_list))
    relay_event_results = dict()
    for value in relay_list:
        if value[2] is "F":
            legs = [value, value[:1]+"1"+value[2:]]
        elif value[2] is "M":
            legs = [value, value[:1] + "2" + value[2:], value[:1] + "3" + value[2:], value[:1] + "4" + value[2:]]
        time_a = lineup_scores_a[legs].sum().sum()
        time_b = lineup_scores_b[legs].sum().sum()
        # if event is in dictionary, update data, if not then add it
        if value[2:-1] in relay_event_results:
            if time_a != 0:
                relay_event_results[value[2:-1]][0].append(time_a)
            if time_b != 0:
                relay_event_results[value[2:-1]][1].append(time_b)
        else:
            relay_event_results[value[2:-1]] = [[time_a],[time_b]]
            if time_a == 0:
                relay_event_results[value[2:-1]][0].pop()
            if time_b == 0:
                relay_event_results[value[2:-1]][1].pop()

    # score the relays
    for event in relay_event_results:
        # get results for each team by event
        results_a = relay_event_results[event][0]
        results_b = relay_event_results[event][1]
        temp_a, temp_b = score_event(results_a, results_b, RELAY_POINTS)
        score_a += temp_a
        score_b += temp_b
    # score individual events
    individual_events = list(filter(lambda x: x[2] not in "MF", event_list))
    for column_name in individual_events:
        results_a = lineup_scores_a[column_name][lineup_scores_a[column_name].notna()].tolist()
        results_b = lineup_scores_b[column_name][lineup_scores_b[column_name].notna()].tolist()
        temp_a, temp_b = score_event(results_a, results_b, INDIVIDUAL_POINTS)
        score_a += temp_a  # cannot add to two values at same time
        score_b += temp_b
    return score_a, score_b


def pred_score_matrix(team_list, lineup_matrix):
    """
    This function can currently only handle two teams at once
    :param team_list: list of pandas dataframes for predicted performances of teams.
    :param lineup_matrix: 2 dimensional array of lineups. each list within the array is the list of lineups for one team
    from team_performance_list
    :return: score_matrix: matrix of scores for teams using each lineup combination
    """
    if (len(team_list) == 2) and (len(lineup_matrix) == 2):
        score_matrix = [[(0,0)] * len(lineup_matrix[1]) for i in range(len(lineup_matrix[0]))]
        # can't just use [[(0,0)]*n]*b for 2D array. due to screwy logic, L = [(0,0)]*n is read as "make a list of n
        # tuples each with value (0,0)", which is good, but M = [[(0,0)*n]*b is read as "make a list of containing b
        # references to the same list L" which would be [L,L,L]. we can change one of the L's to be an R instead, giving
        # us [L,L,R], because we are simply telling M to change one of its elements to reference something else.
        # However, if we want to change a value stored in one of the L's, we end up changing that value in all of the
        # L's because they all reference the same piece of code.
        # TLDR: [[(0,0)]*n]*b says make list of n tuples with value (0,0), then make that same list b times, whereas
        # The method we use here says "make a list of n tuples with value (0,0)" and it says it b separate times
        for team_a_index in range(len(lineup_matrix[0])):
            for team_b_index in range(len(lineup_matrix[1])):
                score_a, score_b = calculate_pred_score(team_list[0], lineup_matrix[0][team_a_index],
                                                        team_list[1], lineup_matrix[1][team_b_index])
                score_matrix[team_a_index][team_b_index] = (score_a,score_b)
    print(score_matrix)
    return score_matrix




def demo_code():
    bucknell_vs_lehigh = 119957
    bucknell_invitational = 136124
    bu_lehigh = 119748
    swims, swimmers, teams, event_list = get_data()
    #swims = swims[swims["meet_id"] == bucknell_vs_lehigh]  # check to see that everything works for single meet
    team_data = get_athlete_data(swims, swimmers, teams, event_list)
    pred_perf = get_predicted_performance_matrix(team_data, 'average_time')
    some_lineup = get_team_lineup(swims, swimmers, teams, event_list, bucknell_vs_lehigh)
    bucknell_perf = filter_by_team(pred_perf, swimmers, 184)
    bucknell_lineup = filter_by_team(some_lineup, swimmers, 184)
    lehigh_perf = filter_by_team(pred_perf, swimmers, 141)
    lehigh_lineup = filter_by_team(some_lineup, swimmers, 141)
    # get additional lineups for matrix
    bucknell_inv_lin = get_team_lineup(swims, swimmers, teams, event_list, bucknell_invitational)
    bucknell_inv_lin = filter_by_team(bucknell_inv_lin, swimmers, 184)
    bu_lehigh_lin = get_team_lineup(swims, swimmers, teams, event_list, bu_lehigh)
    bu_lehigh_lin = filter_by_team(bu_lehigh_lin, swimmers, 141)
    # test individual parts
    print("\n predicted performance of players (based on average time)\n")
    print(bucknell_perf)
    print("\n lineup used during meet {0} (meet names will be incorporated later, for now here is the url that will "
          "lead to that event: https://www.collegeswimming.com/results/{0}/\n".format(bucknell_vs_lehigh))
    score_a, score_b = calculate_pred_score(bucknell_perf, bucknell_lineup, lehigh_perf, lehigh_lineup)
    print(score_a)
    print(score_b)
    # test matrix
    score_matrix = pred_score_matrix([bucknell_perf, lehigh_perf],[[bucknell_lineup, bucknell_inv_lin],
                                                                   [lehigh_lineup, bu_lehigh_lin]])

demo_code()