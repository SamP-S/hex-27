import socket
from random import choice
from time import sleep
from AlphaBeta import AlphaBeta
from Resistance import Resistance
from BoardSupport import BoardSupport
from MCTS import MCTS

class ControlAgent():
    """This class describes the default Hex agent. It will randomly send a
    valid move at each turn, and it will choose to swap with a 50% chance.
    """

    HOST = "127.0.0.1"
    PORT = 1234

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
                    self.make_move()

            elif s[0] == "END":
                print(s)
                return True

            elif s[0] == "CHANGE":
                if s[3] == "END":
                    print(s)
                    return True

                elif s[1] == "SWAP":
                    self.colour = self.opp_colour()
                    if s[3] == self.colour:
                        self.make_move()

                elif s[3] == self.colour:
                    opp_move = [int(x) for x in s[1].split(",")]
                    self.board[opp_move[0]][opp_move[1]] = self.opp_colour()
                    self.make_move()

        return False

    def make_move(self):
        """Makes a move according to turn and mohex state """

        # check if swap choice
        if self.colour == "B" and self.turn_count == 0 and choice([0, 1]) == 1:
            self.s.sendall(bytes("SWAP\n", "utf-8"))
        else:
            # # if close to finishing
            # # use alpha beta to get guaranteed win
            # if (self.turn_count > 60):
            #     move = self.ab.make_move(self.board, self.colour, 3)
            # else:
            #     move = self.resistance.make_move(self.board, self.colour)
            move = self.mcts.make_move(self.board, self.colour)

            # send move
            self.s.sendall(bytes(f"{move[0]},{move[1]}\n", "utf-8"))
            self.board[move[0]][move[1]] = self.colour

        # increment turn counter
        self.turn_count += 1

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
