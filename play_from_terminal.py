from main import *

if __name__ == "__main__":
    lookup_table_loc = 'lookup_table.json'

    if os.path.isfile(lookup_table_loc):
        with open(lookup_table_loc, 'r') as file:
            lookup_table = json.load(file)
            print(f"Loaded lookup table {lookup_table_loc}.")
    else:
        print(f"The file '{lookup_table_loc}' does not exist.")
        lookup_table = dict()


    board = Board()
    game_over = False
    
    while True:
        try:
            turn = int(input("Who starts? (0: Player, 1: Bot): "))
            if turn in [0, 1]:
                break
            else:
                raise ValueError
        except ValueError:
            print("Please enter a valid input")
    play_alg = {
        'easy': easy_play,
        'medium': medium_play,
        'hard': hard_play,
        'impossible': lambda board: optimal_play(board, lookup_table),
    }
    mode = 'impossible'

    winner = 0
    board.pretty_print_board()
    while not game_over:
        if turn == 0:
            valid_move = False
            while not valid_move:
                try:
                    col = int(input("Player 1 Make your Selection (0-6): "))
                    if 0 <= col < param.COLUMN_COUNT and board.is_valid_location(col):
                        valid_move = True
                    else:
                        print("Invalid column. Try again.")
                except ValueError:
                    print("Please enter a valid integer between 0 and 6.")
            game_over = play_turn(board, col, param.PLAYER_PIECE)
            board.pretty_print_board()
            if game_over:
                winner = param.PLAYER_PIECE
        else:
            col = play_alg[mode](board.board_array)
            game_over = play_turn(board, col, param.BOT_PIECE)
            if game_over:
                winner = param.BOT_PIECE
            board.pretty_print_board()

        if len(board.get_valid_locations()) == 0 and not game_over:
            board.pretty_print_board()
            print("Game is a draw!")
            game_over = True
            winner = param.PLAYER_PIECE
        turn ^= 1  # Switch turns

    board.print_final_score(winner)
