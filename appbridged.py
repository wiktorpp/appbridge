# appbridged 

# Ports:
# 54764 - LAN detection
# 54765 - NFS connection
# 54766 - 54786 - for use by apps
# For WAN:
# random - inbound hole punching, SSH bridge
# random - outbound hole punching

# 1. Try to hole punch from both mashines
# 2. If successful, establish SSH bridge both ways

# Remote mounts:
# /home/<username>/ -> /media/<username>/<remote pc name>
# etc

# Example usage
# Generic message
# Socket:
# {
#     "app_name": "com.example.app",
#     "action": "register_app",
#     "data": {
#         "key": "value"
#     }
# }
# matrix:
# {
#     "device": "device_name",
#     "data": {
#         "app_name": "com.example.app",
#         "action": "register_app",
#         "data": {
#             "key": "value"
#         }
#     }
# }

# Hole punching:
# matrix:
# {
#     "device": "device_name",
#     "action": "hole_punch",
#     "public_ip": "123.456.789.012",
#     "inbound_port": 54764,
#     "outbound_port": 54765
# }

# Assingning a port:
# socket:
# {
#     "app_name": "com.example.app",
#     "action": "assign_port",
#     "port_allocation": {
#         "protocol": "RDP",
#         "purpose": "",
# }
# response:
# {
#     "status": "success",
#     "port": 54766,
# }
# matrix:
# {
#     "device": "device_name",
#     "app_name": "com.example.app",
#     "action": "port_allocation",
#     "port": 54766,
#     "protocol": "RDP",
#     "purpose": ""
# }

# LAN detection:
# LAN beacon:
# {
#     "device": "salted_hash",
#     "account": "salted_hash",
# }

# device registration (avoid name collisions):
# matrix:
# {
#     "action": "register_device",
#     "device": "device_name",
#     "account": "account_name",
#     "salt": "salt",
# }

# remote mount:
# to be decided

import os
import socket
import threading
import json
from matrix_client.client import MatrixClient

SOCKET_PATH = "/tmp/appbridged.sock"

class AppRegistry:
    """Class to manage registered apps and their sockets."""
    def __init__(self):
        self._registered_apps = {}

    def __contains__(self, app_name):
        return app_name in self._registered_apps

    def __getitem__(self, app_name):
        return self._registered_apps[app_name]

    def __setitem__(self, app_name, client_socket):
        if app_name in self._registered_apps:
            raise KeyError(f"App '{app_name}' is already registered.")
        self._registered_apps[app_name] = client_socket
        print(f"App '{app_name}' registered successfully.")

    def __delitem__(self, app_name):
        if app_name in self._registered_apps:
            client_socket = self._registered_apps[app_name]
            client_socket.close()
            del self._registered_apps[app_name]
            print(f"App '{app_name}' unregistered successfully.")
        else:
            raise KeyError(f"App '{app_name}' is not registered.")

    def __iter__(self):
        return iter(self._registered_apps)

    def __len__(self):
        return len(self._registered_apps)

# Initialize the AppRegistry
registered_apps = AppRegistry()

def send_json_remote(client, room_id, json_data):
    """Send an arbitrary JSON message to a Matrix room."""
    if "app_name" not in json_data or not isinstance(json_data["app_name"], str):
        raise ValueError("Every message must include 'app_name' in reverse domain format.")
    room = client.join_room(room_id)
    data = {"type": "arbitrary_json", "content": json_data}
    room.send_event("m.appbridge", data)
    print(f"Arbitrary JSON message sent: {json_data}")

def forward_data_to_local_app(app_name, data):
    """Forward data received from the Matrix room to the registered local app."""
    try:
        client_socket = registered_apps[app_name]
        client_socket.send(json.dumps(data).encode('utf-8'))
        print(f"Data forwarded to app '{app_name}': {data}")
    except KeyError:
        print(f"App '{app_name}' is not registered.")
    except Exception as e:
        print(f"Error forwarding data to app '{app_name}': {e}")
        del registered_apps[app_name]

def assign_port_to_remote(client, room_id, app_name, port, protocol, purpose):
    """Send a message to inform a remote app of an assigned port."""
    json_data = {
        "action": "port_allocation",
        "app_name": app_name,
        "port": port,
        "protocol": protocol,
        "purpose": purpose
    }
    send_json_remote(client, room_id, json_data)
    print(f"Assigned port message sent to remote app: {json_data}")

def assign_port_to_local(app_name, port, protocol, purpose):
    """Send a message to inform a local app of an assigned port."""
    try:
        client_socket = registered_apps[app_name]
        json_data = {
            "action": "port_allocation",
            "app_name": app_name,
            "port": port,
            "protocol": protocol,
            "purpose": purpose
        }
        client_socket.send(json.dumps(json_data).encode('utf-8'))
        print(f"Assigned port message sent to local app '{app_name}': {json_data}")
    except KeyError:
        print(f"App '{app_name}' is not registered.")
    except Exception as e:
        print(f"Error sending assigned port message to local app '{app_name}': {e}")
        del registered_apps[app_name]

def remote_message_listener(client, room_id):
    """Listen for messages from the Matrix room and forward them to local apps."""
    def on_event(event):
        if event['type'] == "m.appbridge":
            json_data = event['content']
            app_name = json_data.get("app_name")
            if not app_name or not isinstance(app_name, str):
                print("Invalid message received: Missing or invalid 'app_name'")
                return
            print(f"Received message from Matrix: {json_data}")
            if json_data.get("action") == "port_allocation":
                assign_port_to_local(
                    app_name,
                    json_data.get("port"),
                    json_data.get("protocol"),
                    json_data.get("purpose")
                )
            else:
                forward_data_to_local_app(app_name, json_data)

    room = client.join_room(room_id)
    room.add_listener(on_event)
    print("Listening for remote messages from Matrix...")

def start_local_socket_server(client, room_id):
    """Start a Unix domain socket server for local app communication."""
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(5)
    print(f"Local socket server started at {SOCKET_PATH}")

    def handle_client_connection(client_socket):
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                json_data = json.loads(data)
                print(f"Received from local app: {json_data}")
                app_name = json_data.get("app_name")
                action = json_data.get("action")
                if action == "register_app":
                    if not app_name:
                        response = {"status": "error", "message": "'app_name' is required."}
                    else:
                        registered_apps[app_name] = client_socket
                        response = {"status": "success", "message": f"App {app_name} registered successfully."}
                elif action == "send_data":
                    if not app_name:
                        response = {"status": "error", "message": "'app_name' is required."}
                    else:
                        send_json_remote(client, room_id, {"app_name": app_name, "data": json_data.get("data")})
                        response = {"status": "success", "message": f"Data sent successfully from {app_name}."}
                elif action == "port_allocation":
                    if not app_name or not json_data.get("port") or not json_data.get("protocol") or not json_data.get("purpose"):
                        response = {"status": "error", "message": "'app_name', 'port', 'protocol', and 'purpose' are required."}
                    else:
                        assign_port_to_remote(
                            client,
                            room_id,
                            app_name,
                            json_data.get("port"),
                            json_data.get("protocol"),
                            json_data.get("purpose")
                        )
                        response = {
                            "status": "success",
                            "message": f"Assigned port {json_data.get('port')} to remote app {app_name} for {json_data.get('purpose')}."
                        }
                client_socket.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            print(f"Error handling client connection: {e}")
            client_socket.send(json.dumps({"status": "error", "message": "Internal server error"}).encode('utf-8'))
        finally:
            for app_name in list(registered_apps):
                if registered_apps[app_name] == client_socket:
                    del registered_apps[app_name]
                    print(f"App '{app_name}' unregistered due to disconnection.")
                    break
            client_socket.close()

    def accept_connections():
        while True:
            client_socket, _ = server.accept()
            print("New local app connected")
            threading.Thread(target=handle_client_connection, args=(client_socket,)).start()

    threading.Thread(target=accept_connections, daemon=True).start()

# Initialize the Matrix client and room ID
matrix_client = MatrixClient("https://matrix.org")  # Replace with your Matrix server URL
room_id = "!your_room_id:matrix.org"  # Replace with your Matrix room ID
matrix_client.login_with_password("username", "password")  # Replace with your credentials

# Start listening for remote messages from Matrix
remote_message_listener(matrix_client, room_id)

# Start the local socket server with Matrix client and room ID
start_local_socket_server(matrix_client, room_id)