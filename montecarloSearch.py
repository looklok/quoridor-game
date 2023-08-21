import numpy as np
import random
import game as GAME
#from game import *
import copy
import time

class Node :
    def __init__(self, move, parent, uctConst) :
        # move is one of the following.
        # [[row, col], None, None] for moving pawn
        # [None, [row, col], None] for placing horizontal wall
        # [None, None, [row, col]] for placing vertical wall
        self.move = move
        self.parent = parent
        self.uctConst = uctConst
        self.numWins = 0   
        self.numSims = 0   # number of simulations
        self.children = []
        self.isTerminal = False
    

    def isLeaf(self) :
        return len(self.children) == 0
    
    def uct(self) :
        if (self.parent is None or self.parent.numSims == 0) :
            raise Exception("UCT_ERROR")
        if (self.numSims == 0) :
            return np.inf
        
        return (self.numWins / self.numSims) + np.sqrt((self.uctConst * np.log(self.parent.numSims)) / self.numSims)

    def winRate(self) :
        return self.numWins / self.numSims

    def maxUCTChild(self) :
        maxUCT = -np.inf
        for i in range(len(self.children)) :
            uct = self.children[i].uct()
            if (uct > maxUCT) :
                maxUCT = uct
                maxUCTIndices = [i]  
            elif (uct == maxUCT) :
                maxUCTIndices.append(i)
        maxUCTIndex = random.choice(maxUCTIndices)

        return self.children[maxUCTIndex]

    def maxWinRateChild(self) :
        maxWinRate = -np.inf
        for i in range(len(self.children)) :
            if (self.children[i].winRate() > maxWinRate) :
                maxWinRate = self.children[i].winRate()
                maxWinRateIndex = i  
            
        return self.children[maxWinRateIndex]
    
    def maxSimsChild(self) :
        maxSims = -np.inf
        for i in range(len(self.children)) :
            if (self.children[i].numSims > maxSims) :
                maxSims = self.children[i].numSims
                maxSimsIndex = i  
            
        
        return self.children[maxSimsIndex]

    def addChild(self,  childNode) :
        self.children.append(childNode)
    
    def printChildren(self) :
        for i in range(len(self.children)) :
            print(f"children[{i}].move: {self.children[i].move}")
        
    
class MonteCarloTreeSearch :
    def __init__ (self, game, uctConst) :
        self.game = game
        self.uctConst = uctConst
        self.root =  Node(None, None, self.uctConst)
        self.totalNumOfSimulations = 0
    
    # Returns max depth for a node
    def maxDepth(self, node) :
        max = 0
        for i in range(node.children) :
            d = self.maxDepth(node.children[i]) + 1
            if (d > max) :
                max = d
        return max
    

    def search(self, numOfSimulations) :
        uctConst = self.uctConst

        currentNode = self.root   
        limitOfTotalNumOfSimulations = self.totalNumOfSimulations + numOfSimulations
        while (self.totalNumOfSimulations < limitOfTotalNumOfSimulations) :         
            # Selection
            if (currentNode.isTerminal) :
                self.playout(currentNode)
                currentNode = self.root
            elif (currentNode.isLeaf()) :
                if (currentNode.numSims == 0) :
                    self.playout(currentNode)
                    currentNode = self.root
                else :
                    # Expansion
                    simulationGame = self.getSimulationGameAtNode(currentNode)
                    if (simulationGame.getPawnAtTurn(returnTurn= False).numberOfLeftWalls > 0) :
                        nextPositionTuples = simulationGame.getArrOfValidNextPositionTuples()
                        for i in range(len(nextPositionTuples)) :
                            move = [nextPositionTuples[i], None, None]
                            childNode = Node(move, currentNode, uctConst) 
                            currentNode.addChild(childNode)
                        
                        if (simulationGame.getPawnAtTurn(returnTurn= True).numberOfLeftWalls > 0) :
                            noBlockNextHorizontals = simulationGame.getArrOfValidNoBlockNextHorizontalWallPositions()
                            for i in range(len(noBlockNextHorizontals)): 
                                move = [None, noBlockNextHorizontals[i], None]
                                childNode = Node(move, currentNode, uctConst) 
                                currentNode.addChild(childNode)
                            
                            noBlockNextVerticals = simulationGame.getArrOfValidNoBlockNextVerticalWallPositions ()
                            for i in range(len(noBlockNextVerticals)) :
                                move = [None, None, noBlockNextVerticals[i]]
                                childNode = Node(move, currentNode, uctConst) 
                                currentNode.addChild(childNode)
                            
                        
                    else :
                        # heuristic:
                        # If opponent has no walls left,
                        # my pawn moves only to one of the shortest paths.
                        nextPositions = chooseShortestPathNextPawnPositionsThoroughly(simulationGame)
                        for i in range(len(nextPositions)) :
                            nextPosition = nextPositions[i]
                            move = [[nextPosition.row, nextPosition.col], None, None]
                            childNode = Node(move, currentNode, uctConst)
                            currentNode.addChild(childNode)
                        
                        if (simulationGame.getPawnAtTurn(returnTurn= True).numberOfLeftWalls > 0) :
                            # heuristic:
                            # if opponent has no walls left,
                            # place walls only to interrupt the opponent's path,
                            # not to support my pawn.
                            noBlockNextWallsInterupt = GAME.getArrOfValidNoBlockNextWallsDisturbPathOf(
                                simulationGame.getPawnAtTurn(returnTurn= False), simulationGame)
                            noBlockNextHorizontalsInterupt = noBlockNextWallsInterupt["horizontal"]
                            for i in range(len(noBlockNextHorizontalsInterupt)) :
                                move = [None, noBlockNextHorizontalsInterupt[i], None]
                                childNode = Node(move, currentNode, uctConst)
                                currentNode.addChild(childNode)
                            
                            noBlockNextVerticalsInterupt = noBlockNextWallsInterupt["vertical"]
                            for i in range(len(noBlockNextVerticalsInterupt)) :
                                move = [None, None, noBlockNextVerticalsInterupt[i]]
                                childNode = Node(move, currentNode, uctConst)
                                currentNode.addChild(childNode)
                            
                        
                    
                    self.playout(random.choice(currentNode.children))
                    currentNode = self.root
                
            else :
                currentNode = currentNode.maxUCTChild()
    

    def selectBestMove(self,) :
        best = self.root.maxSimsChild()
        return {"move": best.move, "winRate": best.winRate()}
    
    
    def getSimulationGameAtNode(self, node) :
        simulationGame = copy.deepcopy(self.game)
        stack = []

        ancestor = node
        while(not ancestor.parent is  None) :
            stack.append(ancestor.move) # moves stacked to a child of root. root's move is not stacked.
            ancestor = ancestor.parent
        #print("before ", simulationGame.getPawn0().position)
        #print("before ", simulationGame.getPawn1().position)
        while (len(stack) > 0) :
            move = stack.pop()
            #print("MOVE : ", move)
            simulationGame.doMove(move)
            #print(simulationGame.getPawn0().position)
            #print(simulationGame.getPawn1().position)
        
        #print("winner ",simulationGame.winner)
        return simulationGame

    
    def playout(self, node) :
        self.totalNumOfSimulations +=1
        simulationGame = self.getSimulationGameAtNode(node)  # to be checked
        
        # the pawn of this node is the pawn who moved immediately before,
        # put it another way, the pawn who leads to this node right before,
        # i.e. pawn of not turn.
        nodePawnIndex = (simulationGame.turn +1) %2
        if not simulationGame.winner is None : # to be checked
            node.isTerminal = True
        
        #print(node.move)
        #print(simulationGame.winner)
        # Simulation
        cacheForPawns = [
            {
                "updated": False,
                "prev": None,
                "next": None,
                "distanceToGoal": None
            },
            {
                "updated": False,
                "prev": None,
                "next": None,
                "distanceToGoal": None
            }
        ]
        pawnMoveFlag = False
        
        while (simulationGame.winner is None) :
            if ( not cacheForPawns[0]["updated"]) :
                
                t = get2DArrayPrevAndNextAndDistanceToGoalFor(simulationGame.getPawn0(), simulationGame)
                cacheForPawns[0]["prev"] = t[0]
                cacheForPawns[0]["next"] = t[1]
                cacheForPawns[0]["distanceToGoal"] = t[2]
                cacheForPawns[0]["updated"] = True
            
            if not cacheForPawns[1]["updated"] :
                t = get2DArrayPrevAndNextAndDistanceToGoalFor(simulationGame.getPawn1(), simulationGame)
                cacheForPawns[1]["prev"] = t[0]
                cacheForPawns[1]["next"] = t[1]
                cacheForPawns[1]["distanceToGoal"] = t[2]
                cacheForPawns[1]["updated"] = True
            

            pawnOfTurn = simulationGame.getPawnAtTurn(returnTurn = True) 
            pawnIndexOfTurn = simulationGame.turn % 2
            # heuristic:
            # With a certain probability, move pawn to one of the shortest paths.
            # And with the rest probability, half place a wall randomly / half move pawn randomly.
            # This heuristic shorten the time taken by playout phase.
            if (random.random() < 0.7) :
                # move pawn to one of shortest paths
                pawnMoveFlag = False
                next = cacheForPawns[pawnIndexOfTurn]["next"]
                currentPosition = pawnOfTurn.position
                nextPosition = next[currentPosition.row][currentPosition.col]
                if (nextPosition is None) :
                    print("Error : Maybe already in goal position")
                    raise Exception("already in goal Position....") # to be checked : how to raise
                             
                if (arePawnsAdjacent(simulationGame)) :
                    nextNextPosition = next[nextPosition.row][nextPosition.col]
                    if ((not nextNextPosition is None) and 
                    (simulationGame.getValidNextPositions()[nextNextPosition.row][nextNextPosition.col] == True)) :
                        nextPosition = nextNextPosition
                        cacheForPawns[pawnIndexOfTurn]["distanceToGoal"] -= 2
                    else :
                        nextPositions = chooseShortestPathNextPawnPositionsThoroughly(simulationGame)
                        _nextPosition = random.choice(nextPositions)
                        if (_nextPosition == nextPosition) : # to be checked
                            cacheForPawns[pawnIndexOfTurn]["distanceToGoal"] -= 1
                        else :
                            nextPosition = _nextPosition
                            cacheForPawns[pawnIndexOfTurn]["updated"] = False
                        
                    
                else :
                    cacheForPawns[pawnIndexOfTurn]["distanceToGoal"] -= 1
                
                simulationGame.movePawn(nextPosition.row, nextPosition.col)
            elif ( not pawnMoveFlag and pawnOfTurn.numberOfLeftWalls > 0 ) :
                # place a wall
                # (If a pawn has no wall, this fall in to next else clause so move pawn randomly.
                # So, consuming all wall early gives no advantage, it rather gives a disadvantage)
                nextMove = chooseProbableNextWall(simulationGame)
                
                
                if (not nextMove is None) :
                    simulationGame.doMove(nextMove)
                    cacheForPawns[0]["updated"] = False
                    cacheForPawns[1]["updated"] = False
                else :
                    print("No probable walls possible")
                    pawnMoveFlag = True
                
            else :
                # move pawn backwards
                pawnMoveFlag = False
                #nextRandomPosition = AI.chooseNextPawnPositionRandomly(simulationGame)
                prev = cacheForPawns[pawnIndexOfTurn]["prev"]
                currentPosition = pawnOfTurn.position
                prevPosition = prev[currentPosition.row][currentPosition.col]
                if ((prevPosition is None) or (not simulationGame.getValidNextPositions()[prevPosition.row][prevPosition.col])) :
                    prevPosition = chooseNextPawnPositionRandomly(simulationGame) # to be checked
                    cacheForPawns[pawnIndexOfTurn]["updated"] = False
                else :
                    cacheForPawns[pawnIndexOfTurn]["distanceToGoal"] += 1
                
                simulationGame.movePawn(prevPosition.row, prevPosition.col)
            
        # Backpropagation
        ancestor = node
        ancestorPawnIndex = nodePawnIndex
        while(not ancestor is None) :
            ancestor.numSims +=1
            if (simulationGame.winner.index == ancestorPawnIndex) :
                ancestor.numWins += 1
            
            ancestor = ancestor.parent
            ancestorPawnIndex = (ancestorPawnIndex + 1) % 2
        

def chooseNextMove(game, uctConst, numOfMCTSSimulations, verbose=False) :
        d0 = time.time()
        
        # heuristic:
        # for first move of each pawn
        # go forward if possible
        if (game.turn < 2) :
            nextPosition = chooseShortestPathNextPawnPosition(game)
            pawnPosition = game.getPawnAtTurn(returnTurn = True).position
            pawnMoveTuple = [nextPosition.row - pawnPosition.row , nextPosition.col - pawnPosition.col]
            if (pawnMoveTuple[1] == 0) :
                return [[nextPosition.row, nextPosition.col], None, None]
            
        
        
        # heuristic: common openings
        if (game.turn < 5 and game.getPawnAtTurn(returnTurn = False).position.col == 4 and game.getPawnAtTurn(returnTurn = False).position.row == 6 and random.random() < 0.5) :
            bestMoves = [
                [None, [5, 3], None], 
                [None, [5, 4], None],
                [None, None, [4, 3]],
                [None, None, [4, 4]]
            ]
            bestMove = random.choice(bestMoves) 
            return bestMove
        
        if (game.turn < 5 and game.getPawnAtTurn(returnTurn = False).position.col == 4 and game.getPawnAtTurn(returnTurn = False).position.row == 2 and random.random() < 0.5) :
            bestMoves = [
                [None, [2, 3], None], 
                [None, [2, 4], None],
                [None, None, [3, 3]],
                [None, None, [3, 4]]
            ]
            bestMove = random.choice(bestMoves) 
            return bestMove

        mcts = MonteCarloTreeSearch(game, uctConst)
        
        mcts.search(numOfMCTSSimulations)
        
        best = mcts.selectBestMove()
        print(best)
        bestMove = best["move"]
        winRate = best["winRate"]
        
        # heuristic:
        # For initial phase of a game, AI get difficulty, so help AI.
        # And if AI is loosing seriously, it get difficulty too.
        # So, if it is initial phase of a game or estimated winRate is low enough,
        # help AI to find shortest path pawn move.
        if (((game.turn < 6 and game.getPawnAtTurn(returnTurn = True).position.col == 4) or winRate < 0.1) and not bestMove[0] is None) :
            rightMove = False
            nextPositions = chooseShortestPathNextPawnPositionsThoroughly(game)
            for nextPosition in nextPositions :
                if (bestMove[0][0] == nextPosition.row and bestMove[0][1] == nextPosition.col) :
                    rightMove = True
                    break
            
            if not rightMove :
                nextPosition = random.choice(nextPositions)
                bestMove = [[nextPosition.row, nextPosition.col], None, None]
            
        
        d1 = time.time()
        uctConst = mcts.root.children[0].uctConst
        print(f"\ttime taken by AI for {(numOfMCTSSimulations)} playouts, c={(uctConst)}: {(d1 - d0):.2f} sec")

        if (verbose) :
            print("descend maxWinRateChild")
            node = mcts.root
            i = 1
            while(len(node.children) > 0) :
                node = node.maxWinRateChild()
                print(i, node.move, node.winRate(), node.numWins, node.numSims)
                i +=1
            
            print("descend maxSimsChild")
            node = mcts.root
            i = 1
            while(len(node.children) > 0) :
                node = node.maxSimsChild()
                print(i, node.move, node.winRate(), node.numWins, node.numSims)
                i += 1
            
            print(f"maxDepth: {MonteCarloTreeSearch.maxDepth(mcts.root)}")
            print(f"estimated maxWinRateChild win rate: {mcts.root.maxWinRateChild().winRate()}")
            print(f"estimated maxSimsChild win rate: {mcts.root.maxSimsChild().winRate()}")
        else :
            print(f"estimated AI win rate: {winRate}")
        
        return bestMove


def getRandomShortestPathToGoal(pawn, game) :
        # This is one of bottle neck, so did inlining...
        #visited = create2DArrayInitializedTo(9, 9, False)
        #dist = create2DArrayInitializedTo(9, 9, np.inf)
        #prev = create2DArrayInitializedTo(9, 9, None)
        visited = [
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False],
        ]
        dist = [
            [np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf],
            [np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf],
            [np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf],
            [np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf],
            [np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf],
            [np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf],
            [np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf],
            [np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf],
            [np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf]
        ]
        prev = [
            [None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None]
        ]
        pawnMoveTuples = GAME.MOVES[:]
        random.shuffle(pawnMoveTuples)
        queue = []
        
       
        visited[pawn.position.row][pawn.position.col] = True
        dist[pawn.position.row][pawn.position.col] = 0
        queue.append(pawn.position)
        while (len(queue) > 0) :
            position = queue.pop(0) # to be checked
            if (position.row == pawn.goalRow) :
                goalPosition = position
                return [dist, prev, goalPosition]
            
            for i in range(len(pawnMoveTuples)) : 
                if (game.isOpenWay(position.row, position.col, pawnMoveTuples[i])) :
                    nextPosition = position.newPosition(pawnMoveTuples[i])
                    if not visited[nextPosition.row][nextPosition.col] :
                        alt = dist[position.row][position.col] + 1
                        dist[nextPosition.row][nextPosition.col] = alt
                        prev[nextPosition.row][nextPosition.col] = position
                        visited[nextPosition.row][nextPosition.col] = True
                        queue.append(nextPosition)
                    
                
        return [dist, prev, None]


def chooseShortestPathNextPawnPosition(game) :
        nextPosition = None
        # "if (AI.arePawnsAdjacent(game))"" part can deal with
        # general case, not only adjacent pawns case.
        # But, for not adjacent case, there is a more efficent way
        # to find next position. It is the "else" part.
        # This impoves performece significantly.
        if (arePawnsAdjacent(game)) :
            nextPositions = chooseShortestPathNextPawnPositionsThoroughly(game)
            nextPosition = random.choice(nextPositions)
        else : 
            next = get2DArrayPrevAndNextAndDistanceToGoalFor(game.getPawnAtTurn(returnTurn = True), game)[1]
            currentPosition = game.getPawnAtTurn(returnTurn = True).position
            nextPosition = next[currentPosition.row][currentPosition.col] 

            # if already in goal position.
            if (nextPosition is None) :
                print("really?? already in goal position")
        
        return nextPosition
    


def getShortestDistanceToGoalFor(pawn, game) :
        t = getRandomShortestPathToGoal(pawn, game)
        dist = t[0]
        goalPosition = t[2]
        if (goalPosition is None) :
            return np.inf
        
        return dist[goalPosition.row][goalPosition.col]

def chooseShortestPathNextPawnPositionsThoroughly(game) :
        valids = GAME.indicesOfValueIn2DArray(game.getValidNextPositions(), True)
        distances = []
        for i in range(len(valids)) :
            clonedGame = copy.deepcopy(game)
            clonedGame.movePawn(valids[i][0], valids[i][1])
            distance = getShortestDistanceToGoalFor(clonedGame.getPawnAtTurn(returnTurn = False), clonedGame)
            distances.append(distance)
        
        
        indices_min = [i for i, d in enumerate(distances) if d == np.min(distances)]
        nextPositions = []

        for index in indices_min :
            nextPositions.append( GAME.PawnPosition(valids[index][0], valids[index][1]))
        
        return nextPositions


# get 2D array "next" to closest goal in the game
def get2DArrayPrevAndNextAndDistanceToGoalFor(pawn, game) :
        t = getRandomShortestPathToGoal(pawn, game)
        dist = t[0]
        prev = t[1]
        goalPosition = t[2]
        distanceToGoal = dist[goalPosition.row][goalPosition.col]
        next = getNextByReversingPrev(prev, goalPosition)
        return [prev, next, distanceToGoal]

def arePawnsAdjacent(game) :
        pawn0 = game.getPawnAtTurn(returnTurn= True)
        pawn1 = game.getPawnAtTurn(returnTurn= False)
        return ((pawn1.position.row == pawn0.position.row
                and np.abs(pawn1.position.col - pawn0.position.col) == 1)
                or (pawn1.position.col == pawn0.position.col
                    and np.abs(pawn1.position.row - pawn0.position.row) == 1))
    

def chooseProbableNextWall(game) :
        nextMoves = []
        nextHorizontals = GAME.indicesOfValueIn2DArray(game.probableValidNextWalls()["horizontal"], True) ##TO BE DONE
        for i in range(len(nextHorizontals)) : 
            nextMoves.append([None, nextHorizontals[i], None])
        
        nextVerticals = GAME.indicesOfValueIn2DArray(game.probableValidNextWalls()["vertical"], True) ##TO BE DONE
        for i in range(len(nextVerticals)) :
            nextMoves.append([None, None, nextVerticals[i]])
        
        if (len(nextMoves) == 0) :
            return None
        
        nextMoveIndex = random.choice(list(range(len(nextMoves))))
        while(not game.isPossibleNextMove(nextMoves[nextMoveIndex])) :
            nextMoves.pop(nextMoveIndex)
            if (len(nextMoves) == 0) :
                print("Is it really possible???")
                return None  # is it possible?? I'm not sure..
            
            nextMoveIndex = random.choice(list(range(len(nextMoves))))
        
        return nextMoves[nextMoveIndex]
    

def chooseNextPawnPositionRandomly(game) :
        nextPositionTuples = game.getArrOfValidNextPositionTuples()
        nextPositionTuple = random.choice(nextPositionTuples)
        return GAME.PawnPosition(nextPositionTuple[0], nextPositionTuple[1])
    


def getNextByReversingPrev(prev, goalPosition) :
        next = GAME.initialBoard(9, 9, None)
        position = goalPosition
        while(prev[position.row][position.col]) :
            prevPosition = prev[position.row][position.col]
            next[prevPosition.row][prevPosition.col] = position
            position = prevPosition
        
        return next