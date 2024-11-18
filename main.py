import websocket
import gzip
import json
import random
import hashlib
import time

# Enable WebSocket debugging
websocket.enableTrace(True)

# List of SafeUM nodes (alternative servers)
ADDRESS_LISTS = [
    "193.200.173.45",
    "185.65.206.12",
    "195.13.182.217",
    "195.13.182.213",
    "180.210.203.183",
]
PORT = 8080
ENDPOINT = "/Auth"  # Change this if the endpoint differs

# Generate a random device UID
def generate_device_uid():
    random_string = f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
    return hashlib.md5(random_string.encode()).hexdigest()

# Decompress GZIP responses
def decompress_response(response):
    return gzip.decompress(response).decode('utf-8')

# Fetch Unique Key
def fetch_unique_key(ws, device_uid, software_version="1.0"):
    payload = {
        "action": "Login",
        "subaction": "GetKeyUnique",
        "deviceuid": device_uid,
        "softwareversion": software_version,
        "id": random.randint(1000, 9999),
    }
    ws.send(json.dumps(payload))
    compressed_response = ws.recv()
    response = decompress_response(compressed_response)
    return json.loads(response)

# Login
def login(ws, username, password, unique_key, device_uid, software_version="1.0"):
    # Hash password with the unique key (hypothetical; SafeUM's real hashing is unknown)
    password_hash = hashlib.sha256((password + unique_key['x']).encode()).hexdigest()
    
    payload = {
        "action": "login",
        "subaction": "alt",
        "deviceuid": device_uid,
        "softwareversion": software_version,
        "login": username,
        "password": password_hash,
    }
    ws.send(json.dumps(payload))
    compressed_response = ws.recv()
    response = decompress_response(compressed_response)
    return json.loads(response)

# Connect to a WebSocket node
def connect_to_node(node, port, endpoint):
    websocket_url = f"ws://{node}:{port}{endpoint}"
    headers = {"User-Agent": "SafeUMClient/1.0"}
    try:
        ws = websocket.create_connection(websocket_url, timeout=10, header=headers, subprotocols=["binary"])
        print(f"[+] Connected to {websocket_url}")
        return ws
    except Exception as e:
        print(f"[-] Failed to connect to {websocket_url}: {e}")
        return None

# Main function
def main():
    device_uid = generate_device_uid()
    ws = None

    # Attempt to connect to each node in the list
    for node in ADDRESS_LISTS:
        ws = connect_to_node(node, PORT, ENDPOINT)
        if ws:
            break
    if not ws:
        print("[-] All connection attempts failed.")
        return

    try:
        # Fetch the unique key
        unique_key_response = fetch_unique_key(ws, device_uid)
        if unique_key_response["status"] != "Success":
            print("[-] Failed to fetch unique key:", unique_key_response)
            return
        
        unique_key = unique_key_response["key"]
        print("[+] Unique key fetched:", unique_key)
        
        # Perform login
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        login_response = login(ws, username, password, unique_key, device_uid)
        
        if login_response["status"] == "Success":
            print("[+] Login successful:", login_response)
        else:
            print("[-] Login failed:", login_response)
    finally:
        ws.close()

if __name__ == "__main__":
    main()
