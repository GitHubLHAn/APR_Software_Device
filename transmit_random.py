import socket
import time
import random
import string

# Configuration
DEST_IP = '192.168.1.101'  # Replace with target IP
DEST_PORT = 1111      # Replace with target port

# ======================================================================================================
def crc8(data: bytes, length: int) -> int:
    crc = 0
    for i in range(length - 1):  # Bỏ qua phần tử cuối cùng
        crc ^= data[i]
        for _ in range(8):
            crc = (crc << 1) ^ 0x07 if (crc & 0x80) else (crc << 1)
            crc &= 0xFF  # Giới hạn 8-bit
    return crc


try:
    ipt = input("\n>> Enter destination IP: 192.168.1.")
    if ipt == '':
        raise ValueError
    DEST_IP = "192.168.1." + ipt
    
    print(f"-> Destination IP will be {DEST_IP}")
except ValueError:
    print("-> Default: Destination IP will be 192.168.1.101")
    DEST_IP = '192.168.1.101'
    
try:
    DEST_PORT = int(input("\n>> Enter destination port: "))
except ValueError:
    print("-> Default: Destination port will be 1111")
    DEST_PORT = 1111
    
try:
    cnt_do = int(input("\n>> Quantity of messages: "))
except ValueError:
    print("-> Default: Quantity of mess will be 1000")
    cnt_do = 1000



# ======================================================================================================
# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.03)  # 2 seconds timeout

cnt_sent = 0
cnt_received = 0
cnt_received_exact = 0
t_max = 0
num_max = 0
t_min = 0
t_sum = 0
num_t = 0

try:
    while cnt_do:
        length = 12 
        # length = random.randint(4, 50)
        mess_tx = bytearray(length)

        mess_tx[0] = 0x01
        mess_tx[1] = 0x23
        
        for i in range(2, length - 1):
            mess_tx[i] = random.randint(0, 10)
            
        mess_tx[length - 1] = crc8(mess_tx, length)

        s_ = time.time()
        sock.sendto(mess_tx, (DEST_IP, DEST_PORT))
        print(f"[SENT] - {cnt_sent+1} - {len(mess_tx)} bytes: {' '.join(f'{b:02X}' for b in mess_tx)}")
        sock.settimeout(0.1)  # 2 seconds timeout
        cnt_sent += 1
        
        try:
            mess_rx, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
            print(f"[RECEIVE] - {len(mess_rx)} bytes: {' '.join(f'{b:02X}' for b in mess_rx)}")
            if mess_rx == mess_tx:
                del_t = time.time() - s_
                if del_t > t_max:
                    t_max = del_t
                    num_max = cnt_sent
                if del_t < t_min or t_min == 0:
                    t_min = del_t
                print(f"-> RX OK - {del_t}s")
                print("*")
                cnt_received_exact += 1
                num_t+=1
                t_sum += del_t
            else:
                print("-> RX NOT OK")
                print("*")
        except socket.timeout:
            print("-> Timeout")
            print("*")
        
        # time.sleep(0.001)  # Sleep for 1 millisecond
        
        # input("enter to continue...")
        
        cnt_do -= 1
except KeyboardInterrupt:
    print("Stopped by user")
finally:
    print("Closing socket...")
    sock.close()
    
# ============================================================
print(f"Total packets sent: {cnt_sent}")
print(f"Total packets received exactly: {cnt_received_exact}")
print(f"Ratio: {cnt_received_exact / cnt_sent * 100:.2f}%")
print(f"Max time: {t_max}s at packet {num_max}")
print(f"Min time: {t_min}s")
t_avr = t_sum / num_t if num_t > 0 else 0
print(f"Average time: {t_avr} s")
# ============================================================