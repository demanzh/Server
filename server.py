"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports

class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data:bytes):
        decoded = data.decode()

        print(decoded)
        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                for client in self.server.clients:
                    if client.login == login:
                        self.transport.write(f"Логин {login} занят, попробуйте другой".encode())
                        self.transport.close()
                        print(f"Попытка повторного подключения login - {login}")
                        return 
                self.login = login
                self.transport.write(f"Привет, {self.login}!\r\n".encode())
                if self.server.history:
                    self.send_history()
        else:
            self.send_message(decoded)

    def send_history(self):
        self.transport.write("--history--\r\n".encode()) # просто для красоты
        for message in self.server.history:
            encoded = (message + "\r\n").encode()
            self.transport.write(encoded)
        self.transport.write(">>> -----------\r\n".encode()) # просто для красоты

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        if len(self.server.history) < 10: # проверка на переполнение истории
            self.server.history.append(format_string)
        else:
            self.server.history.pop(0)
            self.server.history.append(format_string)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установленно")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")

class Server:
    clients: list
    history: list


    def __init__(self):
        self.clients = []
        self.history = []


    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )
        print("server start...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")

