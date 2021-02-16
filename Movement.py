import math
import random


##preenche a fila com os proximos movimentos para destruir a parede mais proxima

def destroy_wall(agent):
    
    if len(agent.walls) != 0:
        p = calc_bomb_deploy(agent)
        if p != None:
            if canPutBomb(agent,p):
                l = agent.findPath(agent.pos, p, "")

                calc_letter(l, agent)

                if (l != [] and not agent.quick) or len(l) < 5:
                    agent.moves.append("B")
                agent.quick = False
                agent.action = "Perseguir"
            else:
                agent.action = ""
        else:
            agent.action = ""
    else:
        agent.action = ""

def canPutBomb(agent,bomb_pos):
    if agent.map2[bomb_pos[0]][bomb_pos[1]]!=1:
        return True
    return False

def calc_bomb_deploy(agent):

    condicion = True
    final_pos = []
    w_array = []

    while(condicion):
        esq = True  # bomberman está à esquerda da bomba
        cima = True  # bomberman está a cima da bomba

        bomb = nextWall(agent)

        if(bomb == []):
            return None
        man = agent.pos
        if man[0] > bomb[0]:
            esq = False
        if man[1] > bomb[1]:
            cima = False

        if (agent.map2[bomb[0]][bomb[1] + 1] == 0 or agent.map2[bomb[0]][bomb[1] - 1] == 0):
            if (agent.map2[bomb[0] + 1][bomb[1]] == 0 or agent.map2[bomb[0] - 1][bomb[1]] == 0):
                if bomb[0] == man[0]:
                    if cima:
                        final_pos = [bomb[0], bomb[1] - 2]
                    else:
                        final_pos = [bomb[0], bomb[1] + 2]
                else:
                    if esq:
                        final_pos = [bomb[0] - 2, bomb[1]]
                    else:
                        final_pos = [bomb[0] + 2, bomb[1]]
            else:
                if cima:
                    final_pos = [bomb[0], bomb[1] - 1]
                else:
                    final_pos = [bomb[0], bomb[1] + 1]
        else:
            if esq:
                final_pos = [bomb[0] - 1, bomb[1]]
            else:
                final_pos = [bomb[0] + 1, bomb[1]]

        if agent.map2[final_pos[0]][final_pos[1]] != 4 and agent.map2[final_pos[0]][final_pos[1]] != 5:
            condicion = False
            for w in w_array:
                agent.walls.append(w)
        else:
            agent.walls.remove(bomb)
    return final_pos

##Devolve a posiçao da parede mais proxima

def nextWall(agent):
    if len(agent.walls) != 0:
        pos = agent.pos
        l = agent.walls
        min_value = distance(l[0], pos)
        min_pos = 0
        i = 1
        while i < len(l):
            d = distance(l[i],pos)
            if d <= min_value:
                min_value = d
                min_pos = i
            i =  i + 1

        return l[min_pos]
    return []


def distance(l, pos):
    #return math.sqrt(math.pow(l[0]-pos[0],2)+math.pow(l[1]-pos[1],2))
    return abs(l[0]-pos[0]) + abs(l[1]-pos[1])



def SearchRunBomb(agent):
    if len(agent.bombs) != 0:
        min = nextWall(agent)
        agent.walls.remove(min)
        bomb_pos = calc_bomb_deploy(agent)
        #bomb_pos = agent.safe_place()
        l = agent.findPath(agent.pos, bomb_pos)
        agent.quick = False
        calc_letter(l, agent)


def calc_letter(l, agent):
    
    poss = []

    for i in range(1, len(l)):
        ponto1 = l[i - 1]
        ponto2 = l[i]
        if ponto2[0] == ponto1[0] + 1:
            poss.append("d")
        elif ponto2[0] == ponto1[0] - 1:
            poss.append("a")
        elif ponto2[1] == ponto1[1] + 1:
            poss.append("s")
        elif ponto2[1] == ponto1[1] - 1:
            poss.append("w")
        elif ponto1==ponto2:
            poss.append(" ")

    for i in poss:
        agent.moves.append(i)
    



















