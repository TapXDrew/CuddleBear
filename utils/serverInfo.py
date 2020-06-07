import json
import os
import sqlite3
import time

DATABASE = os.getcwd()+'/databases/serverInfo.db'
TABLE = 'Users'


class Server:
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx

        self.config = json.load(open(os.getcwd() + '/config/config.json'))

        self.conn = None

        try:
            self.conn = sqlite3.connect(DATABASE)
        except sqlite3.Error as e:
            print(e)
        self.cursor = self.conn.cursor()

        self._create_table()
        self._get_server_info()

    def close(self):
        self.conn.close()
        del self

    def _create_table(self):
        query = f"""CREATE TABLE IF NOT EXISTS {TABLE} (id BIGINT PRIMARY KEY, prefix TEXT, commands TEXT)"""
        self.cursor.execute(query)
        self.conn.commit()

    def _create_server(self):
        try:
            query = f"""INSERT INTO {TABLE} VALUES (?, ?, ?)"""
            self.cursor.execute(query, (self.ctx.guild.id, self.config['Bot']['Default_Prefix'], '{}'))
            self.conn.commit()
        except sqlite3.Error:
            pass

    def _get_server_info(self):
        query = f"SELECT * FROM {TABLE} WHERE id = ?"
        self.cursor.execute(query, (self.ctx.guild.id,))
        info = self.cursor.fetchall()
        if info:
            self.id = info[0][0]
            self.prefix = info[0][1]
            self.commands = info[0][2]
            while isinstance(self.commands, str):
                self.commands = eval(self.commands)
        else:
            self._create_server()
            self._get_server_info()

    def update_value(self, column, value):
        query = f"UPDATE {TABLE} SET {column} = ? WHERE id = ?"
        self.cursor.execute(query, (value, self.ctx.guild.id))
        self.conn.commit()
        self._get_server_info()

    def save_customCommand(self, command, response):
        self.commands[command.lower()] = response
        query = f"UPDATE {TABLE} SET commands = ? WHERE id = ?"
        self.cursor.execute(query, (f'{self.commands}', self.ctx.guild.id))
        self.conn.commit()
        self._get_server_info()

    def del_customCommand(self, command):
        del self.commands[command.lower()]
        query = f"UPDATE {TABLE} SET commands = ? WHERE id = ?"
        self.cursor.execute(query, (f'{self.commands}', self.ctx.guild.id))
        self.conn.commit()
        self._get_server_info()

