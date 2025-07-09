import socket
import time

import subprocess

BOOTFOTA_FW_RUNNING     =   0x11
APPLICATION_FW_RUNNING     =   0x22

IP_DEFAULT = "192.168.1.101"  # Default IP for APR
PORT_DEFAULT = 1111           # Default port for APR

# ======================================================================================================
class UdpConnection:
    def __init__(self, socket, host, port):
        self.socket = socket
        self.host = host
        self.port = port

# ======================================================================================================
def crc8(data: bytes, length: int) -> int:
    crc = 0
    for i in range(length - 1):  # Bỏ qua phần tử cuối cùng
        crc ^= data[i]
        for _ in range(8):
            crc = (crc << 1) ^ 0x07 if (crc & 0x80) else (crc << 1)
            crc &= 0xFF  # Giới hạn 8-bit
    return crc

# ======================================================================================================
def check_connection():
    try:
        inp = int(input("\n> Input IP: 192.168.1."))
        HOST_INPUT = "192.168.1." + str(inp)
        Identify = inp
        print(f"-> IP: {HOST_INPUT}, Identify: {Identify}")
    except ValueError:
        print("-> Default IP: 192.168.1.101, Identify: 101")
        HOST_INPUT = IP_DEFAULT 
        
    try:
        PORT_INPUT = int(input("\n> Input Port: "))
        print(f"-> Port: {PORT_INPUT}\n")
    except ValueError:
        print("-> Default Port: 1111\n")
        PORT_INPUT = PORT_DEFAULT 
    
    print("\n>>>>>>>>> Checking connection to APR...")   
    time.sleep(1)
    
    try:
        while True:        
            # '-n 1' sends 1 ping, '-w 1000' sets timeout to 1 second (1000 ms)
            result = subprocess.run(['ping', '-n', '1', '-w', '1000', HOST_INPUT],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if "TTL=" in result.stdout:
                print(f"-> Ping to {HOST_INPUT} successful.")
                return HOST_INPUT, PORT_INPUT
            else:
                print(f"-> Ping to {HOST_INPUT} failed.")
                # return False
                
            time.sleep(1)  # Wait for 1 second before retrying
    except Exception as e:
        print(f"-> Error pinging {HOST_INPUT}: {e}")
        return False, False

# ======================================================================================================
def sendto_APR(data_send:bytearray, UDP_SOCKET):
    UDP_SOCKET.socket.sendto(data_send, (UDP_SOCKET.host, UDP_SOCKET.port))
    
# ======================================================================================================
def build_request_status_APR()->bytearray:
    data_request = bytearray(12)
    data_request[0] = 0xAB
    data_request[1] = 0xCD
    data_request[2] = 0xB4  # Command for request
    for i in range(3, 11):  # Fill bytes 2-10
        data_request[i] = 0xFE  # Fill with 0xFE
    data_request[11] = crc8(data_request, 12)  # Calculate CRC for the message
    return data_request

# ======================================================================================================
def receive_status_APR(UDP_SOCKET):    
    try:
        data_rec, _ = UDP_SOCKET.socket.recvfrom(1024)
        
        if len(data_rec) < 15:
            print("-> [Error]: Response not enough bytes")
            return False, False
        
        if data_rec[-1] == crc8(data_rec, 15):
            print("-> [Received] - ", " ".join(f"{b:02X}" for b in data_rec))
            print(f"-> [Information]:")
            print(f"        * Identify: {data_rec[0]}")
            if data_rec[3] == BOOTFOTA_FW_RUNNING:
                print(f"        * Current Mode: Bootloader")
            elif data_rec[3] == APPLICATION_FW_RUNNING:
                print(f"        * Current Mode: Application")
            else:
                print(f"        * Current Mode: Unknown ({data_rec[3]})")
            
            print(f"        * App verion: {round(data_rec[4]/10,1)}")
            print(f"        * Last Updated on: {data_rec[5]}/{data_rec[6]}/{(data_rec[7] << 8) | data_rec[8]}")
            print(f"        * StackPointer Address: {hex((data_rec[9]<<24) | (data_rec[10]<<16) | (data_rec[11]<<8) | data_rec[12])}")
            
            return data_rec[3], True
        else:
            print("-> [Error] - Unexpected Response !")
            print("-> [Received] - ", " ".join(f"{b:02X}" for b in data_rec))
            return False, False
            
    except socket.timeout:
        print("-> [Timeout] - Receive Response Timeout !")
        return False, False

# ======================================================================================================
def request_status_APR(UDP_SOCKET, retry=100):
    print("\n>>>>>>>>> Requesting APR Booting Status...")
    time.sleep(1)
    msg_sent = build_request_status_APR()
    
    while retry>0:
        sendto_APR(msg_sent, UDP_SOCKET)
        print("-> [Sent] - ", " ".join(f"{b:02X}" for b in msg_sent))
        
        time.sleep(0.001)  # Wait for 1 ms
        
        current_mode, result = receive_status_APR(UDP_SOCKET)
        
        if result:
            return current_mode
        else:
            retry -= 1
            
        time.sleep(0.5)
        
    print(f"-> [Result] - Request Status APR {HOST_INPUT} Fail !")
    return False


# ======================================================================================================
# ======================================================================================================
# ======================================================================================================
if __name__ == "__main__":
    print("\n-------------> READ STATUS OF APR DEVICE <-----------\n")
        
    HOST_INPUT, PORT_INPUT = check_connection()
        
    if not HOST_INPUT or not PORT_INPUT:
        print("-> Unable to establish connection. Exiting...")
        exit(1)
    
    time.sleep(1)
        
    # Tạo socket UDP
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(1)  # Timeout cho việc nhận dữ liệu
    
    udp_params = UdpConnection(udp_socket, HOST_INPUT, PORT_INPUT)
    
    while True:
        mode_current = request_status_APR(udp_params)
        
        get = input("\n>> Press Enter to continue or type 'e' to quit: ")
        if get == 'e':
            print("-> Exiting...")
            udp_socket.close()
            break
        else:
            print("-> Checking status again...\n")
        