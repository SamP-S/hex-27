from copy import deepcopy
import sys

class BoardSupport():
    """ This class describes some support functions for frequent operations
        involving collecting coordinate lists
    """

    DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1), (-1, 1), (1, -1)]

    @staticmethod
    def get_neighbours(board, coord):
        """ Return list of coordinates of neighbouring cells inside board space """
        neighbours = []
        for dx, dy in BoardSupport.DIRECTIONS:
            x = coord[0] + dx
            y = coord[1] + dy
            if x >= 0 and x < len(board) and y >= 0 and y < len(board):
                neighbours.append((x, y))
        return neighbours
            
    @staticmethod
    def get_empty(board):
        """ Creates list of coordinates of all unclaimed cells """
        coords = []
        for i in range(len(board)):
            for j in range(len(board)):
                if (board[i][j]) == "0":
                    coords.append((i, j))
        return coords
    
    @staticmethod
    def create_board(board_size):
        """ Creates new empty board of board_size x board_size """
        return [["0"]*board_size for i in range(board_size)]
    
    @staticmethod
    def dfs(board, player, coord, front, back):
        """ Depth First Search for win checking 
            Red top->bottom
            Blue left->right """
        
        i = coord[0]
        j = coord[1]
        
        # print(f"dfs: i={i}; j={j}; board={board}")
        board_size = len(board)

        # success if at vertical edges for Blue
        if (i == 0) and player == "B":
            front = True
        if (i == board_size - 1 and player == "B"):
            back = True

        # success if at horizontal edges for Red
        if j == 0 and player == "R":
            front = True
        if j == board_size - 1 and player == "R":
            back = True

        # update board to mark where we've been
        if board[i][j] == player:
            board[i][j] = "#"
        # ignore if coord to inspect has already been travelled or is empty
        else:
            return front, back

        # iterate through checking neighbours
        for n in BoardSupport.get_neighbours(board, (i,j)):
            # check neighbours
            next_front, next_back = BoardSupport.dfs(board, player, n, front, back)
            if next_front and next_back:
                return True, True

        # no neighbours or connections to edges
        return front, back

    @staticmethod
    def check_winner(board):
        """ Checks if there is a connection from one side of the board to the other
            Red top->bottom
            Blue left->right
            Return 1 for Red win, -1 for Blue win, 0 for no winner """

        board_size = len(board)
        end_idx = board_size - 1
        empty_line = ["0"]*board_size
        
        # static analysis for speed
        for i in range(board_size):
            if board[i] == empty_line:
                return 0

        # iterate over top row to start dfs search
        for i in range(board_size):
            front, back = BoardSupport.dfs(deepcopy(board), "R", (i, 0), False, False)
            if board[i][0] == 'R' and front and back:
                return 1
        
        # build columns as cant just grab like rows
        for i in range(1, end_idx - 1):
            test_line = [row[i] for row in board]
            if test_line == empty_line:
                return 0
        front_line = [row[0] for row in board]
        back_line = [row[end_idx] for row in board]
        # static analysis to optimise performance
        if front_line != empty_line and back_line != empty_line:
            #  iterate over left column to start dfs search
            for j in range(board_size):
                front, back = BoardSupport.dfs(deepcopy(board), "B", (0, j), False, False)
                if board[0][j] == 'B' and front and back:
                    return -1
        return 0
    
    @staticmethod
    def evaluate_is_win(end_state, player):
        """ Evaluate an end state to the origal player to check if it is a winning state """
        if player == "R" and end_state == 1:
            return True
        elif player == "B" and end_state == -1:
            return True
        else:
            return False
    
    @staticmethod
    def opp_player(player):
        if player == "R":
            return "B"
        else:
            return "R"

if __name__ == "__main__":
    board_size = 5
    board = BoardSupport.create_board(board_size)
    
    # validate empty board
    print("Board")
    print(board)
    print("Win State")
    print(BoardSupport.check_winner(board))

    # fill diagonal R win
    for i in range(board_size):
        board[board_size - i - 1][i] = "R"

    print("Board")
    print(board)
    print("Win State")
    print(BoardSupport.check_winner(board))
    