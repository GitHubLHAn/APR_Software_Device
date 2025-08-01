import socket
import time
import random

UDP_IP = "192.168.1.115"      # Change to target IP if needed
UDP_PORT = 1111               # Change to target port if needed



def crc8(data: bytes, length: int) -> int:
    """Tính CRC-8 cho mảng từ phần tử 0 đến length-2, bỏ qua phần tử cuối."""
    crc = 0
    for i in range(length - 1):  # Bỏ qua phần tử cuối cùng
        crc ^= data[i]
        for _ in range(8):
            crc = (crc << 1) ^ 0x07 if (crc & 0x80) else (crc << 1)
            crc &= 0xFF  # Giới hạn 8-bit
    return crc

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.02)  # Set timeout to t seconds


# ----------------------------------------------------------------------------------
try:
    lan = int(input("\n> Input Number of packets to send : "))
except ValueError:
    print("-> Default: Số lượng gói tin sẽ gửi là 10.")
    lan = 10
    
# ----------------------------------------------------------------------------------
try:
    channel = int(input("\n> Input Channel RF : "))
except ValueError:
    print("-> Default: Channel RF sẽ là 0.")
    channel = 0
    
# ----------------------------------------------------------------------------------
try:
    time_delay = float(input("\n> Input Time delay between packets (s) : "))
    if time_delay < 0:
        print("-> Error: Thời gian trễ không thể âm. Đặt về 0.001 giây.")
        time_delay = 0.001      
except ValueError:
    print("-> Default: Thời gian trễ giữa các gói tin sẽ là 0.001 giây.")
    time_delay = 0.001
    


solangui = 0
solannhan = 0

# ----------------------------------------------------------------------------------
print("\n>>>>>>>>> Resetting APR...")
while True:
    msg_sent = bytearray(12)
    msg_sent[0] = 0xAB
    msg_sent[1] = 0xCD
    msg_sent[2] = 0xEF
    for i in range(3, 11):  # Fill bytes 2-10 with random values
        msg_sent[i] = random.randint(0, 200)
    msg_sent[11] = crc8(msg_sent, 12)  # Calculate CRC8 for first 11 bytes, store at last byte

    sock.sendto(msg_sent, (UDP_IP, UDP_PORT))
    # print("-> Reset APR:", " ".join(f"{b:02X}" for b in msg_sent))
    
    time.sleep(0.001)
    
    try:
        data_rec, _ = sock.recvfrom(1024)
        
        if len(data_rec) <= 1:
            print("-> [Error]: Response too short")
            pass

        if data_rec == msg_sent:
            print("-> Reset OK")
            break  # Exit the loop if reset is successful

    except socket.timeout:
        print("-> Timeout. Can not reset APR")
    
    time.sleep(1)

print("-> Waiting for APR to reset...")
time.sleep(2)

# ----------------------------------------------------------------------------------
sock.settimeout(3)  # Set timeout to t seconds
print("\n>>>>>>>>> Set Channel...")
while True:
    msg_sent = bytearray(12)
    msg_sent[0] = 0xAB
    msg_sent[1] = 0xCD
    msg_sent[2] = 0xFE
    msg_sent[3] = channel  # Set channel R
    for i in range(4, 11):  # Fill bytes 2-10 with random values
        msg_sent[i] = random.randint(0, 200)
    msg_sent[11] = crc8(msg_sent, 12)  # Calculate CRC8 for first 11 bytes, store at last byte

    sock.sendto(msg_sent, (UDP_IP, UDP_PORT))
    # print("-> Reset APR:", " ".join(f"{b:02X}" for b in msg_sent))
    
    time.sleep(0.001)
    
    try:
        data_rec, _ = sock.recvfrom(1024)
        
        if len(data_rec) <= 1:
            print("-> [Error]: Response too short")
            pass

        if data_rec == msg_sent:
            print("-> Config OK")
            break  # Exit the loop if reset is successful

    except socket.timeout:
        print("-> Timeout. Can not Config APR")
    
    time.sleep(1)

time.sleep(0.1)

# ----------------------------------------------------------------------------------
sock.settimeout(0.015)  # Set timeout to t seconds
print("\n>>>>>>>>> Start Transfer Message...")
_start_test = time.time()
try:
    while lan > 0:
        msg_sent = bytearray(12)
        msg_sent[0] = 0xAE
        msg_sent[1] = 12
        for i in range(2, 11):  # Fill bytes 2-10 with random values
            msg_sent[i] = random.randint(0, 200)
        msg_sent[11] = crc8(msg_sent, 12)  # Calculate CRC8 for first 11 bytes, store at last byte

        _start = time.time()
        sock.sendto(msg_sent, (UDP_IP, UDP_PORT))
        print(f"-> [TX - {solangui+1}]:", " ".join(f"{b:02X}" for b in msg_sent))
        solangui += 1
        
        time.sleep(0.001)
        
        try:
            data_rec, _ = sock.recvfrom(1024)
            
            if len(data_rec) <= 1:
                print("-> [Error]: Response too short")
                pass

            if data_rec == msg_sent:
                # print(f"-> [RX]:", " ".join(f"{b:02X}" for b in data_rec))
                print("-> RX OK - Time:", f"{(time.time() - _start) * 1000:.2f} ms")
                solannhan += 1
            # else:
            #     print(f"<- [RX]:", " ".join(f"{b:02X}" for b in data_rec))
            
        except socket.timeout:
            print("-> Timeout 0.2s - No response received")
        
        time.sleep(time_delay)
        lan -= 1
        # input(str(("next: ")))
except KeyboardInterrupt:
    print("Stopped by user.")
finally:
    sock.close()
    
_end_test = time.time()

print("-----")   
print(f"     Total sent: {solangui}, Total received: {solannhan}")
print(f"     Success rate: {solannhan / solangui * 100:.2f}%")
print(f"     Time taken: {(_end_test - _start_test):.2f} s")
print("-----")   