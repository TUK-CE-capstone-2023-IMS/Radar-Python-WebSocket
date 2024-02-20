import socket
import struct
import tensorflow as tf
import numpy as np
from tensorflow.keras.models import load_model
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib

fig = plt.figure(figsize=(12, 6))
ax = fig.add_subplot(111, projection='3d')
ax.set_title('3D Joint Data Visualization')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.legend()
matplotlib.use('TkAgg')

SRS_SERVER_PORT = 29172 # 레이더 기본 포트
SRS_MAX_POINT = 2000
SRS_MAX_TARGET = 250

# Target status
SRS_TARGET_STATUS = {  
    0: "STANDING",
    1: "LYING",
    2: "SITTING",
    3: "FALL",
    4: "UNKNOWN"
}

class SRS_POINT_INFO:
    def __init__(self, data):
        self.posX, self.posY, self.posZ, self.doppler, self.power = struct.unpack('fffff', data)

class SRS_TARGET_INFO:
    def __init__(self, data):
        self.posX, self.posY, self.status, self.id, *self.reserved = struct.unpack('ffIIIfff', data)

def read_packet(sock):
    header = sock.recv(50000)
    if not header:
        return None, -1

    if len(header) < 20:  # 헤더의 길이가 충분하지 않으면 종료
        return None, -1

    packet_size = struct.unpack('I', header[16:20])[0]
    data = sock.recv(packet_size)
    if not data:
        return None, -1

    return data, packet_size


def parse_data(data):
    if data is None:  # 데이터가 None일 경우
        return [], []

    if len(data) < 16:  # 데이터 길이가 충분하지 않으면 종료
        return [], []

    magic_word = struct.unpack('4H', data[:8])
    frame_count = struct.unpack('I', data[8:12])[0]
    point_num = struct.unpack('I', data[12:16])[0]
    print(f"Frame: {frame_count}, Points: {point_num}")

    points = []
    offset = 16
    for _ in range(point_num):
        if len(data) - offset < 20: 
            break 
        point_data = data[offset:offset+20]
        point = SRS_POINT_INFO(point_data)
        points.append([point.posX, point.posY, point.posZ])  # X, Y, Z 좌표만을 리스트에 추가
        offset += 20

    targets = []
    if len(data) - offset >= 32:
        target_num = struct.unpack('I', data[offset:offset+4])[0]
        offset += 4
        for _ in range(target_num):
            if len(data) - offset < 32:  
                break  
            target_data = data[offset:offset+32]
            target = SRS_TARGET_INFO(target_data)
            targets.append(target)
            offset += 32

    return points, targets

def print_data(points, targets, count):   
    point_array = []
    num_points = len(points)
    for i in range(500):
        if i < num_points:
            x, y, z = points[i]
        else:
            x, y, z = 0.0, 0.0, 0.0
        point_array.append([x, y, z])
    
    print("Points:")
    point_array = np.array(point_array)  # 리스트를 넘파이 배열로 변환
    point_array = np.expand_dims(point_array, axis=0)  # 새로운 축을 추가하여 (1, 500, 3)으로 만듦
    print(np.shape(point_array))
    print()  # 빈 줄 추가

    model = load_model('C:/Users/sang1/Desktop/ps/CNN_Model_Skeleton.h5')
    # 모델 예측
    predictions = model.predict(point_array)
    print(predictions)  # 예측된 데이터의 모양 확인
    sendToUnity(predictions)

def sendToUnity(lmList):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverAddressPort = ("127.0.0.1", 5051)
    # 스켈레톤 표현을 위해 lmList의 값에 가중치 곱해줌
    lmList = np.array(lmList) * 1000
    # lmList를 1차원 리스트로 변환
    flattened_list = lmList.flatten().tolist()
    
    sock.sendto(str.encode(str(flattened_list)), serverAddressPort)

def main():
    COUNT = -1
    source_ip = "192.168.30.1"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((source_ip, SRS_SERVER_PORT))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1000000)
        print("Connected.")

        while True:
            COUNT = COUNT + 1 
            print(COUNT)
            data, packet_size = read_packet(sock)
            if packet_size < -1:
                print("Connection closed.")
                break
            elif packet_size == 0:
                continue
            points, targets = parse_data(data)
            print_data(points, targets,COUNT) 

if __name__ == "__main__":
    main()
