import sqlite3

conn = sqlite3.connect('test.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute('''CREATE TABLE games (gameId text, state text, turn int)''')
