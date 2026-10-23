# JC3 fleet — geometry, handling and the donor matrix

Derived from the decode in this folder by `Tools/scripts/jc3fleet.py`.
**145** vehicles have a `land_global` station set; **144** of them are
land vehicles with a measurable body, which is the set that can host the Batmobile.

Batmobile targets (from the built mod): length **7.026 m**, wheelbase **5.029 m**,
track **2.416 m**, tyre radius **0.6826 m**. `score` is the RMS relative error over
those four; lower is closer. It ranks *shape*, not behaviour.

## Nearest shapes

| # | entity | score | L×W×H | wheelbase | track | tyre Ø | mass | top |
|---|---|---|---|---|---|---|---|---|
| 1 | `v0602_car_urga_armoredtransport/v0602_car_urga_armoredtransport_debug` | 0.1336 | 6.17×2.53×2.67 | 4.211 | 2.116 | 1.20 | 6000 | 150 |
| 2 | `v0602_car_urga_armoredtransport/v0602_car_urga_armoredtransport_military_01` | 0.1336 | 6.17×2.53×2.67 | 4.211 | 2.116 | 1.20 | 6000 | 150 |
| 3 | `v0602_car_urga_armoredtransport/v0602_car_urga_armoredtransport_rebel_01` | 0.1336 | 6.17×2.53×2.67 | 4.211 | 2.116 | 1.20 | 6000 | 150 |
| 4 | `v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_debug` | 0.1643 | 8.19×4.67×2.34 | 4.534 | 3.054 | 1.32 | 25000 | 105 |
| 5 | `v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_military_01` | 0.1643 | 8.19×4.67×2.34 | 4.534 | 3.054 | 1.32 | 25000 | 105 |
| 6 | `v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_rebel_01` | 0.1643 | 8.19×4.67×2.34 | 4.534 | 3.054 | 1.32 | 25000 | 105 |
| 7 | `v0202_car_capstone_bavariumtank/v0202_car_capstone_bavariumtank_debug` | 0.1643 | 8.19×4.67×2.34 | 4.534 | 3.054 | 1.32 | 25000 | 105 |
| 8 | `v0202_car_capstone_bavariumtank/v0202_car_capstone_bavariumtank_military_01` | 0.1643 | 8.19×4.67×2.34 | 4.534 | 3.054 | 1.32 | 25000 | 105 |
| 9 | `v0202_car_capstone_bavariumtank/v0202_car_capstone_bavariumtank_rebel_01` | 0.1643 | 8.19×4.67×2.34 | 4.534 | 3.054 | 1.32 | 25000 | 105 |
| 10 | `v0011_car_autostraad_articulatedtruck/v0011_car_autostraad_articulatedtruck_commercial_01` | 0.1821 | 6.45×2.70×3.66 | 3.884 | 2.214 | 1.01 | 8500 | 145 |
| 11 | `v0011_car_autostraad_articulatedtruck/v0011_car_autostraad_articulatedtruck_debug` | 0.1821 | 6.45×2.70×3.66 | 3.884 | 2.214 | 1.01 | 8500 | 145 |
| 12 | `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_commercial_01` | 0.1971 | 6.94×2.24×2.61 | 3.884 | 1.89 | 1.04 | 5100 | 150 |
| 13 | `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_commercial_cargo_barrel` | 0.1971 | 6.94×2.24×2.61 | 3.884 | 1.89 | 1.04 | 5100 | 150 |
| 14 | `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_commercial_cargo_random` | 0.1971 | 6.94×2.24×2.61 | 3.884 | 1.89 | 1.04 | 5100 | 150 |
| 15 | `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_commercial_cargo_wine` | 0.1971 | 6.94×2.24×2.61 | 3.884 | 1.89 | 1.04 | 5100 | 150 |
| 16 | `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_debug` | 0.1971 | 6.94×2.24×2.61 | 3.884 | 1.89 | 1.04 | 5100 | 150 |
| 17 | `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_military_01` | 0.1971 | 6.94×2.24×2.61 | 3.884 | 1.89 | 1.04 | 5100 | 150 |
| 18 | `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_rebel_01` | 0.1971 | 6.94×2.24×2.61 | 3.884 | 1.89 | 1.04 | 5100 | 150 |
| 19 | `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_rebel_emp_01` | 0.1971 | 6.94×2.24×2.61 | 3.884 | 1.89 | 1.04 | 5100 | 150 |
| 20 | `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_rebel_emp_custom_mm250` | 0.1971 | 6.94×2.24×2.61 | 3.884 | 1.89 | 1.04 | 5100 | 150 |

## Current donor

`v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01` ranks **45 of 144** by shape. Wheelbase 3.003 m against the Batmobile's 5.029 m, track 1.77 m against 2.416 m, tyre Ø 0.76 m against 1.365 m.

## All land vehicles

| entity | L | W | H | wheelbase | track | hub y | tyre r | mass | top |
|---|---|---|---|---|---|---|---|---|---|
| `v0005_car_autostraad_minetruck/v0005_car_autostraad_minetruck_commercial_01` | 13.7944 | 11.0284 | 7.1196 | 6.536 | 7.198 | 1.858 | 1.79999995 | 550000 | 100 |
| `v0005_car_autostraad_minetruck/v0005_car_autostraad_minetruck_debug` | 13.7944 | 11.0284 | 7.1196 | 6.536 | 7.198 | 1.858 | 1.79999995 | 550000 | 100 |
| `v0006_car_autostraad_modernbus/v0006_car_autostraad_modernbus_commercial_01` | 10.5008 | 2.6664 | 3.152 | 4.533 | 2.132 | 0.503 | 0.477999985 | 14000 | 150 |
| `v0006_car_autostraad_modernbus/v0006_car_autostraad_modernbus_debug` | 10.5008 | 2.6664 | 3.152 | 4.533 | 2.132 | 0.503 | 0.477999985 | 14000 | 150 |
| `v0507_car_solar_oldbus/v0507_car_solar_oldbus_commercial_01` | 8.5224 | 2.6125 | 2.9648 | 4.36 | 2.19 | 0.4197 | 0.443699986 | 7000 | 150 |
| `v0507_car_solar_oldbus/v0507_car_solar_oldbus_commercial_z80` | 8.5224 | 2.6125 | 2.9648 | 4.36 | 2.19 | 0.4197 | 0.443699986 | 7000 | 150 |
| `v0507_car_solar_oldbus/v0507_car_solar_oldbus_debug` | 8.5224 | 2.6125 | 2.9648 | 4.36 | 2.19 | 0.4197 | 0.443699986 | 7000 | 150 |
| `v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_debug` | 8.1902 | 4.671 | 2.3411 | 4.534 | 3.054 | 0.685 | 0.660000026 | 25000 | 105 |
| `v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_military_01` | 8.1902 | 4.671 | 2.3411 | 4.534 | 3.054 | 0.685 | 0.660000026 | 25000 | 105 |
| `v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_rebel_01` | 8.1902 | 4.671 | 2.3411 | 4.534 | 3.054 | 0.685 | 0.660000026 | 25000 | 105 |
| `v0202_car_capstone_bavariumtank/v0202_car_capstone_bavariumtank_debug` | 8.1902 | 4.671 | 2.3411 | 4.534 | 3.054 | 0.685 | 0.660000026 | 25000 | 105 |
| `v0202_car_capstone_bavariumtank/v0202_car_capstone_bavariumtank_military_01` | 8.1902 | 4.671 | 2.3411 | 4.534 | 3.054 | 0.685 | 0.660000026 | 25000 | 105 |
| `v0202_car_capstone_bavariumtank/v0202_car_capstone_bavariumtank_rebel_01` | 8.1902 | 4.671 | 2.3411 | 4.534 | 3.054 | 0.685 | 0.660000026 | 25000 | 105 |
| `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_commercial_01` | 6.9365 | 2.2443 | 2.6126 | 3.884 | 1.89 | 0.507 | 0.521000028 | 5100 | 150 |
| `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_commercial_cargo_barrel` | 6.9365 | 2.2443 | 2.6126 | 3.884 | 1.89 | 0.507 | 0.521000028 | 5100 | 150 |
| `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_commercial_cargo_random` | 6.9365 | 2.2443 | 2.6126 | 3.884 | 1.89 | 0.507 | 0.521000028 | 5100 | 150 |
| `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_commercial_cargo_wine` | 6.9365 | 2.2443 | 2.6126 | 3.884 | 1.89 | 0.507 | 0.521000028 | 5100 | 150 |
| `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_debug` | 6.9365 | 2.2443 | 2.6126 | 3.884 | 1.89 | 0.507 | 0.521000028 | 5100 | 150 |
| `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_military_01` | 6.9365 | 2.2443 | 2.6126 | 3.884 | 1.89 | 0.507 | 0.521000028 | 5100 | 150 |
| `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_rebel_01` | 6.9365 | 2.2443 | 2.6126 | 3.884 | 1.89 | 0.507 | 0.521000028 | 5100 | 150 |
| `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_rebel_emp_01` | 6.9365 | 2.2443 | 2.6126 | 3.884 | 1.89 | 0.507 | 0.521000028 | 5100 | 150 |
| `v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_rebel_emp_custom_mm250` | 6.9365 | 2.2443 | 2.6126 | 3.884 | 1.89 | 0.507 | 0.521000028 | 5100 | 150 |
| `v0302_car_kensington_modernlimo/v0302_car_kensington_modernlimo_civilian_01` | 6.8793 | 2.0276 | 0.7424 | 4.8118 | 1.6914 | 0.3703 | 0.368000001 | 2780 | 250 |
| `v0302_car_kensington_modernlimo/v0302_car_kensington_modernlimo_debug` | 6.8793 | 2.0276 | 0.7424 | 4.8118 | 1.6914 | 0.3703 | 0.368000001 | 2780 | 250 |
| `v0011_car_autostraad_articulatedtruck/v0011_car_autostraad_articulatedtruck_commercial_01` | 6.4458 | 2.6993 | 3.6583 | 3.884 | 2.214 | 0.485 | 0.505999982 | 8500 | 145 |
| `v0011_car_autostraad_articulatedtruck/v0011_car_autostraad_articulatedtruck_debug` | 6.4458 | 2.6993 | 3.6583 | 3.884 | 2.214 | 0.485 | 0.505999982 | 8500 | 145 |
| `v0200_car_capstone_apc/v0200_car_capstone_apc_debug` | 6.445 | 2.8906 | 2.1052 | 3.128 | 2.316 | 0.536 | 0.479999989 | 6400 | 100 |
| `v0200_car_capstone_apc/v0200_car_capstone_apc_military_01` | 6.445 | 2.8906 | 2.1052 | 3.128 | 2.316 | 0.536 | 0.479999989 | 6400 | 100 |
| `v0200_car_capstone_apc/v0200_car_capstone_apc_rebel_01` | 6.445 | 2.8906 | 2.1052 | 3.128 | 2.316 | 0.536 | 0.479999989 | 6400 | 100 |
| `v0001_car_autostraad_armoredtruck/v0001_car_autostraad_armoredtruck_commercial_01` | 6.2003 | 2.5477 | 2.7159 | 4.064 | 2.148 | 0.462 | 0.449999988 | 8500 | 150 |
| `v0001_car_autostraad_armoredtruck/v0001_car_autostraad_armoredtruck_debug` | 6.2003 | 2.5477 | 2.7159 | 4.064 | 2.148 | 0.462 | 0.449999988 | 8500 | 150 |
| `v0602_car_urga_armoredtransport/v0602_car_urga_armoredtransport_debug` | 6.1687 | 2.5335 | 2.668 | 4.211 | 2.116 | 0.527 | 0.600000024 | 6000 | 150 |
| `v0602_car_urga_armoredtransport/v0602_car_urga_armoredtransport_military_01` | 6.1687 | 2.5335 | 2.668 | 4.211 | 2.116 | 0.527 | 0.600000024 | 6000 | 150 |
| `v0602_car_urga_armoredtransport/v0602_car_urga_armoredtransport_rebel_01` | 6.1687 | 2.5335 | 2.668 | 4.211 | 2.116 | 0.527 | 0.600000024 | 6000 | 150 |
| `v0009_car_autostraad_modernsaloon/v0009_car_autostraad_modernsaloon_civilian_01` | 5.1968 | 2.0417 | 1.4633 | 3.197 | 1.772 | 0.342 | 0.349999994 | 2000 | 250 |
| `v0009_car_autostraad_modernsaloon/v0009_car_autostraad_modernsaloon_debug` | 5.1968 | 2.0417 | 1.4633 | 3.197 | 1.772 | 0.342 | 0.349999994 | 2000 | 250 |
| `v0009_car_autostraad_modernsaloon/v0009_car_autostraad_modernsaloon_premium_01` | 5.1968 | 2.0417 | 1.4633 | 3.197 | 1.772 | 0.342 | 0.349999994 | 2000 | 250 |
| `v0603_car_urga_smalltank/v0603_car_urga_smalltank_debug` | 5.1075 | 2.4586 | 1.5084 | 3.228 | 2.462 | 0.615 | 0.56400001 | 13100 | 90 |
| `v0603_car_urga_smalltank/v0603_car_urga_smalltank_military_01` | 5.1075 | 2.4586 | 1.5084 | 3.228 | 2.462 | 0.615 | 0.56400001 | 13100 | 90 |
| `v0603_car_urga_smalltank/v0603_car_urga_smalltank_rebel_01` | 5.1075 | 2.4586 | 1.5084 | 3.228 | 2.462 | 0.615 | 0.56400001 | 13100 | 90 |
| `v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01` | 4.9999 | 2.1121 | 1.4051 | 3.003 | 1.77 | 0.4 | 0.379999995 | 975 | 250 |
| `v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug` | 4.9999 | 2.1121 | 1.4051 | 3.003 | 1.77 | 0.4 | 0.379999995 | 975 | 250 |
| `v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_signature_preorder` | 4.9999 | 2.1121 | 1.4051 | 3.003 | 1.77 | 0.4 | 0.379999995 | 975 | 250 |
| `v0501_car_solar_smallvan/v0501_car_solar_smallvan_civic_ambulance_01` | 4.9845 | 1.8116 | 2.183 | 3.177 | 1.624 | 0.308 | 0.326999992 | 3500 | 150 |
| `v0501_car_solar_smallvan/v0501_car_solar_smallvan_commercial_01` | 4.9845 | 1.8116 | 2.183 | 3.177 | 1.624 | 0.308 | 0.326999992 | 3500 | 150 |
| `v0501_car_solar_smallvan/v0501_car_solar_smallvan_debug` | 4.9845 | 1.8116 | 2.183 | 3.177 | 1.624 | 0.308 | 0.326999992 | 3500 | 150 |
| `v0501_car_solar_smallvan/v0501_car_solar_smallvan_propaganda_01` | 4.9845 | 1.8116 | 2.183 | 3.177 | 1.624 | 0.308 | 0.326999992 | 3500 | 150 |
| `v0501_car_solar_smallvan/v0501_car_solar_smallvan_propaganda_chaoslist` | 4.9845 | 1.8116 | 2.183 | 3.177 | 1.624 | 0.308 | 0.326999992 | 3500 | 150 |
| `v0600_car_urga_armoredjeep/v0600_car_urga_armoredjeep_debug` | 4.9106 | 2.3381 | 1.7076 | 3.1878 | 1.7602 | 0.5229 | 0.550000012 | 4250 | 150 |
| `v0600_car_urga_armoredjeep/v0600_car_urga_armoredjeep_military_01` | 4.9106 | 2.3381 | 1.7076 | 3.1878 | 1.7602 | 0.5229 | 0.550000012 | 4250 | 150 |
| `v0600_car_urga_armoredjeep/v0600_car_urga_armoredjeep_rebel_01` | 4.9106 | 2.3381 | 1.7076 | 3.1878 | 1.7602 | 0.5229 | 0.550000012 | 4250 | 150 |
| `v0000_car_autostraad_oldjeep/v0000_car_autostraad_oldjeep_military_01` | 4.9096 | 2.1984 | 2.357 | 2.709 | 1.542 | 0.432 | 0.411500007 | 840 | 160 |
| `v0000_car_autostraad_oldjeep/v0000_car_autostraad_oldjeep_military_z80` | 4.9096 | 2.1984 | 2.357 | 2.709 | 1.542 | 0.432 | 0.411500007 | 840 | 160 |
| `v0514_car_solar_modernpickup/v0514_car_solar_modernpickup_civilian_01` | 4.8618 | 2.287 | 1.7596 | 3.064 | 1.782 | 0.394 | 0.360000014 | 2000 | 180 |
| `v0514_car_solar_modernpickup/v0514_car_solar_modernpickup_civilian_z80` | 4.8618 | 2.287 | 1.7596 | 3.064 | 1.782 | 0.394 | 0.360000014 | 2000 | 180 |
| `v0305_car_kensington_moderngrandtourer/v0305_car_kensington_moderngrandtourer_civilian_01` | 4.8611 | 1.8505 | 0.9297 | 3.005 | 1.686 | 0.341 | 0.351999998 | 1650 | 307 |
| `v0305_car_kensington_moderngrandtourer/v0305_car_kensington_moderngrandtourer_debug` | 4.8611 | 1.8505 | 0.9297 | 3.005 | 1.686 | 0.341 | 0.351999998 | 1650 | 307 |
| `v0503_car_solar_modernsuv/v0503_car_solar_modernsuv_civilian_01` | 4.8282 | 2.2105 | 1.7947 | 2.679 | 1.738 | 0.346 | 0.368000001 | 2200 | 235 |
| `v0504_car_solar_technicaljeep/v0504_car_solar_technicaljeep_debug` | 4.8093 | 2.2387 | 1.5917 | 3.208 | 1.782 | 0.394 | 0.360000014 | 2000 | 180 |
| `v0504_car_solar_technicaljeep/v0504_car_solar_technicaljeep_militia_01` | 4.8093 | 2.2387 | 1.5917 | 3.208 | 1.782 | 0.394 | 0.360000014 | 2000 | 180 |
| `v0504_car_solar_technicaljeep/v0504_car_solar_technicaljeep_rebel_01` | 4.8093 | 2.2387 | 1.5917 | 3.208 | 1.782 | 0.394 | 0.360000014 | 2000 | 180 |
| `v0504_car_solar_technicaljeep/v0504_car_solar_technicaljeep_rebel_machinegun` | 4.8093 | 2.2387 | 1.5917 | 3.208 | 1.782 | 0.394 | 0.360000014 | 2000 | 180 |
| `v0401_car_mugello_racingsupercar/v0401_car_mugello_racingsupercar_civilian_01` | 4.6863 | 2.1147 | 1.0423 | 2.823 | 1.736 | 0.323 | 0.335999995 | 1500 | 350 |
| `v0401_car_mugello_racingsupercar/v0401_car_mugello_racingsupercar_debug` | 4.6863 | 2.1147 | 1.0423 | 2.823 | 1.736 | 0.323 | 0.335999995 | 1500 | 350 |
| `v0401_car_mugello_racingsupercar/v0401_car_mugello_racingsupercar_premium_01` | 4.6863 | 2.1147 | 1.0423 | 2.823 | 1.736 | 0.323 | 0.335999995 | 1500 | 350 |
| `v0803_car_na_monstertruck/v0803_car_na_monstertruck_civilian_01` | 4.6659 | 2.0525 | 1.8894 | 3.058 | 3.164 | 0.9565 | 0.899999976 | 4000 | 150 |
| `v0803_car_na_monstertruck/v0803_car_na_monstertruck_civilian_01_z80` | 4.6659 | 2.0525 | 1.8894 | 3.058 | 3.164 | 0.9565 | 0.899999976 | 4000 | 150 |
| `v0803_car_na_monstertruck/v0803_car_na_monstertruck_debug` | 4.6659 | 2.0525 | 1.8894 | 3.058 | 3.164 | 0.9565 | 0.899999976 | 4000 | 150 |
| `v0514_car_solar_modernpickup/v0514_car_solar_modernpickup_debug` | 4.6593 | 2.05 | 1.5972 | 3.064 | 1.782 | 0.394 | 0.360000014 | 2000 | 180 |
| `v9999_car_mugello_dlctestcar/v9999_car_mugello_dlctestcar_debug` | 4.6515 | 1.8305 | 0.874 | 2.823 | 1.736 | 0.323 | 0.335999995 | 1500 | 350 |
| `v0508_car_solar_oldcompact/v0508_car_solar_oldcompact_civilian_01` | 4.638 | 2.1657 | 1.4837 | 2.804 | 1.47 | 0.321 | 0.289999992 | 915 | 120 |
| `v0000_car_autostraad_oldjeep/v0000_car_autostraad_oldjeep_civilian_01` | 4.6159 | 2.1708 | 2.0841 | 2.709 | 1.542 | 0.432 | 0.411500007 | 840 | 160 |
| `v0000_car_autostraad_oldjeep/v0000_car_autostraad_oldjeep_civilian_z80` | 4.6159 | 2.1708 | 2.0841 | 2.709 | 1.542 | 0.432 | 0.411500007 | 840 | 160 |
| `v0000_car_autostraad_oldjeep/v0000_car_autostraad_oldjeep_rebel_01` | 4.5707 | 2.1824 | 2.3703 | 2.709 | 1.542 | 0.432 | 0.411500007 | 840 | 160 |
| `v0403_car_mugello_modernecosuper/v0403_car_mugello_modernecosuper_civilian_01` | 4.5651 | 1.9064 | 1.1476 | 2.734 | 1.632 | 0.334 | 0.347000003 | 1700 | 350 |
| `v0403_car_mugello_modernecosuper/v0403_car_mugello_modernecosuper_debug` | 4.5651 | 1.9064 | 1.1476 | 2.734 | 1.632 | 0.334 | 0.347000003 | 1700 | 350 |
| `v0008_car_autostraad_modernsportssaloon/v0008_car_autostraad_modernsportssaloon_civilian_01` | 4.561 | 1.9205 | 1.3723 | 3.025 | 1.592 | 0.3483 | 0.330000013 | 1250 | 300 |
| `v0008_car_autostraad_modernsportssaloon/v0008_car_autostraad_modernsportssaloon_debug` | 4.561 | 1.9205 | 1.3723 | 3.025 | 1.592 | 0.3483 | 0.330000013 | 1250 | 300 |
| `v0503_car_solar_modernsuv/v0503_car_solar_modernsuv_debug` | 4.5593 | 2.0232 | 1.6338 | 2.679 | 1.738 | 0.346 | 0.368000001 | 2200 | 235 |
| `v0508_car_solar_oldcompact/v0508_car_solar_oldcompact_debug` | 4.4507 | 1.8516 | 1.3069 | 2.804 | 1.47 | 0.321 | 0.289999992 | 915 | 120 |
| `v0002_car_autostraad_oldcampervan/v0002_car_autostraad_oldcampervan_civilian_01` | 4.3992 | 1.9961 | 2.0128 | 2.465 | 1.34 | 0.333 | 0.324999988 | 1100 | 100 |
| `v0002_car_autostraad_oldcampervan/v0002_car_autostraad_oldcampervan_civilian_z80` | 4.3992 | 1.9961 | 2.0128 | 2.465 | 1.34 | 0.333 | 0.324999988 | 1100 | 100 |
| `v0510_car_solar_modernroadster/v0510_car_solar_modernroadster_civilian_01` | 4.3279 | 1.7403 | 0.8155 | 2.636 | 1.624 | 0.319 | 0.339749992 | 1000 | 285 |
| `v0510_car_solar_modernroadster/v0510_car_solar_modernroadster_debug` | 4.3279 | 1.7403 | 0.8155 | 2.636 | 1.624 | 0.319 | 0.339749992 | 1000 | 285 |
| `v0400_car_mugello_vintagesports/v0400_car_mugello_vintagesports_civilian_01` | 4.2877 | 1.6632 | 1.2623 | 2.576 | 1.358 | 0.378 | 0.360000014 | 700 | 170 |
| `v0400_car_mugello_vintagesports/v0400_car_mugello_vintagesports_civilian_z80` | 4.2877 | 1.6632 | 1.2623 | 2.576 | 1.358 | 0.378 | 0.360000014 | 700 | 170 |
| `v0400_car_mugello_vintagesports/v0400_car_mugello_vintagesports_debug` | 4.2877 | 1.6632 | 1.2623 | 2.576 | 1.358 | 0.378 | 0.360000014 | 700 | 170 |
| `v0400_car_mugello_vintagesports/v0400_car_mugello_vintagesports_signature_01` | 4.2877 | 1.6632 | 1.2623 | 2.576 | 1.358 | 0.378 | 0.360000014 | 700 | 170 |
| `v0502_car_solar_modernsedan/v0502_car_solar_modernsedan_civilian_01` | 4.233 | 2.0267 | 1.5113 | 2.4183 | 1.6367 | 0.3161 | 0.317999989 | 1170 | 150 |
| `v0002_car_autostraad_oldcampervan/v0002_car_autostraad_oldcampervan_debug` | 4.2327 | 1.726 | 1.8193 | 2.465 | 1.34 | 0.333 | 0.324999988 | 1100 | 100 |
| `v0502_car_solar_modernsedan/v0502_car_solar_modernsedan_civic_police_01` | 4.2288 | 2.0196 | 1.6261 | 2.4183 | 1.6367 | 0.3161 | 0.317999989 | 1170 | 190 |
| `v0402_car_mugello_vintagesuper/v0402_car_mugello_vintagesuper_civilian_01` | 4.1954 | 1.736 | 0.7548 | 2.51 | 1.496 | 0.302 | 0.319999993 | 1020 | 240 |
| `v0402_car_mugello_vintagesuper/v0402_car_mugello_vintagesuper_civilian_z80_01` | 4.1954 | 1.736 | 0.7548 | 2.51 | 1.496 | 0.302 | 0.319999993 | 1020 | 240 |
| `v0402_car_mugello_vintagesuper/v0402_car_mugello_vintagesuper_debug` | 4.1954 | 1.736 | 0.7548 | 2.51 | 1.496 | 0.302 | 0.319999993 | 1020 | 240 |
| `v0502_car_solar_modernsedan/v0502_car_solar_modernsedan_debug` | 4.1435 | 1.8328 | 1.37 | 2.4183 | 1.6367 | 0.3161 | 0.317999989 | 1170 | 150 |
| `v0604_car_urga_buggy/v0604_car_urga_buggy_debug` | 4.0127 | 1.3618 | 1.3916 | 2.844 | 1.86 | 0.46 | 0.460000008 | 3000 | 170 |
| `v0604_car_urga_buggy/v0604_car_urga_buggy_military_01` | 4.0127 | 1.3618 | 1.3916 | 2.844 | 1.86 | 0.46 | 0.460000008 | 3000 | 170 |
| `v0604_car_urga_buggy/v0604_car_urga_buggy_military_z80` | 4.0127 | 1.3618 | 1.3916 | 2.844 | 1.86 | 0.46 | 0.460000008 | 3000 | 170 |
| `v0604_car_urga_buggy/v0604_car_urga_buggy_premium_01` | 4.0127 | 1.3618 | 1.3916 | 2.844 | 1.86 | 0.46 | 0.460000008 | 3000 | 170 |
| `v0604_car_urga_buggy/v0604_car_urga_buggy_rebel_01` | 4.0127 | 1.3618 | 1.3916 | 2.844 | 1.86 | 0.46 | 0.460000008 | 3000 | 170 |
| `v0604_car_urga_buggy/v0604_car_urga_buggy_signature_preorder` | 4.0127 | 1.3618 | 1.3916 | 2.844 | 1.86 | 0.46 | 0.460000008 | 3000 | 170 |
| `v0513_car_solar_oldfourdoorhatch/v0513_car_solar_oldfourdoorhatch_civilian_01` | 3.9692 | 1.9265 | 1.4302 | 2.463 | 1.312 | 0.2598 | 0.270000011 | 600 | 165 |
| `v0003_car_autostraad_racinghothatch/v0003_car_autostraad_racinghothatch_civilian_01` | 3.9034 | 1.7447 | 1.3818 | 2.473 | 1.496 | 0.311 | 0.314999998 | 800 | 235 |
| `v0003_car_autostraad_racinghothatch/v0003_car_autostraad_racinghothatch_civilian_z80` | 3.9034 | 1.7447 | 1.3818 | 2.473 | 1.496 | 0.311 | 0.314999998 | 800 | 235 |
| `v0003_car_autostraad_racinghothatch/v0003_car_autostraad_racinghothatch_debug` | 3.9034 | 1.7447 | 1.3818 | 2.473 | 1.496 | 0.311 | 0.314999998 | 800 | 235 |
| `v0512_car_solar_oldtwodoorhatch/v0512_car_solar_oldtwodoorhatch_civilian_01` | 3.8647 | 1.8978 | 1.4018 | 2.383 | 1.32 | 0.2658 | 0.270000011 | 600 | 180 |
| `v0513_car_solar_oldfourdoorhatch/v0513_car_solar_oldfourdoorhatch_debug` | 3.8428 | 1.5994 | 1.1913 | 2.463 | 1.312 | 0.2598 | 0.270000011 | 600 | 165 |
| `v0405_car_mugello_moderncircuitracer/v0405_car_mugello_moderncircuitracer_civilian_01` | 3.7724 | 1.4477 | 1.0537 | 3.11 | 1.428 | 0.3205 | 0.326000005 | 250 | 280 |
| `v0405_car_mugello_moderncircuitracer/v0405_car_mugello_moderncircuitracer_debug` | 3.7724 | 1.4477 | 1.0537 | 3.11 | 1.428 | 0.3205 | 0.326000005 | 250 | 280 |
| `v0512_car_solar_oldtwodoorhatch/v0512_car_solar_oldtwodoorhatch_debug` | 3.7526 | 1.5903 | 0.8522 | 2.383 | 1.32 | 0.2658 | 0.270000011 | 600 | 180 |
| `v0000_car_autostraad_oldjeep/v0000_car_autostraad_oldjeep_debug` | 3.4699 | 2.0105 | 1.8748 | 2.709 | 1.542 | 0.432 | 0.411500007 | 840 | 160 |
| `v0509_car_solar_modernmini/v0509_car_solar_modernmini_civilian_01` | 3.4417 | 1.6058 | 0.8108 | 2.22 | 1.364 | 0.3 | 0.291000009 | 450 | 210 |
| `v0509_car_solar_modernmini/v0509_car_solar_modernmini_debug` | 3.4417 | 1.6058 | 0.8108 | 2.22 | 1.364 | 0.3 | 0.291000009 | 450 | 210 |
| `v0500_car_solar_oldmini/v0500_car_solar_oldmini_civilian_01` | 3.2245 | 1.5292 | 1.3696 | 1.936 | 1.24 | 0.236 | 0.243000001 | 510 | 150 |
| `v0500_car_solar_oldmini/v0500_car_solar_oldmini_signature_01` | 3.2245 | 1.5292 | 1.3696 | 1.936 | 1.24 | 0.236 | 0.243000001 | 510 | 150 |
| `v0500_car_solar_oldmini/v0500_car_solar_oldmini_debug` | 3.1126 | 1.4633 | 1.2871 | 1.936 | 1.24 | 0.236 | 0.243000001 | 510 | 150 |
| `v3001_bike_autostraad_snowmobile/v3001_bike_autostraad_snowmobile_debug` | 2.6188 | 1.038 | 0.9709 | 1.5738 | 1.118 | 0.1953 | 0.360000014 | 750 | 150 |
| `v3501_bike_solar_modernmoped/v3501_bike_solar_modernmoped_civilian_01` | 2.1619 | 0.6732 | 1.0792 | 1.4037 | 0.0 | 0.1062 | 0.25 | 180 | 120 |
| `v3501_bike_solar_modernmoped/v3501_bike_solar_modernmoped_debug` | 2.1619 | 0.6732 | 1.0792 | 1.4037 | 0.0 | 0.1062 | 0.25 | 180 | 120 |
| `v0866_car_na_ladbil/v0866_car_na_ladbil_civilian_01` | 1.8346 | 0.8169 | 0.6012 | 1.473 | 0.876 | 0.203 | 0.200000003 | 50 | 200 |
| `v0866_car_na_ladbil/v0866_car_na_ladbil_debug` | 1.8346 | 0.8169 | 0.6012 | 1.473 | 0.876 | 0.203 | 0.200000003 | 50 | 200 |
| `v0012_car_autostraad_atv/v0012_car_autostraad_atv_civilian_01` | 1.7462 | 0.4892 | 0.7903 | 1.256 | 0.992 | 0.2456 | 0.270000011 | 80 | 115 |
| `v0012_car_autostraad_atv/v0012_car_autostraad_atv_civilian_01_z80` | 1.7462 | 0.4892 | 0.7903 | 1.256 | 0.992 | 0.2456 | 0.270000011 | 80 | 115 |
| `v0012_car_autostraad_atv/v0012_car_autostraad_atv_debug` | 1.7462 | 0.4892 | 0.7903 | 1.256 | 0.992 | 0.2456 | 0.270000011 | 80 | 115 |
| `v0012_car_autostraad_atv/v0012_car_autostraad_atv_signature_01` | 1.7462 | 0.4892 | 0.7903 | 1.256 | 0.992 | 0.2456 | 0.270000011 | 80 | 115 |
| `v0506_car_solar_oldtractor/v0506_car_solar_oldtractor_civilian_01` | 1.6915 | 0.8951 | 0.6649 | 1.9848 | 1.438 | 0.494 | 0.349999994 | 1600 | 25 |
| `v0506_car_solar_oldtractor/v0506_car_solar_oldtractor_civilian_z80` | 1.6915 | 0.8951 | 0.6649 | 1.9848 | 1.438 | 0.494 | 0.349999994 | 1600 | 25 |
| `v0506_car_solar_oldtractor/v0506_car_solar_oldtractor_debug` | 1.6915 | 0.8951 | 0.6649 | 1.9848 | 1.438 | 0.494 | 0.349999994 | 1600 | 25 |
| `v3402_bike_mugello_modernsuper/v3402_bike_mugello_modernsuper_civilian_01` | 1.6699 | 0.4605 | 0.9379 | 1.4197 | 0.0 | 0.1654 | 0.299899995 | 190 | 320 |
| `v3402_bike_mugello_modernsuper/v3402_bike_mugello_modernsuper_debug` | 1.6699 | 0.4605 | 0.9379 | 1.4197 | 0.0 | 0.1654 | 0.299899995 | 190 | 320 |
| `v3500_bike_solar_oldmoped/v3500_bike_solar_oldmoped_civilian_01` | 1.6135 | 0.5561 | 0.8492 | 1.531 | 0.0 | 0.1039 | 0.200000003 | 105 | 100 |
| `v3500_bike_solar_oldmoped/v3500_bike_solar_oldmoped_debug` | 1.6135 | 0.5561 | 0.8492 | 1.531 | 0.0 | 0.1039 | 0.200000003 | 105 | 100 |
| `v3600_bike_urga_combatdirt/v3600_bike_urga_combatdirt_debug` | 1.5815 | 0.5957 | 0.8246 | 1.3982 | 0.0 | 0.2197 | 0.319999993 | 180 | 150 |
| `v3600_bike_urga_combatdirt/v3600_bike_urga_combatdirt_military_01` | 1.5815 | 0.5957 | 0.8246 | 1.3982 | 0.0 | 0.2197 | 0.319999993 | 180 | 150 |
| `v3600_bike_urga_combatdirt/v3600_bike_urga_combatdirt_rebel_01` | 1.5815 | 0.5957 | 0.8246 | 1.3982 | 0.0 | 0.2197 | 0.319999993 | 180 | 150 |
| `v3000_bike_autostraad_trials/v3000_bike_autostraad_trials_civilian_01` | 1.5228 | 0.5586 | 0.8603 | 1.6934 | 0.0 | 0.1981 | 0.346700013 | 60 | 140 |
| `v3000_bike_autostraad_trials/v3000_bike_autostraad_trials_debug` | 1.5228 | 0.5586 | 0.8603 | 1.6934 | 0.0 | 0.1981 | 0.346700013 | 60 | 140 |
| `v3000_bike_autostraad_trials/v3000_bike_autostraad_trials_signature_01` | 1.5228 | 0.5586 | 0.8603 | 1.6934 | 0.0 | 0.1981 | 0.346700013 | 60 | 140 |
| `v3502_bike_solar_modernroad/v3502_bike_solar_modernroad_civilian_01` | 1.4734 | 0.443 | 0.699 | 1.3715 | 0.0 | 0.1802 | 0.280000001 | 220 | 235 |
| `v3502_bike_solar_modernroad/v3502_bike_solar_modernroad_debug` | 1.4734 | 0.443 | 0.699 | 1.3715 | 0.0 | 0.1802 | 0.280000001 | 220 | 235 |
| `v3401_bike_mugello_modernsport/v3401_bike_mugello_modernsport_civilian_01` | 1.414 | 0.5701 | 0.7163 | 1.3905 | 0.0 | 0.1733 | 0.280000001 | 170 | 300 |
| `v3401_bike_mugello_modernsport/v3401_bike_mugello_modernsport_debug` | 1.414 | 0.5701 | 0.7163 | 1.3905 | 0.0 | 0.1733 | 0.280000001 | 170 | 300 |
| `v3503_bike_solar_oldroad/v3503_bike_solar_oldroad_civilian_01` | 1.0057 | 0.5997 | 0.8304 | 1.3796 | 0.0 | 0.1821 | 0.309599996 | 120 | 150 |
| `v3503_bike_solar_oldroad/v3503_bike_solar_oldroad_debug` | 1.0057 | 0.5997 | 0.8304 | 1.3796 | 0.0 | 0.1821 | 0.309599996 | 120 | 150 |

## Notes

- 1 vehicles have stations but no comparable body (air/sea, or no mesh bounds).
- 0 land vehicles lack a body bound; they are in the fleet table but cannot be scored.
- `land_global` stations are named members, so this table is a decode, not a heuristic: the Serpente's four quads match its `.physicsc` copy to the last digit.
