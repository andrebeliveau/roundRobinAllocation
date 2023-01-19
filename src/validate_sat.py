#!/usr/bin/env python3
import argparse
from datetime import datetime
from io import FileIO
import json
import math
from operator import mod
import random
from ortools.sat.python import cp_model

"""

Scheduling of friendly games for players sharing tennis courts (double games).

Input:
    number of tennis courts available
    number of players available (some players might sit on bench on some games )
    number of rounds (turn) to be played
    file containing set of players on bench on each round (outputed by bench_sat.py)

"""
class finalCourts:
    def __init__(self, fname, num_players, num_rounds, num_courts):
        self._fname = fname
        self._num_players = num_players
        self._num_rounds = num_rounds
        self._num_courts = num_courts
        self._num_players_per_court=4
        self._num_bench = num_players- (num_courts*self._num_players_per_court)
        self._all_players = range(num_players)
        self._all_rounds = range(num_rounds)
        self._all_played_courts = range(num_courts)
        self._all_courts = range(num_courts+1)
        self._all_bench = range(num_courts+1,num_courts+1)
        self._benchcourt=num_courts  # last "court" is the bench
        self._group_assignements = [[ [0 for x in self._all_players] for y in range(num_courts)] for z in self._all_rounds]
        self._games = []
        self._best = num_rounds
        self._better = num_players


    def read_team_groups(self):
        # Open the file and read the content in a list
        with open(f'final_{self._fname}', 'r') as filehandle:
            self._games = json.load(filehandle)
        #print(self._games)


    def print_final_courts(self):
        print(' '.ljust(14), ' '.join([f'court {i+1:2}'.ljust(19) for i in range(self._num_courts)]), 'bench'.ljust(10))
        for round in range(self._num_rounds):
            games = {}
            for court in range(self._num_courts+1):
                games[court]=self._games[round][f'{court}']
            str_games = [f'{v}'.ljust(18) for v in games.values()]
            print(f' Round {round+1:4}:  ', '  '.join(str_games) )

        playersCourtCount={}

        for court in range(self._num_courts):
            playersCourtCount[court] = []
            for player in range(self._num_players):
                courtCount=0
                for round in range(self._num_rounds):
                    if player+1 in self._games[round][f'{court}']:
                        courtCount=courtCount+1
                        #print(round, court, group, player+1)
                playersCourtCount[court].append(courtCount)
            print(f' Court     {court+1:4}:  {playersCourtCount[court]}') 
        
        playersCourtDiffMax = []
        for player in range(self._num_players):
            maxCount = max(playersCourtCount[court][player] for court in range(self._num_courts))
            minCount = min(playersCourtCount[court][player] for court in range(self._num_courts))
            playersCourtDiffMax.append(maxCount-minCount)
        self._better=playersCourtDiffMax.count(max(playersCourtDiffMax))

        time_now = datetime.now().strftime("%H:%M:%S")
        print(f' MaxDiff {max(playersCourtDiffMax):4}-{self._better}:  {playersCourtDiffMax}') 
            
        


    def print_player_stat(self):
        sameplayers=0
        for p1 in range(self._num_players):
            for p2 in range(p1+1, self._num_players):
                for round in range(self._num_rounds):
                    roundn=mod(round+1,self._num_rounds)
                    for court1 in range(self._num_courts):
                        for court2 in range(self._num_courts):
                            p1r1c1 = self._group_assignements[round][court1][p1]
                            p2r1c1 = self._group_assignements[round][court1][p2]
                            p1r2c2 = self._group_assignements[roundn][court2][p1]
                            p2r2c2 = self._group_assignements[roundn][court2][p2]
                            if p1r1c1+p2r1c1+p1r2c2+p2r2c2==4:
                                sameplayers=sameplayers+1

        time_now = datetime.now().strftime("%H:%M:%S")
        print(f'{time_now} : consecutive games with same players: {sameplayers}')

class groupTeams:
    def __init__(self, fname, num_players, num_rounds, num_courts):
        self._fname = fname
        self._num_players = num_players
        self._num_rounds = num_rounds
        self._num_courts = num_courts
        self._num_players_per_court=4
        self._num_bench = num_players- (num_courts*self._num_players_per_court)
        self._all_players = range(num_players)
        self._all_rounds = range(num_rounds)
        self._all_played_courts = range(num_courts)
        self._all_courts = range(num_courts+1)
        self._all_bench = range(num_courts+1,num_courts+1)
        self._benchcourt=num_courts  # last "court" is the bench
        self._group_assignements = [[ [0 for x in self._all_players] for y in range(num_courts)] for z in self._all_rounds]
        self._groups = []

    def read_team_groups(self):
        # Open the file and read the content in a list
        with open(f'groups_{self._fname}', 'r') as filehandle:
            self._groups = json.load(filehandle)

        for round in self._all_rounds:
            group_ass = self._groups[round]
            for court in self._all_played_courts:
                groupMembers=group_ass[f'{court}']
                self._group_assignements[round][court][groupMembers[0]-1]=1
                self._group_assignements[round][court][groupMembers[1]-1]=1
                self._group_assignements[round][court][groupMembers[2]-1]=1
                self._group_assignements[round][court][groupMembers[3]-1]=1
        #print(self._group_assignements)
        #print(self._groups)

    def print_team_groups(self):
        """Print team groups"""
        print(' '.ljust(14), ' '.join([f'court {i+1:2}'.ljust(19) for i in range(self._num_courts)]))
        for round in range(self._num_rounds):
            games = {}
            for court in range(self._num_courts):
                games[court]=self._groups[round][f'{court}']
            str_games = [f'{v}'.ljust(18) for v in games.values()]
            print(f' Round {round+1:4}:  ', '  '.join(str_games) )

    def print_player_stat(self):
        sameplayers=0
        for p1 in range(self._num_players):
            for p2 in range(p1+1, self._num_players):
                for round in range(self._num_rounds):
                    roundn=mod(round+1,self._num_rounds)
                    for court1 in range(self._num_courts):
                        for court2 in range(self._num_courts):
                            p1r1c1 = self._group_assignements[round][court1][p1]
                            p2r1c1 = self._group_assignements[round][court1][p2]
                            p1r2c2 = self._group_assignements[roundn][court2][p1]
                            p2r2c2 = self._group_assignements[roundn][court2][p2]
                            if p1r1c1+p2r1c1+p1r2c2+p2r2c2==4:
                                sameplayers=sameplayers+1

        time_now = datetime.now().strftime("%H:%M:%S")
        print(f'{time_now} : consecutive games with same players: {sameplayers}')

class benchGroup:
    def __init__(self, fname, num_players, num_rounds, num_courts):
        self._fname = fname
        self._num_players = num_players
        self._num_rounds = num_rounds
        self._num_courts = num_courts
        self._num_players_per_court=4
        self._num_bench = num_players- (num_courts*self._num_players_per_court)
        self._all_players = range(num_players)
        self._all_rounds = range(num_rounds)
        self._all_played_courts = range(num_courts)
        self._all_courts = range(num_courts+1)
        self._all_bench = range(num_courts+1,num_courts+1)
        self._benchcourt=num_courts  # last "court" is the bench
        self._bench_assignements=[ [ 0 for t in self._all_rounds] for p in self._all_players ]

    def read_bench_groups(self):
        if self._num_bench>0:
            bench_list = []
            # Open the file and read the content in a list
            with open(self._fname, 'r') as filehandle:
                bench_list = json.load(filehandle)
            count=0
            bench_matrix=[]
            # assign players on bench for each round in the model
            for y in self._all_rounds:
                bench=[]
                for z in range(self._num_bench):
                    self._bench_assignements[bench_list[count]-1][y]=1
                    count=count+1

    def print_bench(self):
        """Print the tournament schedule"""
        print(' '.ljust(11), ' On bench')
        for round in range(self._num_rounds):
            bench = []
            for player in range(self._num_players):
                if  self._bench_assignements[player][round]:
                    bench.append(player+1)
            print(f' round {round:4}:   {bench}' )

    def print_bench_optimization(self):
        sameplayers=0
        for p1 in range(self._num_players):
            for p2 in range(p1+1, self._num_players):
                for t1 in range(self._num_rounds):
                    for t2 in range(t1+1,self._num_rounds):
                        p1t1 = self._bench_assignements[p1][t1]
                        p2t1 = self._bench_assignements[p2][t1]
                        p1t2 = self._bench_assignements[p1][t2]
                        p2t2 = self._bench_assignements[p2][t2]
                        if p1t1+p2t1+p1t2+p2t2 == 4:
                            sameplayers=sameplayers+1
                            #print(f' Players {p1:2}-{p2:2}-{p3:2}: round:{t1} games:{g1} \
                            #    {p1t1g1}-{p2t1g1}-{p3t1g1} ')
        time_now = datetime.now().strftime("%H:%M:%S")
        print(f'{time_now} : bench with same players: {sameplayers}')

        if 0:
            for p1 in range(self._num_players):
                for t1 in range(self._num_rounds):
                    p1t1 = self._bench_assignements[p1][t1]
                    for t2 in range(self._num_rounds-1):
                        tn=mod(t1+1+t2,self._num_rounds)
                        p1tn = self._bench_assignements[p1][tn]
                        if p1t1==1 and p1tn==1:
                            print(f' Players {p1:2}: round:{t1}-{tn} numconsec {abs(tn-t1)} ')

def main():
    """Entry point of the program"""
    parser = argparse.ArgumentParser(description='Compute friendly tennis schedule.')
    parser.add_argument('--players',
                        '-p',
                        default=12,
                        type=int,
                        help='number of players (default:12)')
    parser.add_argument('--rounds',
                        '-r',
                        default=6,
                        type=int,
                        help='number of rounds (default:6)')
    parser.add_argument('--courts',
                        '-c',
                        default=3,
                        type=int,
                        help='number of courts played per round (default:3)')
    parser.add_argument('--file',
                        '-f',
                        default='bench.txt',
                        type=str,
                        help='filename for list of players on bench (default:bench.txt)')
    args = vars(parser.parse_args())

    # Data.
    fname=args['file']
    num_players = args['players']
    num_rounds = args['rounds']
    num_courts = args['courts'] 
    num_players_per_court=4
    num_bench = num_players- (num_courts*num_players_per_court)
        
    print(f"players: {num_players}, rounds: {num_rounds}, courts played per round: {num_courts}, on bench: {num_bench}")
    if num_bench>0:
        min_bench=math.floor(num_rounds*num_bench/num_players)
        max_bench=math.ceil(num_rounds*num_bench/num_players)
        distance_on_bench=math.ceil(num_players/num_bench)-2
        print(f"min/max presence on bench is {min_bench} / {max_bench}")
        print(f"minimal distance on bench is {distance_on_bench}")


    # Creates games variables.
    all_players = range(num_players)
    all_rounds = range(num_rounds)
    all_played_courts = range(num_courts)
    all_courts = range(num_courts+1)
    all_bench = range(num_courts+1,num_courts+1)
    benchcourt=num_courts  # last "court" is the bench

    rand_players=list(range(num_players))
    random.shuffle(rand_players)
    benchVar = {}
    duoVar = {}
    games = {}

    if 0:
        groupbench = benchGroup(fname, num_players, num_rounds, num_courts)
        groupbench.read_bench_groups()
        groupbench.print_bench()
        groupbench.print_bench_optimization()

        groupteam = groupTeams(fname, num_players, num_rounds, num_courts)
        groupteam.read_team_groups()
        groupteam.print_team_groups()
        groupteam.print_player_stat()

        finalcourts = finalCourts(fname, num_players, num_rounds, num_courts)
        finalcourts.read_team_groups()
        finalcourts.print_final_courts()
    else:
        with open(f'prefinal_{fname}', 'r') as f:
                myfile = f.read().splitlines()

        groups=[]
        for i in range(len(myfile)):
            games={}
            for court in range(num_courts):
                startix=15+(court*20)
                games[f'{court}']=json.loads(myfile[i][startix:startix+20])
            startix=15+(num_courts*20)
            games[f'{num_courts}']=json.loads(myfile[i][startix:])
            groups.append(games)
        print(groups)
        with open(f'final_{fname}', 'w') as filehandle: 
            json.dump(groups, filehandle)

if __name__ == '__main__':
    main()