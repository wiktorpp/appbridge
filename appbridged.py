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
