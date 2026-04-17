from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO, emit
import os
import socket


app = Flask(__name__)
app.config['SECRET_KEY'] = 'segredo_muito_secreto'
socketio = SocketIO(app, cors_allowed_origins="*")

# Estado do Jogo (Memória volátil)
game_state = {
    'buzzer_locked': True,  # Botões começam travados
    'winner': None,         # Quem apertou primeiro
    'scores': {}            # Placar { 'Nome': 0 }
}

def obter_ip_local():
    """Descobre o IP do computador na rede Wi-Fi"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Tenta conectar em um IP qualquer da internet para forçar o sistema a revelar o IP local
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# Adicione este evento no app.py
@socketio.on('toggle_qr_server')
def handle_toggle_qr(data):
    # Simplesmente repassa o estado (true ou false) para todas as telas
    emit('update_qr_visibility', data, broadcast=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/host')
def host():
    return render_template('host.html')

@app.route('/player')
def player():
    return render_template('player.html')

@app.route('/display')
def display():
    # Pega o IP real da sua rede
    ip = obter_ip_local()
    url_do_jogo = f"http://{ip}:5000/"
    
    # Envia essa URL para o HTML do telão
    return render_template('display.html', url_jogo=url_do_jogo)

@app.route('/soundboard')
def soundboard():
    # Caminho até a pasta static/sounds
    sounds_dir = os.path.join(app.root_path, 'static', 'sounds')
    
    # Se a pasta não existir, o Python cria pra você não tomar erro
    if not os.path.exists(sounds_dir):
        os.makedirs(sounds_dir)
        
    # Lê a pasta e pega só os arquivos que terminam em .mp3
    sound_files = [f for f in os.listdir(sounds_dir) if f.endswith('.mp3')]
    
    # Envia a lista de arquivos para o HTML
    return render_template('soundboard.html', sounds=sound_files)

# --- Eventos de Socket (Tempo Real) ---

@socketio.on('join_game')
def handle_join(data):
    username = data['username']
    role = data['role']
    
    if role == 'player':
        if username not in game_state['scores']:
            game_state['scores'][username] = 0
    
    # Envia o estado atual para quem acabou de entrar
    emit('update_scores', game_state['scores'], broadcast=True)

@socketio.on('buzz')
def handle_buzz(data):
    # Se o buzzer estiver liberado e ainda não houver vencedor
    if not game_state['buzzer_locked'] and game_state['winner'] is None:
        game_state['buzzer_locked'] = True
        game_state['winner'] = data['username']
        
        # Avisa todo mundo quem ganhou
        emit('player_won', {'winner': data['username']}, broadcast=True)
        # Toca som de acerto no Host (opcional via front)
        emit('play_sound', {'sound': 'correct'}, broadcast=True)

@socketio.on('host_action')
def handle_host_action(data):
    action = data['action']
    
    if action == 'unlock':
        game_state['buzzer_locked'] = False
        game_state['winner'] = None
        emit('game_status', {'status': 'unlocked'}, broadcast=True)
    
    elif action == 'reset':
        game_state['buzzer_locked'] = True
        game_state['winner'] = None
        emit('game_status', {'status': 'reset'}, broadcast=True)

@socketio.on('update_score')
def handle_score_update(data):
    user = data['username']
    points = data['points'] # +1 ou -1
    
    if user in game_state['scores']:
        game_state['scores'][user] += points
        emit('update_scores', game_state['scores'], broadcast=True)
        
@socketio.on('set_score')
def handle_set_score(data):
    user = data['username']
    val = data['score']
    
    if user in game_state['scores']:
        game_state['scores'][user] = val # Aqui substitui o valor em vez de somar
        emit('update_scores', game_state['scores'], broadcast=True)

# Rodar o servidor acessível na rede local
if __name__ == '__main__':
    # host='0.0.0.0' permite que outros dispositivos na rede acessem
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    


# Atualize a parte final do código para imprimir o IP no terminal e facilitar a sua vida!
if __name__ == '__main__':
    ip_atual = obter_ip_local()
    print("="*50)
    print(f"🚀 SISTEMA INICIADO!")
    print(f"👉 Painel do Host: http://localhost:5000/host")
    print(f"👉 Telão: http://localhost:5000/display")
    print(f"📱 Convidados acessam: http://{ip_atual}:5000/")
    print("="*50)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)