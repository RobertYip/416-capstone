import socket
import threading
import json

# message commands
VIEW = "v"
NEXT_STAGE = "next"
MESSAGE_LOG = "M"

# stage:
STAGE0 = 0 # discovery phase
STAGE1 = 1 # pre-leader election
STAGE2 = 2 # leader election
STAGE3 = 3 # message exchange

# constants
CODE_LEN = 4
PORT_LEN = 4
GET_SESSION_DATA = '0001'
NODE_INTRODUCTION = '0002'
UPDATE_STAGE = '0003'
MESSAGE = '0004'
LOG_UPDATE = '0005'
OK = '00OK'
NO = '00NO'


class Play:
    def __init__(self, port):
        self.id = None
        self.name = None
        self.port = port
        self.initial_connection = None
        self.leader = None
        self.stage = 0
        self.nodes_list = []
        self.socket_connections = []
        self.socket_leader = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lock = threading.Lock()
        self.message_log = []


    def handle_client(self, client_socket, name=None):
        """
        After connection is establishes, handles messages received
        """
        try:
            while True:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break  # Connection closed by the client

                if message[:CODE_LEN] == MESSAGE:
                    # if leader
                    if self.leader == self.port:
                        self.message_log.append((name, message[CODE_LEN:]))
                        message_log_str = json.dumps(self.message_log)
                        self.broadcast_message(LOG_UPDATE+message_log_str)
                    else:
                    # if not leader, relay to leader
                        self.relay_message_to_leader(message)

                elif message[:CODE_LEN] == LOG_UPDATE:
                    # update message log
                    json_obj = json.loads(message[CODE_LEN:])

                    self.fast_forward_message_log(json_obj)

                elif message[:CODE_LEN] == GET_SESSION_DATA:
                    # provide session data to requesting node
                    session_data_str = json.dumps(self.create_session_data())
                    client_socket.send(session_data_str.encode('utf-8'))

                elif message[:CODE_LEN] == NODE_INTRODUCTION:
                    # Get node info and append it to node_list
                    node_obj = json.loads(message[CODE_LEN:])
                    self.nodes_list.append(node_obj)
                    client_socket.send(OK.encode('utf-8'))
                    print(f"Successfully added node {node_obj['id']} to nodes_list")

                elif message[:CODE_LEN] == UPDATE_STAGE:
                    # Update stage
                    self.stage = int(message[CODE_LEN:])
                    print(f"Stage updated to {self.stage}")

                # else:
                #     print(f"{name}: {message}")

        except Exception as e:
            print(f"Error handling client: {e}")
            print(f"Closing connection with {name}")

        finally:
            # Remove the client socket from the list
            with self.lock:
                self.socket_connections.remove(client_socket)
            client_socket.close()


    def accept_connections(self):
        while True:
            client_socket, client_address = self.socket.accept()
            # Exchange names
            name = client_socket.recv(1024).decode('utf-8')
            client_socket.send(self.name.encode('utf-8'))
            print(f"Accepted connection from {name}")

            # Add the new client to the list of connections
            with self.lock:
                self.socket_connections.append(client_socket)

            # Start a new thread to handle the client
            threading.Thread(target=self.handle_client, args=(client_socket, name)).start()

    """
    HELPERS
    """
    def broadcast_message(self, message):
        """
        Broadcasts a message to all socket connections
        """
        for socket in self.socket_connections:
            socket.send(message.encode('utf-8'))


    def relay_message_to_leader(self, message):
        """
        Leader is in position 0, relay message to leader
        """
        leader_socket = self.socket_connections[0]
        leader_socket.send(message.encode('utf-8'))


    def fast_forward_message_log(self, new_message_log):    
        """
        Fast forward the message log
        This part is simplified and not optimized, but it's for the idea
        """
        offset = len(new_message_log) - len(self.message_log)
        for i in range(len(new_message_log)-offset, len(new_message_log)):
            self.message_log.append(new_message_log[i]) 

    def create_session_data(self):
        """
        Creates a session object to update other nodes if requested
        Returns: JSON object
        """
        session_obj = {
            'leader': self.leader,
            'stage': self.stage,
            'nodes_list': self.nodes_list
        }
        return session_obj
    

    def get_session_data(self, client_socket):
        """
        Fetches the session data to find list of nodes and leader
        - stage
        - leader
        - all nodes list
        Updates self.nodes_list
        """
        client_socket.send(GET_SESSION_DATA.encode('utf-8'))
        message = client_socket.recv(1024).decode('utf-8')

        try:
            session_data_json = json.loads(message)
            self.leader = session_data_json['leader']
            self.stage = session_data_json['stage']
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


    def connect_to_all_nodes(self):
        """
        Connects to all nodes in the nodes_list
        Also sets the leader socket
        """
        for node in self.nodes_list:
            if node['port'] != self.port and node['port'] != self.initial_connection:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect(('localhost', node['port']))
                client_socket.send(self.name.encode('utf-8'))
                name = client_socket.recv(1024).decode('utf-8')

                threading.Thread(target=self.handle_client, args=(client_socket, name)).start()
                self.socket_connections.append(client_socket)
            

    def print_view(self):
        """
        Prints the status on the network
        """
        print("connections: " + str(self.socket_connections))
        print("len_connections: " + str(len(self.socket_connections)))
        print("nodes_list: " + str(self.nodes_list))
        print("id: " + self.id)
        print("name: " + self.name)
        print("port: " + str(self.port))
        print("leader: " + str(self.leader))
        print("stage: " + str(self.stage))
    
    def print_message_log(self):
        """
        Prints the message log
        """
        print("Full Message Log History")
        for message in self.message_log:
            print(message[0] + ": " + message[1])
        print("End of Log\n")
        

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

        self.initial_connection = int(input("Enter the node you want to connect to [0 if you are host]: "))
        if self.initial_connection == 0 or self.initial_connection == self.port:
            # Identify self as host
            self.leader = self.port
            self.nodes_list = [self.share_node_data()]
        else:
            # Initial connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('localhost', self.initial_connection))

            # Exchange names
            client_socket.send(self.name.encode('utf-8'))   
            name = client_socket.recv(1024).decode('utf-8')
            self.socket_connections.append(client_socket)

            # Introduce self and check if join successful
            self_data_str = json.dumps(self.share_node_data())

            client_socket.send((NODE_INTRODUCTION+self_data_str).encode('utf-8'))
            message = client_socket.recv(1024).decode('utf-8')
            
            self.get_session_data(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket, name)).start()

            self.connect_to_all_nodes()
         
        return True


    def update_all_nodes_stage(self, stage):
        """
        Updates non-leader nodes stage
        """
        self.broadcast_message(UPDATE_STAGE+str(stage))


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
        
        while self.stage==STAGE0:
            command = input()
            if command == VIEW:
                self.print_view()
            elif command == NEXT_STAGE and self.leader == self.port:
                self.stage = STAGE3 # assume host remains leader
                self.update_all_nodes_stage(self.stage)               

        while self.stage==STAGE3:
            command = input()
            if command == VIEW:
                self.print_view()
            elif command == MESSAGE_LOG:
                self.print_message_log()
            else:
                if self.port == self.leader:
                    self.message_log.append((self.name, command))
                    self.broadcast_message((LOG_UPDATE+json.dumps(self.message_log)))
                else:
                    self.broadcast_message(MESSAGE+command)


if __name__ == "__main__":
    port = int(input("Enter your node's port (8001-8005): "))
    play = Play(port)
    play.start()
