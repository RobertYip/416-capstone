import socket
import threading
import json

# commands:
GET_ALL_NODES_LIST = '0001'

class Node:
    def __init__(self, port):
        self.port = port
        self.leader = None
        self.allNodesList = "[node1, node2, node3]"
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', self.port))
        self.server_socket.listen()

    def receive_messages(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            message = client_socket.recv(1024).decode('utf-8')
            print(f"Received message from {client_address}: {message}")
            if message == GET_ALL_NODES_LIST:
                session_data = self.create_session_data()
                client_socket.send(session_data.encode('utf-8'))
            client_socket.close()

    def broadcast_message(self, message):
        for node_port in [8001, 8002]:
            if node_port != self.port:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect(('localhost', node_port))
                client_socket.send(message.encode('utf-8'))
                message = client_socket.recv(1024).decode('utf-8')
                print(message)
                client_socket.close()

    def get_session_data(self):
        """
        Fetches the session data to find list of nodes and leader
        """
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', self.leader))
        client_socket.send(GET_ALL_NODES_LIST.encode('utf-8'))
        message = client_socket.recv(1024).decode('utf-8')

        # Try decoding the string as JSON
        session_data_json=None
        try:
            session_data_json = json.loads(message)
            # self.allNodesList = session_data['allNodesList']
        except json.JSONDecodeError:
            print("Error decoding JSON object")

        print(session_data_json['allNodesList'])


    def create_session_data(self):
        """
        Creates a session object to update other nodes if requested
        Returns: String of JSON object
        """
        session_obj = {
            # 'leader': self.leader,
            'allNodesList': self.allNodesList
        }
        print(type(json.dumps(session_obj)))
        return json.dumps(session_obj)


    def start(self):
        print(f"Node {self.port} is listening for incoming connections.")

        # Start a thread to handle incoming messages
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.start()

        self.leader = int(input("Enter the node you want to connect to: "))
        
        # Get list of nodes in session
        self.get_session_data()

        while True:
            message = input("Enter your message: ")
            self.broadcast_message(message)

if __name__ == "__main__":
    port = int(input("Enter your node's port (8001-8005): "))
    node = Node(port)
    node.start()
