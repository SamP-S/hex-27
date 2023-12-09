import socket
from random import choice
from time import sleep
import subprocess
import time
RESPONSES = []
# Blue & White connect horizontally
# Red & Black vertically
mohex_colour_map = {'R': 'Bl', 'Bl': 'R', 'B': 'W', 'W': 'B'}
# Colour mapping



class mohexAgent():
    """This class describes the default Hex agent. It will randomly send a
    valid move at each turn, and it will choose to swap with a 50% chance.
    """

    HOST = "127.0.0.1"
    PORT = 1234
    # Create dictionaries to convert between letters and integers

    def __init__(self):
        # Start the subprocess when the agent is initialized
        self._start_subprocess()

    def _start_subprocess(self):
        # Replace 'your_c_agent_executable' with the actual path to your C agent executable
        self._process = subprocess.Popen(["./agents/Group27/mohex"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,  
                                         #stderr=subprocess.DEVNULL, 
                                         text=True)
        time.sleep(1)
        print("Game start")

    def _terminate_subprocess(self):
        # Terminate the subprocess when the agent is closed
        self._process.terminate()

    def run(self):
        """A finite-state machine that cycles through waiting for input
        and sending moves.
        """
        
        self._board_size = 0
        self._board = []
        self._colour = ""
        self._turn_count = 1
        self._choices = []
        self._opponent_moves = []
        self._swapped = True
        
        states = {
            1: mohexAgent._connect,
            2: mohexAgent._wait_start,
            3: mohexAgent._make_move,
            4: mohexAgent._wait_message,
            5: mohexAgent._close
        }

        res = states[1](self)
        while (res != 0):
            res = states[res](self)
    
    

    def _connect(self):
        """Connects to the socket and jumps to waiting for the start
        message.
        """
        
        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._s.connect((mohexAgent.HOST, mohexAgent.PORT))

        return 2

    def _wait_start(self):
        """Initialises itself when receiving the start message, then
        answers if it is Red or waits if it is Blue.
        """
        
        data = self._s.recv(1024).decode("utf-8").strip().split(";")
        if (data[0] == "START"):
            self._board_size = int(data[1])
            for i in range(self._board_size):
                for j in range(self._board_size):
                    self._choices.append((i, j))
            self._colour = data[2]

            if (self._colour == "R"):
                return 3
            else:
                return 4

        else:
            print("ERROR: No START message received.")
            return 0

    def _make_move(self):
        """Updates mohex board and requests it to generate move
        Then plays move
        """
        print(f"Colour: {self._colour}")
        if (self._turn_count == 2 and choice([0, 1]) == 1):
            msg = "SWAP\n"
        else:
            if self._turn_count == 1:
                self._send_mohex_command("boardsize 11 11")
                response = self._read_mohex_response()
                mohex_colour = mohex_colour_map[self._colour]
                self._send_mohex_command(f"genmove {mohex_colour[0]}")
                response = self._read_mohex_response()
                
                move = self.mohex_to_hex_board(response[2], int(response[3]))
                msg = f"{move[0]},{move[1]}\n"
            else:
                # Send opponent's most recent move to mohex
                if self._turn_count != 3:
                    opp_move = self._opponent_moves[-1]
                    
                    opp_move = self.hex_to_mohex_board(opp_move[0], str(opp_move[1]))

                    opp_mohex_colour = mohex_colour_map[self.opp_colour()][0]
                    self._send_mohex_command(f"play {opp_mohex_colour} {opp_move[0]+str(opp_move[1])}")
                    response = self._read_mohex_response()

                # Request move from mohex
                mohex_colour = mohex_colour_map[self._colour][0]
                self._send_mohex_command(f"genmove {mohex_colour}")
                response = self._read_mohex_response()

                # Send move to server
                #move = self._convert_mohex_coordinates(response[2], int(response[3]))
                move = self.mohex_to_hex_board(response[2], int(response[3]))
                print(f"Move: {move}")
                msg = f"{move[0]},{move[1]}\n"
        
        self._s.sendall(bytes(msg, "utf-8"))

        return 4
    
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
                move = (int(x), int(y))
                self._choices.remove(move)
                self._opponent_moves.append(move)  # Store opponent's move

                # Print the most recent opponent's move
                # mohex_coords = self._(move[0], move[1])
                # print(f"Opponent's most recent move: {mohex_coords[0]+mohex_coords[1]}")

            if (data[-1] == self._colour):
                return 3

        return 4

    def _close(self):
        # Close the socket
        self._s.close()
        
        # Terminate the subprocess
        self._terminate_subprocess()

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
    
    def _send_mohex_command(self, command):
        self._process.stdin.write(command + '\n')
        self._process.stdin.flush()
        print(f"Command sent: {command}")

    def _read_mohex_response(self):
        response = ''
        while not response:
            output = self._process.stdout.readline().strip()
            if output == '' or output.endswith('\n'):
                continue  # Skip empty or incomplete lines
            response = output 
        print(f"RESPONSE: {response}")
        return response
    
    def mohex_to_hex_board(self, val1, val2):
        firstval = val2-1
        secondval = ord(val1)-ord('a')
        return firstval, secondval
    
    def hex_to_mohex_board(self, val1, val2):
        firstval = chr(ord('a') + int(val2))
        secondval = val1+1
        return firstval, secondval
    




if (__name__ == "__main__"):
    agent = mohexAgent()
    agent.run()

