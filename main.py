import websocket
import json
import random
import gzip
import traceback

# Define constants
HEADERS = {
    "User-Agent": "SafeUMClient/1.0",
    "Connection": "Upgrade",
    "Upgrade": "websocket",
    "Sec-WebSocket-Protocol": "binary"
}
INITIAL_NODES = [
    "193.200.173.45",
    "185.65.206.12",
    "195.13.182.217",
    "195.13.182.213",
    "180.210.203.183"
]
PORT = 8080
BAL_ENDPOINT = "/Bal"
AUTH_ENDPOINT = "/Auth"


# Function to decompress gzip responses
def decompress_response(compressed_data):
    try:
        return gzip.decompress(compressed_data).decode('utf-8')
    except Exception as e:
        print(f"[-] Failed to decompress response: {e}")
        return compressed_data.decode('utf-8', errors='ignore')


# Function to fetch nodes from the /Bal endpoint
def fetch_nodes(node):
    try:
        print(f"[+] Connecting to node {node}{BAL_ENDPOINT}")
        ws = websocket.create_connection(f"ws://{node}:{PORT}{BAL_ENDPOINT}", header=HEADERS)
        payload = {
            "action": "Balancer",
            "subaction": "Query",
            "id": random.randint(1000, 9999),
        }
        ws.send(json.dumps(payload))
        compressed_response = ws.recv()
        ws.close()
        response = decompress_response(compressed_response)
        return json.loads(response).get("nodes", {})
    except Exception as e:
        print(f"[-] Failed to fetch nodes from {node}: {e}")
        return {}


# Function to fetch a unique key for authentication
def fetch_unique_key(ws, device_uid="1234567890", software_version="1.0"):
    payload = {
        "action": "Login",
        "subaction": "GetKeyUnique",
        "deviceuid": device_uid,
        "softwareversion": software_version,
        "id": random.randint(1000, 9999)
    }
    ws.send(json.dumps(payload))
    compressed_response = ws.recv()
    response = decompress_response(compressed_response)
    return json.loads(response).get("key", {})


# Function to log in using username and password
def login(ws, username, password, unique_key):
    payload = {
        "action": "login",
        "subaction": "alt",
        "login": username,
        "password": password,
        "key": unique_key,
        "id": random.randint(1000, 9999)
    }
    ws.send(json.dumps(payload))
    compressed_response = ws.recv()
    response = decompress_response(compressed_response)
    return json.loads(response)


# Main function
def main():
    global INITIAL_NODES
    dynamic_nodes = {}

    # Step 1: Fetch dynamic nodes from /Bal endpoint
    for node in INITIAL_NODES:
        dynamic_nodes = fetch_nodes(node)
        if dynamic_nodes:
            print("[+] Nodes fetched:", dynamic_nodes)
            break
    else:
        print("[-] Failed to fetch nodes from all initial nodes.")
        return

    # Step 2: Use dynamic nodes to authenticate
    for priority, node in sorted(dynamic_nodes.items()):
        print(f"[+] Trying to connect to node {node} for authentication...")
        try:
            ws = websocket.create_connection(f"ws://{node}:{PORT}{AUTH_ENDPOINT}", header=HEADERS)
            # Fetch unique key
            unique_key = fetch_unique_key(ws)
            print("[+] Unique key fetched:", unique_key)

            # Login with username and password
            username = input("Enter your username: ")
            password = input("Enter your password: ")
            response = login(ws, username, password, unique_key)
            print("[+] Login response:", response)
            ws.close()
            return
        except Exception as e:
            print(f"[-] Failed to connect to {node}: {e}")
            traceback.print_exc()

    print("[-] All connection attempts failed.")


if __name__ == "__main__":
    main()
