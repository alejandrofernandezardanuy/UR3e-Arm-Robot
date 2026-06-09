#!/usr/bin/env python3
"""
Palletizing — UR3e + OnRobot RG2
Picks 4 stacked pieces from A and stacks them at B.
"""

import socket
import time
import sys
import math
import re

# ================================================================
#  CONFIG
# ================================================================

ROBOT_IP   = "10.10.73.236"
ROBOT_PORT = 30002

TCP_GRIPPER = "p[0.0, 0.0, 0.2286, 0.0, 0.0, 0.0]"

VEL_J     = 0.3    # rad/s  movej slow
ACC_J     = 0.3    # rad/s²
VEL_J_RAP = 1.5    # rad/s  movej fast (free-space transitions)
ACC_J_RAP = 1.5    # rad/s²
VEL_L     = 0.05   # m/s    movel
ACC_L     = 0.05   # m/s²

T_MOVE     = 4.0   # s  wait after movel / slow movej
T_MOVE_RAP = 2.0   # s  wait after fast movej
T_GRIPPER  = 2.0   # s  wait for gripper to act
T_PAUSA    = 0.5   # s  pre/post gripper pause

NUM_PIEZAS   = 4
ALTURA_PIEZA = 0.020   # m

PINZA_CERRAR = "pinza10UR3.py"
PINZA_ABRIR  = "pinza40UR3.py"

# Joint positions in radians (from PolyScope degrees)
HOME = [
    math.radians( -90.92),
    math.radians( -99.70),
    math.radians( -57.25),
    math.radians(-112.94),
    math.radians(  89.40),
    math.radians(  -1.21),
]

SOBRE_A = [
    math.radians(-101.08),
    math.radians(-103.69),
    math.radians( -65.40),
    math.radians(-100.72),
    math.radians(  89.44),
    math.radians( -11.37),
]

SOBRE_B = [
    math.radians( -76.19),
    math.radians( -90.36),
    math.radians( -80.67),
    math.radians( -98.99),
    math.radians(  89.41),
    math.radians(  13.54),
]

# Cartesian poses [x, y, z, rx, ry, rz] in metres
POSE_A       = [-0.20000, -0.32000, 0.00900, 0.0, 3.150, 0.0]
SOBRE_A_POSE = [-0.20001, -0.32000, 0.10863, 0.0, 3.150, 0.0]

POSE_B       = [-0.05999, -0.31998, 0.01098, 0.0, 3.150, 0.0]
SOBRE_B_POSE = [-0.06001, -0.31997, 0.10800, 0.0, 3.150, 0.0]

# ================================================================


def movej(sock, punto, descripcion, rapido=False):
    vel = VEL_J_RAP if rapido else VEL_J
    acc = ACC_J_RAP if rapido else ACC_J
    t   = T_MOVE_RAP if rapido else T_MOVE
    joints  = "[" + ", ".join(f"{j:.4f}" for j in punto) + "]"
    sock.sendall(f"set_tcp({TCP_GRIPPER})\nmovej({joints}, a={acc}, v={vel})\n".encode())
    print(f"  movej  {descripcion}")
    time.sleep(t)


def movel_cart(sock, pose, descripcion):
    coords = "[" + ", ".join(f"{v:.5f}" for v in pose) + "]"
    sock.sendall(f"set_tcp({TCP_GRIPPER})\nmovel(p{coords}, a={ACC_L}, v={VEL_L})\n".encode())
    print(f"  movel  {descripcion}")
    time.sleep(T_MOVE)


def activar_pinza(sock, archivo, descripcion):
    # Fix C207A0: disable RTDE watchdog regardless of original value
    with open(archivo, "rb") as f:
        script = f.read().decode("utf-8", errors="replace")
    script = re.sub(
        r'on_set_rtde_watchdog\s*\([^)]*\)',
        'on_set_rtde_watchdog(updateHz=0)',
        script
    )
    time.sleep(T_PAUSA)
    sock.sendall(script.encode("utf-8"))
    print(f"  gripper  {descripcion}")
    time.sleep(T_GRIPPER)
    time.sleep(T_PAUSA)


def conectar(ip, puerto):
    print(f"Connecting to {ip}:{puerto}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, puerto))
        sock.settimeout(None)
        time.sleep(1)
        return sock
    except socket.timeout:
        print(f"Timeout — is the robot on at {ip}?")
        sys.exit(1)
    except OSError as e:
        print(f"Connection error: {e}")
        sys.exit(1)


def pose_recogida(i):
    pose = list(POSE_A)
    pose[2] += (NUM_PIEZAS - 1 - i) * ALTURA_PIEZA
    return pose


def pose_colocacion(i):
    pose = list(POSE_B)
    pose[2] += i * ALTURA_PIEZA
    return pose


def mover_pieza(sock, i):
    pick  = pose_recogida(i)
    place = pose_colocacion(i)

    print(f"\nPiece {i+1}/{NUM_PIEZAS}  A z={pick[2]*1000:.1f}mm  B z={place[2]*1000:.1f}mm")

    movej(sock, SOBRE_A, "over A", rapido=True)
    movel_cart(sock, pick, f"pick {i+1}")
    activar_pinza(sock, PINZA_CERRAR, "close 10mm")
    movel_cart(sock, SOBRE_A_POSE, "up A")
    movej(sock, SOBRE_B, "over B", rapido=True)
    movel_cart(sock, place, f"place {i+1}")
    activar_pinza(sock, PINZA_ABRIR, "open 40mm")
    movel_cart(sock, SOBRE_B_POSE, "up B")


def main():
    print(f"Palletizing {NUM_PIEZAS} pieces  |  {ROBOT_IP}:{ROBOT_PORT}")

    sock = conectar(ROBOT_IP, ROBOT_PORT)

    try:
        movej(sock, HOME, "home", rapido=True)

        for i in range(NUM_PIEZAS):
            mover_pieza(sock, i)

        movej(sock, HOME, "home", rapido=True)
        print(f"\nDone — {NUM_PIEZAS} pieces placed at B.")

    except KeyboardInterrupt:
        print("\nStopped by user.")
    except OSError as e:
        print(f"\nSocket error: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
