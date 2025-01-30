from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Game state
board = ["", "", "", "", "", "", "", "", ""]
players = {"X": {"name": "", "score": 0}, "O": {"name": "", "score": 0}}
current_player = "X"  # Start with Player X
connected_players = 0
player_sids = {}  # Track player sockets

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    global connected_players
    if connected_players < 2:  # Allow only 2 players
        connected_players += 1
        player_sids[request.sid] = {"role": "X" if connected_players == 1 else "O"}  # Assign role
        emit('assign_role', {"role": player_sids[request.sid]["role"]})
    else:
        emit('game_full', {'message': 'The game is full. Please try again later.'})

@socketio.on('set_name')
def handle_set_name(data):
    player_role = player_sids[request.sid]["role"]
    players[player_role]["name"] = data["name"]
    emit('update_player_info', {"players": players}, broadcast=True)
    if connected_players == 2:
        emit('start_game', {"current_player": current_player}, broadcast=True)

@socketio.on('move')
def handle_move(data):
    global current_player
    player_role = player_sids.get(request.sid, {}).get("role")
    if player_role is None:
        emit('invalid_move', {'message': 'You are not a player in this game.'})
        return

    if player_role != current_player:
        emit('invalid_move', {'message': 'It is not your turn.'})
        return

    index = int(data['index'])  # Convert index to an integer
    if board[index] == "":
        board[index] = current_player
        emit('update_board', {'board': board}, broadcast=True)
        if check_winner(current_player):
            players[current_player]["score"] += 1  # Increment score for the winner
            emit('update_player_info', {"players": players}, broadcast=True)  # Emit updated scores
            emit('game_over', {'winner': current_player, "players": players}, broadcast=True)
            reset_game()
        elif "" not in board:
            emit('game_over', {'winner': 'draw', "players": players}, broadcast=True)
            reset_game()
        else:
            current_player = "O" if current_player == "X" else "X"  # Switch turns
            emit('switch_turn', {"current_player": current_player}, broadcast=True)

def check_winner(player):
    win_conditions = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]              # Diagonals
    ]
    for condition in win_conditions:
        if board[condition[0]] == board[condition[1]] == board[condition[2]] == player:
            return True
    return False

def reset_game():
    global board, current_player
    board = ["", "", "", "", "", "", "", "", ""]
    current_player = "X"
    emit('reset_game', broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
