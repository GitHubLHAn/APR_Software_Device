import socket

def udp_listener(host='192.168.1.100', port=1111):

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.bind((host, port))
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
                message = data.decode('utf-8')
                print(f"{message}")

            except socket.timeout:
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