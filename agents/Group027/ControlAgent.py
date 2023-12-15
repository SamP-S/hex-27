import socket
from random import choice
from time import sleep
from AlphaBeta import AlphaBeta
from Resistance import Resistance
from BoardSupport import BoardSupport
from MCTS import MCTS
from MoHex import MoHex
from Dijkstra import Dijkstra

class ControlAgent():
    """This class describes the our ControlAgent. It interfaces with MoHex and
        gets it to generate commands then plays them. It also handles MoHex crashing.
    """

    HOST = "127.0.0.1"
    PORT = 1234

    OPENING_WEIGHTS = [
        [0.312, 0.356, 0.318, 0.301, 0.325, 0.294, 0.297, 0.285, 0.299, 0.324, 0.573],
        [0.449, 0.460, 0.462, 0.445, 0.414, 0.411, 0.399, 0.423, 0.464, 0.708, 0.595],
        [0.446, 0.669, 0.656, 0.624, 0.614, 0.585, 0.569, 0.611, 0.739, 0.558, 0.404],
        [0.583, 0.495, 0.739, 0.673, 0.653, 0.731, 0.627, 0.749, 0.627, 0.709, 0.613],
        [0.594, 0.700, 0.609, 0.726, 0.678, 0.681, 0.748, 0.592, 0.748, 0.701, 0.549],
        [0.574, 0.716, 0.707, 0.723, 0.723, 0.709, 0.732, 0.672, 0.706, 0.706, 0.564],
        [0.603, 0.679, 0.730, 0.613, 0.776, 0.693, 0.705, 0.730, 0.636, 0.674, 0.597],
        [0.607, 0.701, 0.672, 0.734, 0.638, 0.668, 0.665, 0.686, 0.726, 0.529, 0.547],
        [0.451, 0.578, 0.729, 0.627, 0.565, 0.575, 0.604, 0.572, 0.630, 0.622, 0.431],
        [0.611, 0.701, 0.451, 0.428, 0.414, 0.396, 0.405, 0.411, 0.443, 0.449, 0.431],
        [0.607, 0.329, 0.315, 0.287, 0.306, 0.266, 0.260, 0.257, 0.251, 0.273, 0.301]
    ]

    def __init__(self, board_size=11):
        self.s = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )

        self.s.connect((self.HOST, self.PORT))

        self.board_size = board_size
        self.board = []
        self.colour = ""
        self.turn_count = 0
        self.ab = AlphaBeta(board_size)
        self.resistance = Resistance(board_size)
        self.mcts = MCTS(board_size)
        self.mohex = MoHex()
        self.dijkstra = Dijkstra()

    def run(self):
        """Reads data until it receives an END message or the socket closes."""

        while True:
            data = self.s.recv(1024)
            if not data:
                break
            if (self.interpret_data(data)):
                break

    def interpret_data(self, data):
        """Checks the type of message and responds accordingly. Returns True
        if the game ended, False otherwise.
        """

        messages = data.decode("utf-8").strip().split("\n")
        messages = [x.split(";") for x in messages]
        # print(messages)
        for s in messages:
            if s[0] == "START":
                self.board_size = int(s[1])
                self.colour = s[2]
                self.board = BoardSupport.create_board(self.board_size)

                if self.colour == "R":
                    self.make_move(None, True)

            elif s[0] == "END":
                #print(s)
                return True

            elif s[0] == "CHANGE":
                if s[3] == "END":
                    #print(s)
                    return True

                elif s[1] == "SWAP":
                    self.colour = self.opp_colour()
                    if s[3] == self.colour:
                        self.make_move(None, True)

                elif s[3] == self.colour:
                    opp_move = [int(x) for x in s[1].split(",")]
                    self.board[opp_move[0]][opp_move[1]] = self.opp_colour()
                    self.make_move(opp_move)

        return False

    def make_move(self, opp_move, opp_swapped = False):

        use_ai_move = True
        move = None

        # If first move we either need to make the first move or choose to swap
        if self.turn_count == 0:
            if self.colour == "B":
                #we have the chance to swap
                if self.OPENING_WEIGHTS[opp_move[0]][opp_move[1]] > 0.6:
                    self.s.sendall(bytes("SWAP\n", "utf-8"))
                    self.turn_count += 1
                    return
            else:
                # we make the first move
                move_options = []
                for x in range(0, 11):
                    for y in range(0, 11):
                        if self.OPENING_WEIGHTS[x][y] > 0.7:
                            move_options.append((x, y))
                move = choice(move_options)
                #print(move_options)
        if use_ai_move:
            # If need to generate AI move (eg. it is not the first move)

            # Get shortest path across board to win
            dijkstra_path = self.dijkstra.make_path(self.board, self.colour)

            # If one move away from winning then play that move
            if len(dijkstra_path) == 1:
                move = dijkstra_path[0]
                #print("DIJKSTRA - FINAL MOVE", move)
            else:
                # Else use mohex
                try:
                    move = self.mohex.make_move(self.colour, opp_move, opp_swapped)
                except:
                    # If mohex crashes then use Dijkstra
                    move = False
                if move == False:
                    # print("MOHEX CRASHED############################################")
                    #input()
                    move = self.mcts.make_move(self.board, self.colour, max_time=5)
                    # move = choice(dijkstra_path)
                    #print("DIJKSTRA", move)

            # if (self.turn_count > 60):
            #     move = self.ab.make_move(self.board, self.colour, 3)
            # else:
            #     move = self.resistance.make_move(self.board, self.colour)


        # send move
        self.s.sendall(bytes(f"{move[0]},{move[1]}\n", "utf-8"))
        self.board[move[0]][move[1]] = self.colour

        # increment turn counter
        self.turn_count += 1

    def _close(self):
        """Closes the socket."""

        self.mohex._close()

        self.s.close()
        return 0

    def opp_colour(self):
        """Returns the char representation of the colour opposite to the
        current one.
        """
        if self.colour == "R":
            return "B"
        elif self.colour == "B":
            return "R"
        else:
            return "None"


if (__name__ == "__main__"):
    agent = ControlAgent()
    agent.run()
