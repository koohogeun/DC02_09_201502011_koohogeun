import socket
import os
import hashlib
import time
def zero_pad( Str , val ):
    count = val - len(Str);
    for i in range(0, count):
        Str = Str + "0";
    return Str

def resend(socket,data,addr):
    while True:
        try:
            socket.sendto(data, addr)
            res = socket.recv(1)
            return res
        except Exception as e:
            print(e)

def b_zero_pad( btStr , val ):
    count = val - len(btStr);
    for i in range(0, count):
        btStr = btStr + bytes([0]);
    return btStr

def conv_data( data ):
    res = 0
    t = 0
    for i in range(0, len(data), 20):
        for j in range(0, 20):
            t += data[i] << (8*j)
        res += t
    while True:
        if ( res >> 160 ) == 0:
            break
        val = ( res >> 160 ) + ( res & 0xffffffffffffffffffffffffffffffffffffffff )
        res = res >> 160
    return res
    
def intToByte( hexStr ):
    res = bytes()
    while hexStr != 0:
        res += bytes([hexStr & 0xff])
        hexStr = hexStr >> 8
    return res

def h_gen( data ):
    return intToByte(0xffffffffffffffffffffffffffffffffffffffff - conv_data( data ))

def get_ip_address(socket):
    socket.connect(("8.8.8.8", 80))
    return socket.getsockname()[0]

socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket.settimeout(1)
#file_name = input("Input your file name : ")
file_name_ori = 'accu.png'
if len(file_name_ori) > 11:
    print('File name is too long to be transferred.')
    exit()
f = open(file_name_ori,'rb')
seq_num = 0
Type = bytes([0])
file_size = os.path.getsize(file_name_ori)
h_file_size = intToByte(file_size)
if len(h_file_size) > 4:
    print('File capacity is too large to be transferred.')
    exit()
file_name = zero_pad(file_name_ori ,11)
bez = h_file_size
h_file_size = b_zero_pad(h_file_size ,4)
l = f.read(1024)
h_hash = h_gen(l)
header = h_hash + Type + file_name.encode() + h_file_size + l



addr = ('',9000)
print("Send File Info(file Name, file Size, seqNum)to Server...")
header_ack = resend(socket, header, addr)
print("Start File send")
acc = len(l);
print("current_size / total_size = %d/%d, %.3f%%"%(acc,file_size,100*acc/file_size))
seq = bytes([0])
pre_sed = bytes([0])
while True:
    seq = bytes([0]) if seq[0] == 1 else bytes([1])
    l = f.read(1024)
    h_hash = h_gen(l+seq)
    h_hash = b_zero_pad(h_hash,20)
    sed = (h_hash + seq + l)
    recv_ack = resend(socket, sed, addr)
    if acc >= file_size:
        print('end')
        for i in range(0,100):
            socket.sendto(sed, addr)
            time.sleep(0.1)
            if i == 99:
                print('end')
                break
    if recv_ack[0] != seq[0]:
        print('Nak')
        while True:
            recv_ack = resend(socket, pre_sed, addr)
            if recv_ack[0] == seq[0]:
                break
    acc += len(l);
    print("current_size / total_size = %d/%d, %.3f%%"%(acc,file_size,100*acc/file_size))
    seq = recv_ack
    pre_sed = sed
f.close()
print("ok")
print("file_send_end")
print("The md5 value of the sent file is : %s"%(hashlib.md5(open(file_name_ori,'rb').read()).hexdigest()))
