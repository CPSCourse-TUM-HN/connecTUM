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


    board = create_board()
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
    pretty_print_board(board)
    while not game_over:
        if turn == 0:
            valid_move = False
            while not valid_move:
                try:
                    col = int(input("Player 1 Make your Selection (0-6): "))
                    if 0 <= col < COLUMN_COUNT and is_valid_location(board, col):
                        valid_move = True
                    else:
                        print("Invalid column. Try again.")
                except ValueError:
                    print("Please enter a valid integer between 0 and 6.")
            game_over = play_turn(board, col, PLAYER_PIECE)
            pretty_print_board(board)
            if game_over:
                winner = PLAYER_PIECE
        else:
            col = play_alg[mode](board)
            game_over = play_turn(board, col, BOT_PIECE)
            if game_over:
                winner = BOT_PIECE
            pretty_print_board(board)
        if len(get_valid_locations(board)) == 0 and not game_over:
            pretty_print_board(board)
            print("Game is a draw!")
            game_over = True
            winner = PLAYER_PIECE
        turn ^= 1  # Switch turns
    print_final_score(board, winner)
