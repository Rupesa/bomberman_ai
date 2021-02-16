from consts import Powerups, Speed
from game import LEVEL_POWERUPS
import queue
import Movement
import mapa

LEVEL_POWERUPS = {
    1: "Flames",
    2: "Bombs",
    3: "Detonator",
    4: "Speed",
    5: "Bombs",
    6: "Bombs",
    7: "Flames",
    8: "Detonator",
    9: "Bombpass",
    10: "Wallpass",
    11: "Bombs",
    12: "Bombs",
    13: "Detonator",
    14: "Bombpass",
    15: "Flames",
}

class Ai:

    def __init__(self):
        self.perseguir = 0
        self.cb = False #variavel debug para saber quando e posto uma bomba
        self.powersTest = [False,True,False,False,True,True,False,True,True,False,True,True,True,True,True,False]
        self.action = ""
        self.quick = False
        self.step = 0
        self.speed = Speed.SLOWEST
        self.pos = [1,1]
        self.bombs = []
        self.enemies = []
        self.enemiesPrev = []
        self.powerups = []
        self.exit = []
        self.timeout = 0
        self.lives = 0
        self.walls = []
        self.level = 1
        self.moves = []
        self.alvo = []
        self.map = None
        self.map2 = None
        self.xmap = 0 #comprimento do mapa
        self.ymap = 0 #largura do mapa
        self.max_distance = [[0,0], 0]
        self.timeHunting = 0
        self.timeOnWall = 0
        self.timeOnExit = 0
        self.override = False
        self.bombRange = 0
        self.next = None
        self.timeOnPorco = 0
        self.accquiredPowerups = []
        self.timeOnPower = 0 

    #Função para chamar algoritmos que resolvem os problemas
    #Devolve em string a proxima ação a ser executada
    #pode introduzir movimentos na fila
    def think(self):
        #print(self.action)
        if(self.action != "Fugir"):
            self.moves.append('A')
        if self.action != "Hunt"  and self.action != "Assassin":
            self.timeHunting = 0
        if self.action != "Assassin" and self.action != "Fugir":
            self.perseguir = 0
        if self.action != "Wall":
            self.timeOnWall = 0   
        if self.action != "Exit":
            self.timeOnExit = 0
        if self.action != "Porco":
            self.timeOnPorco = 0
        #print(self.action)
        if self.action == "Hunt" or self.action == "Assassin":
            if self.timeHunting > 2 or self.perseguir > 5:
                #self.override = True
                self.perseguir = 0
                self.timeHunting = 0
                Movement.destroy_wall(self)
                if (len(self.moves) == 0):
                    self.moves.append("B")
                self.cb = False
                self.action = "Perseguir"
                    
            else:
                if self.action == "Hunt" :
                    Movement.calc_letter(self.findPath(self.pos, self.closer_enemy(), self.action), self)
                else:
                    Movement.calc_letter(self.findPath(self.pos, self.next, self.action), self)
                self.action = "Perseguir"
                self.timeHunting += 1
                self.perseguir += 1
        elif self.action == "Fugir":
            # Movement.calc_letter(self.findPath(self.pos, Movement.calc_bomb_deploy(self), self.action), self)
            if(self.perseguir > 6):
                self.perseguir = 0
                Movement.destroy_wall(self)
                if (len(self.moves) == 0):
                    self.moves.append("B")
                self.cb = False
                self.action = "Perseguir"
            else:
                s = self.safe_place()
                self.perseguir += 1
                p = self.findPath(self.pos, s, self.action)
                Movement.calc_letter(p, self)
                if self.hasPowerup('Detonator'):
                    self.moves.append('A')
                    for i in range(0,2):
                        self.moves.append("")
                else:
                    for i in range(0,6):
                        self.moves.append("")
            
        elif self.action == "GetItem":
            if self.timeOnPower > 2:
                self.timeOnPower = 0
                Movement.destroy_wall(self) 
            else:
                Movement.calc_letter(self.findPath(self.pos, self.powerups[0][0], self.action), self)
                self.powersTest[self.level-1] = True
                self.accquiredPowerups.append(self.powerups[0])
                self.action = "Fugir"
                self.timeOnPower += 1
        elif self.action == "Wall":
            if self.timeOnWall > 2:
                #self.override = True
                p = self.findPath(self.pos, self.safe_place(), self.action)
                Movement.calc_letter(p, self)
                self.timeOnWall = 0
                self.action = "Perseguir"
            else:
                Movement.destroy_wall(self)
                self.action = "Perseguir"
                self.timeOnWall+=1
        elif self.action == "Porco":

            if self.timeOnPorco > 1:
                self.timeOnPorco = 0

                if len(self.walls) == 0:
                    p = self.findPath(self.pos, [1,1], "sentinela")
                    Movement.calc_letter(p, self)
                    for i in range(0,10):
                        self.moves.append("")
                    self.action = "Perseguir"
                else:
                    Movement.destroy_wall(self)
                    self.action = "Perseguir"
            else:
                self.timeOnPorco += 1
                if len(self.walls) == 0:
                    p = self.findPath(self.pos, [1,1], self.action)
                else:
                    p = self.findPath(self.pos, self.safe_place(), self.action)
                Movement.calc_letter(p,self)
                self.action = "Perseguir"
        elif self.action == "Exit":
            if self.timeOnExit > 2:
                
                #self.override = True
                self.timeOnExit = 0
                Movement.destroy_wall(self)
            else:
                l = self.findPath(self.pos, self.exit, self.action)
                Movement.calc_letter(l, self)
                self.action = "Perseguir"
                self.timeOnExit += 1

    #Função para consumir um movimento da fila "self.moves"
    def move(self):
        p = self.moves.pop(0)
        return p

    def needItem(self):
        if LEVEL_POWERUPS[self.level] == "Detonator" :
            if self.hasPowerup("Detonator"):
                return False
        elif LEVEL_POWERUPS[self.level] == "Bombpass":
            if self.hasPowerup("Bombpass"):
                return False
        return True

    def hasPowerup(self,power):
        for p in self.accquiredPowerups:
            if p[1] == power:
                return True

        return False

    def isSafe(self):
        if self.map2[self.pos[0]][self.pos[1]] != 4:
            return True
        return False

    def moveIsSafe(self):
        lastPos = self.pos
        for move in self.moves:
            if move == 'd':
                lastPos[0] += 1
            elif move == 'a':
                lastPos[0] -= 1
            elif move == 'w':
                lastPos[1] -= 1
            elif move == 's':
                lastPos[1] += 1

        if self.map2[lastPos[0]][lastPos[1]] == 4:
            return False

        return True

    def enemysAlive(self):
        return len(self.enemies) != 0

    def onlyBalloomsAlive(self):
        
        for e in self.enemies:
            if e['name'] != "Balloom":
                return False
        
        return True

    def getStrongEnemy(self):
        if self.onlyBalloomsAlive():
            return None
        min = []
        for e in self.enemies:
            if e['name'] != "Balloom":
                min = e['pos']
                break

        mindis = Movement.distance(self.pos, min)
        for e in self.enemies:
            if e['name'] != "Balloom":
                temp = Movement.distance(self.pos,e['pos'])
                if temp < mindis:
                    min = e['pos']
                    mindis = temp
            
        return min

    def getEnemy(self):
        min = self.enemies[0]["pos"]
        mindis = Movement.distance(self.pos, min)
        for e in self.enemies:
            temp = Movement.distance(self.pos, e['pos'])
            if temp < mindis:
                min = e['pos']
                mindis = temp
        return min


    def wallInRange(self):
        for i in range(1,self.bombRange):
            if self.map.map[self.pos[0]][self.pos[1]+i] == 1 or self.map.map[self.pos[0]][self.pos[1]-i] == 1 or self.map.map[self.pos[0]+i][self.pos[1]] == 1 or self.map.map[self.pos[0]-i][self.pos[1]] == 1:
                return True
        
        return False
    
    def isDestructible(self,wall):
        if self.map2[wall[0]][wall[1]] == 1:
            if wall in self.walls:
                return True
        
        return False


    #Função para limpar a fila "sem movimentos"
    def stop(self):
        while(not len(self.moves) == 0):
            self.moves.pop(0)

    def update(self,state,map):
        try:
            self.pos = state['bomberman']
            self.bombs = state['bombs']
            if len(self.bombs)!= 0:
                self.bombRange = self.bombs[0][2]
            if self.lives != state['lives']:
                self.enemiesPrev = []
            else:
                self.enemiesPrev = self.enemies

            self.enemies = state['enemies']
            self.powerups = state['powerups']
            self.exit = state['exit']
            if self.level == state['level']:
                self.timeout -= 1

            else:
                self.timeout = state['timeout']   

            self.lives = state['lives']
            self.walls = state['walls']
            self.level = state['level']
            self.map = map
        except:
            pass

    def inBombermanRange(self, posToCheck):

        inX = posToCheck[0] < self.pos[0] + 10 or posToCheck[0] > self.pos[0] - 10
        inY = posToCheck[1] < self.pos[0] + 10 or posToCheck[1] > self.pos[0] - 10
        return inX and inY  

    def isWallInPos(self, wallPos):
        if self.map.map[wallPos[0]][wallPos[1]] == 1:
            return True
        return False

    
    def isPosValid(self,pos):
        return pos[0] > 0 and pos[0] < 50 and pos[1] > 0 and pos[1] < 30

    def findPath(self, currPos, finalPos, type):
        try:
            max = 30
            if type == "Fugir":
                max = 30
            elif type == "sentinela":
                max = 200
            

            mapa = self.map.map

            startNode = Node(None, currPos)
            startNode.g = 0
            startNode.h = 0
            startNode.f = 0
            endNode = Node(None, finalPos)
            endNode.g = 0
            endNode.h = 0
            endNode.f = 0
            # initialize lists
            openList = []
            closedList = []

            openList.append(startNode)
            # loop until empty
            limit = 0
            while len(openList) > 0:

                # get current node
                currentNode = openList[0]
                currInd = 0
                for index, item in enumerate(openList):
                    if item.f < currentNode.f:
                        currentNode = item
                        currInd = index

                openList.pop(currInd)
                closedList.append(currentNode)

                # found final pos

                if currentNode == endNode or limit == max:
                    if limit == max:
                        self.quick = True
                    path = []
                    currentNode = currentNode
                    while currentNode is not None:
                        path.append(currentNode.pos)
                        currentNode = currentNode.parent
                        
                    return path[::-1]

                elif len(openList) > 100:
                    return []

                children = []
                for newPos in [[0,0],[0, -1], [0, 1], [-1, 0], [1, 0]]:
                    
                    nodePos = [currentNode.pos[0] + newPos[0], currentNode.pos[1] + newPos[1]]
                    
                    if nodePos[0] > (len(mapa) - 1) or nodePos[0] < 0 or nodePos[1] > (len(mapa[len(mapa) - 1]) - 1) or nodePos[1] < 0:
                        continue
                    #not self.hasPowerup('Wallpass')) on True
                    if ((mapa[nodePos[0]][nodePos[1]] == 1 and not self.isDestructible(nodePos)) or (mapa[nodePos[0]][nodePos[1]] == 1 and self.isDestructible(nodePos) and True )) or (self.map2[nodePos[0]][nodePos[1]] == 5 and True) or self.map2[self.pos[0]][self.pos[1]] == 6:
                        continue
                    
                    if self.exit != []:
                        if nodePos == self.exit and len(self.enemies)==0 and self.existItem() and self.needItem():
                            
                            continue
                    ##if len(self.powerups) != 0 and self.powerups[0][0] == nodePos and self.powerups[0][1] == "Detonator":
                        ##  continue

                    newNode = Node(currentNode, nodePos)

                    children.append(newNode)

                for child in children:
                    for closedChild in closedList:
                        if child == closedChild:
                            continue

                    child.g = currentNode.g + 1
                    child.h = ((child.pos[0] - endNode.pos[0]) ** 2) + ((child.pos[1] - endNode.pos[1]) ** 2)
                    if self.map2[child.pos[0]][child.pos[1]] == 4  :

                        child.h += 4

                    if self.action == "Fugir":
                        if self.map2[child.pos[0]][child.pos[1]] == 3:
                            child.h += 10
                        if self.map2[child.pos[0]][child.pos[1]] == 2:
                            child.h += 15
                        if currentNode.pos == child.pos:
                            child.h += 5

                    child.f = child.g + child.h

                    for openNode in openList:
                        if child == openNode and child.g > openNode.g:
                            continue

                    openList.append(child)
                limit += 1
        except:
            print("Findpath: ",finalPos)


    def update_map(self, state, mapa_inicial): #Função para refrescar o mapa que contem P.D. e inimigos
        # novoMapa = self.map.map[:][:]
        # novoMapa[0][0] = 7
        # print("Aqui")
        # print(self.map.map)
        # novoMapa = mapa.map.copy() #este mapa é da classe mapa
        # novoMapa = np.zeros((len(self.map.map),len(self.map.map[0])))
        try:
            self.max_distance = [[0,0], 0]
            novoMapa = []
            p = False
            for i in range(self.xmap):
                novoMapa = novoMapa + [[0] * self.ymap]

            for i in range(self.xmap):
                for j in range(self.ymap):
                    novoMapa[i][j] = mapa_inicial[i][j]
                    self.map.map[i][j] = mapa_inicial[i][j]
                    # print("Aqui")

            # Neste momento o novoMapa já tem as dimensões corretas e as paredes indestrutiveis marcadas com um 1

            # 0 = Livre
            # 1 = Parede indestrutivel, parede destrutivel e inimigos
            # 2 = Bomba, explosão e 1 tile do inimigo
            # 3 = Local onde colocar a bomba pra matar inimigo (2 tiles dele)

            for i in state['walls']:
                # Parede destrutivel
                novoMapa[i[0]][i[1]] = 1
                self.map.map[i[0]][i[1]] = 1
            # if False:
            for f in state['enemies']:
                i = f['pos']
                # Local do inimigo
                novoMapa[i[0]][i[1]] = 6
                self.map.map[i[0]][i[1]] = 6

                # Local onde fugir dos inimigos
                if novoMapa[i[0] - 1][i[1]] != 1:
                    novoMapa[i[0] - 1][i[1]] = 2
                if novoMapa[i[0] + 1][i[1]] == 0:
                    novoMapa[i[0] + 1][i[1]] = 2
                if novoMapa[i[0]][i[1] - 1] == 0:
                    novoMapa[i[0]][i[1] - 1] = 2
                if novoMapa[i[0]][i[1] + 1] == 0:
                    novoMapa[i[0]][i[1] + 1] = 2

                if novoMapa[i[0] - 1][i[1] - 1] == 0:
                    novoMapa[i[0] - 1][i[1] - 1] = 2
                if novoMapa[i[0] + 1][i[1] + 1] == 0:
                    novoMapa[i[0] + 1][i[1] + 1] = 2
                if novoMapa[i[0] + 1][i[1] - 1] == 0:
                    novoMapa[i[0] + 1][i[1] - 1] = 2
                if novoMapa[i[0] - 1][i[1] + 1] == 0:
                    novoMapa[i[0] - 1][i[1] + 1] = 2

                # Local onde colocar a bomba para matar inimigos
                # Depois é necessário rever se devemos colocar este 5 visto que vamos querer que o bomberman vá
                # para esta tile em vez de a contornar com o algoritmo de pesquisa
                if (i[0] - 2 > 0):
                    if (novoMapa[i[0] - 2][i[1]] == 0) and (novoMapa[i[0] - 1][i[1]] == 2):
                        novoMapa[i[0] - 2][i[1]] = 3
                if (i[0] + 2 < self.xmap):
                    if (novoMapa[i[0] + 2][i[1]] == 0) and (novoMapa[i[0] + 1][i[1]] == 2):
                        novoMapa[i[0] + 2][i[1]] = 3
                if (i[1] - 2 > 0):
                    if (novoMapa[i[0]][i[1] - 2] == 0) and (novoMapa[i[0]][i[1] - 1] == 2):
                        novoMapa[i[0]][i[1] - 2] = 3
                if (i[1] + 2 < self.ymap):
                    if (novoMapa[i[0]][i[1] + 2] == 0) and (novoMapa[i[0]][i[1] + 1] == 2):
                        novoMapa[i[0]][i[1] + 2] = 3

            # Local da explosão da bomba
            # if False:
            for f in state['bombs']:
                i = f[0]
                raio = f[2]
                p = False
                novoMapa[i[0]][i[1]] = 5
                if novoMapa[i[0] - 1][i[1]] == 0 or self.is_destr(state, [i[0] - 1, i[1]]):
                    if not self.is_destr(state, [i[0] - 1, i[1]]):
                        novoMapa[i[0] - 1][i[1]] = 4
                    else:
                        p = True
                    for x in range(2, raio+1):
                        if self.is_map([i[0]-x, i[1]]):
                            if novoMapa[i[0]-x][i[1]] == 0:
                                novoMapa[i[0]-x][i[1]] = 4
                if novoMapa[i[0] + 1][i[1]] == 0 or self.is_destr(state, [i[0] + 1, i[1]]):
                    if not self.is_destr(state, [i[0] + 1, i[1]]):
                        novoMapa[i[0] + 1][i[1]] = 4
                    else:
                        p = True
                    for x in range(2, raio+1):
                        if self.is_map([i[0]+x, i[1]]):
                            if novoMapa[i[0]+x][i[1]] == 0:
                                novoMapa[i[0]+x][i[1]] = 4
                if novoMapa[i[0]][i[1] - 1] == 0 or self.is_destr(state, [i[0], i[1] - 1]):
                    if not self.is_destr(state, [i[0], i[1] - 1]):
                        novoMapa[i[0]][i[1] - 1] = 4
                    else:
                        p = True
                    for x in range(2, raio+1):
                        if self.is_map([i[0], i[1]-x]):
                            if novoMapa[i[0]][i[1]-x] == 0:
                                novoMapa[i[0]][i[1]-x] = 4
                if novoMapa[i[0]][i[1] + 1] == 0 or self.is_destr(state, [i[0], i[1] + 1]):
                    if not self.is_destr(state, [i[0], i[1] + 1]):
                        novoMapa[i[0]][i[1] + 1] = 4
                    else:
                        p = True
                    for x in range(2, raio+1):
                        if self.is_map([i[0], i[1]+x]):
                            if novoMapa[i[0]][i[1]+x] == 0:
                                novoMapa[i[0]][i[1]+x] = 4

            # if p:
            #    print(novoMapa)
            # print(novoMapa)

            self.map2 = novoMapa.copy()
            # print("map:")
            # print(self.map.map)
            # print("map2:")
            # print(self.map2)
        except:
            pass

    def is_map(self, pos):
        return pos[0] >= 0 and pos[0] < self.xmap and pos[1] >= 0 and pos[1] < self.ymap

    def is_destr(self, state, pos):
        for a in state['walls']:
            if pos == a:
                return True
        return False

    def existItem(self):
        return len(self.powerups) != 0

    def enemysInRange(self):
        p = self.closer_enemy()
        return Movement.distance(p, self.pos) < 3


    def run_from_enemies(self, state): #Verifica se o bomberman se encontra perto de um inimigo e se assim
        #for, limpa a fila dos moves e adiciona movimentos para fugir
        #Tem de ser chamada depois de se atualizar o mapa
        pos = state['bomberman']
        if self.map2[pos[0]][pos[1]] == 2:
            letra = 'a'
            self.moves = []
            if self.map2[pos[0]+1][pos[1]] != 1 and self.map2[pos[0]+1][pos[1]] != 2:
                letra = 'd'
            elif self.map2[pos[0]][pos[1]-1] != 1 and self.map2[pos[0]][pos[1]-1] != 2:
                letra = 'w'
            elif self.map2[pos[0]][pos[1]+1] != 1 and self.map2[pos[0]][pos[1]+1] != 2:
                letra = 's'
            self.moves.append(letra)
        

    def deploy_and_run(self, state): #completar
        pos = state['bomberman']
        if self.map2[pos[0]][pos[1]] == 3:
            self.moves = ["B"]
            self.alvo = self.pos
            return True
        return False


    def closer_enemy(self):
        min = 1000
        min_e = [0,0]
        man = self.pos
        for en in self.enemies:
            e = en['pos']
            dis = abs(man[0] - e[0]) + abs(man[1] - e[1])
            if dis < min:
                min = dis
                min_e = e
        return min_e

    def closer_enemy2(self, man):
        min = 1000
        min_e = [0,0]
        #man = self.pos
        for en in self.enemies:
            e = en['pos']
            dis = abs(man[0] - e[0]) + abs(man[1] - e[1])
            if dis < min:
                min = dis
                min_e = e
        return min_e
    
    def closer_enemy_class(self):
        man = self.pos
        en_pos = self.enemies[0]['pos']
        min = abs(man[0] - en_pos[0]) + abs(man[1] - en_pos[1])
        min_e = []
        min_enemy= self.enemies[0]
        for en in self.enemies:
            e = en['pos']
            dis = abs(man[0] - e[0]) + abs(man[1] - e[1])
            if dis < min:
                min = dis
                min_enemy = en
        return min_enemy

    def safe_place(self):
        man = self.pos
        aux = [1, 1]

        if self.map2[man[0]+1][man[1]] != 1:

            if self.map2[man[0]+1][man[1]-1] != 1:
                aux = [man[0]+1,man[1]-1]
                if self.is_far(aux):
                    return aux
                if self.map2[man[0]+1][man[1]-2] != 1:
                    aux = [man[0]+1,man[1]-2]
                    if self.is_far( aux):
                        return aux
                    aux = [man[0],man[1]-2]
                    if self.is_far(aux) and self.map2[man[0]][man[1]-2] != 1:
                        return aux
                    aux = [man[0]+2,man[1]-2]
                    if self.is_far(aux) and self.map2[man[0]+2][man[1]-2] != 1:
                        return aux  

            if self.map2[man[0]+1][man[1]+1] != 1:
                aux = [man[0]+1,man[1]+1]
                if self.is_far(aux):
                    return aux
                if self.map2[man[0]+1][man[1]+2] != 1:
                    aux = [man[0]+1,man[1]+2]
                    if self.is_far( aux):
                        return aux
                    aux = [man[0],man[1]+2]
                    if self.is_far(aux) and self.map2[man[0]][man[1]+2] != 1:
                        return aux
                    aux = [man[0]+2,man[1]+2]
                    if self.is_far( aux) and self.map2[man[0]+2][man[1]+2] != 1:
                        return aux

            if self.map2[man[0]+2][man[1]] != 1:
                if self.map2[man[0]+2][man[1]-1] != 1:
                    aux = [man[0]+2,man[1]-1]
                    if self.is_far( aux):
                        return aux
                    aux = [man[0]+2,man[1]-2]
                    if self.is_far(aux) and self.map2[man[0]+2][man[1]-2] != 1:
                        return aux
                
                if self.map2[man[0]+2][man[1]+1] != 1:
                    aux = [man[0]+2,man[1]+1]
                    if self.is_far( aux):
                        return aux
                    aux = [man[0]+2,man[1]+2]
                    if self.is_far( aux) and self.map2[man[0]+2][man[1]+2] != 1:
                        return aux
                
                if self.map2[man[0]+3][man[1]] != 1:
                    aux = [man[0]+3,man[1]-1]
                    if self.is_far(aux) and self.map2[man[0]+3][man[1]-1] != 1:
                        return aux
                    aux = [man[0]+3,man[1]+1]
                    if self.is_far(aux) and self.map2[man[0]+3][man[1]+1] != 1:
                        return aux
                    
                    if self.map2[man[0]+4][man[1]] != 1:
                        aux = [man[0]+4,man[1]-1]
                        if self.is_far(aux) and self.map2[man[0]+4][man[1]-1] != 1:
                            return aux
                        aux = [man[0]+4,man[1]+1]
                        if self.is_far(aux) and self.map2[man[0]+4][man[1]+1] != 1:
                            return aux

                        if self.map2[man[0]+5][man[1]] != 1:
                            aux = [man[0]+5,man[1]-1]
                            if self.is_far(aux) and self.map2[man[0]+5][man[1]-1] != 1:
                                return aux
                            aux = [man[0]+5,man[1]+1]
                            if self.is_far(aux) and self.map2[man[0]+5][man[1]+1] != 1:
                                return aux

                    


        if self.map2[man[0]-1][man[1]] != 1:

            if self.map2[man[0]-1][man[1]-1] != 1:
                aux = [man[0]-1,man[1]-1]
                if self.is_far( aux):
                    return aux
                if self.map2[man[0]-1][man[1]-2] != 1:
                    aux = [man[0]-1,man[1]-2]
                    if self.is_far( aux):
                        return aux
                    aux = [man[0],man[1]-2]
                    if self.is_far( aux) and self.map2[man[0]][man[1]-2] != 1:
                        return aux
                    aux = [man[0]-2,man[1]-2]
                    if self.is_far( aux) and self.map2[man[0]-2][man[1]-2] != 1:
                        return aux  

            if self.map2[man[0]-1][man[1]+1] != 1:
                aux = [man[0]-1,man[1]+1]
                if self.is_far( aux):
                    return aux
                if self.map2[man[0]-1][man[1]+2] != 1:
                    aux = [man[0]-1,man[1]+2]
                    if self.is_far( aux):
                        return aux
                    aux = [man[0],man[1]+2]
                    if self.is_far( aux) and self.map2[man[0]][man[1]+2] != 1:
                        return aux
                    aux = [man[0]-2,man[1]+2]
                    if self.is_far (aux) and self.map2[man[0]-2][man[1]+2] != 1:
                        return aux

            if self.map2[man[0]-2][man[1]] != 1:
                if self.map2[man[0]-2][man[1]-1] != 1:
                    aux = [man[0]-2,man[1]-1]
                    if self.is_far( aux):
                        return aux
                    aux = [man[0]-2,man[1]-2]
                    if self.is_far(aux) and self.map2[man[0]-2][man[1]-2] != 1:
                        return aux
                
                if self.map2[man[0]-2][man[1]+1] != 1:
                    aux = [man[0]-2,man[1]+1]
                    if self.is_far( aux):
                        return aux
                    aux = [man[0]-2,man[1]+2]
                    if self.is_far(aux) and self.map2[man[0]-2][man[1]+2] != 1:
                        return aux

                if self.map2[man[0]-3][man[1]] != 1:
                    aux = [man[0]-3,man[1]-1]
                    if self.is_far(aux) and self.map2[man[0]-3][man[1]-1] != 1:
                        return aux
                    aux = [man[0]-3,man[1]+1]
                    if self.is_far(aux) and self.map2[man[0]-3][man[1]+1] != 1:
                        return aux

                    if self.map2[man[0]-4][man[1]] != 1:
                        aux = [man[0]-4,man[1]-1]
                        if self.is_far(aux) and self.map2[man[0]-4][man[1]-1] != 1:
                            return aux
                        aux = [man[0]-4,man[1]+1]
                        if self.is_far(aux) and self.map2[man[0]-4][man[1]+1] != 1:
                            return aux

                        if self.map2[man[0]-5][man[1]] != 1:
                            aux = [man[0]-5,man[1]-1]
                            if self.is_far(aux) and self.map2[man[0]-5][man[1]-1] != 1:
                                return aux
                            aux = [man[0]-5,man[1]+1]
                            if self.is_far(aux) and self.map2[man[0]-5][man[1]+1] != 1:
                                return aux


        if self.map2[man[0]][man[1]-1] != 1:

            if self.map2[man[0]-1][man[1]-1] != 1:
                aux = [man[0]-1,man[1]-1]
                if self.is_far(aux):
                    return aux
                if self.map2[man[0]-2][man[1]-1] != 1:
                    aux = [man[0]-2,man[1]-1]
                    if self.is_far(aux):
                        return aux
                    aux = [man[0]-2,man[1]]
                    if self.is_far( aux) and self.map2[man[0]-2][man[1]] != 1:
                        return aux
                    aux = [man[0]-2,man[1]-2]
                    if self.is_far(aux) and self.map2[man[0]-2][man[1]-2] != 1:
                        return aux  

            if self.map2[man[0]+1][man[1]-1] != 1:
                aux = [man[0]+1,man[1]-1]
                if self.is_far(aux):
                    return aux
                if self.map2[man[0]+2][man[1]-1] != 1:
                    aux = [man[0]+2,man[1]-1]
                    if self.is_far( aux):
                        return aux
                    aux = [man[0]+2,man[1]]
                    if self.is_far(aux) and self.map2[man[0]+2][man[1]] != 1:
                        return aux
                    aux = [man[0]+2,man[1]-2]
                    if self.is_far(aux) and self.map2[man[0]+2][man[1]-2] != 1:
                        return aux  

            if self.map2[man[0]][man[1]-2] != 1:
                if self.map2[man[0]-1][man[1]-2] != 1:
                    aux = [man[0]-1,man[1]-2]
                    if self.is_far(aux):
                        return aux
                    aux = [man[0]-2,man[1]-2]
                    if self.is_far(aux) and self.map2[man[0]-2][man[1]-2] != 1:
                        return aux
                
                if self.map2[man[0]+1][man[1]-2] != 1:
                    aux = [man[0]+1,man[1]-2]
                    if self.is_far(aux):
                        return aux
                    aux = [man[0]+2,man[1]-2]
                    if self.is_far(aux) and self.map2[man[0]+2][man[1]-2] != 1:
                        return aux

                if self.map2[man[0]][man[1]-3] != 1:
                    aux = [man[0]-1,man[1]-3]
                    if self.is_far(aux) and self.map2[man[0]-1][man[1]-3] != 1:
                        return aux
                    aux = [man[0]+1,man[1]-3]
                    if self.is_far(aux) and self.map2[man[0]+1][man[1]-3] != 1:
                        return aux

                    if self.map2[man[0]][man[1]-4] != 1:
                        aux = [man[0]-1,man[1]-4]
                        if self.is_far(aux) and self.map2[man[0]-1][man[1]-4] != 1:
                            return aux
                        aux = [man[0]+1,man[1]-4]
                        if self.is_far(aux) and self.map2[man[0]+1][man[1]-4] != 1:
                            return aux

                        if self.map2[man[0]][man[1]-5] != 1:
                            aux = [man[0]-1,man[1]-5]
                            if self.is_far(aux) and self.map2[man[0]-1][man[1]-5] != 1:
                                return aux
                            aux = [man[0]+1,man[1]-5]
                            if self.is_far(aux) and self.map2[man[0]+1][man[1]-5] != 1:
                                return aux
                        

                    
        if self.map2[man[0]][man[1]+1] != 1:

            if self.map2[man[0]-1][man[1]+1] != 1:
                aux = [man[0]-1,man[1]+1]
                if self.is_far( aux):
                    return aux
                if self.map2[man[0]-2][man[1]+1] != 1:
                    aux = [man[0]-2,man[1]+1]
                    if self.is_far( aux):
                        return aux
                    aux = [man[0]-2,man[1]]
                    if self.is_far( aux) and self.map2[man[0]-2][man[1]] != 1:
                        return aux
                    aux = [man[0]-2,man[1]+2]
                    if self.is_far( aux) and self.map2[man[0]-2][man[1]+2] != 1:
                        return aux  

            if self.map2[man[0]+1][man[1]+1] != 1:
                aux = [man[0]+1,man[1]+1]
                if self.is_far( aux):
                    return aux
                if self.map2[man[0]+2][man[1]+1] != 1:
                    aux = [man[0]+2,man[1]+1]
                    if self.is_far( aux):
                        return aux
                    aux = [man[0]+2,man[1]]
                    if self.is_far( aux) and self.map2[man[0]+2][man[1]] != 1:
                        return aux
                    aux = [man[0]+2,man[1]+2]
                    if self.is_far( aux) and self.map2[man[0]+2][man[1]+2] != 1:
                        return aux  

            if self.map2[man[0]][man[1]+2] != 1:
                if self.map2[man[0]-1][man[1]+2] != 1:
                    aux = [man[0]-1,man[1]+2]
                    if self.is_far( aux):
                        return aux
                    aux = [man[0]-2,man[1]+2]
                    if self.is_far( aux) and self.map2[man[0]-2][man[1]+2] != 1:
                        return aux
                
                if self.map2[man[0]+1][man[1]+2] != 1:
                    aux = [man[0]+1,man[1]+2]
                    if self.is_far(aux):
                        return aux
                    aux = [man[0]+2,man[1]+2]
                    if self.is_far(aux) and self.map2[man[0]+2][man[1]+2] != 1:
                        return aux

                if self.map2[man[0]][man[1]+3] != 1:
                    aux = [man[0]-1,man[1]+3]
                    if self.is_far(aux) and self.map2[man[0]-1][man[1]+3] != 1:
                        return aux
                    aux = [man[0]+1,man[1]+3]
                    if self.is_far(aux) and self.map2[man[0]+1][man[1]+3] != 1:
                        return aux

                    if self.map2[man[0]][man[1]+4] != 1:
                        aux = [man[0]-1,man[1]+4]
                        if self.is_far(aux) and self.map2[man[0]-1][man[1]+4] != 1:
                            return aux
                        aux = [man[0]+1,man[1]+4]
                        if self.is_far(aux) and self.map2[man[0]+1][man[1]+4] != 1:
                            return aux

                        if self.map2[man[0]][man[1]+5] != 1:
                            aux = [man[0]-1,man[1]+5]
                            if self.is_far(aux) and self.map2[man[0]-1][man[1]+5] != 1:
                                return aux
                            aux = [man[0]+1,man[1]+5]
                            if self.is_far(aux) and self.map2[man[0]+1][man[1]+5] != 1:
                                return aux

                        

        return self.max_distance[0]
        #Substituir pelo minimo
        #if self.map2[man[0]+2][man[1]+2] != 1:
        #    return [man[0]+2,man[1]+2]
        #if self.map2[man[0]+2][man[1]-2] != 1:
        #    return [man[0]+2,man[1]-2]
        #if self.map2[man[0]-2][man[1]+2] != 1:
        #    return [man[0]-2,man[1]+2]
        #return [man[0]-2,man[1]-2]

    def is_far(self,pos):
        min_distance = 4
        #print("Inimigo:")
        #print(self.closer_enemy())
        distance = Movement.distance(pos, self.closer_enemy2(pos))
        if distance > self.max_distance[1]:
            self.max_distance = [pos, distance]
        return distance > min_distance

            
    
class Node():

    def __init__(self, parent=None, pos=None):
        self.parent = parent
        self.pos = pos

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, node):
        return self.pos == node.pos

    def __str__(self):
        return "["+str(self.pos[0])+","+str(self.pos[1])+"]"
