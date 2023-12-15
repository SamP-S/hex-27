import subprocess
import time
import select

class MoHex():

    def __init__(self, board_size=11, eval_func=1):
        self.mohex_colour_map = {'R': 'Bl', 'Bl': 'R', 'B': 'W', 'W': 'B'}
        self._board_size = board_size
        self._start_subprocess()
    
    def _start_subprocess(self):
        self._process = subprocess.Popen(["./agents/Group27/mohex/mohex"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,  
                                         stderr=subprocess.DEVNULL, 
                                         text=True)
        time.sleep(1)
        self._send_mohex_command("boardsize 11 11")
        response = self._read_mohex_response()
        self._send_mohex_command("param_mohex num_threads 24")
        response = self._read_mohex_response()
        self._send_mohex_command("param_mohex max_time 5")
        response = self._read_mohex_response()
        self._send_mohex_command("param_mohex lock_free 1")
        response = self._read_mohex_response()
        self._send_mohex_command("param_mohex ponder 0")
        #print("Game start")
    
    def _terminate_subprocess(self):
        # Terminate the subprocess when the agent is closed
        self._process.terminate()
        #print("Victory!")
    
    def _close(self):
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
        if self._process.poll() is None:  # Check if the process is still running
            self._process.stdin.write(command + '\n')
            self._process.stdin.flush()
        else:
            raise Exception("Cannot send command: The process has terminated")
        #print(f"Command sent: {command}")

    def _read_mohex_response(self, timeout=15.0):
        response = 'timeout'
        end_time = time.time() + timeout
        while time.time() < end_time:
            ready, _, _ = select.select([self._process.stdout], [], [], end_time - time.time())
            if ready:
                output = self._process.stdout.readline().strip()
                if output == '' or output.endswith('\n'):
                    continue  # Skip empty or incomplete lines
                response = output
                break
        #print(f"RESPONSE: {response}")
        return response
    
    def mohex_to_hex_board(self, val1, val2):
        firstval = int(val2)-1
        secondval = ord(val1)-ord('a')
        return firstval, secondval
    
    def hex_to_mohex_board(self, val1, val2):
        firstval = chr(ord('a') + int(val2))
        secondval = val1+1
        return firstval, secondval
    
    def separate_letter_and_number(self, input_str):
        letter = ''.join(char for char in input_str if char.isalpha())
        number = ''.join(char for char in input_str if char.isdigit())
        return letter, number
    
    def make_move(self, colour, opp_move, opp_swapped = False):
        """Play a round of Hex."""
        opp_colour = "R" if colour == "B" else "B"
        # First we need to play opponents last move on MoHex
        # Check if opponent swapped or not
        if not opp_swapped:
            # Play opponents last move
            opp_move = self.hex_to_mohex_board(opp_move[0], str(opp_move[1]))
            opp_mohex_colour = self.mohex_colour_map[opp_colour][0]
            self._send_mohex_command(f"play {opp_mohex_colour} {opp_move[0]+str(opp_move[1])}")
            response = self._read_mohex_response()
            if response == 'timeout':
                return False
            #print(f"DEBUG: Opponent move: {opp_move}")
        
        # Then we need to generate our move
        mohex_colour = self.mohex_colour_map[colour][0]
        self._send_mohex_command(f"genmove {mohex_colour}")
        response = self._read_mohex_response()
        #print("Response: ", response)
        if response == 'timeout':
            #print("Timeout")
            return False
            # sys.exit()#############################
        
        # Send move to server
        #print(f"RESPONSE: {response}")
        move = self.separate_letter_and_number(response)
        move = self.mohex_to_hex_board(move[0], move[1])
        return move

if (__name__ == "__main__"):
    print("MoHex.py has no main")
