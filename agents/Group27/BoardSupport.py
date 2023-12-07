

class Coordinates():
    """ This class describes some support functions for frequent operations
        involving collecting coordinate lists
    """

    DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1), (-1, 1), (1, -1)]

    @staticmethod
    def get_neighbours(board, coord):
        """ Return list of coordinates of neighbouring cells inside board space """
        neighbours = []
        for dx, dy in Coordinates.DIRECTIONS:
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