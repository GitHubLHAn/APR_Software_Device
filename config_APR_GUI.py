import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import socket

def crc8(data: bytes, length: int) -> int:
    crc = 0
    for i in range(length - 1):  # Bỏ qua phần tử cuối cùng
        crc ^= data[i]
        for _ in range(8):
            crc = (crc << 1) ^ 0x07 if (crc & 0x80) else (crc << 1)
            crc &= 0xFF  # Giới hạn 8-bit
    return crc

class ConnectApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("APR Device Configuration Tool")
        self.geometry("600x400")
        self.resizable(False, False)

        frm_conn = ttk.LabelFrame(self, text="Device Connection")
        frm_conn.pack(padx=40, pady=40, fill="x")
        
        
        self.find_ip_btn = tk.Button(frm_conn, text="Find IP", command=self.on_find_ip, width=20)
        self.find_ip_btn.config(text="Find IP", bg="lightyellow", fg="purple", activebackground="lightyellow")
        self.find_ip_btn.grid(row=0, column=2, columnspan=2, pady=10)   

        ttk.Label(frm_conn, text="IP Address:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.ip_var = tk.StringVar(value="192.168.1.101")
        self.ip_entry = ttk.Entry(frm_conn, textvariable=self.ip_var, width=20)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=10)

        ttk.Label(frm_conn, text="Port:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.port_var = tk.StringVar(value="1111")
        self.port_entry = ttk.Entry(frm_conn, textvariable=self.port_var, width=20)
        self.port_entry.grid(row=1, column=1, padx=5, pady=10)

        self.connect_btn = tk.Button(frm_conn, text="CONNECT", command=self.on_connect, width=20, bg="SystemButtonFace")
        self.connect_btn.config(text="CONNECT", bg="green", fg="white", activebackground="green")
        self.connect_btn.grid(row=1, column=2, columnspan=5, pady=10)
        
        # Thêm nút Check Version, mặc định disable
        self.check_version_btn = tk.Button(frm_conn, text="Check Version", command=self.on_check_version, width=20, state="disabled")
        self.check_version_btn.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Nút Read Parameters, mặc định disable
        self.read_param_btn = tk.Button(frm_conn, text="Read Parameters", command=self.on_read_parameters, width=20, state="disabled")
        self.read_param_btn.grid(row=3, column=3, columnspan=2, pady=10)

        # Thêm các trường nhập cho New ID, New Port, New Channel
        ttk.Label(frm_conn, text="New ID:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.new_id_var = tk.StringVar()
        self.new_id_entry = ttk.Entry(frm_conn, textvariable=self.new_id_var, width=20)
        self.new_id_entry.grid(row=5, column=1, padx=5, pady=10)

        ttk.Label(frm_conn, text="New Port:").grid(row=6, column=0, padx=5, pady=5, sticky="e")
        self.new_port_var = tk.StringVar()
        self.new_port_entry = ttk.Entry(frm_conn, textvariable=self.new_port_var, width=20)
        self.new_port_entry.grid(row=6, column=1, padx=5, pady=10)

        ttk.Label(frm_conn, text="New Channel:").grid(row=7, column=0, padx=5, pady=5, sticky="e")
        self.new_channel_var = tk.StringVar()
        self.new_channel_entry = ttk.Entry(frm_conn, textvariable=self.new_channel_var, width=20)
        self.new_channel_entry.grid(row=7, column=1, padx=5, pady=10)

        # Nút Set Parameters
        self.set_param_btn = tk.Button(frm_conn, text="Set Parameters", command=self.on_set_parameters, width=20, state="normal")
        self.set_param_btn.grid(row=7, column=2, columnspan=2, pady=10)

        self.udp_socket = None
        self.connected = False

    def on_connect(self):
        if not self.connected:
            ip = self.ip_var.get().strip()
            port = self.port_var.get().strip()
            if not ip or not port:
                messagebox.showwarning("Input Error", "Please enter both IP and port.")
                return
            try:
                result = subprocess.run(['ping', '-n', '1', '-w', '1000', ip],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if "TTL=" in result.stdout:
                    try:
                        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        udp_socket.settimeout(0.2)
                        self.udp_socket = udp_socket
                        self.connected = True
                        self.connect_btn.config(text="DISCONNECT", bg="red", fg="white", activebackground="red")
                        self.check_version_btn.config(state="normal")  # Enable nút Check Version
                        self.read_param_btn.config(state="normal")  
                        self.set_param_btn.config(state="normal")  
                        
                    except Exception as sock_err:
                        messagebox.showerror("Socket Error", f"Ping OK but cannot create socket:\n{sock_err}")
                else:
                    messagebox.showerror("Connection", f"Ping to {ip} fail.")
                    self.check_version_btn.config(state="disabled")
                    self.read_param_btn.config(state="disabled")
                    self.set_param_btn.config(state="disabled")  
            except Exception as e:
                messagebox.showerror("Connection", f"Cannot Ping to {ip}:\n{e}")
                self.check_version_btn.config(state="disabled")
                self.read_param_btn.config(state="disabled")
                self.set_param_btn.config(state="disabled") 
        else:
            if self.udp_socket:
                try:
                    self.udp_socket.close()
                except Exception:
                    pass
                self.udp_socket = None
            self.connected = False
            self.connect_btn.config(text="CONNECT", bg="green", fg="white", activebackground="green")
            self.check_version_btn.config(state="disabled")  # Disable nút Check Version
            self.read_param_btn.config(state="disabled")
            self.set_param_btn.config(state="disabled") 
            
    def on_check_version(self):
        # messagebox.showinfo("Check Version", "Đã nhấn nút Check Version!\n(Bạn cần bổ sung chức năng gửi lệnh thực tế ở đây.)")
        if not self.connected or not self.udp_socket:
            messagebox.showwarning("Warning", "You need to connect first!")
            return
        
         # Tạo bản tin 12 byte: AB CD B1 random... CRC8
        data_send = bytearray(12)
        data_send[0] = 0xAB
        data_send[1] = 0xCD
        data_send[2] = 0xB2
        for i in range(3, 11):
            data_send[i] = 0xFE
        data_send[11] = crc8(data_send, 12)

        ip = self.ip_var.get().strip()
        port = int(self.port_var.get().strip())

        try:
            self.udp_socket.sendto(data_send, (ip, port))
            print("-> Send:", " ".join(f"{b:02X}" for b in data_send))
            self.udp_socket.settimeout(1)
            data_read, _ = self.udp_socket.recvfrom(256)
            
            if crc8(data_read, len(data_read)) == data_read[-1] and             \
                                                    data_read[0] == 0xAB and   \
                                                    data_read[1] == 0xCD and    \
                                                    data_read[2] == 0xB2:
                ver = str(round(data_read[3]/10,1))
                messagebox.showinfo("Result ", f"Current Application Version: {ver}")
                print("-> Rec:", " ".join(f"{b:02X}" for b in data_read))
            else:
                print("-> Rec:", " ".join(f"{b:02X}" for b in data_read))
                messagebox.showerror("Error", "Response Unexpected or CRC mismatch.")

        except socket.timeout:
            messagebox.showerror("Error", "Response Timeout")

    def on_read_parameters(self):
        if not self.connected or not self.udp_socket:
            messagebox.showwarning("Warning", "You need to connect first!")
            return
        
         # Tạo bản tin 12 byte: AB CD B1 random... CRC8
        data_send = bytearray(12)
        data_send[0] = 0xAB
        data_send[1] = 0xCD
        data_send[2] = 0xB1
        for i in range(3, 11):
            data_send[i] = 0xFE
        data_send[11] = crc8(data_send, 12)

        ip = self.ip_var.get().strip()
        port = int(self.port_var.get().strip())

        try:
            self.udp_socket.sendto(data_send, (ip, port))
            print("-> Send: ", " ".join(f"{b:02X}" for b in data_send))
            self.udp_socket.settimeout(1)
            data_read, _ = self.udp_socket.recvfrom(256)
            
            if crc8(data_read, len(data_read)) == data_read[-1] and             \
                                                    data_read[0] == 0xAB and   \
                                                    data_read[1] == 0xCD and    \
                                                    data_read[2] == 0xB1:
                ip__ = str(data_read[3]) + "." + str(data_read[4]) + "." + str(data_read[5]) + "." + str(data_read[6])
                port__ = str((data_read[7] << 8) | data_read[8])
                fre__ = str((data_read[9] << 8) | data_read[10])
                messagebox.showinfo("Result ", f"   IP: {ip__}\n   Port: {port__}\n   Frequency: {fre__} MHz")
                print("-> Rec:", " ".join(f"{b:02X}" for b in data_read))
            else:
                print("-> Rec:", " ".join(f"{b:02X}" for b in data_read))
                messagebox.showerror("Error", "Response Unexpected or CRC mismatch.")

        except socket.timeout:
            messagebox.showerror("Error", "Response Timeout")
             
    def on_find_ip(self):
        base_ip = "192.168.1."
        start = 101
        end = 254
        found = False
        for i in range(start, end + 1):
            ip = base_ip + str(i)
            self.ip_var.set(ip)
            self.update()  # Cập nhật giao diện để thấy IP đang thử
            try:
                result = subprocess.run(['ping', '-n', '1', '-w', '500', ip],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if "TTL=" in result.stdout:
                    messagebox.showinfo("Find IP", f"Find device at host: {ip}")
                    self.ip_var.set(ip)
                    found = True
                    break
            except Exception:
                pass
        if not found:
            messagebox.showerror("Find IP", "Cannot find device in range 192.168.1.101 - 192.168.1.254")     
       
       
    def on_set_parameters(self):
        if not self.connected or not self.udp_socket:
            messagebox.showwarning("Warning", "You need to connect first!")
            return

        try:
            ip_str = self.new_id_var.get().strip()
            new_ip = ip_str.split('.')  # Kết quả: ['192', '168', '1', '101']
            # new_id = int()
            new_port = int(self.new_port_var.get().strip())
            new_channel = int(self.new_channel_var.get().strip())
        except ValueError:
            messagebox.showerror("Input Error", "ID/Port/Channel value invalid!")
            return

        # Tạo bản tin 12 byte: AB CD B3 [ID, PortH, PortL, ChanH, ChanL, ...] CRC8
        data_send = bytearray(12)
        data_send[0] = 0xAB
        data_send[1] = 0xCD
        data_send[2] = 0xA1
        data_send[3] = int(new_ip[0])
        data_send[4] = int(new_ip[1])
        data_send[5] = int(new_ip[2])
        data_send[6] = int(new_ip[3])
        
        data_send[7] = (new_port >> 8) & 0xFF
        data_send[8] = new_port & 0xFF
        
        data_send[9] =  (new_channel >> 8) & 0xFF
        data_send[10] = new_channel & 0xFF
            
        data_send[11] = crc8(data_send, 12)

        ip = self.ip_var.get().strip()
        port = int(self.port_var.get().strip())

        try:
            self.udp_socket.sendto(data_send, (ip, port))
            self.udp_socket.settimeout(1)
            data_read, _ = self.udp_socket.recvfrom(256)
            if crc8(data_read, len(data_read)) == data_read[-1] and \
                                                data_read[0] == 0xAB and  \
                                            data_read[1] == 0xCD and \
                                            data_read[2] == 0xA1:
                if data_read[3] == 0x59:
                    messagebox.showinfo("Set Parameters", "Configurations Successfully Set!")
                else:
                    messagebox.showerror("Set Parameters", "Configurations Failed to Set!")
            else:
                messagebox.showerror("Set Parameters", "Response Unexpected or CRC mismatch.")
        except socket.timeout:
            messagebox.showerror("Set Parameters", "Response Timeout")
                   
                 
if __name__ == "__main__":
    app = ConnectApp()
    app.mainloop()