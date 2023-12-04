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

# message key words:
OK = '00OK'
NO = '00NO'

# message commands
GET_SESSION_DATA = '0001'
NODE_INTRODUCTION = '0002'

"""
Interface info for reference (Python doesn't have interfaces)
    node_obj = {
        'id': self.id,
        'name': self.name,
        'port': self.port,
    }
"""

class Play:
    def __init__(self, port):
        self.id = None
        self.name = None
        self.port = port
        self.leader = None
        self.state = 0
        self.nodes_list = []
        self.socket_connections = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lock = threading.Lock()

    def handle_client(self, client_socket):
        try:
            name = None
            while True:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break  # Connection closed by the client

                if message[:CODE_LEN] == GET_SESSION_DATA:
                    # provide session data to requesting node
                    session_data_str = json.dumps(self.create_session_data())
                    client_socket.send(session_data_str.encode('utf-8'))
                elif message[:CODE_LEN] == NODE_INTRODUCTION:
                    # Get node info and append it to node_list
                    node_obj = json.loads(message[CODE_LEN:len(message)])
                    # check if node already exists in list
                    if any(node['id'] == node_obj['id'] for node in self.nodes_list):
                        client_socket.send(NO.encode('utf-8'))
                    else:
                        self.socket_connections.append(client_socket)
                        self.nodes_list.append(node_obj)
                        print(f"Successfully added node {node_obj['id']} to nodes_list")
                        client_socket.send(OK.encode('utf-8'))
                else:
                    input("PAUSE")
                    print(f"Received message from {name}: {message}")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            # Remove the client socket from the list
            with self.lock:
                self.socket_connections.remove(client_socket)
            client_socket.close()

    def accept_connections(self):
        while True:
            client_socket, client_address = self.socket.accept()
            print(f"Accepted connection from {client_address}")

            # Add the new client to the list of connections
            with self.lock:
                self.socket_connections.append(client_socket)

            # Start a new thread to handle the client
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    """
    HELPERS
    """
    def broadcast_message(self, message):
        for socket in self.socket_connections:
            socket.send(message.encode('utf-8'))

    def create_session_data(self):
        """
        Creates a session object to update other nodes if requested
        Returns: JSON object
        """
        session_obj = {
            'leader': self.leader,
            'state': self.state,
            'nodes_list': self.nodes_list
        }
        return session_obj
    
    def get_session_data(self, client_socket):
        """
        Fetches the session data to find list of nodes and leader
        - state
        - leader
        - all nodes list
        Updates self.nodes_list
        """
        client_socket.send(GET_SESSION_DATA.encode('utf-8'))
        message = client_socket.recv(1024).decode('utf-8')

        # Try decoding the string as JSON
        session_data_json=None
        try:
            session_data_json = json.loads(message)
            self.leader = session_data_json['leader']
            self.state = session_data_json['state']
            self.nodes_list = session_data_json['nodes_list']
            
            print("Successfully retrieved session data")
        except json.JSONDecodeError:
            print("Error decoding JSON object")

    def share_node_data(self):
        """
        Provides all of the self node's data
        Returns: JSON object
        """
        node_obj = {
            'id': self.id,
            'name': self.name,
            'port': self.port,
        }
        return node_obj


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
        Returns if joining network was successful
        """
        self.name = str(input("Enter your name: "))
        self.id = self.name+str(self.port)

        self.leader = int(input("Enter the node you want to connect to [0 if you are host]: "))
        if self.leader == 0 or self.leader == self.port:
            # Identify self as host
            self.leader = self.port
            self.nodes_list = [self.share_node_data()]
        else:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('localhost', self.leader))
            
            # Introduce self and check if join successful
            self_data_str = json.dumps(self.share_node_data())

            client_socket.send((NODE_INTRODUCTION+self_data_str).encode('utf-8'))
            message = client_socket.recv(1024).decode('utf-8')

            if message == OK:
                print("Successfully joined network")
            else:
                print("Error joining network")
                return False

            # Get list of nodes in session
            self.get_session_data(client_socket)
         
        return True

    def start(self):
        self.socket.bind(('localhost', self.port))
        self.socket.listen()
        print(f"Node {self.port} is listening for incoming connections.")

        # Start a thread to handle incoming connections
        threading.Thread(target=self.accept_connections).start()

        # Join procedures
        is_joined = False
        while not is_joined:
            is_joined = self.init_join_procedures()
        
        while self.state==STAGE0:
            command = input("Enter your command: ")
            if command == "view":
                print("connections: " + str(self.socket_connections))
                print("len_connections: " + str(len(self.socket_connections)))
                print("nodes_list: " + str(self.nodes_list))
                print("id: " + self.id)
                print("name: " + self.name)
                print("port: " + str(self.port))
                print("leader: " + str(self.leader))
            else:
                self.broadcast_message(command)

if __name__ == "__main__":
    port = int(input("Enter your node's port (8001-8005): "))
    play = Play(port)
    play.start()
