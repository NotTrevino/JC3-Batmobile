"""Mirror the Batmobile wheel across X (axle) for the other side: same file on
both sides shows the rim mirrored (dished face inward on one side). Winding is
flipped to preserve culling; normals mirrored + renormalized."""
import sys

import numpy as np

sys.path.insert(0, "Tools/scripts")
import rbm_geom as R  # noqa: E402
from psk2rbm import build_rbm, smooth_normals  # noqa: E402

SRC = r"Working\Batmobile\bat_wheel_2k5.rbm"
TPL = (r"Builds\test-045\aaf\models\jc_vehicles\01_land"
       r"\v0300_car_kensington_sportsmuscle\sportsmuscle_wheel_f_l_lod1.rbm")
DST = r"Working\Batmobile\bat_wheel_R.rbm"

m = R.decode(open(SRC, "rb").read())
b = m.blocks[0]
V = np.frombuffer(b.vb0.data, "<f4").reshape(-1, 3).astype(np.float64)
I = np.frombuffer(b.ib.data, "<u2").reshape(-1, 3).astype(np.int64)
UV = np.frombuffer(b.vb1.data, "<f4").reshape(-1, 6)[:, 0:2].astype(np.float64)

V2 = V.copy()
V2[:, 0] *= -1.0
I2 = I[:, [0, 2, 1]]
_, first, inv = np.unique(np.round(V2, 6), axis=0,
                          return_index=True, return_inverse=True)
N2 = smooth_normals(V2, I2, inv)
m2 = build_rbm(TPL, V2, UV, I2, N2)
raw = m2.write()
open(DST, "wb").write(raw)

back = R.decode(raw)
pb = np.array(back.blocks[0].vb0.positions())
assert abs(pb[:, 0].max() - 0.214) < 0.01 and len(pb) == len(V)
print("mirrored wheel OK:", DST, len(raw), "B,",
      len(V2), "verts,", len(I2), "tris")
