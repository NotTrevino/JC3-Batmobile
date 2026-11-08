# JC3 fleet relationships (T-1 evidence)

Fitted over **156** land vehicles that carry both `rigid_body.mass` and the
member, by log-log least squares: `value = a * mass^b`. `R²` is on the log scale; a
value near 0 means **the fleet does not relate these two numbers**, so the translation
table must not pretend it does.

Predicted column is the fit evaluated at **4000 kg** (the built
Batmobile's mass).

| member | a | b | R² | n | fleet min…max | at 4,000 kg |
|---|---|---|---|---|---|---|
| `suspension front strength` | 53.48 | -0.103 | -0.010 | 125 | 4 … 80 | 22.84 |
| `suspension rear strength` | 84.96 | -0.160 | +0.050 | 125 | 4 … 100 | 22.62 |
| `suspension front compression` | 0.9667 | +0.076 | -0.009 | 125 | 1 … 4 | 1.813 |
| `suspension front relaxation` | 4.186 | +0.007 | -0.070 | 125 | 2 … 15 | 4.452 |
| `front max brake torque` | 24.57 | +0.708 | +0.042 | 144 | 250 … 1e+07 | 8752 |
| `front tyre radius` | 0.1061 | +0.177 | +0.682 | 144 | 0.2 … 1.8 | 0.4592 |
| `front tyre width` | 0.0332 | +0.264 | +0.525 | 144 | 0.0375 … 1.42 | 0.2958 |
| `front wheel mass` | 2.18 | +0.512 | +0.022 | 144 | 10 … 1e+05 | 152.5 |
| `unit inertia yaw` | 0.08553 | +0.454 | +0.277 | 156 | 0.31 … 37 | 3.701 |
| `unit inertia roll` | 0.1138 | +0.255 | +0.409 | 156 | 0.1 … 9.2 | 0.9438 |
| `optimal rpm` | 2.105e+04 | -0.264 | +0.516 | 144 | 1100 … 9000 | 2365 |
| `torque at optimal rpm` | 2.153 | +0.719 | +0.808 | 142 | 12 … 5e+04 | 834.1 |
| `max rpm` | 7.112e+04 | -0.342 | -0.011 | 144 | 2000 … 1e+07 | 4186 |
| `transmission top speed` | 310.7 | -0.086 | +0.042 | 144 | 90 … 505 | 152.5 |
| `frontal area` | 0.07742 | +0.501 | +0.875 | 144 | 0.2 … 80 | 4.924 |
| `drag coefficient` | 0.2815 | +0.085 | +0.127 | 141 | 0.15 … 4 | 0.5707 |
| `time to full steer` | 0.2654 | +0.240 | +0.088 | 125 | 0.5 … 10 | 1.944 |
| `steer angle at min speed` | 29.85 | +0.024 | +0.074 | 125 | 20 … 45 | 36.29 |
| `steer angle at max speed` | 11.24 | +0.052 | +0.112 | 125 | 10 … 30 | 17.24 |

## What the fleet decides

Fits strong enough to interpolate (R² ≥ 0.5): `front tyre radius` (0.68), `front tyre width` (0.52), `optimal rpm` (0.52), `torque at optimal rpm` (0.81), `frontal area` (0.87).

Fits that are noise (R² < 0.2) and must be treated as **per-vehicle art**, not a law: `suspension front strength`, `suspension rear strength`, `suspension front compression`, `suspension front relaxation`, `front max brake torque`, `front wheel mass`, `max rpm`, `transmission top speed`, `drag coefficient`, `time to full steer`, `steer angle at min speed`, `steer angle at max speed`.

## Median by mass class

Where the fit is noise, this is what the fleet actually does — a band to stay inside,
not a target.

**`suspension front strength`**

| mass class (kg) | n | median |
|---|---|---|
| 0-1500 | 48 | 30 |
| 1500-3000 | 25 | 25 |
| 3000-6000 | 26 | 30 |
| 6000-15000 | 18 | 30 |
| 15000-∞ | 8 | 4 |

**`front max brake torque`**

| mass class (kg) | n | median |
|---|---|---|
| 0-1500 | 67 | 2500 |
| 1500-3000 | 25 | 5000 |
| 3000-6000 | 26 | 5000 |
| 6000-15000 | 18 | 1e+04 |
| 15000-∞ | 8 | 3e+04 |

**`unit inertia yaw`**

| mass class (kg) | n | median |
|---|---|---|
| 0-1500 | 67 | 1.45 |
| 1500-3000 | 25 | 2.3 |
| 3000-6000 | 26 | 2.48 |
| 6000-15000 | 18 | 4.65 |
| 15000-∞ | 20 | 25 |

**`front tyre radius`**

| mass class (kg) | n | median |
|---|---|---|
| 0-1500 | 67 | 0.318 |
| 1500-3000 | 25 | 0.352 |
| 3000-6000 | 26 | 0.521 |
| 6000-15000 | 18 | 0.48 |
| 15000-∞ | 8 | 0.66 |

**`torque at optimal rpm`**

| mass class (kg) | n | median |
|---|---|---|
| 0-1500 | 67 | 150 |
| 1500-3000 | 25 | 550 |
| 3000-6000 | 26 | 550 |
| 6000-15000 | 18 | 1100 |
| 15000-∞ | 8 | 2500 |
