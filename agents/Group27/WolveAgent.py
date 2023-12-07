import socket
from random import choice
from time import sleep, perf_counter
from copy import deepcopy


class WolveAgent():
    """This class describes the default Hex agent. It will randomly send a
    valid move at each turn, and it will choose to swap with a 50% chance.
    """

    HOST = "127.0.0.1"
    PORT = 1234

    DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1), (-1, 1), (1, -1)]

    def __init__(self, eval_func=1):
        if eval_func == 0:
            self.evaluate_board = self.flat_board_evaluation
        elif eval_func == 1:
            self.evaluate_board = self.simple_board_evaluation
        else:
            print("ERROR: NO EVAL FUNCTION")

    def run(self):
        """A finite-state machine that cycles through waiting for input
        and sending moves.
        """
        
        self._board_size = 0
        self._board = []
        self._colour = ""
        self._turn_count = 1
        self._choices = []
        self._red_moves = []
        self._blue_moves = []
        self.node_count = 0
        
        states = {
            1: WolveAgent._connect,
            2: WolveAgent._wait_start,
            3: WolveAgent._make_move,
            4: WolveAgent._wait_message,
            5: WolveAgent._close
        }

        res = states[1](self)
        while (res != 0):
            res = states[res](self)

    def _connect(self):
        """Connects to the socket and jumps to waiting for the start
        message.
        """

        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._s.connect((WolveAgent.HOST, WolveAgent.PORT))
        return 2

    def _wait_start(self):
        """Initialises itself when receiving the start message, then
        answers if it is Red or waits if it is Blue.
        """
        
        data = self._s.recv(1024).decode("utf-8").strip().split(";")
        if (data[0] == "START"):
            self._board = []
            self._board_size = int(data[1])
            
            for i in range(self._board_size):
                row = []
                for j in range(self._board_size):
                    self._choices.append((i, j))
                    row.append("0")
                self._board.append(row)
            self._colour = data[2]

            print(f"boardsize: {self._board_size}")
            print(f"colour: {self._colour}")

            if (self._colour == "R"):
                return 3
            else:
                return 4

        else:
            print("ERROR: No START message received.")
            return 0

    def _make_move(self):
        """Makes a random valid move. It will choose to swap with
        a coinflip.
        """
        # print(f"board: {self._board}")
        # print(f"choices: {self._choices}")
        print(f"turncount: {self._turn_count}")
        
        if (self._turn_count == 2 and choice([0, 1]) == 1):
            msg = "SWAP\n"
        else:
            # move = choice(self._choices)
            self.node_count = 0
            start_time = perf_counter()
            val, move = self.alpha_beta(deepcopy(self._board), deepcopy(self._choices), self._colour, 3)
            print(f"ab finish: val={val}; move={move}; nodes={self.node_count}; time={perf_counter() - start_time}")
            msg = f"{move[0]},{move[1]}\n"
        
        self._s.sendall(bytes(msg, "utf-8"))

        return 4

    def dfs(self, board, player, i, j, front, back):
        """ Depth First Search for win checking 
            Red top->bottom
            Blue left->right """
        # print(f"dfs: i={i}; j={j}; board={board}")

        # validate the coordinates to check
        if i < 0 or i >= self._board_size or j < 0 or j >= self._board_size or board[i][j] != player:
            return front, back

        # success if at vertical edges for Blue
        if (i == 0) and player == "B":
            front = True
        if (i == self._board_size - 1 and player == "B"):
            back = True

        # success if at horizontal edges for Red
        if j == 0 and player == "R":
            front = True
        if j == self._board_size - 1 and player == "R":
            back = True

        # update board to mark where we've been
        board[i][j] = "#"
        # iterate through checking neighbours
        for dx, dy in self.DIRECTIONS:
            # check neighbours
            next_front, next_back = self.dfs(board, player, i + dx, j + dy, front, back)
            if next_front and next_back:
                return True, True

        # no neighbours or connections to edges
        return front, back

    def check_winner(self, board):
        """ Checks if there is a connection from one side of the board to the other
            Red top->bottom
            Blue left->right
            Return 1 for Red win, -1 for Blue win, 0 for no winner """

        # start_time = perf_counter()
        # iterate over top row to start dfs search
        for i in range(self._board_size):
            front, back = self.dfs(deepcopy(board), "R", i, 0, False, False)
            if board[i][0] == 'R' and front and back:
                # print(f"AB WIN RED ({i},{0})")
                # print(f"check_win time: {perf_counter() - start_time}")
                return 1
        #  iterate over left column to start dfs search
        for j in range(self._board_size):
            front, back = self.dfs(deepcopy(board), "B", 0, j, False, False)
            if board[0][j] == 'B' and front and back:
                # print(f"AB WIN BLUE ({0},{j})")
                # print(f"check_win time: {perf_counter() - start_time}")
                return -1
        # print(f"check_win time: {perf_counter() - start_time}")
        return 0

    def alpha_beta(self, board, choices, player, depth, alpha=-1000.0, beta=1000.0):
        """ Using min-max with alpha beta pruning
            Red maximising
            Blue minimising
            return the move we want to make """
        # print(f"alpha beta: depth={depth}; alpha={alpha}; beta={beta}; choices={len(choices)}")
        best_move = (-1, -1)
        self.node_count += 1

        if depth == 0 or len(choices) == 0:
            win = self.check_winner(deepcopy(board))
            if win == 0:
                return self.evaluate_board(board, player), best_move
            return win, best_move

        # maximising
        if player == "R":
            best_val = -10000
            for i, choice in enumerate(choices):
                sim_board = deepcopy(board)
                sim_board[choice[0]][choice[1]] = player
                sim_choices = deepcopy(choices)
                move = sim_choices.pop(i)
                val, next_move = self.alpha_beta(sim_board, sim_choices, "B", depth-1, alpha, beta)
                if val > best_val:
                    best_move = move
                    best_val = val
                    alpha = val
                if alpha >= beta:
                    break
            return best_val, best_move

        # minimising
        else:
            best_val = 10000
            for i, choice in enumerate(choices):
                sim_board = deepcopy(board)
                sim_board[choice[0]][choice[1]] = player
                sim_choices = deepcopy(choices)
                move = sim_choices.pop(i)
                val, next_move  = self.alpha_beta(sim_board, sim_choices, "R", depth-1, alpha, beta)
                if val < best_val:
                    best_move = move
                    best_val = val
                    beta = val
                if alpha >= beta:
                    break
            return best_val, best_move

    def flat_board_evaluation(self, board, player):
        """ return value of current board according to player as float """
        return 0.5
        
    def simple_board_evaluation(self, board, player):
        """ return value of current board according to player as float """
        return 0.5

    def _wait_message(self):
        """Waits for a new change message when it is not its turn."""

        self._turn_count += 1

        data = self._s.recv(1024).decode("utf-8").strip().split(";")
        if (data[0] == "END" or data[-1] == "END"):
            return 5
        else:

            if (data[1] == "SWAP"):
                self._colour = self.opp_colour()
            else:
                x, y = data[1].split(",")
                print("data:", data)
                self._choices.remove((int(x), int(y)))
                self._board[int(x)][int(y)] = self.opp_colour()
                if data[-1] == "R":
                    self._red_moves.append((int(x), int(y)))
                elif data[-1] == "B":
                    self._blue_moves.append((int(x), int(y)))

            if (data[-1] == self._colour):
                return 3

        return 4

    def _close(self):
        """Closes the socket."""

        self._s.close()
        return 0

    def opp_colour(self):
        """Returns the char representation of the colour opposite to the
        current one.
        """
        
        if self._colour == "R":
            return "B"
        elif self._colour == "B":
            return "R"
        else:
            return "None"


if (__name__ == "__main__"):
    agent = WolveAgent()
    agent.run()
