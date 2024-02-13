import socket
import struct

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
    header = sock.recv(36)
    if not header:
        return None, -1

    packet_size = struct.unpack('I', header[16:20])[0]
    data = sock.recv(packet_size)
    if not data:
        return None, -1

    return data, packet_size

def parse_data(data):
    magic_word = struct.unpack('4H', data[:8])
    frame_count = struct.unpack('I', data[8:12])[0]
    point_num = struct.unpack('I', data[12:16])[0]
    print(f"Frame: {frame_count}, Points: {point_num}")

    points = []
    offset = 16
    for _ in range(point_num):
        point_data = data[offset:offset+20]
        if len(point_data) < 20:
            break 
        point = SRS_POINT_INFO(point_data)
        points.append(point)
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


def print_data(points, targets):
    for i, point in enumerate(points):
        print(f"Point {i}: X={point.posX}, Y={point.posY}, Z={point.posZ}, Doppler={point.doppler}, Power={point.power}")
    
    for i, target in enumerate(targets):
        status = SRS_TARGET_STATUS.get(target.status, "UNKNOWN")
        print(f"Target {i}: ID={target.id}, X={target.posX}, Y={target.posY}, Status={status}")

def main():
    source_ip = "192.168.30.1"
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((source_ip, SRS_SERVER_PORT))
        print("Connected.")

        while True:
            data, packet_size = read_packet(sock)
            if packet_size < -1:
                print("Connection closed.")
                break
            elif packet_size == 0:
                continue

            points, targets = parse_data(data)
            print_data(points, targets)

if __name__ == "__main__":
    main()