import socket
import threading
import json

# states:
STAGE0 = 0 # discovery phase
STAGE1 = 1 # pre-leader election
STAGE2 = 2 # leader election
STAGE3 = 3 # message exchange

# constants
CODE_LEN = 4
PORT_LEN = 4

# commands:
GET_SESSION_DATA = '0001'
NODE_INTRODUCTION = '0002'

class Node:
    def __init__(self, port):
        self.name = None
        self.port = port
        self.leader = None
        self.state = 0
        self.nodes_list = []
        self.socket_connections = []
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', self.port))
        self.server_socket.listen()

    def receive_messages(self):
        client_socket, client_address = self.server_socket.accept()
        name = None
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if message[:CODE_LEN] == GET_SESSION_DATA:
                session_data = self.create_session_data()
                client_socket.send(session_data.encode('utf-8'))
            elif message[:CODE_LEN] == NODE_INTRODUCTION:
                # Get id
                id = message[CODE_LEN:len(message)]
                self.nodes_list.append(id)

                # get name
                name = message[CODE_LEN:len(message)-PORT_LEN]

            else:
                print(f"Received message from {name}: {message}")
            


    def broadcast_message(self, message):
        for socket in self.socket_connections:
            socket.send(message.encode('utf-8'))

    """
    HELPERS
    """
    def create_session_data(self):
        """
        Creates a session object to update other nodes if requested
        Returns: String of JSON object
        """
        session_obj = {
            'leader': self.leader,
            'state': self.state,
            'nodes_list': self.nodes_list
        }
        return json.dumps(session_obj)
    
    def get_session_data(self, client_socket):
        """
        Fetches the session data to find list of nodes and leader
        - state
        - leader
        - all nodes list
        """
        client_socket.send(GET_SESSION_DATA.encode('utf-8'))
        message = client_socket.recv(1024).decode('utf-8')

        # Try decoding the string as JSON
        session_data_json=None
        try:
            session_data_json = json.loads(message)
            self.nodes_list = session_data_json['nodes_list']
            
            print("Successfully retrieved session data")
        except json.JSONDecodeError:
            print("Error decoding JSON object")

    """
    PROCEDURES
    """

    def init_join_procedures(self):
        """
        Executes the join procedures from the new node. 
        Fills in:
        - name
        - id
        - leader
        - nodes_list
        """
        self.name = str(input("Enter your name: "))
        self.id = self.name+str(self.port)

        self.leader = int(input("Enter the node you want to connect to [0 if you are host]: "))
        if self.leader != 0:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('localhost', self.leader))
            self.socket_connections.append(client_socket)

        # Get list of nodes in session
        self.get_session_data(client_socket)
        
        # Introduce self
        client_socket.send((NODE_INTRODUCTION+self.id).encode('utf-8'))

    def start(self):
        print(f"Node {self.port} is listening for incoming connections.")

        # Handle receiving messages from up to 3 nodes
        receive_thread1 = threading.Thread(target=self.receive_messages)
        receive_thread2 = threading.Thread(target=self.receive_messages)
        receive_thread1.start()
        receive_thread2.start()

        # Join procedures
        self.init_join_procedures()
        

        while self.state==STAGE0:
            command = input("Enter your command: ")
            if command == "view":
                print("connections: " + str(self.socket_connections))
                print("nodes_list: " + str(self.nodes_list))
                print("name: " + self.name)
                print("port: " + str(self.port))
            else:
                self.broadcast_message(command)

if __name__ == "__main__":
    port = int(input("Enter your node's port (8001-8005): "))
    node = Node(port)
    node.start()
