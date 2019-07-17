import pandas as pd
import sqlite3
from constants import *
import re
import helperfunctions as hf
from collections import Counter
# This file is for processing the data


def get_data():
    """
    :return: swims, swimmers, teams, raw data from collegeswimming website.
    """
    # open sqlite connection
    connection = sqlite3.connect(DATABASE_FILE_NAME)
    # read sqlite database tables into pandas database tables
    swims = pd.read_sql_query("SELECT * FROM Swims", connection)
    swimmers = pd.read_sql_query("SELECT * FROM Swimmers", connection).rename({"name": "athlete_name"}, axis="columns")
    teams = pd.read_sql_query("SELECT * FROM Teams", connection).rename({"name": "team_name"}, axis="columns")
    # set primary keys for swimmer and team tables as table indices.
    swimmers.set_index("swimmer_id", inplace=True)
    teams.set_index("team_id", inplace=True)
    connection.close()

    event_list = list(swims["event"].unique())  # TODO: this should come from user input in the future
    return swims, swimmers, teams, event_list


def get_athlete_data(swims, swimmers, teams, event_list):
    """
    :param swims: dataframe containing data on individual swims
    :param swimmers: dataframe with names and IDs of swimmers
    :param teams: dataframe containing team data
    :param event_list: list of events included in the dataset
    :return: team_data, a dataframe of all swimmers, as well as different measures of their performance
    """
    # group swim data by swimmer ID and event code
    grouped_dataset = swims.groupby(["swimmer", "event"])
    # get list of all groups made above
    swimmer_event_pairs_used = grouped_dataset.groups.keys()

    team_data = []
    for swimmer, swimmer_data in swimmers.iterrows():
        team = teams.loc[swimmer_data["team_id"]]["team_name"]
        for event in event_list:
            if (swimmer, event) not in swimmer_event_pairs_used:
                # swimmer-event pair is not an existing group (meaning swimmer never participated in that event), so
                # put down their predicted times for the event as None
                team_data.append({"swimmer_id": swimmer, "event": event, "team": team, "minimum_time": None,
                                  "average_time": None, "median_time": None})
            else:
                # swimmer-event pair exists, so calculate and insert predicted times for that swimmer-event pair
                individual_event_data = grouped_dataset.get_group((swimmer, event))
                minimum_time = individual_event_data["time"].min()
                average_time = individual_event_data["time"].mean()
                median_time = individual_event_data["time"].median()
                team_data.append({"swimmer_id": swimmer, "event": event, "team": team,
                                  "minimum_time": minimum_time, "average_time": average_time, "median_time": median_time})
    # convert team_data dictionary into a pandas dataframe
    team_data = pd.DataFrame(team_data, columns=["swimmer_id", "event", "team", "minimum_time", "average_time", "median_time"])
    # This will have every possible athlete-event pairing, even if an athlete hasn't done that event before
    return team_data


def filter_from_dataset(swims, swimmers, team=None, gender=None, start_year=None, end_year=None):  # Not in use
    """
    function for filtering raw data
    :param swims: the database of swims from which we begin to whittle down the group data
    :param swimmers: database of swimmers containing swimmer name, gender, swimmer_id, and team_id
    :param team: an integer team id for the team whose data you may want to collect
    :param gender: character M or F representing gender whose swims you want to collect
    :param start_year: all data on the group must be after this year (a default month and start day are used)
    :param end_year: all data on the group must be before this year (a default month and start day are used)
    :return: filtered_data: dataset containing only data that you want
    """
    #NOTE: this might not be what is wanted, spend some time figuring out what is wrong with it, then make sure it is
    # what you are being asked for. If it can't separate the other parts then it is useless.
    filtered_data = swims.copy()
    filtered_swimmers = swimmers.copy()

    # filter by team, if one is specified
    if team:
        filtered_data = filtered_data[filtered_data["team"] == team]
        filtered_swimmers = filtered_swimmers[filtered_swimmers["team"] == team]
    # filter by gender, if one is specified
    if gender:
        filtered_swimmers = filtered_swimmers[filtered_swimmers["gender"].isin(gender)]
        gender_swimmers = filtered_swimmers.index.tolist()
        #for swimmer in swimmers.iterrows():
        #    if swimmer[1]["gender"] in gender:  # not sure why the 1 is needed but it works now
        #        gender_swimmers.append(swimmer[0])
        filtered_data = filtered_data[filtered_data["swimmer"].isin(gender_swimmers)]
    # filter out any dates from before start_year
    if start_year:
        start_timestamp = hf.convert_to_time(int(start_year), SEASON_LINE_MONTH, SEASON_LINE_DAY)
        filtered_data = filtered_data[filtered_data["date"] >= start_timestamp]
    # filter out any dates from after end_year
    if end_year:
        end_timestamp = hf.convert_to_time(int(end_year), SEASON_LINE_MONTH, SEASON_LINE_DAY)
        filtered_data = filtered_data[filtered_data["date"] <= end_timestamp]

    return filtered_data, filtered_swimmers

# TODO: might be worth to implement this and filter_by_team into get_athlete_data
def filter_by_date_range(swims, swimmers, start_timestamp=None, end_timestamp=None):  # Not in use
    """
    function for filtering raw data
    :param swims: the database of swims from which we begin to whittle down the group data
    :param swimmers: database of swimmers and general information about them
    :param start_timestamp: all data on the group must be after this timestamp
    :param end_year: all data on the group must be before this timestamp
    :return filtered_data: dataset containing only swim data that you want
    :return filtered_swimmers: dataset containing only swimmers that are mentioned in filtered_data.
    NOTE: may not contain swimmers who were present during desired time frame but don't have existing records in swims
    """
    #NOTE: this might not be what is wanted, spend some time figuring out what is wrong with it, then make sure it is
    # what you are being asked for. If it can't separate the other parts then it is useless.
    filtered_data = swims.copy()
    # if start timestamp is provided, filter out anything from before that timestamp
    if start_timestamp:
        filtered_data = filtered_data[filtered_data["date"] >= start_timestamp]
    # if end timestamp is provided, filter out anything from after that timestamp
    if end_timestamp:
        filtered_data = filtered_data[filtered_data["date"] < end_timestamp]

    # filter swimmers so that only swimmers present in filtered_data are present in the swimmer list.
    # the good: can be used for filtering out swimmers who have graduated and are no longer active swimmers
    # the bad: may remove currently active swimmers if they don't have swims from that time frame.
    filtered_swimmers = swimmers[swimmers.index.isin(list(filtered_data.swimmer.unique()))]

    return filtered_data, filtered_swimmers


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
    #  different input types to be equal to these values (i.e. {"minimum" : MIN,...}), or the reverse of this
    # NOTE: It also might be a good idea to use athlete ID instead of name somewhere in case two team members have the
    #  same name, but that is a problem for another time

    group_by_individual = team_data.groupby("swimmer_id")  # should uniquely identify every player

    athlete_prediction_dictionary = {}
    for athlete, athlete_data in group_by_individual:
        # get a single athlete's performance in all events, using performance measurement preference
        individual_data = athlete_data[["event", preference]].transpose()
        # name columns after events
        individual_data.columns = individual_data.iloc[0]
        # there should be an extra row that has all the column names in it. get rid of it
        individual_data.drop("event", inplace=True)
        # add a dictionary entry for that athlete with all of the events and predicted times
        athlete_prediction_dictionary[athlete] = individual_data.to_dict('records')[0]
    # convert dictionary to pandas dataframe and return it
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
    # retrieve times in swims table that were recorded from meet meet_id
    filter_by_meet = swims[swims["meet_id"] == meet_id].copy()  # works without copy() but will throw a warning
    # change values in time column of filter_by_meet to be either 1 or 0 depending on if a time is recorded in the row
    filter_by_meet['time'] = filter_by_meet['time'].notna().astype(int)

    group_by_individual = filter_by_meet.groupby("swimmer")

    # make a dictionary where keys are event codes and values are all 0
    event_dict = {event: 0 for event in event_list}

    meet_lineup = {}
    # makes a nested dictionary containing all athletes and events. all values in event dicts are False (0)
    for swimmer, swimmer_data in swimmers.iterrows():
        meet_lineup[swimmer] = event_dict.copy()

    # updates the dictionary made above so that events an athlete participated in are True (1)
    for swimmer, swimmer_data in group_by_individual:
        #  print(swimmer_data[["event","time"]])
        individual_data = swimmer_data[["event","time"]].transpose()
        individual_data.columns = individual_data.iloc[0]
        individual_data.drop("event", inplace=True)
        meet_lineup[swimmer].update(individual_data.to_dict('records')[0])
    return pd.DataFrame.from_dict(meet_lineup, orient='index')


def score_event(results_a, results_b, places, scoring_limit):
    """
    assigns points to groups based on who has the smallest score/time.
    :param results_a: list of recorded times for team a
    :param results_b: list of recorded times for team b
    :param places: list of point values awarded for first, second, etc place
    :param scoring_limit: the maximum number of swimmers per team that can score in the event
    :return: scores of team a and b
    """
    score_a = score_b = place_counter = 0
    all_times = results_a + results_b  # make a list of all times scored in the event
    all_times.sort()  # sort the list in ascending order
    a_scorers = b_scorers = 0
    results_dict = dict(Counter(all_times))  # convert list to dictionary. key is time, value is frequency of time

    for i in results_dict:
        if place_counter >= len(places):  # When there are no more points to award for the event break the loop
            break

        if results_dict[i] == 1:  # only one instance of the given time in either list (i.e. not a tie)
            if i in results_a:
                if a_scorers <= scoring_limit:
                    score_a = score_a + places[place_counter]
            else:
                if b_scorers <= scoring_limit:
                    score_b = score_b + places[place_counter]

        else:  # this signifies a tie, results_dict[i] > 1
            # split points awarded among all tied players
            points_per_player = sum(places[place_counter: place_counter + results_dict[i]]) / results_dict[i]
            if a_scorers <= scoring_limit:
                score_a += results_a.count(i) * points_per_player
            if b_scorers <= scoring_limit:
                score_b += results_b.count(i) * points_per_player

        a_scorers += results_a.count(i)
        b_scorers += results_b.count(i)
        place_counter = place_counter + results_dict[i]

    return score_a, score_b


def calculate_pred_score(perf_team_a, line_team_a, perf_team_b, line_team_b, scoring_method="Six Lane"):
    """
    returns the predicted score of team A for a swimming meet
    :param perf_team_a: Pandas dataframe of predicted performances for a given team A's swimmers
    :param line_team_a: Pandas Dataframe of a given lineup for a team A
    :param perf_team_b: Pandas dataframe of predicted performances for a given team B's swimmers
    :param line_team_b: Pandas Dataframe of a given lineup for a team B
    :param scoring_method: used to determine how points are allocated
    :return: pred_score: Integer value of team A's predicted
    """
    # create predicted performance matrices that only contain values for swimmers in the lineup
    lineup_scores_a = perf_team_a[line_team_a == 1]
    lineup_scores_b = perf_team_b[line_team_b == 1]

    # Team scores are integer values, initialize them at 0
    score_a = score_b = 0

    # Find times for all relay events and put them together in one dictionary
    event_list = lineup_scores_a.columns.tolist()
    r = re.compile(".L[MF].+")  # look for relay events. the lookup is performed by finding the leadoff
    relay_list = list(filter(r.match, event_list))
    relay_event_results = dict()
    for value in relay_list:
        #find out what type of relay value is and make list of legs in relay
        if value[2] is "F":
            # relay is a freestyle relay, so there are two types of legs
            legs = [value, value[:1]+"1"+value[2:]]
        elif value[2] is "M":
            # relay is medley relay, so there are four different legs
            legs = [value, value[:1] + "2" + value[2:], value[:1] + "3" + value[2:], value[:1] + "4" + value[2:]]
        # get sum of legs in relay for full relay time.
        time_a = lineup_scores_a[legs].sum().sum()
        time_b = lineup_scores_b[legs].sum().sum()
        # if event is in dictionary, update data, if not then append it
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
        temp_a, temp_b = score_event(results_a, results_b, RELAY_POINTS[scoring_method], SCORER_LIMIT[scoring_method][1])
        score_a += temp_a
        score_b += temp_b
    # score individual events, which we identify in the line below
    individual_events = list(filter(lambda x: x[2] not in "MF", event_list))
    for column_name in individual_events:
        results_a = lineup_scores_a[column_name][lineup_scores_a[column_name].notna()].tolist()
        results_b = lineup_scores_b[column_name][lineup_scores_b[column_name].notna()].tolist()
        temp_a, temp_b = score_event(results_a, results_b, INDIVIDUAL_POINTS[scoring_method],
                                     SCORER_LIMIT[scoring_method][0])
        # cannot add to two values at same time, so we have to assign points to temp values and then add those to score
        score_a += temp_a
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
            # get predicted scores for each possible lineup combination and add them to score matrix
            for team_b_index in range(len(lineup_matrix[1])):
                score_a, score_b = calculate_pred_score(team_list[0], lineup_matrix[0][team_a_index],
                                                        team_list[1], lineup_matrix[1][team_b_index])
                score_matrix[team_a_index][team_b_index] = (score_a, score_b)
    return score_matrix


# not sure if I should comment this for now just because its the messy demo code
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
    score_a, score_b = calculate_pred_score(bucknell_perf, bucknell_lineup, lehigh_perf, lehigh_lineup)
    print(score_a)
    print(score_b)
    # test matrix
    score_matrix = pred_score_matrix([bucknell_perf, lehigh_perf], [[bucknell_lineup, bucknell_inv_lin],
                                                                    [lehigh_lineup, bu_lehigh_lin]])
    print(score_matrix)

#demo_code()


def demo_code_with_time_filter():
    bucknell_vs_lehigh = 119957
    bucknell_invitational = 136124
    bu_lehigh = 119748
    swims, swimmers, teams, event_list = get_data()
    team_data_in_range, filtered_swimmers= filter_by_date_range(swims, swimmers, None, 1548460800) #day of bu_lehigh meet
    #swims = swims[swims["meet_id"] == bucknell_vs_lehigh]  # check to see that everything works for single meet
    team_data = get_athlete_data(team_data_in_range, filtered_swimmers, teams, event_list)
    pred_perf = get_predicted_performance_matrix(team_data, 'average_time')
    some_lineup = get_team_lineup(swims, filtered_swimmers, teams, event_list, bucknell_vs_lehigh)
    bucknell_perf = filter_by_team(pred_perf, filtered_swimmers, 184)
    bucknell_lineup = filter_by_team(some_lineup, filtered_swimmers, 184)
    lehigh_perf = filter_by_team(pred_perf, filtered_swimmers, 141)
    lehigh_lineup = filter_by_team(some_lineup, filtered_swimmers, 141)
    print("lineup example")
    print(bucknell_lineup)
    print("pred perf example")
    print(bucknell_perf)
    # get additional lineups for matrix
    bucknell_inv_lin = get_team_lineup(team_data_in_range, filtered_swimmers, teams, event_list, bucknell_invitational)
    bucknell_inv_lin = filter_by_team(bucknell_inv_lin, filtered_swimmers, 184)
    bu_lehigh_lin = get_team_lineup(team_data_in_range, filtered_swimmers, teams, event_list, bu_lehigh)
    bu_lehigh_lin = filter_by_team(bu_lehigh_lin, filtered_swimmers, 141)
    # test individual parts
    score_a, score_b = calculate_pred_score(bucknell_perf, bucknell_lineup, lehigh_perf, lehigh_lineup)
    print(score_a)
    print(score_b)
    # test matrix
    score_matrix = pred_score_matrix([bucknell_perf, lehigh_perf],[[bucknell_lineup, bucknell_inv_lin],
                                                                   [lehigh_lineup, bu_lehigh_lin]])
    print(score_matrix)
    print("tie test")
    score_matrix = pred_score_matrix([bucknell_perf, bucknell_perf], [[bucknell_lineup, bucknell_inv_lin],
                                                                      [bucknell_lineup, bucknell_inv_lin]])
    print(score_matrix)

demo_code_with_time_filter()