import sys
import json
import asyncio
import websockets
import getpass
import os
from Ai import Ai
import queue

from mapa import Map
import Movement



async def agent_loop(server_address="localhost:8000", agent_name="student"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:

        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)

        # You can create your own map representation or use the game representation:
        mapa = Map(size=game_properties["size"], mapa=game_properties["map"])

        agent = Ai()
        agent.map = mapa
        agent.xmap = len(mapa.map)
        agent.ymap = len(mapa.map[0])

        mapa_inicial = []
        for i in range(agent.xmap):
            mapa_inicial = mapa_inicial + [[0]*agent.ymap]

        for i in range(agent.xmap):
            for j in range(agent.ymap):
                if agent.map.map[i][j] != 2:
                    mapa_inicial[i][j] = agent.map.map[i][j]
                else:
                    agent.map.map[i][j] = 0

        
        i = 0
        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server
                
                agent.update(state, mapa)
                agent.update_map(state, mapa_inicial)
                
                if agent.action != "Perseguir" and agent.action != "Fugir":
                    if agent.cb:
                        
                        if len(agent.bombs) == 0:
                            agent.cb = False
                        agent.action = "Fugir"
                        agent.think()
                    else:
                        if agent.enemysAlive() and agent.enemysInRange():    
                            agent.action = "Hunt"
                            agent.think()
                        else:
                            #if agent.existItem() and not (agent.level ==3 or agent.level ==8):
                            if agent.existItem() and agent.needItem():
                                agent.action = "GetItem"
                                agent.think()
                            else:
                                if (agent.level == 4 or agent.level == 3 or agent.level == 2):
                                    if not agent.enemysAlive():
                                        if len(agent.exit) != 0 and (agent.powersTest[agent.level - 1] or (not agent.powersTest[agent.level - 1] and agent.needItem())):
                                            agent.action = "Exit"
                                            agent.think()
                                        else:
                                            agent.action = "Wall"
                                            agent.think()
                                    else:
                                        agent.next = agent.getEnemy()
                                        agent.action = "Assassin"
                                        agent.think()
                                elif agent.level == 1 :
                                    if len(agent.exit) != 0 and (agent.powersTest[agent.level - 1] or (not agent.powersTest[agent.level - 1] and agent.needItem())):
                                        if not agent.enemysAlive():
                                            agent.action = "Exit"
                                            agent.think()
                                        else:
                                            agent.next = agent.getStrongEnemy()
                                            if agent.next is None:
                                                agent.action = "Porco"
                                                agent.think()
                                            else:
                                                agent.action = "Assassin"
                                                agent.think()
                                    else:
                                        agent.action = "Wall"
                                        agent.think()
                                else:
                                    if not agent.enemysAlive():
                                        if(agent.level == 15):
                                            return 0
                                        if len(agent.exit) != 0 and (agent.powersTest[agent.level - 1] or (not agent.powersTest[agent.level - 1] and agent.needItem())):
                                            agent.action = "Exit"
                                            agent.think()
                                        else:
                                            agent.action = "Wall"
                                            agent.think()
                                    else:
                                        agent.next = agent.getStrongEnemy()
                                        if agent.next is None:
                                            agent.action = "Porco"
                                            agent.think()
                                        else:
                                            agent.action = "Assassin"
                                            agent.think()

                #print(agent.action)
                #print(agent.moves)
                #print(agent.powersTest)
                if agent.action == "Perseguir":
                    if agent.map2[agent.pos[0]][agent.pos[1]] == 2 or agent.map2[agent.pos[0]][agent.pos[1]] == 3 and not agent.override:
                        agent.moves = []
                        await websocket.send(
                            json.dumps({"cmd": "key", "key": "B"})
                        )  # send key command to server - you must implement this send in the AI agent
                        agent.cb = True
                        agent.action = ""
                    elif len(agent.moves) != 0:
                        key= agent.move()
                        if key == "B" and not agent.wallInRange:
                            agent.action = ""
                        else:
                            await websocket.send(
                                json.dumps({"cmd": "key", "key": key})
                            )  # send key command to server - you must implement this send in the AI agent
                            if key == "B":
                                agent.cb = True
                                agent.action = ""
                            if len(agent.moves) == 0:
                                agent.action = ""
                    else:
                        agent.override = False
                        agent.action = ""
                
                elif agent.action == "Fugir":
                    #if agent.map2[agent.pos[0]][agent.pos[1]] == 2 or agent.map2[agent.pos[0]][agent.pos[1]] == 3:
                     #   agent.moves.queue.clear()
                      #  agent.think()
                    if len(agent.moves) != 0:     
                        if agent.moveIsSafe():
                            
                            if len(agent.moves) != 0:
                                key = agent.move()
                                if key == 'A' and not agent.isSafe():
                                    agent.moves = []
                                    agent.action = ""
                                else:
                                    await websocket.send(
                                        json.dumps({"cmd": "key", "key": key})
                                    )  # send key command to server - you must implement this send in the AI agent
                                    if len(agent.moves) == 0:
                                        agent.action = ""
                                        agent.cb = False
                            else:
                                agent.action = ""
                        else:
                            agent.moves = []
                            agent.think()
                            agent.cb = False
                    else:
                        agent.action = "" 
                        if len(agent.bombs) == 0:
                            agent.cb = False


            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return









# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", "BombJack") #getpass.getuser()
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
