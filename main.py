
from game import *
from utils import *
from montecarloSearch import *
from draw_board import Drawer, cls
from time import sleep

numOfMCTSSimulations = 3000
uctConst = 0.4

print("Do you want to play first?")
isHumanPlayerFirst = get_boolean_input("Enter 'yes' or 'no': ")

numOfMCTSSimulations = get_numOfMCTSSimulations(f"Please enter integer for the number of monte carlo simulations you want to use \
                                                \nDefault value is : {numOfMCTSSimulations} \n")

game = Game(isHumanPlayerFirst)
drawer = Drawer(isHumanPlayerFirst)

stop = False
max_plays=50
while True :
    if game.turn ==max_plays : 
        break
    
    if (game.turn != 0) or isHumanPlayerFirst:
        
        # HUMAN MOVES
        drawer.display()
        drawer.display_turn()
        move_accepted = False
        while not move_accepted : 
            # Choose another move
            move = drawer.get_move()
            print("\n\tChosen move : ", move)

            if (not move is None) and move[0]:
                move_aj = [[move[0][0] + game.getPawnAtTurn(returnTurn = True).position.row , 
                        move[0][1] + game.getPawnAtTurn(returnTurn = True).position.col], None, None]
            else:
                move_aj = move 
            sleep(1)
            move_accepted = game.doMove(move_aj, needCheck=True)
            if not move_accepted : 
                print("Move not accepted : It violates the rules of the game")
            else:
                movePawnTo = move[0]
                placeHorizontalWallAt = move[1]
                placeVerticalWallAt = move[2]
                if (movePawnTo) :
                    drawer.apply_pawn_move(1, movePawnTo)
                elif (placeHorizontalWallAt) :
                    drawer.apply_wall(1, placeHorizontalWallAt, vertical=False)
                elif (placeVerticalWallAt) :
                    drawer.apply_wall(1, placeVerticalWallAt, vertical=True)
                    
        if (not game.winner is None) :
            #cls()
            print("🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉")
            print("🎊 🎊 🎊 🎊 🎊 🎊 🎊 🎊")
            print("🎈 🎈 🎈 🎈 🎈 🎈 🎈 🎈")

            print("The winner is : " + "HUMAN" if game.winner.isHumanPlayer else "AI")
            
            print("🎇 🎇 🎇 🎇 🎇 🎇 🎇 🎇")
            print("🎆 🎆 🎆 🎆 🎆 🎆 🎆 🎆")
            print("🏆 🏆 🏆 🏆 🏆 🏆 🏆 🏆")
            break


    # AI MOVES

    drawer.display()
    drawer.display_turn()

    move_accepted = False
    while not move_accepted : 
        # Choose another move
        #move = drawer.get_move()
        move = chooseNextMove(game=game, uctConst=uctConst, numOfMCTSSimulations=numOfMCTSSimulations)
        if move[0]:
            move_aj = [[move[0][0] - game.getPawnAtTurn(returnTurn = True).position.row , 
                     move[0][1] - game.getPawnAtTurn(returnTurn = True).position.col], None, None]
        else:
            move_aj = move
        
        print("\n\tChosen move : ", move)
        sleep(1)
        move_accepted = game.doMove(move, needCheck=True)
        if not move_accepted : 
            #drawer.warn("Move not accepted : It violates the game rules")
            print("Move not accepted : It violates the rules of the game")
        else:
            movePawnTo = move_aj[0]
            placeHorizontalWallAt = move[1]
            placeVerticalWallAt = move[2]
            if (movePawnTo) :
                drawer.apply_pawn_move(0, movePawnTo)
            elif (placeHorizontalWallAt) :
                drawer.apply_wall(0, placeHorizontalWallAt, vertical=False)
            elif (placeVerticalWallAt) :
                drawer.apply_wall(0, placeVerticalWallAt, vertical=True)

    
    if (not game.winner is None) :
        #cls()
        print("🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉")
        print("🎊 🎊 🎊 🎊 🎊 🎊 🎊 🎊")
        print("🎈 🎈 🎈 🎈 🎈 🎈 🎈 🎈")

        print("The winner is : " + "HUMAN" if game.winner.isHumanPlayer else "AI")
        
        print("🎇 🎇 🎇 🎇 🎇 🎇 🎇 🎇")
        print("🎆 🎆 🎆 🎆 🎆 🎆 🎆 🎆")
        print("🏆 🏆 🏆 🏆 🏆 🏆 🏆 🏆")
        break
        






