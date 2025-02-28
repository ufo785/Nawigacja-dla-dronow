from pymavlink import mavutil
import time
import socket
import threading
import math


def rotate_drone(connection, yaw_angle):
    
    # zmienia na radiany
    yaw_angle_rad = math.radians(yaw_angle)
    
    msg = connection.mav.command_long_encode(
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_CMD_CONDITION_YAW,
        0, 
        yaw_angle_rad,  # kąt 
        0, 
        0,  
        0, 0, 0, 0  
    )
    connection.mav.send(msg)
    print("obrot")

def establish_connection(connection_string):
    #poczenie z Ardu
    while True:

            connection = mavutil.mavlink_connection(connection_string)
            connection.wait_heartbeat()
            print("Połączono z ArduPilotem")
            return connection


def set_mode(connection, mode):
    #tryb lotu
    mode_mapping = connection.mode_mapping()
    if mode not in mode_mapping:
        return
    mode_id = mode_mapping[mode]
    msg = connection.mav.command_long_encode(
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_CMD_DO_SET_MODE,
        0,
        1,
        mode_id,
        0, 0, 0, 0, 0
    )
    connection.mav.send(msg)

def check_gps_lock(connection):
    
    while True:
        gps = connection.recv_match(type='GPS_RAW_INT', blocking=True)
        if gps.fix_type >= 3:
            break       
        time.sleep(1)

def arm_drone(connection):
    
    msg = connection.mav.command_long_encode(
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, 
        1, 
        0, 0, 0, 0, 0, 0
    )
    connection.mav.send(msg)
    ack = connection.recv_match(type='COMMAND_ACK', blocking=True)
    if ack.result != 0:
        print(f"Problem z wlaczeniem")
        return False
    return True

def takeoff(connection, altitude):
    #start
    msg = connection.mav.command_long_encode(
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        0, 0, 0, 0, 0,
        0,0,
        altitude
    )
    connection.mav.send(msg)
    ack = connection.recv_match(type='COMMAND_ACK', blocking=True)
    if ack.result != 0:
        print(f"nie wystartowal")
        return False
    print("Start zakończony")
    return True

def position_listener(connection):
    #zmiana pozycji drona z mapy
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 5001))
        s.listen(1)
        while True:
            conn, addr = s.accept()
            with conn:
                while True:
                    try:
                        data = conn.recv(1024).decode().strip()
                        if not data:
                            break
                        lat, lon = map(float, data.split(","))
                        print(f"Pozycja tryb manual: Lat {lat}, Lon {lon}, Alt 10")
                        update_drone_position(connection, lat, lon, 10)
                    except Exception as e:
                        print(f"Błąd")
                        break

def update_drone_position(connection, latitude, longitude, altitude):
    #zmiana pozycji
    try:
        current_mode = connection.recv_match(type='HEARTBEAT', blocking=True).custom_mode

        
        msg = connection.mav.set_position_target_global_int_encode(
            0, connection.target_system, connection.target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            0b0000111111111000,  # używane są tylko pozycje i wysokość
            int(latitude * 1e7),
            int(longitude * 1e7),
            altitude,
            0, 0, 0, 0, 0, 0, 0, 0
        )
        connection.mav.send(msg)
    except Exception as e:
        print(f"Błąd wysyłania pozycji")

def waypoint_listener(connection):
    #Nasłuchiwanie port 5000
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 5000))
        s.listen(1)
        while True:
            conn, addr = s.accept()
            print(f"Połączono z {addr}")
            with conn:
                waypoints = []
                while True:
                    data = conn.recv(1024).decode().strip()
                    if not data or data == "END":
                        break
                    lat, lon = map(float, data.split(","))
                    waypoints.append((lat, lon))
                print(f"Odebrano punkty trasy: {waypoints}")
                fly_mission(connection, waypoints, 10)

def fly_mission(connection, waypoints, altitude):
    #Realizuje misję na podstawie listy punktów GPS
    for idx, (lat, lon) in enumerate(waypoints):
        print(f"Lecenie do punktu {idx + 1}: Lat {lat}, Lon {lon}")
        update_drone_position(connection, lat, lon, altitude)

if __name__ == "__main__":
    connection_string = "127.0.0.1:14550"
    connection = establish_connection(connection_string)

    check_gps_lock(connection)
    set_mode(connection, "GUIDED")

    if arm_drone(connection):
        takeoff(connection, 10)

    threading.Thread(target=waypoint_listener, args=(connection,), daemon=True).start()
    threading.Thread(target=position_listener, args=(connection,), daemon=True).start()

    while True:
        time.sleep(1)



