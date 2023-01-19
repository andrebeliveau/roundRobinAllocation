# roundRobinAllocation
Scheduling of friendly games for players sharing tennis (or other racket sport) courts (doubles).

Addressed problem:
18 friendly players want to share 3 courts to play tennis (doubles). 
On every round, 12 players (3 courts x 4 players) are assigned on courts 
and 6 players stay on the bench.

A number of constrains are defined and the program will allocate players 
on different courts and on the bench.

The following basic constrains are defined:
    Each player must sit on bench between min and max number of times
    Each player must play a minimal number of games before sitting on bench again
    Every player should have a chance to play with or against every other player
    Every player should play an equal (or almost) number of rounds
    Every player should not play with the same player (partner) more than once, but he/she could
        play against him/her multiple times
Constrains details are available in source code

At the end, we want players to have a chance to play with and against different players, 
on different courts and distribute those allocation fairly

The program has been validated for different number of players, courts and rounds

Make sure the following python packages are locally avalaible:
ortools.sat.python

Inputs/Parameters:
    number of courts (-c)
    number of players (-p)
    number of rounds (turn) to be played (-r)
    filename used to save/restore results (-f)

Typical usage:

The allocation occurs in 3 phases:
1) First, allocate players on bench (benchAlloc.py) using bench constraints only
    results are saved in file
    ex:  python3 benchAlloc.py -p18 -r12 -c3 -f allocationResult_18.txt
2) Second, allocate players in groups of 4 players using group constrains
    result are save in file and list group of players.
    ex:  python3 teamAlloc.py -p18 -r12 -c3 -f allocationResult_18.txt
3) Third, allocate pair of players (who plays with and against eachother) 
    and allocate them on specific courts
    ex:  python3 courtAlloc.py -p18 -r12 -c3 -f allocationResult_18.txt




