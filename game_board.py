import numpy as np
import modules.board_param as param

class Board:
	def __init__(self, *args):
		if len(args) == 1 and isinstance(args[0], np.ndarray) and args[0].ndim == 2:
			self.board = args[0]
			self.score = self.score_position(param.PLAYER_PIECE)
		else:
			self.board = np.zeros((param.ROW_COUNT, param.COLUMN_COUNT), dtype=np.int8)
			self.score = 0
		

	def pretty_print_board(self):
		flipped_board = np.flipud(self.board)

		print("\033[0;37;41m 0 \033[0;37;41m 1 \033[0;37;41m 2 \033[0;37;41m 3 \033[0;37;41m 4 \033[0;37;41m 5 \033[0;37;41m 6 \033[0m")
		for i in flipped_board:
			row_str = ""

			for j in i:
				if j == param.BOT_PIECE:
					#print(yellow)
					row_str +="\033[0;37;43m 1 "
				elif j ==param.PLAYER_PIECE:
					row_str +="\033[0;37;44m 2 "
				else:
					#print black
					row_str +="\033[0;37;45m   "

			print(row_str+"\033[0m")
		print("\033[0;37;41m 0 \033[0;37;41m 1 \033[0;37;41m 2 \033[0;37;41m 3 \033[0;37;41m 4 \033[0;37;41m 5 \033[0;37;41m 6 \033[0m")

	def get_valid_locations(self):
		valid_locations = []
		for col in range(param.COLUMN_COUNT):
			if self.is_valid_location(col):
				valid_locations.append(col)

		return valid_locations
	
	def is_valid_location(self, col):
		return self.board[param.ROW_COUNT - 1][col] == 0

	def is_valid_board(self):
		# For each column, check that there are no empty cells below a filled cell
		for col in range(param.COLUMN_COUNT):
			found_empty = False
			for row in range(param.ROW_COUNT):
				if self.board[row][col] == 0:
					found_empty = True
				elif found_empty:
					# Found a token above an empty cell, invalid board
					return False
		return True
	
	# TODO add more error / cheating & interim state handling
	def get_valid_state(self, new_grid):
		new_board = Board(new_grid)

		# First, check if the new board is valid
		if not new_board.is_valid_board():
			return None

		# The new board must have exactly one more token than the old board
		old_count = np.count_nonzero(self.board)
		new_count = np.count_nonzero(new_board)
		if new_count != old_count + 1:
			return None

		# Find the difference between the boards
		diff = new_board.board - self.board
		changed_positions = np.argwhere(diff != 0)

		# There must be exactly one changed position
		if changed_positions.shape[0] != 1:
			return None

		row, col = changed_positions[0]
		# The change must be on top of the stack (all rows below must be non-empty in new_board)
		if row > 0 and new_board[row-1][col] == 0:
			return None

		return int(col)

	def drop_piece(self, col, piece):
		for row in range(param.ROW_COUNT):
			if self.board[row][col] == 0:
				self.board[row][col] = piece
				break

	def winning_move(self, piece):
		# Check valid horizontal locations for win
		for c in range(param.COLUMN_COUNT - param.WINDOW_LENGTH + 1):
			for r in range(param.ROW_COUNT):
				if all(self.board[r][c + i] == piece for i in range(param.WINDOW_LENGTH)):
					return True

		# Check valid vertical locations for win
		for c in range(param.COLUMN_COUNT):
			for r in range(param.ROW_COUNT - param.WINDOW_LENGTH + 1):
				if all(self.board[r + i][c] == piece for i in range(param.WINDOW_LENGTH)):
					return True

		# Check valid positive diagonal locations for win
		for c in range(param.COLUMN_COUNT - param.WINDOW_LENGTH + 1):
			for r in range(param.ROW_COUNT - param.WINDOW_LENGTH + 1):
				if all(self.board[r + i][c + i] == piece for i in range(param.WINDOW_LENGTH)):
					return True

		# check valid negative diagonal locations for win
		for c in range(param.COLUMN_COUNT - param.WINDOW_LENGTH + 1):
			for r in range(param.WINDOW_LENGTH - 1, param.ROW_COUNT):
				if all(self.board[r - i][c + i] == piece for i in range(param.WINDOW_LENGTH)):
					return True

		return False

	def score_position(self, piece):
		score = 0

		# Score centre column
		centre_array = [int(i) for i in list(self.board[:, param.COLUMN_COUNT // 2])]
		centre_count = centre_array.count(piece)
		score += centre_count * (param.WINDOW_LENGTH - 1)

		# Score horizontal positions
		for r in range(param.ROW_COUNT):
			row_array = [int(i) for i in list(self.board[r, :])]
			for c in range(param.COLUMN_COUNT - param.WINDOW_LENGTH + 1):
				# Create a horizontal window of 4
				window = row_array[c:c + param.WINDOW_LENGTH]
				score += Board.evaluate_window(window, piece)

		# Score vertical positions
		for c in range(param.COLUMN_COUNT):
			col_array = [int(i) for i in list(self.board[:, c])]
			for r in range(param.ROW_COUNT - param.WINDOW_LENGTH + 1):
				# Create a vertical window of 4
				window = col_array[r:r + param.WINDOW_LENGTH]
				score += Board.evaluate_window(window, piece)

		# Score positive diagonals
		for r in range(param.ROW_COUNT - param.WINDOW_LENGTH + 1):
			for c in range(param.COLUMN_COUNT - param.WINDOW_LENGTH + 1):
				# Create a positive diagonal window of 4
				window = [self.board[r + i][c + i] for i in range(param.WINDOW_LENGTH)]
				score += Board.evaluate_window(window, piece)

		# Score negative diagonals
		for r in range(param.ROW_COUNT - param.WINDOW_LENGTH + 1):
			for c in range(param.COLUMN_COUNT - param.WINDOW_LENGTH + 1):
				# Create a negative diagonal window of 4
				window = [self.board[r + param.WINDOW_LENGTH - 1 - i][c + i] for i in range(param.WINDOW_LENGTH)]
				score += Board.evaluate_window(window, piece)

		self.score = score

	@staticmethod
	def evaluate_window(window, piece):
		score = 0
		# Switch scoring based on turn
		opp_piece = param.PLAYER_PIECE
		if piece == param.PLAYER_PIECE:
			opp_piece = param.BOT_PIECE

		# Prioritise a winning move
		# Minimax makes this less important
		if window.count(piece) == param.WINDOW_LENGTH:
			score += 100
		# Make connecting param.WINDOW_LENGTH - 1 second priority
		elif param.WINDOW_LENGTH > 2 and window.count(piece) == param.WINDOW_LENGTH - 1 and window.count(param.EMPTY) == 1:
			score += 5
		# Make connecting param.WINDOW_LENGTH - 2 third priority
		elif param.WINDOW_LENGTH > 3 and window.count(piece) == param.WINDOW_LENGTH - 2  and window.count(param.EMPTY) == 2:
			score += 2
		# Prioritise blocking an opponent's winning move (but not over bot winning)
		# Minimax makes this less important
		if window.count(opp_piece) == param.WINDOW_LENGTH and window.count(param.EMPTY) == 1:
			score -= 50

		return score

	def compute_score(self, winner):
		moves_played = int(np.sum(self.board != 0))
		max_moves = self.board.shape[0] * self.board.shape[1]
		if winner == param.BOT_PIECE:
			score = moves_played
		else:
			score = max_moves * 2 - moves_played

		self.score = score * 10
	
	def print_final_score(self, winner):
		self.compute_score(winner)
		print(f"Final score for your game: {self.score}")
