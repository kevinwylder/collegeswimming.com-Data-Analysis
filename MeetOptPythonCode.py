# MISSING ALL DATA STRUCTURES FROM EXCEL USING SOLVERSTUDIO (NAMED DICTIONARIES)
# SEE "SwimModel_FlyingStarts_OrderedOutput_WAR_LOOP_withEventsWithRelay.xlsm" WITH SOLVERSTUDIO  
#
#


# -*- coding: utf-8 -*-
"""
Created on Sat Jan 12 09:14:40 2019

@author: mdb025
"""
#NEED: 
    #MaxSolveTime minutes of solve time
    #OptGap decimal gap to stop 0-1 search

#Import PuLP modeller functions
from math import *
from pulp import *
import time
import os

## Begin INPUT SETTINGS
#1 if want to write output to file at the following path
#WriteOutput = 0
#path of the output file adjust for user
#would not  append to a file created in the SolverStudio working files folder
#if WriteOutput == 1:    
#    path = "G:\My Drive\SwimMeetOpt" + "\SwimMeetOptTrialResults.csv"

#Set solve time limit in seconds and optimality gap
#MaxSolveTime = 100
SolverTimeLimit = MaxSolveTime*60
#OptGap = 0.05
#Which Solver?
#SolverUsed = "CBC"
SolverUsed = "Gurobi"

if SolverUsed == "CBC":
    #Choose solver, and set it to problem, and build the model
    #Solve with CBC with logging and time limit. Parameter option: keepFiles=1 breaks it!
    #solver = pulp.COIN_CMD(msg=1, keepFiles=1, presolve=0, threads=1, maxSeconds=SolverTimeLimit,fracGap = OptGap)
    solver = pulp.COIN_CMD(msg=1, keepFiles=1, presolve=1, maxSeconds=SolverTimeLimit,fracGap=OptGap)
else:
    #Solve with Gurobi
    #Wouldn't work without changing SolverStudio settings to reference "GUROBI_CL.exe" (command line)
    #solver = pulp.GUROBI_CMD(keepFiles=1,options=[("MIPFocus",1),("TimeLimit",SolverTimeLimit)])
    solver = pulp.GUROBI_CMD(keepFiles=1,options=[("MIPFocus",1),("MIPGap",OptGap),("TimeLimit",SolverTimeLimit)])

    #Solve with Cplex. Throws error for write sol file
    #solver = pulp.CPLEX_scCMD(msg=1,options = ['set mip tolerances mipgap 0.2'])
    #solver = pulp.CPLEX_CMD(msg=1,timelimit=30)

## End INPUT SETTINGS

#DATA arrays from Excel workbook:
    #%data: athlete set, event set, stroke set,  event_noMR set, event11 set, indivrun set, relay set, relaynoMR set, homerank set, opprank set, place set, scenario set, scenprob[scenario], BigM[event11], opptime[opprank,event11,scenario], playperf[athlete, event_noMR], playperfMR[athlete, stroke],indivplcscore[place], relayplcscore[place], Maxevent, Maxindevent, Maxrelayevent, TopopprankIndiv, TopopprankRelay, TopplaceIndiv, TopplaceRelay

#highest relative rank for home
Tophomerank = 3;
# small constant
EPS = 0.0001;
#number of people on a relay team
relaySize = 4;

#subset of the actual athletes with some 
#ghosts because of hard relay requirements
#realathlete are only the actual athletes
athlete = athleteFull[:int(ActAthNum)+4]
realathlete = athleteFull[:int(ActAthNum)]
#for i in realathlete:
#    print "current realathlete index ", realathlete.index(i)
#    print "previous athlete ", realathlete[realathlete.index(i)-1]

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



#Print Entered Data
#print "NumStudents = ", int(NumStudents)

#UPDATE the ranges based on size of input problem
#rng_Students = range(int(NumStudents))

#Start the clock for first setup
setupStart = time.time()

#CLEAR THE OUTPUT ARRAYS
#for p in range(16):
#    for s in range(120):
#        array_AssignTeacherToStudent[s,p] = None
    
#INPUT CHECK
#empty cells are being read in as 'Nonetype.' Check for this and make them zero
#for s in rng_Students:
#    if StudentTeams[s] is None: #ADD ERROR CHECK that it's on the TeamNames list!
#        StudentTeams[s] = TeamNames[0] #default to first team
#    for t in rng_Teachers:
#        if array_TeacherTrain[s,t] is None:
#            array_TeacherTrain[s,t] = 0.0
            
print("Check Done")

#Instantiate our problem class
SwimMeetOpt = LpProblem("MeetMax", pulp.LpMaximize) 

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

scenscorevar = LpVariable.dicts('scenscorevar',(scenario),0,None,LpContinuous)

xvar = LpVariable.dicts('xvar',(athlete,event_noMR),0,1,LpBinary)
yvar = LpVariable.dicts('yvar',(athlete,event_noMR),0,1,LpBinary)
zvar = LpVariable.dicts('zvar',(athlete,event_noMR),0,1,LpBinary)

xvarstart = LpVariable.dicts('xvarstart',(athlete,relaynoMR),0,1,LpBinary)
yvarstart = LpVariable.dicts('yvarstart',(athlete,relaynoMR),0,1,LpBinary)
zvarstart = LpVariable.dicts('zvarstart',(athlete,relaynoMR),0,1,LpBinary)
 
xMRvar = LpVariable.dicts('xMRvar',(athlete, stroke),0,1,LpBinary)
yMRvar = LpVariable.dicts('yMRvar',(athlete, stroke),0,1,LpBinary)
zMRvar = LpVariable.dicts('zMRvar',(athlete, stroke),0,1,LpBinary)

rvar = LpVariable.dicts('rvar',(homerank,event11),None,None,LpContinuous)
wvar = LpVariable.dicts('wvar',(event11,homerank, place, scenario),0,1,LpBinary)
asgnvar = LpVariable.dicts('asgnvar',(athlete,event),0,1,LpBinary)

#print event11
#print indiv
#print indivplcscore
#print playperf

print(EventNoTimeArray)
   
   
#Objective Function - Maximize the weighted scenario (or expected) score against
#over eact scenario (or against each team)
SwimMeetOpt += lpSum(scenprob[s]*scenscorevar[s] for s in scenario), "Total Expected Score"
print "obj done"

# Multiple relay teams and they cannot sweep
for s in scenario:
    SwimMeetOpt += scenscorevar[s] == (lpSum(indivplcscore[p]*wvar[j][k][p][s] for j in indiv for k in homerank for p in place if k<=p) +
        lpSum(relayplcscore[p]*wvar[j][k][p][s] for j in relay for k in homerank for p in place if k<=p) +
        lpSum(2*wvar[j][1][4][s] - 2*wvar[j][3][3][s] for j in relay)), "Scenario %s Score"%s

# Exactly one 1st, 2nd, 3rd best time athlete in each indiv event
#WHAT IF CONCEDE A RACE or a PLACE?
for j in indiv:        
    SwimMeetOpt += lpSum(xvar[i][j] for i in athlete)  <= 1, "Exactly one 1st for indiv event %s"%j
    SwimMeetOpt += lpSum(yvar[i][j] for i in athlete)  <= 1, "Exactly one 2nd for indiv event %s"%j
    SwimMeetOpt += lpSum(zvar[i][j] for i in athlete)  <= 1, "Exactly one 3rd for indiv event %s"%j

# exactly 4 athletes in a relay. 
# IN SWIMMING CAN HAVE MORE THAN 1 team in relay
for j in relaynoMR:
    SwimMeetOpt += lpSum(xvar[i][j] for i in athlete) == relaySize-1, "Exactly 4 in 1st relay %s"%j
    SwimMeetOpt += lpSum(yvar[i][j] for i in athlete) == relaySize-1, "Exactly 4 in 2nd relay %s"%j
    SwimMeetOpt += lpSum(zvar[i][j] for i in athlete) == relaySize-1, "Exactly 4 in 3rd relay %s"%j
    SwimMeetOpt += lpSum(xvarstart[i][j] for i in athlete) == 1, "Exactly 1 to start 1st relay %s"%j
    SwimMeetOpt += lpSum(yvarstart[i][j] for i in athlete) == 1, "Exactly 1 to start 2nd relay %s"%j
    SwimMeetOpt += lpSum(zvarstart[i][j] for i in athlete) == 1, "Exactly 1 to start 3rd relay %s"%j

# exactly 4 athletes in a medly relay. 
# IN SWIMMING CAN HAVE MORE THAN 1 team in relay
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
    SwimMeetOpt += xvar[i]["100F"] + yvar[i]["100F"] + zvar[i]["100F"] + xvar[i]["500F"] + yvar[i]["500F"] + zvar[i]["500F"]<= 1,"No back to back 100F/500F for athlete %s"%i
    SwimMeetOpt += xvar[i]["200F"] + yvar[i]["200F"] + zvar[i]["200F"] + xvar[i]["200IM"] + yvar[i]["200IM"] + zvar[i]["200IM"]<= 1,"No back to back 200F/200IM for athlete %s"%i
    SwimMeetOpt += xvar[i]["100BS"] + yvar[i]["100BS"] + zvar[i]["100BS"] + xvar[i]["100BR"] + yvar[i]["100BR"] + zvar[i]["100BR"]<= 1,"No back to back 100BS/100BR for athlete %s"%i

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
    SwimMeetOpt += rvar[1][j] == lpSum(playperf[i,j]*xvar[i][j] for i in athlete) + 0.5*BigM[j] + 1.0 - lpSum(xvar[i][j]*(0.5*BigM[j] + 1) for i in athlete)
    SwimMeetOpt += rvar[2][j] == lpSum(playperf[i,j]*yvar[i][j] for i in athlete) + 0.5*BigM[j] + 2.0 - lpSum(yvar[i][j]*(0.5*BigM[j] + 2) for i in athlete)
    SwimMeetOpt += rvar[3][j] == lpSum(playperf[i,j]*zvar[i][j] for i in athlete) + 0.5*BigM[j] + 3.0 - lpSum(zvar[i][j]*(0.5*BigM[j] + 3) for i in athlete)
    
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
print "Total Setup Time = ", int(setupStop - setupStart), " secs"

#Test indiv athlete for WAR
if athletetest != "ALL" and athletetest != "ALL EVENTS" and athletetest in realathlete:
    print "Excluding athlete ",athletetest,"!"
    for j in indiv:
        SwimMeetOpt += xvar[athletetest][j]==0
        SwimMeetOpt += yvar[athletetest][j]==0
        SwimMeetOpt += zvar[athletetest][j]==0
    
    for j in relaynoMR:    
        SwimMeetOpt += xvar[athletetest][j]==0
        SwimMeetOpt += yvar[athletetest][j]==0
        SwimMeetOpt += zvar[athletetest][j]==0
        SwimMeetOpt += xvarstart[athletetest][j]==0
        SwimMeetOpt += yvarstart[athletetest][j]==0
        SwimMeetOpt += zvarstart[athletetest][j]==0

    for j in stroke:
        SwimMeetOpt += xMRvar[athletetest][j]==0
        SwimMeetOpt += yMRvar[athletetest][j]==0
        SwimMeetOpt += zMRvar[athletetest][j]==0

# The problem data is written to an .lp file
SwimMeetOpt.writeLP("SwimMeetOpt.lp")
SwimMeetOpt.setSolver(solver)

#test team for WAR
#add names to these constraints
#add a "prob.constraints["constraint name"].addterm(x_3, 10)" to add terms to a constraint
#you can remove terms by "prob.constraints["constraint name"].pop(x_1)"
#delete constraints by del prob.constraints[constraint_name]
#add them as usual
#if user wants to find PAR for all then,
if athletetest == "ALL":
    #loop through all the athletes and add constraints and subtract previous
    #constraints (if exist)
    print "Excluding ALL athletes sequentially:"
    for i in realathlete:
        print " Excluding athlete ",i,"!"
        
        #Add the constraints to exclude the current athlete 
        print " Adding constraints for athlete ",i,"!"
        for j in indiv:
            SwimMeetOpt += xvar[i][j]==0,"indiv xvar excl " + str(j)
            SwimMeetOpt += yvar[i][j]==0,"indiv yvar excl " + str(j)
            SwimMeetOpt += zvar[i][j]==0,"indiv zvar excl " + str(j)
        for j in relaynoMR:    
            SwimMeetOpt += xvar[i][j]==0, "relaynoMR xvar excl " + str(j)
            SwimMeetOpt += yvar[i][j]==0, "relaynoMR yvar excl " + str(j)
            SwimMeetOpt += zvar[i][j]==0, "relaynoMR zvar excl " + str(j)
            SwimMeetOpt += xvarstart[i][j]==0, "relaynoMR start xvar excl " + str(j)
            SwimMeetOpt += yvarstart[i][j]==0, "relaynoMR start yvar excl " + str(j)
            SwimMeetOpt += zvarstart[i][j]==0, "relaynoMR start zvar excl " + str(j)
        for j in stroke:
            SwimMeetOpt += xMRvar[i][j]==0, "relayMR xvar excl " + str(j)
            SwimMeetOpt += yMRvar[i][j]==0, "relayMR yvar excl " + str(j)
            SwimMeetOpt += zMRvar[i][j]==0, "relayMR zvar excl " + str(j)
        
        # The problem data is written AGAIN to an .lp file
        SwimMeetOpt.writeLP("SwimMeetOpt.lp")
        
        #Re-solve the model with "excluding athlete i" constraints above
        solveStart = time.time()
        SwimMeetOpt.solve()
        solveStop = time.time()
        #write the new total to the output data structure
        ScoreExcludeAthlete[i] = value(SwimMeetOpt.objective)
        print " Total Solve Time = ", int((solveStop - solveStart)/60.0), " mins. without student ",i
        print " Objective:", value(SwimMeetOpt.objective), " points"

        #Delete all the constraints you just added
        print " Delete last athlete's constraints"
        for j in indiv:
            del SwimMeetOpt.constraints["indiv_xvar_excl_" + str(j)]
            del SwimMeetOpt.constraints["indiv_yvar_excl_" + str(j)]
            del SwimMeetOpt.constraints["indiv_zvar_excl_" + str(j)]
        for j in relaynoMR: 
            del SwimMeetOpt.constraints["relaynoMR_xvar_excl_" + str(j)]
            del SwimMeetOpt.constraints["relaynoMR_yvar_excl_" + str(j)]
            del SwimMeetOpt.constraints["relaynoMR_zvar_excl_" + str(j)]
            del SwimMeetOpt.constraints["relaynoMR_start_xvar_excl_" + str(j)]
            del SwimMeetOpt.constraints["relaynoMR_start_yvar_excl_" + str(j)]
            del SwimMeetOpt.constraints["relaynoMR_start_zvar_excl_" + str(j)]
        for j in stroke:
            del SwimMeetOpt.constraints["relayMR_xvar_excl_" + str(j)]
            del SwimMeetOpt.constraints["relayMR_yvar_excl_" + str(j)]
            del SwimMeetOpt.constraints["relayMR_zvar_excl_" + str(j)]
            
#If all events, the exclude each athlete event pair, solve and report.
if athletetest == "ALL EVENTS":
    #loop through all the individual events for each athlete and add constraints and subtract previous
    #constraints (if exist)
    print "Excluding ALL athletes for each EVENT sequentially:"
    for i in realathlete:
        print " Excluding events for athlete ",i,"!"
        for j in indiv:
            if playperf[i,j] != EventNoTimeArray[j]: #if athlete has a REAL time in this event!
                print " Excluding event ",j," for athlete ",i, " and resolving!"
                #Add the constraints to remove the event for the athlete
                SwimMeetOpt += xvar[i][j]==0,"indiv xvar excl " + str(j)
                SwimMeetOpt += yvar[i][j]==0,"indiv yvar excl " + str(j)
                SwimMeetOpt += zvar[i][j]==0,"indiv zvar excl " + str(j)
                
                #Solve the problem for 
                #The problem data is written AGAIN to an .lp file
                SwimMeetOpt.writeLP("SwimMeetOpt.lp")
        
                #Re-solve the model with "excluding athlete i" constraints above
                solveStart = time.time()
                SwimMeetOpt.solve()
                solveStop = time.time()
                #write the new total to the output data structure
                ScoreExcludeAthandEvent[i,j] = value(SwimMeetOpt.objective)
                print " Total Solve Time = ", int((solveStop - solveStart)/60.0), " mins. without student ",i
                print " Objective:", value(SwimMeetOpt.objective), " points"

                #delete the constraints you just made!
                print " Delete last constraints"
                del SwimMeetOpt.constraints["indiv_xvar_excl_" + str(j)]
                del SwimMeetOpt.constraints["indiv_yvar_excl_" + str(j)]
                del SwimMeetOpt.constraints["indiv_zvar_excl_" + str(j)]
        for j in relaynoMR:
            if playperf[i,j] != EventNoTimeArray[j]: #if athlete has a REAL time in this event!
                print " Excluding event ",j," for athlete ",i, " and resolving!"
                #Add the constraints to remove the event for the athlete
                SwimMeetOpt += xvar[i][j]==0, "relaynoMR xvar excl " + str(j)
                SwimMeetOpt += yvar[i][j]==0, "relaynoMR yvar excl " + str(j)
                SwimMeetOpt += zvar[i][j]==0, "relaynoMR zvar excl " + str(j)
                SwimMeetOpt += xvarstart[i][j]==0, "relaynoMR start xvar excl " + str(j)
                SwimMeetOpt += yvarstart[i][j]==0, "relaynoMR start yvar excl " + str(j)
                SwimMeetOpt += zvarstart[i][j]==0, "relaynoMR start zvar excl " + str(j)
                
                #Solve the problem for 
                #The problem data is written AGAIN to an .lp file
                SwimMeetOpt.writeLP("SwimMeetOpt.lp")
        
                #Re-solve the model with "excluding athlete i" constraints above
                solveStart = time.time()
                SwimMeetOpt.solve()
                solveStop = time.time()
                #write the new total to the output data structure
                ScoreExcludeAthandEvent[i,j] = value(SwimMeetOpt.objective)
                print " Total Solve Time = ", int((solveStop - solveStart)/60.0), " mins. without student ",i
                print " Objective:", value(SwimMeetOpt.objective), " points"

                #delete the constraints you just made!
                print " Delete last constraints"
                del SwimMeetOpt.constraints["relaynoMR_xvar_excl_" + str(j)]
                del SwimMeetOpt.constraints["relaynoMR_yvar_excl_" + str(j)]
                del SwimMeetOpt.constraints["relaynoMR_zvar_excl_" + str(j)]
                del SwimMeetOpt.constraints["relaynoMR_start_xvar_excl_" + str(j)]
                del SwimMeetOpt.constraints["relaynoMR_start_yvar_excl_" + str(j)]
                del SwimMeetOpt.constraints["relaynoMR_start_zvar_excl_" + str(j)]
            
        #remove the athlete from the MR
        print " Excluding event MR for athlete ",i, " and resolving!"
        for j in stroke:
            SwimMeetOpt += xMRvar[i][j]==0, "relayMR xvar excl " + str(j)
            SwimMeetOpt += yMRvar[i][j]==0, "relayMR yvar excl " + str(j)
            SwimMeetOpt += zMRvar[i][j]==0, "relayMR zvar excl " + str(j)
            
        #The problem data is written AGAIN to an .lp file
        SwimMeetOpt.writeLP("SwimMeetOpt.lp")

        #Re-solve the model with "excluding athlete i" from MR constraints above
        solveStart = time.time()
        SwimMeetOpt.solve()
        solveStop = time.time()
        #write the new total to the output data structure
        ScoreExcludeAthandEvent[i,"200MR"] = value(SwimMeetOpt.objective)
        print " Total Solve Time = ", int((solveStop - solveStart)/60.0), " mins. without student ",i
        print " Objective:", value(SwimMeetOpt.objective), " points"

        #delete the constraints you just made!
        print " Delete last MR constraints"
        for j in stroke:
            del SwimMeetOpt.constraints["relayMR_xvar_excl_" + str(j)]
            del SwimMeetOpt.constraints["relayMR_yvar_excl_" + str(j)]
            del SwimMeetOpt.constraints["relayMR_zvar_excl_" + str(j)]    

#Solve the WHOLE problem with selected Solver and report it to Excel
print "Solve the baseline problem:"
solveStart = time.time()
SwimMeetOpt.solve()
solveStop = time.time()
print " Total Solve Time = ", int((solveStop - solveStart)/60.0), " mins"

#The status of the solution is printed to the screen
print " Status:", LpStatus[SwimMeetOpt.status]
print " Objective:", value(SwimMeetOpt.objective), " points"
#Return the objective function value for the best feasible soln found
BestObjective = lpSum(scenprob[s]*scenscorevar[s].varValue for s in scenario)
print " Best Found Solution Objective= ", BestObjective

OptObj = value(SwimMeetOpt.objective)
for s in scenario:
    scenscore[s] = scenscorevar[s].varValue
    print " Score under Scenario ",s, "is ", int(scenscorevar[s].varValue)


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

#output the finishing place of your three entered athletes in each event
#output array on "4. Assignment and Prediction": HomeAthFinPlace[homerank,event11]
#w[event11,homerank, place, scenario]
for k in homerank:
    for j in event11:
        mins = int(rvar[k][j].varValue/60)
        secs = rvar[k][j].varValue - mins*60
        HomeAthPredTime[k,j] = str(mins)+":"+str(secs)
        for p in place:
            if wvar[j][k][p][1].varValue == 1:
                HomeAthFinPlace[k,j] = p
                
                #if j == "200F":
                #print "athrank = ",k,", event = ",j,", p = ",p,", w = ", wvar[j][k][p][1].varValue
                
#For each event/relay leg record the athletes the times of athletes that are 
#entered into a list and sort them. Then write to the output arrays.
#repeat for next event.
#HARD CODED Cell locations - so fix if change "4. Assignment and Prediction" worksheet
for j in indiv:
    for i in athlete:
        if xvar[i][j].varValue == 1:
            HomeAthAssgnNamesIndiv[1,j] = i 
        elif yvar[i][j].varValue == 1:
            HomeAthAssgnNamesIndiv[2,j] = i
        elif zvar[i][j].varValue == 1:
            HomeAthAssgnNamesIndiv[3,j] = i

for j in relaynoMR:
    xl2 = 2
    xl4 = 2
    yl2 = 2
    yl4 = 2
    zl2 = 2
    zl4 = 2
    for i in athlete:
        if xvarstart[i][j].varValue == 1:
            if j == "200FR":
                HomeAthAssgnNamesRelay[1,1] = i
            else:
                HomeAthAssgnNamesRelay[1,4] = i
        if yvarstart[i][j].varValue == 1:
            if j == "200FR":
                HomeAthAssgnNamesRelay[1,2] = i
            else:
                HomeAthAssgnNamesRelay[1,5] = i
        if zvarstart[i][j].varValue == 1:
            if j == "200FR":
                HomeAthAssgnNamesRelay[1,3] = i
            else:
                HomeAthAssgnNamesRelay[1,6] = i
        if xvar[i][j].varValue == 1:
            if j == "200FR":
                HomeAthAssgnNamesRelay[xl2,1] = i
                xl2 += 1
            else:
                HomeAthAssgnNamesRelay[xl4,4] = i
                xl4 += 1
        if yvar[i][j].varValue == 1:
            if j == "200FR":
                HomeAthAssgnNamesRelay[yl2,2] = i
                yl2 += 1
            else:
                HomeAthAssgnNamesRelay[yl4,5] = i
                yl4 += 1
        if zvar[i][j].varValue == 1:
            if j == "200FR":
                HomeAthAssgnNamesRelay[zl2,3] = i
                zl2 += 1
            else:
                HomeAthAssgnNamesRelay[zl4,6] = i
                zl4 += 1
l=1                
for j in stroke:
    for i in athlete:
        if xMRvar[i][j].varValue == 1:
            HomeAthAssgnNamesRelay[l,7] = i
        if yMRvar[i][j].varValue == 1:
            HomeAthAssgnNamesRelay[l,8] = i
        if zMRvar[i][j].varValue == 1:
            HomeAthAssgnNamesRelay[l,9] = i
    l += 1
                          