import socket
import random
import time

import subprocess
import platform

import sys

def ping(host, count=2, timeout=0.05):
    # Xác định hệ điều hành
    system = platform.system()
    
    # Tạo lệnh ping phù hợp với hệ điều hành
    if system == "Windows":
        cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
    else:
        cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
    
    try:
        # Chạy lệnh ping và kiểm tra kết quả
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # In kết quả ping để debug
        output = result.stdout
        # print(output)

        # Kiểm tra nếu có "TTL=" trong phản hồi -> thành công
        if "TTL=" in output:
            return True
    except Exception as e:
        print(f"Lỗi khi ping: {e}")
        return False

def crc8(data: bytes, length: int) -> int:
    """Tính CRC-8 cho mảng từ phần tử 0 đến length-2, bỏ qua phần tử cuối."""
    crc = 0
    for i in range(length - 1):  # Bỏ qua phần tử cuối cùng
        crc ^= data[i]
        for _ in range(8):
            crc = (crc << 1) ^ 0x07 if (crc & 0x80) else (crc << 1)
            crc &= 0xFF  # Giới hạn 8-bit
    return crc


data_send = bytearray(12)
data_send[0] = 0xAB
data_send[1] = 0xCD

if __name__ == "__main__":  
    
    nhap_ip = input("> Nhập IP (hoặc nhập f để dò IP): ")
    
    if nhap_ip == "f":
        index = 101
        while index <= 200:
            host_do = "192.168.1." + str(index)
            result_ping = ping(host_do)
            if result_ping:
                print("-> Ping thành công đến địa chỉ IP: " + host_do)
                break
            else:
                print(f"-> Ping thất bại ({host_do}), tiếp tục dò ...")
                index += 1
            
        # time.sleep(1)
        nhap_ip = host_do
    else:
        result_ping = ping(nhap_ip)
        if result_ping:
            print("-> Ping thành công đến địa chỉ IP: " + nhap_ip)
        else:
            print(f"-> Ping thất bại ({nhap_ip}) ?????")
            sys.exit()
    
    nhap_port = int(input("\n> Nhập PORT: "))       
            
    IP = nhap_ip
    PORT = nhap_port
    
    # print(type(IP))
    
    print("")
    # Tạo socket UDP
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(1)  # Timeout cho việc nhận dữ liệu
    
    while True:
        
        print("     1. Xem thông số APR             2. Xem phiên bản APR")
        print("     3. Cài đặt thông số APR         4. Xem chế độ lọc ID robot")
        print("     5. Cài đặt chế độ lọc ID robot")  
        print("     t. Test truyền nhận")
        print("     e. Kết thúc \n")

        chedo = input("> Nhập chế độ: ")
        
        # Xem thông số APR-------------------------------------------------------------------------------------------------------------------------------
        if chedo == "1":
            data_send[2] = 0xB1
            
            for index in range(3,10):
                data_send[index] = 0xFE
            data_send[11] = crc8(data_send, 12)
            
            print("Bản tin xem thông số:", " ".join(f"{b:02X}" for b in data_send))
            udp_socket.sendto(data_send, (IP, PORT))
            
            time.sleep(0.001)

            try:
                data_read, _ = udp_socket.recvfrom(256)
                
                if crc8(data_read, len(data_read)) == data_read[-1] and data_read[0] == 0xAB and data_read[1] == 0xCD and data_read[2] == 0xB1:
                    print("-> Bản tin phản hồi:", " ".join(f"{b:02X}" for b in data_read))
                    print("-> APR này có thông số như sau:")
                    print("     * IP: " + str(data_read[3]) + "." + str(data_read[4]) + "." + str(data_read[5]) + "." + str(data_read[6]))
                    print("     * PORT: " + str((data_read[7] << 8) | data_read[8]))
                    print("     * Tần số: " + str((data_read[9] << 8) | data_read[10]))
                else:
                    print("-> Bản tin phản hồi:", " ".join(f"{b:02X}" for b in data_read))
                    print("Bản tin phản hồi sai cấu trúc!")
            except socket.timeout:
                print("Timeout khi nhận phản hồi!")
        
        # Xem phiên bản APR-------------------------------------------------------------------------------------------------------------------------------
        if chedo == "2":
            data_send[2] = 0xB2
            
            for index in range(3,10):
                data_send[index] = 0xFE
            data_send[11] = crc8(data_send, 12)
            
            print("Bản tin xem version:", " ".join(f"{b:02X}" for b in data_send))
            udp_socket.sendto(data_send, (IP, PORT))
            
            time.sleep(0.1)

            try:
                data_read, _ = udp_socket.recvfrom(256)
                if crc8(data_read, len(data_read)) == data_read[-1] and data_read[0] == 0xAB and data_read[1] == 0xCD and data_read[2] == 0xB2:
                    print("-> Bản tin phản hồi:", " ".join(f"{b:02X}" for b in data_read))
                    if data_read[3] == 205:
                        print("-> Version Access Point Robot Device:  3.2")
                    else:
                        print("-> Version Access Point Robot Device:  " + str(round(data_read[3]/10,1)))
                    
                else:
                    print("Bản tin phản hồi sai cấu trúc!")
            except socket.timeout:
                print("Timeout khi nhận phản hồi!")
            
        # Cài đặt thông số APR-------------------------------------------------------------------------------------------------------------------------------
        if chedo == "3":
            print("> Nhập vào các thông số cần config: ")
            ip_new = input("IP: ")
            port_new = int(input("Port: "))
            F_new = int(input("Tần số: "))
            
            inside_ip_new = ip_new.split(".")
            numbers_ip_new = [int(part) for part in inside_ip_new]
            
            # print(type(numbers_ip_new[0]))
            # print(type(port_new))
            
            data_send[2] = 0xA1
            
            data_send[3] = numbers_ip_new[0]
            data_send[4] = numbers_ip_new[1]
            data_send[5] = numbers_ip_new[2]
            data_send[6] = numbers_ip_new[3]
            
            data_send[7] = (port_new >> 8) & 0xFF
            data_send[8] = port_new & 0xFF
            
            data_send[9] =  (F_new >> 8) & 0xFF
            data_send[10] = F_new & 0xFF
            
            data_send[11] = crc8(data_send, 12)
            
            print("Bản tin cài đặt APR:", " ".join(f"{b:02X}" for b in data_send))
            udp_socket.sendto(data_send, (IP, PORT))
            
            try:
                data_read, _ = udp_socket.recvfrom(256)
                if crc8(data_read, len(data_read)) == data_read[-1] and data_read[0] == 0xAB and data_read[1] == 0xCD and data_read[2] == 0xA1:
                    print("-> Bản tin phản hồi:", " ".join(f"{b:02X}" for b in data_read))
                    if data_read[3] == 0x59:
                        print("-> Cài đặt thông số APR thành công !")
                    else:
                        print("-> Cài đặt APR thất bại !")
                else:
                    print("-> Bản tin phản hồi sai cấu trúc!")
                break
            except socket.timeout:
                print("-> Timeout khi nhận phản hồi!")
             
        # Xem chế độ lọc ID robot-------------------------------------------------------------------------------------------------------------------------------
        if chedo == "4":
            i = 11
            
        # 5. Cài đặt chế độ lọc ID robot-------------------------------------------------------------------------------------------------------------------------------
        if chedo == "5":
            i = 11
        
        # t. Test truyền nhận bản tin-------------------------------------------------------------------------------------     
        if chedo == "t":
            
            solantest = 1000
            cycle_test = 0.03
            
            sobantingui = 0
            sobantinnhan = 0
            sobantinnhandung = 0
            tylenhandung = 0
            sobantin_timeout = 0
            
            t_s = time.time()
            while solantest > 0:
                id_rb = random.randint(500, 5000)
                data_send[0] = random.randint(0, 1)
                data_send[1] = id_rb & 0xFF
                data_send[2] = (id_rb >> 8) &0xFF
                data_send[3] = random.randint(0, 255)
                data_send[4] = random.randint(0, 255)
                data_send[5] = random.randint(0, 255)
                data_send[6] = random.randint(0, 255)
                data_send[7] = random.randint(0, 255)
                data_send[8] = random.randint(0, 255)
                data_send[9] = random.randint(0, 255)
                data_send[10] = random.randint(0, 255)
                data_send[11] = crc8(data_send, 12)
                
                print("Bản tin gửi:", " ".join(f"{b:02X}" for b in data_send))
                udp_socket.sendto(data_send, (IP, PORT))
                sobantingui += 1
                
                time.sleep(0.003)

                try:
                    data_read, _ = udp_socket.recvfrom(256)
                    sobantinnhan += 1
                    if data_read == data_send:
                        print("-> Bản tin phản hồi đúng:", " ".join(f"{b:02X}" for b in data_read))
                        sobantinnhandung += 1
                    else:
                        print("Bản tin phản hồi sai cấu trúc!")
                except socket.timeout:
                    print("Timeout khi nhận phản hồi!")
                    sobantin_timeout += 1
                    
                    
                solantest -= 1
                time.sleep(cycle_test)
            
            t_i = time.time() - t_s
            print("\n*** KẾT QUẢ:")
            print("-> Thời gian test: " + str(round(t_i,1)) + " (s)")
            print("-> Số bản tin gửi: " +str(sobantingui))
            print("-> Số bản tin nhận: " +str(sobantinnhan))
            print("-> Số bản tin nhận đúng: " +str(sobantinnhandung) + "  (" + str(round(sobantinnhandung*100/sobantingui, 2)) + "%)")
            
        if chedo == "e":
            print("Kết thúc chương trình !")
            sys.exit()
            
        print("")
            
        print("*******************************************************************************")
        ee = input("> Nhấn Enter để tiếp tục, nhập e để kết thúc: ")
        if ee == "e":
            break
        print("*******************************************************************************")