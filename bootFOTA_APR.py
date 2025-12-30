import socket
import os
import time

import subprocess

from datetime import datetime
from analysis_hex import analysis_hex


class UdpConnection:
    def __init__(self, socket, host, port):
        self.socket = socket
        self.host = host
        self.port = port
        
        
CMD_STATUS			=		0xB4
CMD_RUN_BOOTLOADER	=       0xB5

CMD_START_FLASHING	=       0xA2
CMD_FLASHING		=		0xA3
CMD_VERIFY_DATA		=	    0xA4

CMD_RUN_APP			=		0xA5


BOOTFOTA_FW_RUNNING     =   0x11
APPLICATION_FW_RUNNING     =   0x22

APR_CIRCUIT = 0x03

SUCCESS = 0x59
FAIL = 0x4E

IP_DEFAULT = "192.168.1.101"  # Default IP for APR
PORT_DEFAULT = 1111           # Default port for APR
Identify = 101  # Default IP for APR

def wait_for_enter():   
    while True:
        user_input = input("\n>>> Press Enter to start flashing...")
        if user_input == "":
            break
        else:
            print("-> Please press Enter to continue...")
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
        Identify = 101
    
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
                return HOST_INPUT, PORT_INPUT, Identify
            else:
                print(f"-> Ping to {HOST_INPUT} failed.")
                # return False
                
            time.sleep(1)  # Wait for 1 second before retrying
    except Exception as e:
        print(f"-> Error pinging {HOST_INPUT}: {e}")
        return False, False, False
    
# ======================================================================================================
def sendto_APR(data_send:bytearray, UDP_SOCKET):
    UDP_SOCKET.socket.sendto(data_send, (UDP_SOCKET.host, UDP_SOCKET.port))
    
# ======================================================================================================
def build_reset_APR()->bytearray:
    data_reset = bytearray(12)
    data_reset[0] = 0xAB
    data_reset[1] = 0xCD
    data_reset[2] = 0xA0  # Command for reset
    for i in range(3, 11):  # Fill bytes 2-10
        data_reset[i] = 0xFE  # Fill with 0xFE
    data_reset[11] = crc8(data_reset, len(data_reset))  # Calculate CRC for the message
    return data_reset

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
def build_start_mess_bootFota_process(Identify: int, addr_start, addr_end)->bytearray:
    mess_start_boot = bytearray(12)
    
    mess_start_boot[0] = Identify                 
    mess_start_boot[1] = 12                        
    mess_start_boot[2] = CMD_START_FLASHING        
    mess_start_boot[3] =  (addr_start >> 24)  & 0xFF                  
    mess_start_boot[4] =  (addr_start >> 16)  & 0xFF                        
    mess_start_boot[5] =  (addr_start >> 8)  & 0xFF                           
    mess_start_boot[6] =  (addr_start)  & 0xFF                           
    mess_start_boot[7] =  (addr_end >> 24)  & 0xFF                     
    mess_start_boot[8] =  (addr_end >> 16)  & 0xFF                        
    mess_start_boot[9] =  (addr_end >> 8)  & 0xFF                          
    mess_start_boot[10] = (addr_end)  & 0xFF                        
    mess_start_boot[11] = crc8(mess_start_boot, mess_start_boot[1])  
    
    return mess_start_boot  

# ======================================================================================================
def receive_startBootFota_response(UDP_SOCKET, Identify):
    try:
        data_read, _ = UDP_SOCKET.socket.recvfrom(256)
        
        if len(data_read) < 2:
            print("-> [Error]: Response not enough bytes")
            return False
        
        id_m = data_read[0]
        
        if id_m != Identify:
            print(f"-> [Error] - Unexpected Identify: {id_m} != {Identify}")
            return False
        
        cmd = data_read[2]
        if cmd != CMD_START_FLASHING:
            print(f"-> [Error] - Unexpected Command: {cmd} != {CMD_START_FLASHING}")
            return False
        
        if crc8(data_read, len(data_read)) != data_read[-1]:
            print("-> [Error] - CRC Check Failed !")
            print("-> [Received] - ", " ".join(f"{b:02X}" for b in data_read))
            return False
                  
        print("-> [Received] - ", " ".join(f"{b:02X}" for b in data_read))
        rlt = data_read[3]                  # result
        num_page = data_read[4]
        
        if rlt == SUCCESS:
            print(f"-> [Result] - Erased {num_page} pages on APR. Start Flashing Success !")
            return True
        else:
            print("-> [Result] - Erased Fail. Start Flashing Fail !")

    except socket.timeout:
        print("-> [Timeout] - Receive Response Timeout !")
        return False

# ======================================================================================================
def build_runApp_fw_mess(Identify, version, _date_now, type_circuit)->bytearray:
        mess_run_app = bytearray(10)
        
        mess_run_app[0] = Identify
        mess_run_app[1] = 10
        mess_run_app[2] = CMD_RUN_APP
        
        mess_run_app[3] = version & 0xFF
        
        mess_run_app[4] = _date_now.day & 0xFF
        mess_run_app[5] = _date_now.month & 0xFF
        mess_run_app[6] = (_date_now.year>>8) & 0xFF
        mess_run_app[7] = _date_now.year & 0xFF
        mess_run_app[8] = type_circuit
        
        mess_run_app[mess_run_app[1]-1] = crc8(mess_run_app, mess_run_app[1])
        
        return mess_run_app
        
# ======================================================================================================
def receive_runApp_fw_mess(UDP_SOCKET, ID_master):
    try:
        data_read, _ = UDP_SOCKET.socket.recvfrom(256)
        
        if len(data_read) < 2:  # Check if the response is too short
            print("-> [Error]: Response not enough bytes")
            return False
 
        id_m = data_read[0]
        if id_m != ID_master:
            print(f"-> [Error] - Unexpected Identify: {id_m} != {ID_master}")
            return False
        
        cmd = data_read[2]
        if cmd != CMD_RUN_APP:
            print(f"-> [Error] - Unexpected Command: {cmd} != {CMD_RUN_APP}")
            return False
        
        if crc8(data_read, len(data_read)) == data_read[-1]:
            print("-> [Received] - ", " ".join(f"{b:02X}" for b in data_read))
            rlt = data_read[3]

            if rlt == SUCCESS:
                # print(f"-> Send Command Run Application Fw on Master {ID_master_input} SUCCESS !")
                return True
            else:
                # print(f"-> Send Command Run Application Fw on Master {ID_master_input} FAILURE !")
                return False
        else:
            print("-> [Error] - CRC Check Failed !")
            return False

    except socket.timeout:
        print("-> Timeout Response !")
    
# ======================================================================================================
def build_mess_run_bootloader_APR(Identify: int) -> bytearray:
    runFOTA_mess = bytearray(12)
    
    runFOTA_mess[0] = 0xAB
    runFOTA_mess[1] = 0xCD
    runFOTA_mess[2] = CMD_RUN_BOOTLOADER  # Command for request
    runFOTA_mess[3] = 0xB6
    runFOTA_mess[4] = 0xB7
    
    for i in range(5, 11):
        runFOTA_mess[i] = 0xFE
    runFOTA_mess[11] = crc8(runFOTA_mess, 12)  # Calculate CRC for the message
    
    return runFOTA_mess

# ======================================================================================================
def receive_runBootloader_response(UDP_SOCKET, Identify):
    try:
        data_read, _ = UDP_SOCKET.socket.recvfrom(256)
        
        if len(data_read) < 2:  # Check if the response is too short
            print("-> [Error]: Response not enough bytes")
            return False
        
        id_m = data_read[0]
        if id_m != Identify:
            print(f"-> [Error] - Unexpected Identify: {id_m} != {Identify}")
            return False
        
        cmd = data_read[2]
        if cmd != CMD_RUN_BOOTLOADER:
            print(f"-> [Error] - Unexpected Command: {cmd} != {CMD_RUN_BOOTLOADER}")
            return False
        
        # Kiểm tra CRC và byte phản hồi hợp lệ
        if crc8(data_read, len(data_read)) == data_read[-1]:           
            print("-> [Received] - ", " ".join(f"{b:02X}" for b in data_read))
            
            if data_read[3] == SUCCESS:
                print("-> [Result] - Run Bootloader APR Success !")
                return True
            else:
                print("-> [Result] - Run Bootloader APR Fail !")
                return False
        else:
            print("-> [Error] - CRC Check Failed !")
            return False

    except socket.timeout:
        print("-> [Timeout] - Receive Response Timeout !")
        return False
    
#######################################################################################################
#######################################################################################################
#######################################################################################################
#######################################################################################################
def reset_APR(udp_params):
    print("\n>>>>>>>>> Resetting APR...")
    
    msg_sent = build_reset_APR()
    
    sendto_APR(msg_sent, udp_params)
    
    time.sleep(0.001)  # Wait for 1 ms
    
    try:
        data_rec, _ = udp_params.socket.recvfrom(1024)
        
        if len(data_rec) <= 1:
            print("-> [Error]: Response too short")
            return False
        
        if data_rec == msg_sent:
            print("-> Reset OK")
            return True  # Exit the loop if reset is successful
            
    except socket.timeout:
        print("-> Timeout. Can not reset APR")
        
    return False

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
def start_bootFota_process(Identify, UDP_SOCKET={}, addr_start=0, addr_end=0, retry=100):
    # Send start boot command to Master ------------------------------------------------------------
    print(f"\n>>>>>>>>>>>>>> START BOOT FOTA PROCESS ON APR "
          f"HOST '{UDP_SOCKET.host}', PORT '{UDP_SOCKET.port}'\n") 
    time.sleep(1)
    
    mess_start = build_start_mess_bootFota_process(Identify, addr_start, addr_end)
        
    while retry>0:
        sendto_APR(mess_start, UDP_SOCKET)
        print("-> [Sent] - ", " ".join(f"{b:02X}" for b in mess_start))
        
        time.sleep(0.01)
        
        result = receive_startBootFota_response(UDP_SOCKET, Identify)
        
        if result:
            print(f"-> [Result] - Start Flashing from {hex(addr_start)} to {hex(addr_end)} !")
            return True
        else:
            retry -= 1
            
        time.sleep(0.5)
    print(f"-> [Result] - Start Flashing Process on APR Fail !")
    return False

# ======================================================================================================    
def flashing_master_process(Identify, UDP_SOCKET={}, _list_hex_data=[], retry=10):
    print(f"\n>>>>>>>>>>>>>> FLASHING  PROCESS ON APR {Identify}, "
          f"HOST '{UDP_SOCKET.host}', PORT '{UDP_SOCKET.port}'\n") 
    time.sleep(1)
    cnt_line_data = 0   
    cnt_error = 0
    start_flash_t = time.time()
    data_already_updated = 0
    while cnt_line_data < len(_list_hex_data):    
        lenData = len(_list_hex_data[cnt_line_data]['data'])    # length of data to flash
        mess_flash_data = bytearray(lenData+8)  # 8 bytes for header and CRC
        
        mess_flash_data[0] = Identify    # Identify APR, 4 bits
        mess_flash_data[1] = lenData+8  # Total length of message
        mess_flash_data[2] = CMD_FLASHING   # Command for flashing
        
        mess_flash_data[3] = (_list_hex_data[cnt_line_data]['address'] >> 24) & 0xFF    # address to flash  
        mess_flash_data[4] = (_list_hex_data[cnt_line_data]['address'] >> 16) & 0xFF    # address to flash
        mess_flash_data[5] = (_list_hex_data[cnt_line_data]['address'] >> 8) & 0xFF   # address to flash
        mess_flash_data[6] = (_list_hex_data[cnt_line_data]['address'] >> 0) & 0xFF   # address to flash
        
        for j in range(0, len(_list_hex_data[cnt_line_data]['data'])):          # data to flash
            mess_flash_data[j+7] = _list_hex_data[cnt_line_data]['data'][j]
            
        start_send = time.time()
        mess_flash_data[mess_flash_data[1]-1] = crc8(mess_flash_data, mess_flash_data[1])
    
        sendto_APR(mess_flash_data, UDP_SOCKET)    
        # print("-> [Sent] - ", " ".join(f"{b:02X}" for b in mess_flash_data))
    
        time.sleep(0.001)
        
        try:
            data_read, _ = UDP_SOCKET.socket.recvfrom(256)
            
            if len(data_read) < 2:
                print("-> [Error]: Response not too short bytes")
            
            id_m = data_read[0]
            
            if id_m != Identify:
                print(f"-> [Error] - Unexpected Identify: {id_m} != {Identify}")
                cnt_error+=1
                continue
                
            cmd = data_read[2]
            if cmd != CMD_FLASHING:
                print(f"-> [Error] - Unexpected Command: {cmd} != {CMD_FLASHING}")
                cnt_error+=1
                continue

            if crc8(data_read, len(data_read)) == data_read[-1]:
                # print("-> Data rec:", " ".join(f"{b:02X}" for b in data_read))
                
                rlt = data_read[3]
                num_byte = data_read[4]
   
                if rlt == SUCCESS:
                    data_already_updated += lenData  
                    # print("OK", end='-')
                    ratio = cnt_line_data*100/len(_list_hex_data)
                    # if ratio % 10 == 0 or data_already_updated == len(_list_hex_data):
                    #     print(f"-> [Result] - Flashing {data_already_updated} bytes Success ({round((time.time()-start_send)*1000,1)}ms, "
                    #          f"{round(ratio,2)}%)")
                         
                    print(f"-> [Result] - Flashed {num_byte} bytes Success ({round((time.time()-start_send)*1000,1)}ms, "
                             f"{round(ratio,1)}%)")
                    cnt_line_data+=1
                    time.sleep(0.001)
                else:
                    print(f"-> [Result] - Flashing {num_byte} bytes Fail !")
                    cnt_error+=1
            else:
                print("-> [Error] - CRC Check Failed !")
                print("-> [Received] - ", " ".join(f"{b:02X}" for b in data_read))
                cnt_error+=1

        except socket.timeout:
            print("-> [Timeout] - Receive Response Timeout !")
            cnt_error+=1
        
        if cnt_error == 10:
            print("\n-> [Error] - Flashing BROKEN and FAIL!\n")
            return False
        
        time.sleep(0.001)
        # wait_for_enter()

    print(f"\n-> FINISH FLASHING SUCCESS ({round(time.time()-start_flash_t,3)}s) !\n")
    return True
 
# ======================================================================================================
def run_newApplication_fw_APR(Identify, UDP_SOCKET, addr_start, new_version, circuit, retry=10):
    print(f"\n>>>>>>>>>>>>>> RUN APPLICATION FIRMWARE ON APR "
          f"HOST '{UDP_SOCKET.host}, PORT '{UDP_SOCKET.port}'\n")    
    
    date_now = datetime.now()
        
    mess_run_app = build_runApp_fw_mess(Identify, new_version, date_now, circuit)

    while retry>0:   
        sendto_APR(mess_run_app, UDP_SOCKET)    
        print("-> [Sent] - ", " ".join(f"{b:02X}" for b in mess_run_app))
    
        time.sleep(0.01)
    
        result = receive_runApp_fw_mess(UDP_SOCKET, Identify)
        
        if result:
            print(f"-> [Result] - Run New App Firmware on APR new version {round(new_version/10,1)}")
            return True
            
        time.sleep(0.5)
        
    print(f"-> [Result] - Run New App Firmware on APR Fail !")
    return False 

# ======================================================================================================   
def run_bootloader_APR(Identify, UDP_SOCKET={}, retry=5):
    # Send FOTA boot command to Master ------------------------------------------------------------
    print(f"\n>>>>>>>>>>>>>> RUN BOOTLOADER ON APR "
          f"HOST '{UDP_SOCKET.host}', PORT '{UDP_SOCKET.port}'\n")
    time.sleep(1.5)
    mess_fota = build_mess_run_bootloader_APR(Identify)
        
    while retry>0:
        sendto_APR(mess_fota, UDP_SOCKET)
        print("-> [Sent] - ", " ".join(f"{b:02X}" for b in mess_fota))
        
        time.sleep(0.01)
        
        result = receive_runBootloader_response(UDP_SOCKET, Identify)
        
        if result:
            return True
        else:
            retry -= 1
            
        time.sleep(0.5)
    print(f"-> [Result] - Run Boot FOTA Program on APR Fail !")
    return False

# ======================================================================================================     
def analysisHex_APR(type="halfword"):
    # Analysing hex file--------------------------------------------------------------------
    print("\n>>>>>>>>>>>>>> ANALYSING HEX FILE   \n")
    
    # path_firmware = "E:\DEV_SPACE__\Chute_Master_FW_developing\Chute_Master_FW_v4.1_KV3_KV1_Developing\MDK-ARM\Chute_Master_Firmware\Chute_Master_Firmware.hex"
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # hex_folder = os.path.join(current_dir, "CodeHex_APR")
    # if not os.path.exists(hex_folder):
    #     print(f"-> [Error] - Folder '{hex_folder}' does not exist.")
    #     exit(1)
    
    # hex_files = [f for f in os.listdir(hex_folder) if os.path.isfile(os.path.join(hex_folder, f))]
    # if not hex_files:
    #     print(f"-> [Error] - No files found in '{hex_folder}'.")
    #     exit(1)
        
    # print("-> [Result] - Available HEX files in 'CodeHex_APR':")
    # for idx, fname in enumerate(hex_files):
    #     print(f"        {idx+1}: {fname}")
    # while True:
    #     try:
    #         choice = int(input("> Select a file by number: "))
    #         if 1 <= choice <= len(hex_files):
    #             path_firmware = os.path.join(hex_folder, hex_files[choice-1])
    #             break
    #         else:
    #             print("-> [Error] - Invalid selection. Try again.")
    #     except ValueError:
    #         print("-> [Error] - Please enter a valid number.")

    # path_firmware = "E:\DEV_SPACE__\APR_Lora\APR_FW_v3.6_useForTesBootFOTA\MDK-ARM\AP_Board_v3.1_Config\AP_Board_v3.hex"
    
    while True:
        inp_fw = str(input("\n> Input Firmware Path: "))
        
        # if inp_fw == "":    
        #     print("-> Default Firmware Path: E:\DEV_SPACE__\APR_Lora\APR_FW_v3.7_developing\MDK-ARM\AP_Board_v3.1_Config\AP_Board_v3.hex")
        #     path_firmware = "E:\DEV_SPACE__\APR_Lora\APR_FW_v3.7_developing\MDK-ARM\AP_Board_v3.1_Config\AP_Board_v3.hex"
        # else:
        path_firmware = inp_fw
        
        if not os.path.exists(path_firmware):
            print(f"-> [Error] - File '{path_firmware}' does not exist.")
        else:
            break
        
    path_firmware = "E:\DEV_SPACE__\APR_Lora\APR_FW_v3.7_developing\MDK-ARM\AP_Board_v3.1_Config\AP_Board_v3.hex"
    
    # path_firmware = ""E:\DEV_SPACE__\APR_Lora\APR_FW_v3.7\MDK-ARM\AP_Board_v3.1_Config\AP_Board_v3.hex""
    num_Line, list_data_flash, size_Hex, addr_start, addr_end = analysis_hex(path_firmware, type)

    print(f"-> [INFOR NEW FIRMWARE] - [{type}]")
    print(f"->                      - Number Line: {num_Line}")
    print(f"->                      - Address start Flashing: {hex(addr_start)}")
    print(f"->                      - Address end Flashing: {hex(addr_end)}")
    print(f"->                      - Size program: {size_Hex}", " bytes = ", str(round(size_Hex/1024,2)) + "kB")
    
    return list_data_flash, addr_start, addr_end

#######################################################################################################
#######################################################################################################
#######################################################################################################
#######################################################################################################

if __name__ == "__main__":
    print("\n-------------> START BOOTING FOTA PROGRAM FOR ACCESS POINT ROBOT <-----------\n")
    
    list_hex_data, addr_start_flash, addr_end_flash = analysisHex_APR("word")
        
    HOST_INPUT, PORT_INPUT, Identify = check_connection()
        
    if not HOST_INPUT or not PORT_INPUT:
        print("-> Unable to establish connection. Exiting...")
        exit(1)
        
    while True:
        try:
            newVersion = int(input("\n> Input new APR Application Version: "))
            if newVersion < 0 or newVersion > 99:  
                print("-> [Error] - Version must be between 0 and 99. Please try again.")
                continue
            else:
                print(f"-> New Version: {newVersion}")
                break 
        except ValueError:
            print("-> [Error] - Invalid input. Please enter a number between 0 and 99.")
            continue
    
    
    time.sleep(1)
        
    # Tạo socket UDP
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(1)  # Timeout cho việc nhận dữ liệu
    
    udp_params = UdpConnection(udp_socket, HOST_INPUT, PORT_INPUT)
    
    # while not reset_APR(udp_params):
    #     print("-> Retrying APR reset...")
    #     time.sleep(1)
        
    # print("-> Waiting 5s for APR to reset...")
    # timedown = 5
    # while timedown > 0:
    #     print(f"-> {timedown} s remaining...")
    #     time.sleep(1)
    #     timedown -= 1

    while True:
        mode_current = request_status_APR(udp_params)
        
        while mode_current != BOOTFOTA_FW_RUNNING:       # check bootloader mode
            rlt = run_bootloader_APR(Identify, udp_params, retry=5)
            
            if rlt == False:
                continue
            
            print("\n>>>>>>>>>>>>>> WAIT MCU RESET AND RUNNING BOOT FOTA POROGRAM.... \n") 
            
            timedown = 5
            print(f"-> Waiting {timedown}s for APR to reset...")
            while timedown > 0:
                print(f"-> {timedown} s remaining...")
                time.sleep(1)
                timedown -= 1
            mode_current = request_status_APR(udp_params, retry=5)
            if mode_current == BOOTFOTA_FW_RUNNING:
                print("\n-> [Result] - APR is in Bootloader mode. Ready to flash new application firmware...\n")
            
                
        wait_for_enter()
        # -------------------------------------------------------------------------------------------
        
        rlt = start_bootFota_process(Identify, udp_params, addr_start_flash, addr_end_flash, retry=10)
        if rlt == False:
            print("\nxxxxxxxxx SOMETHINGS ERROR - TRY AGAIN xxxxxxxxxxxxx\n")
            time.sleep(3)
            break
        
        # wait_for_enter()
        time.sleep(1)
        
        # -------------------------------------------------------------------------------------------
        
        rlt = flashing_master_process(Identify, udp_params, list_hex_data)
        
        if rlt == False:
            print("\nxxxxxxxxx SOMETHINGS ERROR - TRY AGAIN xxxxxxxxxxxxx\n")
            time.sleep(3)
            break
        
        time.sleep(2)        
        
        # -------------------------------------------------------------------------------------------
        rlt = run_newApplication_fw_APR(Identify, udp_params, addr_start_flash, newVersion, APR_CIRCUIT)
        
        if rlt == False:
            print("\nxxxxxxxxx SOMETHINGS ERROR - TRY AGAIN xxxxxxxxxxxxx\n")
            time.sleep(3)
            break
        
        time.sleep(1)
        print("\n>>>>>>>>>>>>>> WAIT MCU RESET AND RUNNING NEW APPLICATION FW.... \n") 
        timedown = 7
        print(f"-> Waiting {timedown}s for APR to reset...")
        while timedown > 0:
            print(f"-> {timedown} s remaining...")
            time.sleep(1)
            timedown -= 1
            
        time.sleep(2)
        mode_current = request_status_APR(UDP_SOCKET=udp_params)
        
        if mode_current == APPLICATION_FW_RUNNING:
            print(f"\n======> UPDATED NEW APPLICATION ON APR "
                f"HOST '{HOST_INPUT}', PORT '{HOST_INPUT}' SUCCESS TOTALLY :=))\n")
        else:
            print(f"\nxxxxxx> UPDATED NEW APPLICATION ON APR "
                f"HOST '{HOST_INPUT}', PORT '{HOST_INPUT}' FAILURE :=((\n")
            
        break
    
    print("\n                          -------------> CLOSING PROGRAM <-----------\n")

    
    
       
    # Verify Data: 0xe9194b15
    
    
    
        #  print("\n>>>>>>>>>>>>>> VERIFY FLASHED DATA .... \n") 
        # mess_verify = bytearray(8)
        # mess_verify[0] = Identify
        # mess_verify[1] = 9
        # mess_verify[2] = CMD_VERIFY_DATA
        # mess_verify[3] = (addr_start_flash >> 24) & 0xFF
        # mess_verify[4] = (addr_start_flash >> 16) & 0xFF
        # mess_verify[5] = (addr_start_flash >> 8) & 0xFF
        # mess_verify[6] = (addr_start_flash >> 0) & 0xFF
        # mess_verify[7] = crc8(mess_verify, 8)
        
        # sendto_APR(mess_verify, udp_params)
        # print("-> [Sent] - ", " ".join(f"{b:02X}" for b in mess_verify))
        # time.sleep(0.001)
        
        # try:
        #     data_read, _ = udp_params.socket.recvfrom(256)
            
        #     if len(data_read) < 2:
        #         print("-> [Error]: Response not enough bytes")
        #         break
            
        #     id_m = data_read[0]
        #     if id_m != Identify:
        #         print(f"-> [Error] - Unexpected Identify: {id_m} != {Identify}")
        #         break
            
        #     cmd = data_read[2]
        #     if cmd != CMD_VERIFY_DATA:
        #         print(f"-> [Error] - Unexpected Command: {cmd} != {CMD_VERIFY_DATA}")
        #         break
            
        #     if crc8(data_read, len(data_read)) == data_read[-1]:
        #         print("-> [Received] - ", " ".join(f"{b:02X}" for b in data_read))
                
        #         rlt = data_read[3]
                
        #         print(f"-> [Result] - Verify Data: {hex((data_read[4]<<24)|(data_read[5]<<16)|(data_read[6]<<8)|data_read[7])} ")
        #     else:
        #         print("-> [Error] - CRC Check Failed !")
        
        # except socket.timeout:
        #     print("-> [Timeout] - Receive Response Timeout !")
        
        
        
        
        
        
        
        
        
        # break