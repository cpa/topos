from math import sqrt

import string
from flask import Flask, render_template, send_from_directory, redirect
from flask_socketio import SocketIO, send, emit, join_room
import sqlite3
from random import random, choice
import json

app = Flask(__name__)

if app.debug:
    app.config.from_pyfile('dev.cfg')
else:
    app.config.from_pyfile('prod.cfg')

socketio = SocketIO(app, cors_allowed_origins='*')

class GameState:
    _colorIndex = 0

    def __init__(self, colors=None, particles=None, currentColor=None):
        if colors:
            self.colors = colors
        else:
            # self.colors = ['#004c6d','#346888','#5886a5','#7aa6c2','#9dc6e0','#c1e7ff']
            # self.colors = ['#eca400', '#eaf8bf', '#006992', '#27476e', '#88958d']
            # self.colors = ["#fff2fc","#fed6f4","#fdbbed","#fa86df","#f557d3","#ed30ca","#e413c3","#d700bf","#c700bb","#b300b3","#94009e","#770087"]
            self.colors = ["#dffed6", "#c9fdbb", "#9cfa86", "#70f557", "#46ed30", "#1ee413", "#00d707", "#00c71b", "#00b32e", "#009e3b", "#008741"]
        if particles:
            self.particles = particles
        else:
            # self.particles = [(random(), random(), choice(self.colors)) for x in range(40)]
            self.particles = [(random(), random(), "#eeeeee") for x in range(100)]
            self.particles = [(x, y, c if (sqrt((x-0.5)**2 + (y-0.5)**2)) > 0.15 else choice(self.colors)) for (x,y,c) in self.particles]

        if currentColor:
            self.currentColor = currentColor
        else:
            self.currentColor = choice(self.colors)


    def nextColor(self):
        # self._colorIndex += 1
        # self._colorIndex %= len(self.colors)
        # self.currentColor = self.colors[self._colorIndex]
        self.currentColor = choice(self.colors)
        

    def asdict(self):
        return {'colors': self.colors, 'particles': self.particles, 'currentColor': self.currentColor}


    def json(self):
        j = {'colors': self.colors,
             'particles': self.particles,
             'currentColor': self.currentColor}
        return json.dumps(j)


@socketio.on('mousemove')
def handle_move(data):
    gameId = data['gameId']
    with sqlite3.connect("test.db") as conn:
        # TODO: vérifier que celui qui envoie le message est bien dans la room
        cur = conn.cursor()
        cur.execute("SELECT state FROM games WHERE gameId=(?)", (gameId,))
        gameState = GameState(**json.loads(cur.fetchone()[0]))
        gameState.particles.append(data['data'])
        
        emit('refresh', json.loads(gameState.json()), room=gameId, include_self=True)


@socketio.on('click')
def handle_message(data):
    gameId = data['gameId']
    app.logger.debug('click: %s' % data)
    with sqlite3.connect("test.db") as conn:
        # TODO: vérifier que celui qui envoie le message est bien dans la room
        cur = conn.cursor()
        cur.execute("SELECT state FROM games WHERE gameId=(?)", (gameId,))
        gameState = GameState(**json.loads(cur.fetchone()[0]))
        gameState.particles.append(data['data'])
        gameState.nextColor()
        
        emit('refresh', json.loads(gameState.json()), room=gameId, include_self=True)

        cur.execute("UPDATE games SET state=(?) WHERE gameId=(?)", (gameState.json(), gameId))
        conn.commit()

@socketio.on('hello')
def handle_hello(data):
    with sqlite3.connect("test.db") as conn:
        gameId = data['gameId']
        join_room(gameId)
        app.logger.debug("Moving %s to %s" % (data['playerId'], gameId))
        cur = conn.cursor()
        cur.execute("SELECT state FROM games WHERE gameId=(?)", (gameId,))
        gameState = GameState(**json.loads(cur.fetchone()[0]))
        app.logger.debug('hello %s' % gameState.json())
        emit('refresh', gameState.asdict(), room=gameId)
        
@app.route('/<gameId>')
def getGame(gameId):
    with sqlite3.connect("test.db") as conn:
      cur = conn.cursor()
      cur.execute("SELECT * FROM games WHERE gameId=(?)", (gameId,)) # TODO : vérifier l'unicité de l'insertion (pas besoin vu la logique je pense)
      if cur.fetchone():
          app.logger.debug("found %s" % gameId)
      else:
          cur.execute("INSERT INTO games VALUES (?,?,?)", (gameId, 0, 0))
          conn.commit()
          state = GameState()
          cur.execute("UPDATE games SET state=(?) WHERE gameId=(?)", (state.json(), gameId))
          conn.commit()
          app.logger.debug("created %s" % gameId)
    return send_from_directory('static', 'index.html')

@app.route('/app.js')
def app_js():
    return render_template('app.js', server_name=app.config['SERVER_NAME'])

@app.route('/')
def index():
    letters = string.ascii_lowercase
    gameId = ''.join(choice(letters) for _ in range(8))
    return redirect(gameId)

if __name__ == '__main__':
    if app.debug:
        app.logger.basicConfig(level=app.logger.DEBUG)

    socketio.run(app)
