"""chase_namescan_b.py - namescan for the F-33…F-40 property set (chase-05).

Same pass as `chase_namescan.py`, different needles: the eight fields of
`Research/BatmobileGrab/FOOTAGE.md` F-33…F-40 plus the three class-mates whose shipped
values are known (`BattleModeWidth`, `BattleModeLength`, `ImpactShakeVehicleFactor`), used as
controls. Read-only; writes `E:\Modding\_gamedata\BmAKgrab\chase\namescan_b.json`.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chase_namescan as N  # noqa: E402

NAMES = [b"BattleModeHeight", b"JumpRampUpwardForce", b"ImpactShakeAbandonedVehicleFactor",
         b"ImpactShakeDestructiblesFactor", b"ImpactShakeCoolDown", b"BattleModeSpeedDelta",
         b"TurnOnSpotSteeringSpeedCurve", b"BattleModeMoving",
         b"BattleModeWidth", b"BattleModeLength", b"ImpactShakeVehicleFactor"]
N.NAMES = NAMES
import re  # noqa: E402
N.RX = re.compile(b"|".join(NAMES))
N.OUT = os.path.join(r"E:\Modding\_gamedata\BmAKgrab", "chase", "namescan_b.json")

if __name__ == "__main__":
    N.main()
