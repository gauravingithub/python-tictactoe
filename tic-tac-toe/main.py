from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Game state
games = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    if room not in games:
        games[room] = {
            'board': ['' for _ in range(9)],
            'current_turn': 'X',
            'players': []
        }
    if request.sid not in games[room]['players']:
        games[room]['players'].append(request.sid)
    emit('update', games[room], room=room)

@socketio.on('make_move')
def on_make_move(data):
    room = data['room']
    index = data['index']
    game = games[room]
    if game['board'][index] == '' and len(game['players']) == 2:
        game['board'][index] = game['current_turn']
        game['current_turn'] = 'O' if game['current_turn'] == 'X' else 'X'
        winner = check_winner(game['board'])
        emit('update', game, room=room)
        if winner:
            emit('game_over', {'winner': winner}, room=room)

def check_winner(board):
    win_conditions = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]              # Diagonals
    ]
    for condition in win_conditions:
        if board[condition[0]] == board[condition[1]] == board[condition[2]] and board[condition[0]] != '':
            return board[condition[0]]
    if '' not in board:
        return 'Draw'
    return None

if __name__ == '__main__':
    socketio.run(app, debug=True)
