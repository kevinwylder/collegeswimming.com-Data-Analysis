#Import PuLP modeller functions
from math import *
from pulp import *
import time
import os

# MISSING ALL DATA STRUCTURES FROM EXCEL USING SOLVERSTUDIO (NAMED DICTIONARIES)
# SEE "SwimModel_FlyingStarts_OrderedOutput_WAR_LOOP_withEventsWithRelay.xlsm" WITH SOLVERSTUDIO  
#
#TODO: Will Need to add PuLP and Gurobipy
#Print statements are Pyhon2 syntax and need to be updated

"""
Created on Sat Jan 12 09:14:40 2019

@author: mdb025
"""

# def MeetOpt(athleteFull,scenario,event_noMR,relaynoMR,stroke,homerank,event11, place,scenprob,indivplcscore,relayplcscore,indiv,opptime,BigM,Maxevent,Maxrelayevent,Maxindevent, playperf,playperfMR,playperfstart ):
def MeetOpt(athleteFull,scenario,scenprob,indiv_scored_events,relaynoMR,stroke,event11,event,relay,playperf):
    """
    #returns optimal response line up to the given opponent lineup(s) (called scenarios)
    :param athlete: dictionary of all the athlete names

    :return: opptime_team_a: dictionary of team A's top three times in each event
    """
        
    print("NOW WE'RE IN MEETOPT: \n")


    ## Begin INPUT SETTINGS
    #1 if want to write output to file at the following path
    #WriteOutput = 0
    #path of the output file adjust for user
    #would not  append to a file created in the SolverStudio working files folder
    #if WriteOutput == 1:    
    #    path = "G:\My Drive\SwimMeetOpt" + "\SwimMeetOptTrialResults.csv"

    #tuples for dictionaries
    event_noMR = indiv_scored_events + relaynoMR
    print("event_noMR: ", event_noMR)
    for item in scenprob.items():
        print(item)
    print("total SCORED events: ", event11)
    print("total ASSIGNED events: ", event)
    
    homerank = (1,2,3)  
    place = (1,2,3,4,5,6)
    ind_points = (9, 4, 3, 2, 1, 0)
    relay_points = (11,4,2,0,0,0)
    indivplcscore = dict(zip(place,ind_points))
    relayplcscore = dict(zip(place,relay_points)) 

    indiv = indiv_scored_events

    

    #Do these exist in college?
    Maxevent = 4
    Maxrelayevent = 1
    Maxindevent = 3


    #Set solve time limit in seconds and optimality gap
    MaxSolveTime = 10
    SolverTimeLimit = MaxSolveTime*60
    OptGap = 0.05
    #Which Solver?
    #SolverUsed = "CBC"
    #SolverUsed = "Gurobi"

    #if SolverUsed == "CBC":
        #Choose solver, and set it to problem, and build the model
        #Solve with CBC with logging and time limit. Parameter option: keepFiles=1 breaks it!
        #solver = pulp.COIN_CMD(msg=1, keepFiles=1, presolve=0, threads=1, maxSeconds=SolverTimeLimit,fracGap = OptGap)
        #solver = pulp.COIN_CMD(msg=1, keepFiles=1, presolve=1, maxSeconds=SolverTimeLimit,fracGap=OptGap)
    #else:
        #Solve with Gurobi
        #Wouldn't work without changing SolverStudio settings to reference "GUROBI_CL.exe" (command line)
        #solver = pulp.GUROBI_CMD(keepFiles=1,options=[("MIPFocus",1),("TimeLimit",SolverTimeLimit)])
        #solver = pulp.GUROBI_CMD(keepFiles=1,options=[("MIPFocus",1),("MIPGap",OptGap),("TimeLimit",SolverTimeLimit)])

        #Solve with Cplex. Throws error for write sol file
        #solver = pulp.CPLEX_scCMD(msg=1,options = ['set mip tolerances mipgap 0.2'])
        #solver = pulp.CPLEX_CMD(msg=1,timelimit=30)

    ## End INPUT SETTINGS

    #DATA arrays from Excel workbook:
        #%data: athlete set, event set, stroke set,  event_noMR set, event11 set, indivrun set, relay set, relaynoMR set, homerank set, opprank set, place set, scenario set, scenprob[scenario], BigM[event11], opptime[opprank,event11,scenario], playperf[athlete, event_noMR], playperfMR[athlete, stroke],indivplcscore[place], relayplcscore[place], Maxevent, Maxindevent, Maxrelayevent, TopopprankIndiv, TopopprankRelay

    #highest relative rank for home
    Tophomerank = 3;
    # small constant
    EPS = 0.0001;
    #number of people on a relay team
    relaySize = 4;

    
    #subset of the actual athletes with some 
    #ghosts because of hard relay requirements
    #realathlete are only the actual athletes
    ActAthNum = len(athleteFull)
    athlete = athleteFull[:int(ActAthNum)+4]
    realathlete = athleteFull[:int(ActAthNum)]
    for i in realathlete:
        print("current realathlete index ", realathlete.index(i))
        print("previous athlete ", realathlete[realathlete.index(i)-1])

    BigM = dict()

    #how big does BigM need to be?
    for e in event:
        maxEventTime = 0
        for a in athlete:     
            temp = playperf[a][e]        
            if temp > maxEventTime:
                maxEventTime = temp 
        BigM[e] = 2*maxEventTime
        print("event ", e," big M is ", BigM[e]) 

    #OUTPUT Arrays and Variables
        
    #Objective Value
    #OptObj

    #Scenario scores vs. opps
    #scenscore[scenario]: real[0..]
    # if assigned athlete has 1st time in event
    #x[athlete,event_noMR]: binary
    # if assigned athlete has 2nd best time in event 
    #y[athlete,event_noMR]: binary
    # if assigned athlete has 3rd best time in event
    #z[athlete, event_noMR]: binary
    # if assigned athlete has 1st time in medley
    #xMR[athlete,stroke]: binary
    # if assigned athlete has 2nd best time in medley 
    #yMR[athlete,stroke]: binary
    # if assigned athlete has 3rd best time in medley
    #zMR[athlete, stroke]: binary
    # rank of our athletes assigned to events
    #r[homerank,event11]: real
    #indicator variables of for outcome of event j versus opp 1
    #w[event11,homerank, place, scenario]: binary

    #assignments
    #asgn[athlete,event]: binary;

    #Start the clock for first setup
    setupStart = time.time()
                
    print("Check Done")

    

    #Instantiate our problem class
    SwimMeetOpt = LpProblem("MeetMax", LpMaximize) 

    #Initialize the decision variables
    #Scenario scores vs. opps
    scenscorevars = {}
    # if assigned athlete has 1st time in event
    xvars = {}
    # if assigned athlete has 2nd best time in event 
    yvars = {}
    # if assigned athlete has 3rd best time in event
    zvars = {}
    # if assigned athlete has 1st time in start time in event 200MR
    xvarstarts = {}
    # if assigned athlete has 2nd best time in start time in event 200MR
    yvarstarts = {}
    # if assigned athlete has 3rd best time in start time in event 200MR
    zvarstarts = {}
    # if assigned athlete has 1st time in medley
    xMRvars = {}
    # if assigned athlete has 2nd best time in medley 
    yMRvars = {}
    # if assigned athlete has 3rd best time in medley
    zMRvars = {}
    # rank of our athletes assigned to events
    rvars = {}
    #indicator variables of for outcome of event j versus opp 1
    wvars = {}
    #assignments
    asgnvars = {}

    #the actual lineup - NEED to have the fields match the fields for data frame
    optlineup = dict()

    
    #OPTIMIZATION DECISION VARIABLES defined in the MeetOpt paper using PuLP:

    #scenscorevar is a placeholder which will hold the expected score of our optimal
    #lineup against the lineup given in scenario i
    scenscorevar = LpVariable.dicts('scenscorevar',(scenario),0,None,LpContinuous)

    #these are placement variables for our athletes to events
    #xvar will hold the best assigned athlete from our team in an event
    #yvar will hold the second best assigned athlete from our team in an event
    #zvar will hold the third best assigned athlete from our team in an event
    #We assume that exactly three athletes are assigned to each event
    #the optimization creates the assignment and the ordering
    xvar = LpVariable.dicts('xvar',(athlete,event_noMR),0,1,LpBinary)
    yvar = LpVariable.dicts('yvar',(athlete,event_noMR),0,1,LpBinary)
    zvar = LpVariable.dicts('zvar',(athlete,event_noMR),0,1,LpBinary)

    
    #Same as above, but the starting leg for the "non-Medley Relay" relays
    xvarstart = LpVariable.dicts('xvarstart',(athlete,relaynoMR),0,1,LpBinary)
    yvarstart = LpVariable.dicts('yvarstart',(athlete,relaynoMR),0,1,LpBinary)
    zvarstart = LpVariable.dicts('zvarstart',(athlete,relaynoMR),0,1,LpBinary)
    
    #Same ordering as above, but for the athletes assigned to the 
    #best, second best, and third best medley relay
    xMRvar = LpVariable.dicts('xMRvar',(athlete, stroke),0,1,LpBinary)
    yMRvar = LpVariable.dicts('yMRvar',(athlete, stroke),0,1,LpBinary)
    zMRvar = LpVariable.dicts('zMRvar',(athlete, stroke),0,1,LpBinary)

    #rvar will hold the TIME of our first, second, and third fastest entrants in each event
    rvar = LpVariable.dicts('rvar',(homerank,event11),None,None,LpContinuous)
    #wvar will be 1 if our athlete with homerank h, in event j, finishes in overall place k, against
    #opponent scenario l
    #with this we can answer in which place our assigned athletes actually finish and score the meet! 
    wvar = LpVariable.dicts('wvar',(event11,homerank, place, scenario),0,1,LpBinary)
    #asgnvar is a generic variable which will be 1 if athlete i is assigned to event j (ignoring rank, etc.)
    #just answers the question "Is this athlete doing in this event?"
    asgnvar = LpVariable.dicts('asgnvar',(athlete,event),0,1,LpBinary)
    

    #Objective Function - Maximize the weighted scenario (or expected) score against
    #over eact scenario (or against each team)
    SwimMeetOpt += lpSum(scenprob[s]*scenscorevar[s] for s in scenario), "Total Expected Score"
    print("obj done")

    # Multiple relay teams and they cannot sweep so only the top two relay teams are included in the home team score
    #defines the variable scenscorevar (scenario score variable) for each scenario
    for s in scenario:
        SwimMeetOpt += scenscorevar[s] == (lpSum(indivplcscore[p]*wvar[j][k][p][s] for j in indiv for k in homerank for p in place if k<=p) +
            lpSum(relayplcscore[p]*wvar[j][k][p][s] for j in relay for k in homerank for p in place if k<=p) +
            lpSum(2*wvar[j][1][4][s] - 2*wvar[j][3][3][s] for j in relay)), "Scenario %s Score"%s

    
    #CREATING THE CONSTRAINTS FOR THE OPTIMIZATION PROBLEM:

    # Exactly one 1st, 2nd, 3rd best time athlete in each indiv event
    #WHAT IF CONCEDE A RACE or a PLACE?
    for j in indiv:        
        SwimMeetOpt += lpSum(xvar[i][j] for i in athlete)  <= 1, "Exactly one 1st for indiv event %s"%j
        SwimMeetOpt += lpSum(yvar[i][j] for i in athlete)  <= 1, "Exactly one 2nd for indiv event %s"%j
        SwimMeetOpt += lpSum(zvar[i][j] for i in athlete)  <= 1, "Exactly one 3rd for indiv event %s"%j

    # exactly 4 athletes in a relay for our first, second, and third relays
    # accounting for the opening leg not being a flying start in the non-MR relays
    for j in relaynoMR:
        SwimMeetOpt += lpSum(xvar[i][j] for i in athlete) == relaySize-1, "Exactly 3 legs in 1st relay %s"%j
        SwimMeetOpt += lpSum(yvar[i][j] for i in athlete) == relaySize-1, "Exactly 3 legs in 2nd relay %s"%j
        SwimMeetOpt += lpSum(zvar[i][j] for i in athlete) == relaySize-1, "Exactly 3 legs in 3rd relay %s"%j
        SwimMeetOpt += lpSum(xvarstart[i][j] for i in athlete) == 1, "Exactly 1 to start 1st relay %s"%j
        SwimMeetOpt += lpSum(yvarstart[i][j] for i in athlete) == 1, "Exactly 1 to start 2nd relay %s"%j
        SwimMeetOpt += lpSum(zvarstart[i][j] for i in athlete) == 1, "Exactly 1 to start 3rd relay %s"%j

    # Exactly 4 athletes in the first, second, and third best medley relay
    SwimMeetOpt += lpSum(xMRvar[i][j] for i in athlete for j in stroke) == relaySize, "Exactly 4 in 1st MR"
    SwimMeetOpt += lpSum(yMRvar[i][j] for i in athlete for j in stroke) == relaySize, "Exactly 4 in 2nd MR"
    SwimMeetOpt += lpSum(zMRvar[i][j] for i in athlete for j in stroke) == relaySize, "Exactly 4 in 3rd MR"
    
    # Athletes in at most Maxevent 
    for i in athlete: 
        SwimMeetOpt += lpSum(xvar[i][j] + yvar[i][j] + zvar[i][j] for j in indiv)  + lpSum(xvar[i][j] + yvar[i][j] + zvar[i][j] + xvarstart[i][j] + yvarstart[i][j] + zvarstart[i][j] for j in relaynoMR)+ lpSum(xMRvar[i][j]+yMRvar[i][j]+zMRvar[i][j] for j in stroke) <= Maxevent, "Max events for athlete %s"%i

    # Athletes in at most Maxrelayevent
    for i in athlete:
        SwimMeetOpt += lpSum(xvar[i][j] + yvar[i][j] + zvar[i][j] + xvarstart[i][j] + yvarstart[i][j] + zvarstart[i][j] for j in relaynoMR)+ lpSum(xMRvar[i][j]+yMRvar[i][j]+zMRvar[i][j] for j in stroke) <= Maxrelayevent,"Max Relay events for athlete %s"%i
        # Athletes in at most Maxindivevent
        SwimMeetOpt += lpSum(xvar[i][j] + yvar[i][j] + zvar[i][j] for j in indiv) <= Maxindevent,"Max Indiv events for athlete %s"%i 

        # Back to back event constraints
        #HARD CODED WITH EVENT NAMES AND NEEDS TO BE CHECKED
        '''
        SwimMeetOpt += xvar[i]["100F"] + yvar[i]["100F"] + zvar[i]["100F"] + xvar[i]["500F"] + yvar[i]["500F"] + zvar[i]["500F"]<= 1,"No back to back 100F/500F for athlete %s"%i
        SwimMeetOpt += xvar[i]["200F"] + yvar[i]["200F"] + zvar[i]["200F"] + xvar[i]["200IM"] + yvar[i]["200IM"] + zvar[i]["200IM"]<= 1,"No back to back 200F/200IM for athlete %s"%i
        SwimMeetOpt += xvar[i]["100BS"] + yvar[i]["100BS"] + zvar[i]["100BS"] + xvar[i]["100BR"] + yvar[i]["100BR"] + zvar[i]["100BR"]<= 1,"No back to back 100BS/100BR for athlete %s"%i
        '''

        # Athletes can only be one of the 1st, 2nd, or 3rd ranked atheletes assigned to an event j
        for j in indiv:
            SwimMeetOpt += xvar[i][j] + yvar[i][j] + zvar[i][j] <= 1,"athlete %s can only be one of the 1st, 2nd, or 3rd ranked athletes assigned to an event %s"%(i,j)

    #Athletes can only be 1st, 2nd, or 3rd ranked relay team for each relay j
    for i in athlete:  
        for j in relaynoMR:
            SwimMeetOpt += xvar[i][j] + yvar[i][j] + zvar[i][j] + xvarstart[i][j] + yvarstart[i][j] + zvarstart[i][j] <= 1,"athlete %s can only be one of the 1st, 2nd, or 3rd ranked athletes assigned to a relay event %s"%(i,j)
        
        # Each athlete can only perform one stroke in medley relay
        SwimMeetOpt += lpSum(xMRvar[i][j]+yMRvar[i][j]+zMRvar[i][j] for j in stroke) <= 1, "Athlete %s can only perform one stroke in medley relay"%i
    
        
    #Each stroke on each relay team can only have one athlete assigned
    for j in stroke:
        SwimMeetOpt += lpSum(xMRvar[i][j]for i in athlete) <= 1, "Stroke %s on 1st MR can only have one athlete"%j
        SwimMeetOpt += lpSum(yMRvar[i][j]for i in athlete) <= 1, "Stroke %s on 2nd MR can only have one athlete"%j    
        SwimMeetOpt += lpSum(zMRvar[i][j]for i in athlete) <= 1, "Stroke %s on 3rd MR can only have one athlete"%j
    
    #realized rank of athletes from assignments
    #IF NO RUNNER NEED TO ASSIGN A time larger than the third runner, smaller than the BigM for rank
    for j in indiv: 
        SwimMeetOpt += rvar[1][j] == lpSum(playperf[i][j]*xvar[i][j] for i in athlete) + 0.5*BigM[j] + 1.0 - lpSum(xvar[i][j]*(0.5*BigM[j] + 1) for i in athlete)
        SwimMeetOpt += rvar[2][j] == lpSum(playperf[i][j]*yvar[i][j] for i in athlete) + 0.5*BigM[j] + 2.0 - lpSum(yvar[i][j]*(0.5*BigM[j] + 2) for i in athlete)
        SwimMeetOpt += rvar[3][j] == lpSum(playperf[i][j]*zvar[i][j] for i in athlete) + 0.5*BigM[j] + 3.0 - lpSum(zvar[i][j]*(0.5*BigM[j] + 3) for i in athlete)
    
     # The problem data is written to an .lp file
    SwimMeetOpt.writeLP("SwimMeetOpt.lp")
    '''
       
    for j in relaynoMR: 
        SwimMeetOpt += rvar[1][j] == lpSum(playperf[i,j]*xvar[i][j] + playperfstart[i,j]*xvarstart[i][j] for i in athlete) + relaySize*0.5*BigM[j] + relaySize*1.0 - lpSum((xvar[i][j]+xvarstart[i][j])*(0.5*BigM[j] + 1) for i in athlete)
        SwimMeetOpt += rvar[2][j] == lpSum(playperf[i,j]*yvar[i][j] + playperfstart[i,j]*yvarstart[i][j] for i in athlete) + relaySize*0.5*BigM[j] + relaySize*2.0 - lpSum((yvar[i][j]+yvarstart[i][j])*(0.5*BigM[j] + 2) for i in athlete)
        SwimMeetOpt += rvar[3][j] == lpSum(playperf[i,j]*zvar[i][j] + playperfstart[i,j]*zvarstart[i][j] for i in athlete) + relaySize*0.5*BigM[j] + relaySize*3.0 - lpSum((zvar[i][j]+zvarstart[i][j])*(0.5*BigM[j] + 3) for i in athlete)

    SwimMeetOpt += rvar[1]["200MR"] == lpSum(playperfMR[i,j]*xMRvar[i][j] for i in athlete for j in stroke) + relaySize*0.5*BigM["200MR"] + relaySize*1.0 - lpSum(xMRvar[i][j]*(0.5*BigM["200MR"] + 1) for i in athlete for j in stroke)
    SwimMeetOpt += rvar[2]["200MR"] == lpSum(playperfMR[i,j]*yMRvar[i][j] for i in athlete for j in stroke) + relaySize*0.5*BigM["200MR"] + relaySize*2.0 - lpSum(yMRvar[i][j]*(0.5*BigM["200MR"] + 2) for i in athlete for j in stroke)
    SwimMeetOpt += rvar[3]["200MR"] == lpSum(playperfMR[i,j]*zMRvar[i][j] for i in athlete for j in stroke) + relaySize*0.5*BigM["200MR"] + relaySize*3.0 - lpSum(zMRvar[i][j]*(0.5*BigM["200MR"] + 2) for i in athlete for j in stroke)

    #force consistency in rank order
    for k in homerank:
        for j in event11:
            if k < Tophomerank:
            SwimMeetOpt += rvar[k][j] <= rvar[k+1][j]

    #runner/team of rank k can be place in at most one place (1st, 2nd, or 3rd) vs opp 1
    for j in indiv:
        for k in homerank:
            for s in scenario:
                SwimMeetOpt += lpSum(wvar[j][k][l][s] for l in place if l >= k) <= 1 
    for j in relay:
        for k in homerank:
            for s in scenario:        
                SwimMeetOpt += lpSum(wvar[j][k][l][s] for l in place if l >= k) <= 1

    #Did your first runner 1st runner 1st, 2nd in 2nd or 3rd in third vs opp 
    for j in indiv:
        for k in homerank: 
            for l in place: 
                for s in scenario:
                    if k==l: 
                        SwimMeetOpt += rvar[k][j] <= opptime[1,j,s]*wvar[j][k][l][s] + BigM[j] - BigM[j]*wvar[j][k][l][s]
                    if l>k and l<(TopopprankIndiv + k): 
                        SwimMeetOpt += rvar[k][j] <= opptime[l-k+1,j,s]*wvar[j][k][l][s] + BigM[j] - BigM[j]*wvar[j][k][l][s]
                    if l>k  and l<=(TopopprankIndiv + k):
                        SwimMeetOpt += rvar[k][j] >= opptime[l-k,j,s]*wvar[j][k][l][s]

    #Did your first relay 1st runner 1st, 2nd in 2nd or 3rd in third vs opp
    for j in relay: 
        for k in homerank:
            for l in place:
                for s in scenario: 
                    if k==l: 
                        SwimMeetOpt += rvar[k][j] <= opptime[1,j,s]*wvar[j][k][l][s] + 5*BigM[j]- 5*BigM[j]*wvar[j][k][l][s]
                    if l>k and l< (TopopprankRelay + k):
                        SwimMeetOpt += rvar[k][j] <= opptime[l-k+1,j,s]*wvar[j][k][l][s] + 5*BigM[j]- 5*BigM[j]*wvar[j][k][l][s]
                    if l>k  and l<=(TopopprankRelay + k):
                        SwimMeetOpt += rvar[k][j] >= opptime[l-k,j,s]*wvar[j][k][l][s]

    #events assigned to athletes
    for i in athlete: 
        for j in event_noMR: 
            SwimMeetOpt += asgnvar[i][j] == xvar[i][j] + yvar[i][j] + zvar[i][j]


    #events assigned to athletes
    for i in athlete:
        for j in stroke: 
            SwimMeetOpt += asgnvar[i][j] == xMRvar[i][j] + yMRvar[i][j] + zMRvar[i][j]

    #Report the total setup time
    setupStop = time.time()
    print("Total Setup Time = ", int(setupStop - setupStart), " secs")

    # The problem data is written to an .lp file
    SwimMeetOpt.writeLP("SwimMeetOpt.lp")
    SwimMeetOpt.setSolver(solver)

    #Solve the WHOLE problem with selected Solver and report it to Excel
    print("Solve the baseline problem:")
    solveStart = time.time()
    SwimMeetOpt.solve()
    solveStop = time.time()
    print(" Total Solve Time = ", int((solveStop - solveStart)/60.0), " mins")

    #The status of the solution is printed to the screen
    print(" Status:", LpStatus[SwimMeetOpt.status]
    print(" Objective:", value(SwimMeetOpt.objective), " points")

    #Return the objective function value for the best feasible soln found
    BestObjective = lpSum(scenprob[s]*scenscorevar[s].varValue for s in scenario)
    print(" Best Found Solution Objective= ", BestObjective)

    OptObj = value(SwimMeetOpt.objective)
    for s in scenario:
        scenscore[s] = scenscorevar[s].varValue
        print(" Score under Scenario ",s, "is ", int(scenscorevar[s].varValue))


    # Each of the variables is printed with it's resolved optimum value
    for i in athlete:
        for j in event_noMR:
            asgn[i,j] = asgnvar[i][j].varValue
            x[i,j] = xvar[i][j].varValue
            y[i,j] = yvar[i][j].varValue
            z[i,j] = zvar[i][j].varValue
        for j in relaynoMR:
            xstart[i,j] = xvarstart[i][j].varValue
            ystart[i,j] = yvarstart[i][j].varValue
            zstart[i,j] = zvarstart[i][j].varValue
        for j in stroke: 
            xMR[i,j] = xMRvar[i][j].varValue
            yMR[i,j] = yMRvar[i][j].varValue
            zMR[i,j] = zMRvar[i][j].varValue

    
    #Return the lineup found in form of a 2-D dictionary of assignment for each athlete
    #NEED this to match the events and A/B/C team of relays.
    return optlineup
    '''
    return

                            