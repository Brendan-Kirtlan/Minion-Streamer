import socket
import threading

class TwitchChatBot:
    def __init__(self, channel, nickname, token):
        self.channel = channel
        self.nickname = nickname
        self.token = token
        self.server = "irc.twitch.tv"
        self.port = 6667
        self.socket = socket.socket()
        self.stop_event = threading.Event()
        self.started = False
        self.chat_history = []

    def connect(self):
        self.socket.connect((self.server, self.port))
        self.socket.send(f"PASS {self.token}\r\n".encode("utf-8"))
        self.socket.send(f"NICK {self.nickname}\r\n".encode("utf-8"))
        self.socket.send(f"JOIN #{self.channel}\r\n".encode("utf-8"))

    def receive_messages(self):
        while not self.stop_event.is_set():
            response = self.socket.recv(1024).decode("utf-8")
            if "PING" in response:
                self.socket.send("PONG\r\n".encode("utf-8"))
            elif "PRIVMSG" in response:
                username = response.split('!')[0][1:]
                message = response.split('PRIVMSG #')[1].split(' :')[1]
                print(f"{username}: {message}")
                self.chat_history.append((username, message))

    def stop(self):
        self.stop_event.set()
        self.socket.close()

    def run(self):
        self.connect()
        self.started = True  # Set the flag to indicate that the bot has been started
        threading.Thread(target=self.receive_messages).start()