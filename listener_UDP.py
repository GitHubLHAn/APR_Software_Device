# import socket
# import time

# UDP_IP = "192.168.1.100"
# UDP_PORT = 1111
# BUFFER_SIZE = 1024  # Adjust as needed

# def main():
#     # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     # sock.bind((UDP_IP, UDP_PORT))

#     print(f"Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")

#     try:
#         while True:
#             sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#             sock.bind((UDP_IP, UDP_PORT))
            
#             data, addr = sock.recvfrom(BUFFER_SIZE)
#             print(f"Received message from {addr}: {data}")
            
#             sock.close()
#             time.sleep(0.001)  # Sleep for 1 millisecond
#     except KeyboardInterrupt:
#         print("\nStopped by user.")
#     finally:
#         sock.close()

# if __name__ == "__main__":
#     main()
    
    
import socket
import sys

def udp_listener(host='0.0.0.0', port=12345):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.bind((host, port))
            # Đặt timeout cho socket (ví dụ: 1 giây)
            sock.settimeout(1.0)
            print(f"Đang lắng nghe các gói tin UDP trên {host}:{port}...")
            print("Nhấn Ctrl+C để dừng.")
        except OSError as e:
            print(f"Lỗi khi ràng buộc socket: {e}")
            print("Đảm bảo cổng không bị chương trình khác sử dụng hoặc bạn có quyền truy cập.")
            return

        while True:
            try:
                data, address = sock.recvfrom(1024)
                print(f"Nhận được từ {address}: {data.decode('utf-8')}")
            except socket.timeout:
                # Không có dữ liệu trong khoảng timeout, tiếp tục vòng lặp
                continue
            except KeyboardInterrupt:
                print("\nĐã nhận tín hiệu Ctrl+C. Đang tắt trình lắng nghe...")
                break
            except Exception as e:
                print(f"Lỗi khi nhận dữ liệu: {e}")
                break
    print("Trình lắng nghe UDP đã dừng.")

if __name__ == "__main__":
    udp_listener()