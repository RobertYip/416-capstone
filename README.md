# 416-capstone: Peer-to-Peer Messaging App with Strong Consistency
This is an implementation for my design on a **Peer-to-Peer messaging app with strong consistency**. The design can be found [here](https://github.students.cs.ubc.ca/CPSC416-2023W-T1/Capstone-Project-Designs/blob/main/ccea9b01434cd2660bd42421eb0df300.pdf).

## Commands
V - View node's, such as this node's port, name, connections, stage.  
M - View Message Log of chat, to the knowledge of this node. Available only in Stage 3.  
N - Advances stage. Can only be executed by leader.  


## How to use:
1. For each node you want to simulate, run `python3 main.py` in separate terminal windows.
2. It will ask for the following:
- **Enter your node's port (8001-8005):** Enter any value, suggest to use 8000~. Make sure each node uses a different port.
- **Enter your name:** Enter any name for the node
- **Enter the node to connect to:** Enter 0 or own port to be host, or the port number of the host.
3. Once some nodes have joined, host should type `N` to advance to messaging stage.
4. Nodes can start typing in their messages. Due to the implementation only available in CLI, the full message log can only be viewable by typing `M`.

## Overview of Design
4 Stages:
1. Discovery Phase - Nodes should join at this time
2. Pre-leader election phase - Confirms nodes are alive (automatic step)
3. Leader election phase - Use Paxos to randomly select leader. This is skipped in the implementation, host remains leader.
4. Message Exchange Phase - Normal messaging app behavior. Type `M` to view messsage log. New nodes can still join at this time.
