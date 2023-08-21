from typing import final
import copy
from collections import deque
import numpy as np

# Possible positions of a pawn
MOVE_UP: final = [-1, 0]
MOVE_DOWN: final = [1, 0]
MOVE_LEFT : final= [0, -1]
MOVE_RIGHT: final = [0, 1]
MOVES = [MOVE_UP, MOVE_LEFT, MOVE_RIGHT, MOVE_DOWN]

def initialBoard (numRows, numCols, value):
    array = []
    for i in range(numRows):
        array.append([value for j in range(numCols)])

    return array
        

class PawnPosition :
    def __init__(self, row , col) -> None:
        self.row = row
        self.col = col
    
    def __eq__(self, __value: object) -> bool:
        return self.row == __value.row and self.col == __value.col
    def __str__(self) -> str:
        return "row : " + str(self.row)+ ", col : "+str(self.col) 

    def newPosition (self, moveTuple):
        return PawnPosition(self.row + moveTuple[0], self.col + moveTuple[1])
    
    
    
class Pawn :
    def __init__(self, index, isHumanSide, isHumanPlayer, forClone = False) -> None:
        ## TO BE CHECKED

        self.index = None
        self.isHumanSide = None
        self.isHumanPlayer = None
        self.position = None
        self.goalRow = None
        self.numberOfLeftWalls = None
        if not forClone :
            # index == 0 represents a light-colored pawn (which moves first).
            # index == 1 represents a dark-colored pawn.
            self.index = index
            self.isHumanPlayer = isHumanPlayer
            if (isHumanSide == True) :
                self.isHumanSide = True
                self.position = PawnPosition(8, 4)
                self.goalRow = 0
            else: 
                self.isHumanSide = False
                self.position =  PawnPosition(0, 4)
                self.goalRow = 8
            
            self.numberOfLeftWalls = 10


class Board :
    def __init__(self, isHumanPlayerFirst, forClone = False) -> None:
        self.pawns = None
        self.walls = None
        if not forClone :
            # self.pawns[0] represents a light-colored pawn (which moves first).
            # self.pawns[1] represents a dark-colored pawn.
            if isHumanPlayerFirst == True : 
                self.pawns = [Pawn(0, True, True),  Pawn(1, False, False)]
            else :
                self.pawns = [Pawn(0, False, False), Pawn(1, True, True)]

            # horizontal, vertical: each is a 8 by 8 2D array, True: there is a wall, false: there is not a wall.
            self.walls = {"horizontal": initialBoard(8, 8, False), "vertical": initialBoard(8, 8, False)}


class Game :
    def __init__(self,isHumanPlayerFirst, forClone = False):
        self.board = None
        self.winner = None
        self.turn = None
        self.validNextWalls = None
        self._probableNextWalls = None
        self._probableValidNextWalls = None
        self._probableValidNextWallsUpdated = None
        self.openWays = None
        self._validNextPositions = None
        self._validNextPositionsUpdated = None
        if  not forClone : 
            self.board =  Board(isHumanPlayerFirst)
            self.winner = None
            self.turn = 0

            # horizontal, vertical: each is a 8 by 8 2D bool array True indicates valid location, false indicates not valid wall location.
            # this should be only updated each time placing a wall 
            self.validNextWalls = {"horizontal": initialBoard(8, 8, True), "vertical": initialBoard(8, 8, True)}

            # probable next probable walls: it's for expansion phase of Monte Carlo Tree Search.
            self._probableNextWalls = {"horizontal": initialBoard(8, 8, False), "vertical": initialBoard(8, 8, False)}
            self._probableValidNextWalls = None
            self._probableValidNextWallsUpdated = False

            # whether ways to adjacency is blocked (not open) or not blocked (open) by a wall
            # this should be only updated each time placing a wall
            self.openWays = {"upDown": initialBoard(8, 9, True), "leftRight": initialBoard(9, 8, True)}

            # Possible next positions at the start : 9x9 
            self._validNextPositions = initialBoard(9, 9, False)
            self._validNextPositionsUpdated = False



    def setTurn (self, newTurn):
        self.turn = newTurn
        self._validNextPositionsUpdated = False
        self._probableValidNextWallsUpdated = False


    def getPawn0 (self):
        return self.board.pawns[0]
    
    def getPawn1 (self):
        return self.board.pawns[1]
    
    def getPawnAtTurn (self, returnTurn = True):
        if returnTurn :
            return self.board.pawns[self.turn % 2]
        else:
            return self.board.pawns[ (self.turn +1) % 2 ]

    def getArrOfValidNextPositionTuples  (self,):
        return indicesOfValueIn2DArray(self.getValidNextPositions(), True)
    
    def isOpenWay(self, currentRow, currentCol, pawnMoveTuple) :
        if (pawnMoveTuple[0] == -1 and  pawnMoveTuple[1] == 0)  :   # up
            return (currentRow > 0 and  self.openWays["upDown"][currentRow - 1][currentCol])
        elif (pawnMoveTuple[0] == 1 and  pawnMoveTuple[1] == 0) :  #down
            return (currentRow < 8 and  self.openWays["upDown"][currentRow][currentCol])
        elif (pawnMoveTuple[0] == 0 and  pawnMoveTuple[1] == -1) :  # left
            return (currentCol > 0 and  self.openWays["leftRight"][currentRow][currentCol - 1])
        elif (pawnMoveTuple[0] == 0 and  pawnMoveTuple[1] == 1) :  # right
            return (currentCol < 8 and  self.openWays["leftRight"][currentRow][currentCol])
        else :
            raise("pawnMoveTuple should be one of [1, 0], [-1, 0], [0, 1], [0, -1]") 
        
    

    def getValidNextPositions(self) : 
        if (self._validNextPositionsUpdated == True) :
            return self._validNextPositions
        
        self._validNextPositionsUpdated = True

        self._validNextPositions = initialBoard(9, 9, False)
        
        self.set_validNextPositionsToward(MOVE_UP, MOVE_LEFT, MOVE_RIGHT)
        self.set_validNextPositionsToward(MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT)
        self.set_validNextPositionsToward(MOVE_LEFT, MOVE_UP, MOVE_DOWN)
        self.set_validNextPositionsToward(MOVE_RIGHT, MOVE_UP, MOVE_DOWN)
        
        return self._validNextPositions
 
    def set_validNextPositionsToward(self, mainMove, subMove1, subMove2):
        if self.isValidNextMoveNotConsideringOtherPawn(self.getPawnAtTurn(returnTurn = True).position, mainMove) :
            # mainMovePosition: the pawn's position after main move
            mainMovePosition = self.getPawnAtTurn(returnTurn = True).position.newPosition(mainMove)
            # if the other pawn is on the position after main move 
            if mainMovePosition == self.getPawnAtTurn(returnTurn = False).position :
                # check for jumping toward main move (e.g. up) direction
                if self.isValidNextMoveNotConsideringOtherPawn(mainMovePosition, mainMove) :
                    # mainMainMovePosition: the pawn's position after two main move
                    mainMainMovePosition = mainMovePosition.newPosition(mainMove)
                    self._validNextPositions[mainMainMovePosition.row][mainMainMovePosition.col] = True
                else :
                    # check for jumping toward sub move 1 (e.g. left) direction
                    if (self.isValidNextMoveNotConsideringOtherPawn(mainMovePosition, subMove1)) :
                        # mainSub1MovePosition: the pawn's position after (main move + sub move 1)
                        mainSub1MovePosition = mainMovePosition.newPosition(subMove1)
                        self._validNextPositions[mainSub1MovePosition.row][mainSub1MovePosition.col] = True
                    
                    # check for jumping toward sub move 2 (e.g. right) direction
                    if self.isValidNextMoveNotConsideringOtherPawn(mainMovePosition, subMove2) :
                        # mainSub2MovePosition: the pawn's position after (main move + sub move 2)
                        mainSub2MovePosition = mainMovePosition.newPosition(subMove2)
                        self._validNextPositions[mainSub2MovePosition.row][mainSub2MovePosition.col] = True
                   
            else :
                self._validNextPositions[mainMovePosition.row][mainMovePosition.col] = True

    def isPossibleNextMove(self, move) :
        movePawnTo = move[0]
        placeHorizontalWallAt = move[1]
        placeVerticalWallAt = move[2]
        if (movePawnTo) :
            return self.getValidNextPositions()[movePawnTo[0]][movePawnTo[1]]
        elif (placeHorizontalWallAt) :
            return self.testIfExistPathsToGoalLinesAfterPlaceHorizontalWall(placeHorizontalWallAt[0], placeHorizontalWallAt[1])
        elif (placeVerticalWallAt) :
            return self.testIfExistPathsToGoalLinesAfterPlaceVerticalWall(placeVerticalWallAt[0], placeVerticalWallAt[1])
        
    
    def isValidNextMoveNotConsideringOtherPawn(self, position, moveTuple):
        """
        this method checks if the moveTuple of the pawn of this turn is valid against walls on the board and the board size.
        this method do not check the validity against the other pawn's position. 
        """
        if (moveTuple[0] == -1 and moveTuple[1] == 0) : # up
            return (position.row > 0 and self.openWays["upDown"][position.row - 1][position.col])
        
        if (moveTuple[0] == 1 and moveTuple[1] == 0) : # down
            return (position.row < 8 and self.openWays["upDown"][position.row][position.col])
    
        elif (moveTuple[0] == 0 and moveTuple[1] == -1) : # left
            return (position.col > 0 and self.openWays["leftRight"][position.row][position.col - 1])
    
        elif (moveTuple[0] == 0 and moveTuple[1] == 1) : # right
            return (position.col < 8 and self.openWays["leftRight"][position.row][position.col])
        else :
            raise Exception("moveTuple should be one of [1, 0], [-1, 0], [0, 1], [0, -1]")
        
    def movePawn(self, row, col, needCheck = False) :
        if row >= len(self._validNextPositions) or col >= len(self._validNextPositions[0]):
            return False
        self.getValidNextPositions()  
        
        if needCheck and not self._validNextPositions[row][col]  :
            return False
        
        self.getPawnAtTurn(returnTurn=True).position.row = row
        self.getPawnAtTurn(returnTurn=True).position.col = col
        if self.getPawnAtTurn(returnTurn=True).goalRow == self.getPawnAtTurn(returnTurn=True).position.row :
            self.winner = self.getPawnAtTurn(returnTurn=True)
        
        self.setTurn(self.turn +1)

        return True
    

    def testIfExistPathsToGoalLinesAfterPlaceHorizontalWall(self, row, col) :
        # wall which does not connected on two points do not block path.
        
        self.openWays["upDown"][row][col] = False
        self.openWays["upDown"][row][col + 1] = False
        result = self.existPathsToGoalLines()
        self.openWays["upDown"][row][col] = True
        self.openWays["upDown"][row][col + 1] = True
        return result

    def testIfExistPathsToGoalLinesAfterPlaceVerticalWall(self, row, col) :
        # wall which does not connected on two points do not block path.
        
        self.openWays["leftRight"][row][col] = False
        self.openWays["leftRight"][row+1][col] = False
        result = self.existPathsToGoalLines()
        self.openWays["leftRight"][row][col] = True
        self.openWays["leftRight"][row+1][col] = True
        return result
    
    def existPathsToGoalLines (self):
        return self.existPathsToGoalLineFor(self.getPawnAtTurn(returnTurn=True)) and  self.existPathsToGoalLineFor(self.getPawnAtTurn(returnTurn=False))
     
    def depthFirstSearch(self, visited, currentRow, currentCol, goalRow):
        if currentRow == goalRow :
            return True
        for pawnMove in MOVES :
            if self.isValidNextMoveNotConsideringOtherPawn(PawnPosition(currentRow, currentCol), pawnMove) :
                    nextRow = currentRow + pawnMove[0]
                    nextCol = currentCol + pawnMove[1]
                    if not visited[nextRow][nextCol]  :
                        visited[nextRow][nextCol] = True
                    
                        if self.depthFirstSearch(visited, nextRow, nextCol, goalRow) :
                            return True         
                        

    def existPathsToGoalLineFor(self, pawn):
        visited = initialBoard(9, 9, False)
        res = self.depthFirstSearch(visited, pawn.position.row, pawn.position.col, pawn.goalRow)
        if res : 
            return True
        else:
            return False
    
    # To be checked
    def placeHorizontalWall(self, row, col, needCheck = False) :
        if (needCheck and not self.testIfExistPathsToGoalLinesAfterPlaceHorizontalWall(row, col)) :
            print("You need to leave at least one path to the goal for each pawn.")
            return False
        
        self.openWays["upDown"][row][col] = False
        self.openWays["upDown"][row][col + 1] = False
        self.validNextWalls["vertical"][row][col] = False
        self.validNextWalls["horizontal"][row][col] = False
        if (col > 0) :
            self.validNextWalls["horizontal"][row][col - 1] = False
        
        if (col < 7) :
            self.validNextWalls["horizontal"][row][col + 1] = False
        
        self.board.walls["horizontal"][row][col] = True
        
        #self.adjustProbableValidNextWallForAfterPlaceHorizontalWall(row, col)
        self.getPawnAtTurn(returnTurn=True).numberOfLeftWalls -= 1
        self.setTurn(self.turn +1)
        return True
    

    def placeVerticalWall(self, row, col, needCheck = False) :
        if (needCheck and not self.testIfExistPathsToGoalLinesAfterPlaceVerticalWall(row, col)) :
            print("You need to leave at least one path to the goal for each pawn.")
            return False
        
        self.openWays["leftRight"][row][col] = False
        self.openWays["leftRight"][row+1][col] = False
        self.validNextWalls["horizontal"][row][col] = False
        self.validNextWalls["vertical"][row][col] = False
        if (row > 0) :
            self.validNextWalls["vertical"][row-1][col] = False
        
        if (row < 7) :
            self.validNextWalls["vertical"][row+1][col] = False
        
        self.board.walls["vertical"][row][col] = True
        
        #self.adjustProbableValidNextWallForAfterPlaceVerticalWall(row, col)
        self.getPawnAtTurn(returnTurn=True).numberOfLeftWalls -= 1
        self.setTurn(self.turn +1)
        return True
    

    def doMove(self, move, needCheck = False) :
        if not move :
            return False
        if (not self.winner is None) :
            print("error: doMove after already terminal state") # for debug
        
        movePawnTo = move[0]
        placeHorizontalWallAt = move[1]
        placeVerticalWallAt = move[2]
        if (movePawnTo) :
            return  self.movePawn( movePawnTo[0], movePawnTo[1], needCheck)
        elif (placeHorizontalWallAt) :
            return  self.placeHorizontalWall(placeHorizontalWallAt[0], placeHorizontalWallAt[1], needCheck)
        elif (placeVerticalWallAt) :
            return  self.placeVerticalWall(placeVerticalWallAt[0], placeVerticalWallAt[1], needCheck)
        

    def getArrOfValidNoBlockNextHorizontalWallPositions(self,):
        nextHorizontals = indicesOfValueIn2DArray(self.validNextWalls["horizontal"], True)
        noBlockNextHorizontals = []
        for i in range(len(nextHorizontals)) :
            if (self.testIfExistPathsToGoalLinesAfterPlaceHorizontalWall(nextHorizontals[i][0], nextHorizontals[i][1])):   
                noBlockNextHorizontals.append(nextHorizontals[i])

        return noBlockNextHorizontals

    def getArrOfValidNoBlockNextVerticalWallPositions(self,):
        nextVerticals = indicesOfValueIn2DArray(self.validNextWalls["vertical"], True)
        noBlockNextVerticals = []
        for i in range(len(nextVerticals)) :
            if (self.testIfExistPathsToGoalLinesAfterPlaceVerticalWall(nextVerticals[i][0], nextVerticals[i][1])):
                noBlockNextVerticals.append(nextVerticals[i])

        return noBlockNextVerticals
    

    # heuristic:
    # In expansion phase,
    # do not consider all possible wall positions,
    # only consider probable next walls.
    # This heuristic decreases the branching factor.
    #
    # Probable next walls are
    # 1. near pawns (to disturb opponent or support myself)
    # 2. near already placed walls
    # 3. leftest side, rightest side horizontal walls
    def probableValidNextWalls(self) :
        if (self._probableValidNextWallsUpdated) :
            return self._probableValidNextWalls
        
        self._probableValidNextWallsUpdated = True
        
        # near already placed walls
        _probableValidNextWalls = {
            "horizontal": copy.deepcopy(self._probableNextWalls["horizontal"]),
            "vertical": copy.deepcopy(self._probableNextWalls["vertical"])
        }

        # leftmost and rightmost horizontal walls
        # after several turns
        if (self.turn >= 6) :
            for i in range(8) :
                _probableValidNextWalls["horizontal"][i][0] = True
                _probableValidNextWalls["horizontal"][i][7] = True

        # near pawns
        # place walls to diturb opponent or support myself
        # only after several turns
        if (self.turn >= 3) :
            # disturb opponent
            setWallsBesidePawn(_probableValidNextWalls, self.getPawnAtTurn(returnTurn=False))
        
        if (self.turn >= 6
            or len(indicesOfValueIn2DArray(self.board.walls["horizontal"], True)) > 0
            or len(indicesOfValueIn2DArray(self.board.walls["vertical"], True)) > 0) :
            # support myself    
            setWallsBesidePawn(_probableValidNextWalls, self.getPawnAtTurn(returnTurn=True))
        
        _probableValidNextWalls["horizontal"] = logicalAndBetween2DArray(_probableValidNextWalls["horizontal"], self.validNextWalls["horizontal"])
        _probableValidNextWalls["vertical"] = logicalAndBetween2DArray(_probableValidNextWalls["vertical"], self.validNextWalls["vertical"])
        self._probableValidNextWalls = _probableValidNextWalls
        return _probableValidNextWalls
    
def getArrOfValidNoBlockNextWallsDisturbPathOf(pawn, game) :
    validNextWallsInterupt = getValidNextWallsDisturbPathOf(pawn, game)
    nextHorizontals = indicesOfValueIn2DArray(validNextWallsInterupt["horizontal"], True)
    noBlockNextHorizontals = []
    for i in range(len(nextHorizontals)) :
        if (game.testIfExistPathsToGoalLinesAfterPlaceHorizontalWall(nextHorizontals[i][0], nextHorizontals[i][1])) :   
            noBlockNextHorizontals.append(nextHorizontals[i])
        
    
    nextVerticals = indicesOfValueIn2DArray(validNextWallsInterupt["vertical"], True)
    noBlockNextVerticals = []
    for i in range(len(nextVerticals)) :
        if (game.testIfExistPathsToGoalLinesAfterPlaceVerticalWall(nextVerticals[i][0], nextVerticals[i][1])) :
            noBlockNextVerticals.append(nextVerticals[i])
        
    
    return {"horizontal": noBlockNextHorizontals, "vertical": noBlockNextVerticals}


def getValidNextWallsDisturbPathOf(pawn, game):
    validInterruptHorizontalWalls = initialBoard(8, 8, False)
    validInterruptVerticalWalls = initialBoard(8, 8, False)
    
    # add (1) walls interrupt shortest paths of the pawn
    visited = initialBoard(9, 9, False)
    t = getAllShortestPathsToEveryPosition(pawn, game)
    dist = t[0]
    prev = t[1]
    goalRow = pawn.goalRow
    goalCols = [ ind for ind, v in enumerate(dist[goalRow]) if v == min(dist[goalRow])]
    
    queue = deque([])
    for i in range(len(goalCols)) :
        goalPosition = PawnPosition(goalRow, goalCols[i])
        queue.append(goalPosition)
    
    
    while (len(queue) > 0) :
        position = queue.popleft()
        prevs = prev[position.row][position.col]
        if (prevs is None) :
            # for debug
            if (not len(queue) == 0) :
                raise Exception("some error occured....")
            continue # this can be "break"
            # because if condition holds true only if current position is start position.
        
        for i in range(len(prevs)) :
            prevPosition = prevs[i]
            pawnMoveTuple = [position.row - prevPosition.row, position.col - prevPosition.col]  
            # mark valid walls which can interupt the pawn move
            if (pawnMoveTuple[0] == -1 and pawnMoveTuple[1] == 0) : # up
                if (prevPosition.col < 8) :
                    validInterruptHorizontalWalls[prevPosition.row-1][prevPosition.col] = True
                
                if (prevPosition.col > 0) :
                    validInterruptHorizontalWalls[prevPosition.row-1][prevPosition.col-1] = True
                    
            elif (pawnMoveTuple[0] == 1 and pawnMoveTuple[1] == 0) : # down
                if (prevPosition.col < 8) :
                    validInterruptHorizontalWalls[prevPosition.row][prevPosition.col] = True                   
                if (prevPosition.col > 0) :
                    validInterruptHorizontalWalls[prevPosition.row][prevPosition.col-1] = True
                    
            elif (pawnMoveTuple[0] == 0 and pawnMoveTuple[1] == -1) : # left
                if (prevPosition.row < 8) :
                    validInterruptVerticalWalls[prevPosition.row][prevPosition.col-1] = True
                
                if (prevPosition.row > 0) :
                    validInterruptVerticalWalls[prevPosition.row-1][prevPosition.col-1] = True
                    
            elif (pawnMoveTuple[0] == 0 and pawnMoveTuple[1] == 1) : # right
                if (prevPosition.row < 8) :
                    validInterruptVerticalWalls[prevPosition.row][prevPosition.col] = True
                
                if (prevPosition.row > 0) :
                    validInterruptVerticalWalls[prevPosition.row-1][prevPosition.col] = True
                
            
                            
            if (not visited[prevPosition.row][prevPosition.col]) :
                visited[prevPosition.row][prevPosition.col] = True
                queue.append(prevPosition)
    
    # add (2) walls beside the pawn
    wall2DArrays = {"horizontal": validInterruptHorizontalWalls, "vertical": validInterruptVerticalWalls}
    setWallsBesidePawn(wall2DArrays, pawn)

    # extract only valid walls
    wall2DArrays["horizontal"] = logicalAndBetween2DArray(wall2DArrays["horizontal"], game.validNextWalls["horizontal"])
    wall2DArrays["vertical"] = logicalAndBetween2DArray(wall2DArrays["vertical"], game.validNextWalls["vertical"])
    
    return wall2DArrays

def getAllShortestPathsToEveryPosition(pawn, game) :
        searched = initialBoard(9, 9, False)
        visited = initialBoard(9, 9, False)
        dist = initialBoard(9, 9, np.inf)
        multiPrev = initialBoard(9, 9, None)

        pawnMoveTuples = [MOVE_UP, MOVE_RIGHT, MOVE_DOWN, MOVE_LEFT]
        queue = deque([])
        visited[pawn.position.row][pawn.position.col] = True
        dist[pawn.position.row][pawn.position.col] = 0
        queue.append(pawn.position)
        while (len(queue) > 0) :
            position = queue.popleft()
            for i in range(len(pawnMoveTuples)) :
                if (game.isOpenWay(position.row, position.col, pawnMoveTuples[i])) :
                    nextPosition = position.newPosition(pawnMoveTuples[i])
                    if ( not searched[nextPosition.row][nextPosition.col]) :
                        alt = dist[position.row][position.col] + 1
                        # when this inequality holds, dist[nextPosition.row][nextPosition.col] === infinity
                        # because alt won't be decreased in this BFS.
                        if (alt < dist[nextPosition.row][nextPosition.col]) :
                            dist[nextPosition.row][nextPosition.col] = alt
                            multiPrev[nextPosition.row][nextPosition.col] = [position]
                        elif alt == dist[nextPosition.row][nextPosition.col] :
                            multiPrev[nextPosition.row][nextPosition.col].append(position)
                        
                        if (not visited[nextPosition.row][nextPosition.col]) :
                            visited[nextPosition.row][nextPosition.col] = True
                            queue.append(nextPosition)
           
            searched[position.row][position.col] = True
        
        return [dist, multiPrev]



def indicesOfValueIn2DArray(arr2D, value):
    t = []
    for i in range(len(arr2D)) : 
        for j in range(len(arr2D[0])):
            if (arr2D[i][j] == value):
                t.append([i, j])
            
    return t
def setWallsBesidePawn(wall2DArrays, pawn) :       
        row = pawn.position.row
        col = pawn.position.col
        if (row >= 1) :
            if (col >= 1) :
                wall2DArrays["horizontal"][row-1][col-1] = True
                wall2DArrays["vertical"][row-1][col-1] = True
                if (col >= 2) :
                    wall2DArrays["horizontal"][row-1][col-2] = True
                
            
            if (col <= 7) :
                wall2DArrays["horizontal"][row-1][col] = True
                wall2DArrays["vertical"][row-1][col] = True
                if (col <= 6) :
                    wall2DArrays["horizontal"][row-1][col+1] = True
                
            
            if (row >= 2) :
                if (col >= 1) : 
                    wall2DArrays["vertical"][row-2][col-1] = True
                
                if (col <= 7) :
                    wall2DArrays["vertical"][row-2][col] = True
                
            
        
        if (row <= 7) :
            if (col >= 1) :
                wall2DArrays["horizontal"][row][col-1] = True
                wall2DArrays["vertical"][row][col-1] = True
                if (col >= 2) :
                    wall2DArrays["horizontal"][row][col-2] = True
                
            
            if (col <= 7) :
                wall2DArrays["horizontal"][row][col] = True
                wall2DArrays["vertical"][row][col] = True
                if (col <= 6) :
                    wall2DArrays["horizontal"][row][col+1] = True
                
            
            if (row <= 6) :
                if (col >= 1) : 
                    wall2DArrays["vertical"][row+1][col-1] = True
                
                if (col <= 7) :
                    wall2DArrays["vertical"][row+1][col] = True
                
            
        
    
def logicalAndBetween2DArray(arr2DA, arr2DB) :
    arr2D = []
    for i in range(len(arr2DA)) :
        row = []
        for j in range(len(arr2DA)) :
            row.append(arr2DA[i][j] and arr2DB[i][j])
        
        arr2D.append(row)
    
    return arr2D


if __name__ == "__main__":
    pass