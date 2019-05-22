import socket
import os
import hashlib

def invers_zero_pad( Str ):
	for i in range(len(Str)-1, 0, -1):
		if Str[i] != '0':
			Str = Str[0:i+1]
			return Str

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

def h_gen( data ):
	return 0xff - conv_data( data )

def BytetoInt( byteStr ):
	res = 0
	for i in range(0, len(byteStr)):
		res += byteStr[i] << (8 * i)
	return res

def match( b_data, h_val ):
	ans = conv_data( b_data )  + h_val
	if ans == 0xffffffffffffffffffffffffffffffffffffffff:
		return False
	else:
		return True

def get_ip_address(server_socket):
    server_socket.connect(("8.8.8.8", 80))
    return server_socket.getsockname()[0]

if not os.path.isdir('received_data'):
	os.mkdir('received_data')
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.settimeout(1)
server_socket.bind(('localhost',9000))
while True:
	try:
		data, addr = server_socket.recvfrom(20 + 1 + 11 + 4 + 1024)
		server_socket.sendto(bytes([0]), addr)
		break
	except Exception as e:
		print('* TimeOut!! ***')
print('file recv start from %s'%(addr[0]))
if data[20] == 1:
	print('File header is crashed.')
	exit()
header_hash = BytetoInt(data[0:20])
file_name = invers_zero_pad(data[21:32].decode())
file_size = BytetoInt(data[32:36])
head_data = data[36:]
print('File Name : %s'%(file_name))
print('File Size : %d'%(file_size))
acc = len(head_data);
if match( head_data, header_hash ):
	print('Data is corrupt')
	exit()
print("current_size / total_size = %d/%d, %.3f%%"%(acc,file_size,100*acc/file_size))
ack = bytes([data[20]])
with open('./received_data/' + file_name, 'wb') as f:
	f.write(head_data)
	while acc != file_size:
		ack = bytes([0]) if ack[0] == 1 else bytes([1])
		while True:
			try:
				data = server_socket.recv(20 + 1 + 1024)
				break
			except Exception as e:
				server_socket.sendto(ack, addr)
				print('* TimeOut!! ***')
		if not data:
			break
		if ack[0] != data[20]:
			print('Nak')
			while True:
				try:
					data = server_socket.recv(20 + 1 + 1024)
					if ack[0] == data[20]:
						break
				except Exception as e:
					server_socket.sendto(ack, addr)
					print('* TimeOut!! ***')
		server_socket.sendto(ack, addr)
		data_hash = BytetoInt(data[0:20])
		data = data[21:]
		f.write(data)
		if match( data+bytes([data[20]]), data_hash ):
			print('Data is corrupt')
			exit()
		acc += len(data)
		if  acc == file_size:
			print("current_size / total_size = %d/%d, %.3f%%"%(acc,file_size,100*acc/file_size))
			break
		print("current_size / total_size = %d/%d, %.3f%%"%(acc,file_size,100*acc/file_size))
print("The md5 value of the received file is : %s"%(hashlib.md5(open('./received_data/' + file_name,'rb').read()).hexdigest()))
f.close()
