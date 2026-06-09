# UR3e Palletizing — UR Studio Activity D2

Python script for automated pick-and-place palletizing using a **UR3e** robot arm and an **OnRobot RG2** gripper. Transfers 4 stacked pieces from position A to position B, managing stack height dynamically on both ends.

Viedo Demo: https://drive.google.com/file/d/1zRhHxwBk3I1x2xsgBs_HITWXUZJ_FTaS/view?usp=drive_link


## Requirements

- Python 3.x (no external libraries)
- UR3e controller reachable at the configured IP
- OnRobot RG2 gripper scripts: `pinza10UR3.py` and `pinza40UR3.py` in the same directory

## Usage

```bash
python paletizado_final.py
```

Adjust the constants at the top of the file before running:

| Constant | Default | Description |
|---|---|---|
| `ROBOT_IP` | `10.10.73.236` | Controller IP address |
| `ALTURA_PIEZA` | `0.020` m | Height of each piece |
| `VEL_J_RAP` | `1.5` rad/s | Speed for free-space joint moves |
| `VEL_L` | `0.05` m/s | Speed for linear moves near pieces |
| `T_MOVE` | `4.0` s | Wait time after movel |
| `T_GRIPPER` | `2.0` s | Wait time for gripper actuation |

## How it works

Commands are sent as URScript strings to the controller on port 30002 over a plain TCP socket. There is no SDK dependency.

Each piece follows an 8-step cycle:

1. Move over A (fast `movej`)
2. Lower to piece (slow `movel`)
3. Close gripper
4. Lift (slow `movel`)
5. Move over B (fast `movej`)
6. Lower to stack level (slow `movel`)
7. Open gripper
8. Lift (slow `movel`)

Pick height decreases each iteration (taking from the top of stack A). Place height increases each iteration (building stack B from the bottom).

## Note on the RTDE watchdog (error C207A0)

The OnRobot gripper scripts contain a call to `on_set_rtde_watchdog(updateHz=X)` which sets an RTDE watchdog that the controller expects to be refreshed periodically. If it is not, the controller raises a C207A0 fault and halts.

The script neutralises this using a regex replacement before sending the gripper file:

```python
script = re.sub(
    r'on_set_rtde_watchdog\s*\([^)]*\)',
    'on_set_rtde_watchdog(updateHz=0)',
    script
)
```

Setting `updateHz=0` disables the watchdog entirely, regardless of the original value in the file.

## File structure

```
paletizado_final.py   # main script
pinza10UR3.py         # gripper close script (OnRobot, not included)
pinza40UR3.py         # gripper open script  (OnRobot, not included)
```
