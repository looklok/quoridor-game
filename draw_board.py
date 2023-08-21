import numpy as np
import os
from time import sleep


def cls():
    """Wipes the screen altogether. Works on Linux BASH and Windows Command Line.
    Should also work on Mac OS, not sure."""
    os.system('cls' if os.name == 'nt' else 'clear')

class Drawer ():
    def __init__(self, isHumanFirst) -> None:
        """Sets all the global variables to their correct amount."""


        self.N = 9
        # length of the grid excluding the lines

        self.M = 2 * self.N + 1
        # length of the grid including the lines

        self.K = self.M - 1
        # the ordinal corresponding to the last cell in the grid
        # (for convenience of not having to subtract 1 every time)

        self.grid = np.full((self.M, self.M), '+')
        # first making an array of '+'s with the shape (M, M)

        self.grid[1:-1:2, 1:-1:2] = np.full((self.N, self.N), ' ')
        # then replacing our free cells (which are for pawns to be at) with ' '

        # drawing the box with box-drawing characters
        self.grid[::2, :] = '─'
        self.grid[:, ::2] = '│'
        self.grid[2:self.M - 2:2, 2:self.M - 2:2] = '┼'
        self.grid[2::2, self.K] = '┤'
        self.grid[2::2, 0] = '├'
        self.grid[0, 0], self.grid[0, self.K], self.grid[self.K, 0], self.grid[self.K, self.K] = '┌', '┐', '└', '┘'
        self.grid[0, 2:-1:2] = '┬'
        self.grid[self.K, 2:-1:2] = '┴'

        # bringing all box characters to a single list for further checking
        self.line = ['─', '│', '┼', '┌', '┐', '└', '┘', '┤', '┬', '├', '┴', '*']

        # bringing all wall characters to a single list for further checking
        self.wall = ['x', 'X']

        # turn = 1 indicates player 0 turn and
        # turn = -1 indicates player 1 turn
        self.turn = -1 if isHumanFirst else 1

        # labels used to mark rows
        # extra ' ' at two ends are because no one needs to block a border so
        # no labels required to mark borders
        self.row_labels = [' '] + [chr(i) for i in range(65 + self.M - 3, 64, -1)] + [' ']

        # labels used to mark columns
        self.col_labels = [chr(i) for i in range(97, 97 + self.M - 2)]

        # a list of all the players as dictionaries of their
        # attributes such as symbol and walls left
        self.players = [dict(symbol='AI', row=1, col=2 * int(self.M / 4) + 1, walls=10),
                dict(symbol='H', row=-2, col=2 * int(self.M / 4) + 1, walls=10)]
        
    def display(self):
        """Prints stuff on the screen in a pretty way."""
        self.grid[self.players[0]['row'], self.players[0]['col']] = self.players[0]['symbol']
        self.grid[self.players[1]['row'], self.players[1]['col']] = self.players[1]['symbol']

        i = 0
        for row in self.grid:
            print(self.row_labels[i], end=' ')
            i += 1
            for cell in row:
                if cell in [self.line[0], self.wall[0]]:
                    print(5 * cell, sep='', end='')
                elif cell in self.line + self.wall:
                    print(cell, sep='', end='')
                else:
                    print('  ', cell, '  ', sep='', end='')
            print()
        final_label = '     '
        for char in self.col_labels:
            final_label += char + 2 * ' '
        print(final_label)
        

    def display_turn(self):
        """Prints on the screen which player's turn it is."""
        if self.turn == 1:
            print(f"""
    \tTurn: AI
    \tWalls Left: {self.players[0]['walls']}
    \tOpponent Walls Left: {self.players[1]['walls']}""")
        elif self.turn == -1:
            print(f"""
    \tTurn: HUMAN
    \tWalls Left: {self.players[1]['walls']}
    \tOpponent Walls Left: {self.players[0]['walls']}""")
        else:
            pass

    def get_move(self):
        inp = input(
            """\n\t\t[GUIDE]
        • u for UP      • d for DOWN
        • l for LEFT    • r for RIGHT
        • Use an uppercase and a lowercase letter for placing a wall in the relevant coordinates.

        Example 1: Bc (or cB) --> The wall will take take two segments : intersection of B and c and B and e
        Example 2: fE (or Ef) --> The wall will take take two segments : intersection of E and f and C and f
> """)
        vect = char_to_vector(inp)
        if inp in ['u', 'd', 'l', 'r']:
            vect = char_to_vector(inp)
            return [vect, None, None]
        else:
            if self.is_in_wall_position_format(inp):
                move = self.label_to_tuple(inp)
                vec_res, warning_string = check_wall(move)
                if vec_res:
                    if vec_res == "h":
                        move = translate_wall(move)
                        return [None, move, None]
                    if vec_res == "v":
                        move = translate_wall(move)
                        return [None, None, move] 
                else:
                    self.warn("Incorrect WALL entry : "+ warning_string)
                
            else:
                self.warn("Incorrect entry : NOT A WALL NOR A PAWN MOVE")
        

    def label_to_tuple(self, place):
        """Converts a string looking like 'iB' to a tuple looking like (9, 4)."""
        if len(place) == 2 and place[0].isupper() and place[1].islower():
            upper = place[0]
            lower = place[1]
        elif len(place) == 2 and place[1].isupper() and place[0].islower():
            upper = place[1]
            lower = place[0]
        else:
            self.warn("Invalid place.")
        return - ord(upper) + 82, ord(lower) - 96

    def wall_char_from_line_char(self, line_char):
        """Decides what wall character ('x' or 'X') should
        be chosen based on what line character (horizontal or vertical) it
        is going to replace."""
        try:
            return self.wall[self.line.index(line_char)]
        except ValueError:
            return line_char
        
    def warn(self, string):
        """Wipes screen and then shows the warning
        and then comes back to the game"""
        cls()
        print(string)
        sleep(1.5)
        self.display()
        self.display_turn()

    def apply_pawn_move(self, numPlayer, move):
        vector = translate_move(move)
        player = self.players[numPlayer]
        """Moves player one cell with the vector given."""
        before_row = player['row']
        before_col = player['col']
        # multiplies by two because we need to skip lines
        player['row'] -= 2 * vector[1]
        player['col'] -= 2 * vector[0]
        self.grid[self.players[0]['row'], self.players[0]['col']] = self.players[0]['symbol']
        self.grid[self.players[1]['row'], self.players[1]['col']] = self.players[1]['symbol']
        self.grid[before_row, before_col] = ' '

        self.turn *= -1

    def apply_wall (self, numPlayer, move, vertical):
        player = self.players[numPlayer]
        player["walls"] -=1
        r,c = move[0]+1, move[1]+1
        if vertical: # EACH wall in our game takes two edges
            self.grid[r*2-1, c*2] = self.wall_char_from_line_char(self.grid[r*2-1, c*2])
            self.grid[r*2+1, c*2] = self.wall_char_from_line_char(self.grid[r*2+1, c*2])
        else:
            self.grid[r*2, c*2-1] = self.wall_char_from_line_char(self.grid[r*2, c*2-1])
            self.grid[r*2, c*2+1] = self.wall_char_from_line_char(self.grid[r*2, c*2+1])
        self.turn *= -1

    #Bon
    def is_in_wall_position_format(self, place):
        """Decides whether its input has a form like 'iB' or not."""
        if len(place) == 2 and place[0].isupper() and place[1].islower():
            upper = place[0]
            lower = place[1]
        elif len(place) == 2 and place[1].isupper() and place[0].islower():
            upper = place[1]
            lower = place[0]
        else:
            return False
        if upper in self.row_labels[1:-1] and lower in self.col_labels:
            return True
        else:
            return False

        

# Bon
def translate_move(vector):

    if vector[0] < 3 and vector[0] > -3 and vector[1] < 3 and vector[1] > -3 :
        return [-1* vector[1], -1*vector[0]]
    else : 
        raise Exception("TRANSLATE MOVE : Invalid vector move :"+str(vector))

def translate_wall(move):
    return (move[0]-1) // 2 , (move[1] -1) // 2 

# Bon
def check_wall(move):
    print("check_wall", move)
    if (move[0] % 2) ==  (move[1] % 2) :
        return False, "The intersection of the row and col coordinates are not a segment"
    if (move[1] % 2) == 0 :
        if (move[0] < 17):
            return "v", ""  # vertical wall if row %2 =0
        else:
            return False, "The choosen wall would go beyond the boundries of the board" # because each wall will take to poisiton, the last one cannot be selected
    else :
        if (move[1] < 17):
            return "h", ""  # horizental wall if row %2 =1
        else:
            return False, "The choosen wall would go beyond the boundries of the board" # because each wall will take to positions, the last one cannot be selected

# Bon
def char_to_vector(char):
    """Converts w, a, s, d to their appropriate vectors."""
    if char == 'u':
        return [-1, 0]
    elif char == 'd':
        return [1, 0]
    elif char == 'l':
        return [0, -1]
    elif char == 'r':
        return [0, 1]


def declare_winner(player):
    """Winner's pawn gets some beautiful asterisks ('*') to celebrate their
    winner-ship. Nice, eh?"""
    global grid, winner, M, players
    index = players.index(player)
    if index == 0:
        winner = players[0]
        r = M - 2
        c = players[0]['col']
        grid[r - 1:r + 2, c - 1:c + 2:2] = '*'
        grid[r, c] = players[0]['symbol']
    elif index == 1:
        winner = players[1]
        r = - M + 1
        c = players[1]['col']
        grid[r - 1:r + 2, c - 1:c + 2:2] = '*'
        grid[r, c] = players[1]['symbol']
    else:
        pass


def run():
    """The main function. All the good stuff happen here!"""
    global winner
    if players[0]['row'] == M - 2:
        declare_winner(players[0])
        finish()
    elif players[1]['row'] == -M + 1:
        declare_winner(players[1])
        finish()
    else:
        global turn
        turn_index = int(-0.5 * turn + 0.5)
        cls()
        display()
        display_turn()
        inp = input(
            """\n\t\t[GUIDE]
        • w for moving your pawn UP
        • s for moving your pawn DOWN
        • a for moving your pawn LEFT
        • d for moving your pawn RIGHT
        • Use an uppercase and a lowercase
          letter for placing a wall in the
          relevant coordinates.
        Example 1: Bc (or cB)
        Example 2: iD (or Di)
> """)
        vect = char_to_vector(inp)
        if inp in ['w', 's', 'a', 'd']:
            vect = char_to_vector(inp)
            if move_allowed(vect, players[turn_index]) == 'T':
                turn *= -1
                move(players[turn_index], vect)
                run()
            elif move_allowed(vect, players[turn_index]) == 'J':
                turn *= -1
                move(players[turn_index], [2 * i for i in vect])
                run()
            else:
                warn("Incorrect! What are you missing?")
        else:
            if is_in_wall_position_format(inp):
                draw_wall(players[turn_index], inp)
                run()
            else:
                warn("Incorrect! What are you missing?")


def finish():
    """Brings game to a conclusion and asks the player whether
    they intend to do another game or not."""
    cls()
    display()
    winner_symbol = winner['symbol']
    print(f'{winner_symbol} has won! Congrats!')
    prompt = "Another hand? [Y/n]\n> "
    answer = input(prompt)
    if answer in ['Y', 'y', '']:
        set_up()
        run()
    else:
        quit()



