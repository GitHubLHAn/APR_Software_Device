
# def parse_intel_hex_line(line):
#     """Phân tích một dòng HEX theo chuẩn Intel HEX."""
#     if not line.startswith(":"):
#         return None

#     try:
#         line = line.strip()
#         length = int(line[1:3], 16)
#         address = int(line[3:7], 16)
#         record_type = int(line[7:9], 16)
#         data = [int(line[i:i+2], 16) for i in range(9, 9 + length * 2, 2)]
#         checksum = int(line[9 + length * 2:11 + length * 2], 16)
        
#         return {
#             "length": length,
#             "address": address,
#             "type": record_type,
#             "data": data,
#             "checksum": checksum,
#             "raw_line": line
#         }
#     except Exception as e:
#         print(f"Lỗi dòng: {line.strip()} — {e}")
#         return None

# def parse_hex_file(filename):
#     memory = {}              # address -> byte
#     high_addr = 0            # high 16-bit address

#     with open(filename, 'r') as f:
#         for line in f:
#             line = line.strip()

#             if not line.startswith(':'):
#                 continue

#             ll   = int(line[1:3], 16)
#             addr = int(line[3:7], 16)
#             rect = int(line[7:9], 16)
#             data = line[9:9 + ll * 2]

#             # -------- Extended Linear Address --------
#             if rect == 0x04:
#                 high_addr = int(data, 16) << 16

#             # -------- Data Record --------
#             elif rect == 0x00:
#                 base_addr = high_addr + addr

#                 for i in range(ll):
#                     byte = int(data[i*2:i*2+2], 16)
#                     memory[base_addr + i] = byte

#             # -------- End Of File --------
#             elif rect == 0x01:
#                 break

#     return memory

# def merge_data_pairs(list_halfword):
#     list_hex_word = []
    
#     # length = len(list_halfword)
    
    

#     for i in range(0, len(list_halfword),2):
#         if i + 1 < len(list_halfword):  # đảm bảo có cặp
#             merged_item = {
#                 "address": list_halfword[i]["address"],
#                 "data": list_halfword[i]["data"] + list_halfword[i + 1]["data"]
#             }
#         else:
#             merged_item = {
#                 "address": list_halfword[i]["address"],
#                 "data": list_halfword[i]["data"]
#             }
#         list_hex_word.append(merged_item)

#     return list_hex_word



# def advanced_analysis_hex(path_fw, type="halfword"):
#     print(f"\n-> Path FiwmWare: {path_fw}\n")
        
#     lines_hexFile = parse_hex_file(path_fw)

#     num_Line_hexFile = len(lines_hexFile)

#     size_off_dataHex = 0
#     list_halfword_data = []

#     for i, line in enumerate(lines_hexFile):
#         if line['type'] == 4:
#             # print(line)
#             phan_mo_rong_hex = line['data'][0]<<8 | line['data'][1]
#             # print(f"-> Phần mở rộng: {hex(phan_mo_rong_hex)}")

#         if line['type'] == 0:
#             size_off_dataHex += line['length']
#             len_last_data = line['length']
#             list_halfword_data.append({"address" : (phan_mo_rong_hex<<16) | line['address'], "data" : line['data']}) 
            
#     min_address = list_halfword_data[0]['address']
#     max_address = min_address

            
#     for i, line in enumerate(list_halfword_data):
#         if line['address'] > max_address:
#             max_address = line['address']            
#         if line['address'] < min_address:
#             min_address = line['address'] 


#     address_start_data = min_address
#     address_end_data = max_address+len_last_data-1

#     list_word_data = merge_data_pairs(list_halfword_data)
    
#     if type == "word":
#         list_data_flash = list_word_data
#     else:
#         list_data_flash = list_halfword_data

#     return num_Line_hexFile, list_data_flash, size_off_dataHex, address_start_data, address_end_data
   
    
def parse_hex_file(filename):
    memory = {}          # address(str) -> byte(str)
    high_addr = "0000"   # high 16-bit address (HEX STRING)

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().upper()

            if not line.startswith(":"):
                continue

            ll   = line[1:3]      # byte count (string)
            addr = line[3:7]      # offset address (string)
            rect = line[7:9]      # record type (string)
            data = line[9:9 + int(ll, 16)*2]  # ⚠️ chỉ dùng để cắt chuỗi
            # nếu bạn muốn, mình có thể bỏ luôn dòng này và dùng len(data)//2

            # -------- Extended Linear Address (04) --------
            if rect == "04":
                high_addr = data  # ví dụ "0800"

            # -------- Data Record (00) --------
            elif rect == "00":
                # tạo base address bằng GHÉP CHUỖI
                base_addr = high_addr + addr  # ví dụ "0800" + "8000"

                # duyệt từng byte (2 ký tự)
                for i in range(0, len(data), 2):
                    byte_str = data[i:i+2]

                    # địa chỉ = base + index (HEX STRING)
                    # index cũng là HEX STRING
                    index_hex = f"{i//2:04X}"

                    full_addr = base_addr[:-4] + f"{int(base_addr[-4:],16) + int(index_hex,16):04X}"

                    memory[f"{full_addr}"] = f"{byte_str}"

            # -------- End Of File (01) --------
            elif rect == "01":
                break

    return memory

    
    
    
def build_blocks(memory, block):
    """
    memory: {'08008000': '00', '08008001': '80', ...}
    block : 'hw' | 'w' | 'qw'
    return: m_hw | m_w | m_qw (dict, string only)
    """

    if block == "hw":       # half-word
        size = 2
    elif block == "w":      # word
        size = 4
    elif block == "qw":     # quad-word
        size = 16
    elif block == "dqw":       # double-quad-word
        size = 32
    else:
        raise ValueError("block must be hw, w, or qw")

    # sắp xếp theo địa chỉ (string, nhưng đúng vì HEX fixed-length)
    addrs = sorted(memory.keys())

    result = {}
    i = 0
    cnt = 0
    
    while True:
        if i+size <= len(addrs):
            base_addr = addrs[i]
            data = ""

            for j in range(size):
                data += memory[addrs[i + j]]

            result[cnt] = {
                    "addr": base_addr,
                    "size": len(data)//2,
                    "data": data 
            }
            cnt+=1
            i += size
        else:
            if i < len(addrs):
                # xử lý phần còn lại
                base_addr = addrs[i]
                data = ""

                # while i < len(addrs):
                #     data += memory[addrs[i]]
                #     i += 1
                    
                remaining = len(addrs) - i
                base_addr = addrs[i]
                data = ""

                # lấy dữ liệu còn lại
                for _ in range(remaining):
                    data += memory[addrs[i]]
                    i += 1

                # padding thêm 00 cho đủ block
                missing = size - remaining
                data += "00" * missing

                result[cnt] = {
                    "addr": base_addr,
                    "size": len(data)//2,
                    "data": data 
                }
                cnt+=1
            break

    return result
      
    
def get_hex_info(memory):
    addrs = sorted(memory.keys())

    addr_start_str = addrs[0]
    addr_end_str   = addrs[-1]

    addr_start = int(addr_start_str, 16)
    addr_end   = int(addr_end_str, 16)

    size = addr_end - addr_start + 1  # +1 vì tính cả byte cuối

    return {
        "addr_start": addr_start_str,
        "addr_end": addr_end_str,
        "size_hex": f"{size:X}",
        "size_dec": str(size)
    }
    
    
    
    
def advanced_analysis_hex(path_firmware, type="qw"):
    print(f"\n-> Confirmed Path FiwmWare: {path_firmware}\n")
        
    memory = parse_hex_file(path_firmware)

    block_hex = build_blocks(memory, block=type)
    
    infor_hex  = get_hex_info(memory)
    
    size_of_dataHex = int(infor_hex["size_dec"])
    address_start_data = int(infor_hex["addr_start"],16)
    address_end_data = int(infor_hex["addr_end"],16)
    
    
    return block_hex, size_of_dataHex, address_start_data, address_end_data

    # size_off_dataHex = 0
    # list_halfword_data = []

    # for i, line in enumerate(lines_hexFile):
    #     if line['type'] == 4:
    #         # print(line)
    #         phan_mo_rong_hex = line['data'][0]<<8 | line['data'][1]
    #         # print(f"-> Phần mở rộng: {hex(phan_mo_rong_hex)}")

    #     if line['type'] == 0:
    #         size_off_dataHex += line['length']
    #         len_last_data = line['length']
    #         list_halfword_data.append({"address" : (phan_mo_rong_hex<<16) | line['address'], "data" : line['data']}) 
            
    # min_address = list_halfword_data[0]['address']
    # max_address = min_address

            
    # for i, line in enumerate(list_halfword_data):
    #     if line['address'] > max_address:
    #         max_address = line['address']            
    #     if line['address'] < min_address:
    #         min_address = line['address'] 


    # address_start_data = min_address
    # address_end_data = max_address+len_last_data-1

    # list_word_data = merge_data_pairs(list_halfword_data)
    
    # if type == "word":
    #     list_data_flash = list_word_data
    # else:
    #     list_data_flash = list_halfword_data

    # return num_Line_hexFile, list_data_flash, size_off_dataHex, address_start_data, address_end_data
    
    
    
    
    
    
    
    
    
    
if __name__ == "__main__":
     # ------------------- Phan tich file hex ------------------------
    print("\n>>> Phân tích file Hex theo tung byte\n")
    
    path_firmware = input("> Nhập vào đường dẫn file hex: ")
    
    memory = parse_hex_file(path_firmware)
    # print(memory)
    
    with open("mom.txt", "w", encoding="utf-8") as f:
        for addr, value in memory.items():
            f.write(f"{addr} {value}\n")
    
    block_hex = build_blocks(memory, block='qw')    
    print(block_hex)
    
    # with open("w.txt", "w", encoding="utf-8") as f:
    #     for addr, value in block_hex:
    #         f.write(f"{addr:08X} : {value:04X}\n")
    
    # print(f"-> Đã phân tích {num_Line} dòng.")
    
    infor_hex  = get_hex_info(memory)
    print("-> Kích thước chương trình firmware = ", infor_hex["size_dec"], " bytes = ", str(int(infor_hex["size_dec"])/1024) + " kB")
    print("-> Địa chỉ bắt đầu flash: 0x", infor_hex["addr_start"])
    print("-> Địa chỉ kết thúc flash: 0x", infor_hex["addr_end"])

    # print("-> Kích thước chương trình firmware = ", str(size_Hex), " bytes = ", str(size_Hex/1024) + " kB")
