import socket
import time
import random
import string

import winsound

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

cnt_do = 1000
try:
    ipt = input("\n>> Enter destination IP: 192.168.1.")
    if ipt == '':
        raise ValueError
    DEST_IP = "192.168.1." + ipt
    
    print(f"-> Destination IP will be {DEST_IP}")
except ValueError:
    print("-> Default: Destination IP will be 192.168.1.101")
    DEST_IP = '192.168.1.101'
    
# try:
#     DEST_PORT = int(input("\n>> Enter destination port: "))
# except ValueError:
#     print("-> Default: Destination port will be 1111")
#     DEST_PORT = 1111
    
try:
    cnt_do = int(input("\n>> Quantity of messages: "))
    if cnt_do == 0:
        cnt_do = 1000000
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
cnt_not_OK = 0

try:
    while cnt_do:
        length = 12 
        # length = random.randint(4, 50)
        mess_tx = bytearray(length)

        mess_tx[0] = 0x01
        mess_tx[1] = 0x64
        mess_tx[2] = 0x46
        
        for i in range(3, length - 1):
            mess_tx[i] = random.randint(0, 255)
            
        mess_tx[length - 1] = crc8(mess_tx, length)

        s_ = time.time()
        sock.sendto(mess_tx, (DEST_IP, DEST_PORT))
        print(f"[SENT] - {cnt_sent+1} - {len(mess_tx)} bytes: {' '.join(f'{b:02X}' for b in mess_tx)}")
        sock.settimeout(0.03)  # 2 seconds timeout
        cnt_sent += 1
        
        try:
            mess_rx, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
            
            # sock.sendto(mess_tx, (DEST_IP, DEST_PORT))
            # print(f"[RECEIVE] - {len(mess_rx)} bytes: {' '.join(f'{b:02X}' for b in mess_rx)}")
            if mess_rx == mess_tx:
                print(f"[RECEIVE] - {len(mess_rx)} bytes: {' '.join(f'{b:02X}' for b in mess_rx)}")
                del_t = time.time() - s_
                if del_t > t_max:
                    t_max = del_t
                    num_max = cnt_sent
                if del_t < t_min or t_min == 0:
                    t_min = del_t
                print(f"-> RX OK - {del_t}s                                             Ratio: {(cnt_received_exact+1) / cnt_sent * 100:.2f}%")
                print("*")
                cnt_received_exact += 1
                num_t+=1
                t_sum += del_t
            else:
                print(f"[RECEIVE] - {len(mess_rx)} bytes: {' '.join(f'{b:02X}' for b in mess_rx)}")
                print("-> RX NOT OK                                                     Ratio: {cnt_received_exact / cnt_sent * 100:.2f}%")
                # winsound.Beep(3000, 20)
                print("*")
                cnt_not_OK += 1
        except socket.timeout:
            print(f"-> Timeout                                                           Ratio: {cnt_received_exact / cnt_sent * 100:.2f}%")
            # winsound.Beep(1500, 50)
            print("*")
        
        # time.sleep(0.001)  # Sleep for 1 millisecond
        # time.sleep(0.01)  # Sleep for 1 millisecond
        # time.sleep(0.5)  # Sleep for 1 millisecond
        # time.sleep(1)  # Sleep for 1 millisecond

        # input("enter to continue...")
        
        cnt_do -= 1
except KeyboardInterrupt:
    print("Stopped by user")
finally:
    print("Finish test\n")
    
print("\n========= Log Data on AP=========")
time.sleep(0.5)  # Sleep for 1 millisecond
data_send = bytearray(12)
data_send[0] = 0xAB
data_send[1] = 0xCD
data_send[2] = 0xC0
for i in range(3, 11):
    data_send[i] = 0xFE
data_send[11] = crc8(data_send, 12)

try:
    sock.sendto(data_send, (DEST_IP, DEST_PORT))
    print("-> Send: ", " ".join(f"{b:02X}" for b in data_send))
    sock.settimeout(1)  # 2 seconds timeout
    data_read, _ = sock.recvfrom(1024)
    print("-> Rec:", " ".join(f"{b:02X}" for b in data_read))
    
    if crc8(data_read, len(data_read)) == data_read[-1] and             \
                                            data_read[0] == 0xAB and   \
                                            data_read[1] == 0xCD and    \
                                            data_read[2] == 0xC0:
        day__ = data_read[3]
        hour__ = data_read[4]
        minute__ = data_read[5]
        second__ = data_read[6]
        rx_udp = (data_read[7] << 24) | (data_read[8] << 16) | (data_read[9] << 8) | data_read[10]
        tx_rf = (data_read[11] << 24) | (data_read[12] << 16) | (data_read[13] << 8) | data_read[14]
        rx_rf = (data_read[15] << 24) | (data_read[16] << 16) | (data_read[17] << 8) | data_read[18]
        tx_udp = (data_read[19] << 24) | (data_read[20] << 16) | (data_read[21] << 8) | data_read[22]
        id_wrong = data_read[23]
        time_transfer_rf = (data_read[24] << 8) | data_read[25]
    
        print(f"\nOperation: {day__} d, {hour__} h, {minute__} m, {second__} s")
        print(f"RX UDP:{rx_udp}")
        print(f"TX RF: {tx_rf}")
        print(f"RX RF: {rx_rf}")
        print(f"TX UDP: {tx_udp}")
        print(f"ID Wrong RX RF: {id_wrong}")
        print(f"Interval Transfer RF: {time_transfer_rf/1000} ms")
    else:
        print("-> Response Unexpected or CRC mismatch.")

except socket.timeout:
    print("-> Timeout while waiting for response.")
    
sock.close()
    
# ============================================================
print("\n========= Test Summary =========")
print(f"Total packets sent: {cnt_sent}")
print(f"Total packets received exactly: {cnt_received_exact}")
print(f"Total packets not OK: {cnt_not_OK}")
print(f"Ratio: {cnt_received_exact / cnt_sent * 100:.2f}%")
print(f"Max time: {t_max}s at packet {num_max}")
print(f"Min time: {t_min}s")
t_avr = t_sum / num_t if num_t > 0 else 0
print(f"Average time: {t_avr} s\n")
# ============================================================