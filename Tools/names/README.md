# Derived names

Name lists in here were **not** shipped with the game or Gibbed. They were
recovered by hash search, and every line is accepted by `jc3index.py` only when
its Jenkins hash is an actual tab record of the archive it lands in — a wrong
guess cannot enter `INDEX.json`, but the provenance is weaker than a filelist, so
the index marks these rows `"source": "derived-names"`.

| file | how it was derived |
|---|---|
| `jc3_navmesh_tiles.filelist` | The 88 unnamed patch records that begin with the Havok binary tag `0x57E0E057` and contain `hkaiNavMesh` / `hkcdStaticAabbTree` were matched against every `ai/tiles/<x>_<y>.navmeshc` path for `x, y` in 0..299. Each hit is unique; the hash equality plus the decoded content (a Havok navmesh) is what makes the name certain. |
| `jc3_neighbour_order.filelist` | A `.arc` stores payloads in ascending path order, so an unnamed record is bracketed by its alphabetical neighbours. `patch_win64/game4` `9EBCE9A4` sits between `…/dlc3_starfish_base_02/…_landmark_dif.hmddsc` and `…/dlc3_starfish_base_04/…_landmark_dif.hmddsc`, giving the `_03` sibling; its hash equals the record, and the same ordering reproduces a known neighbour (`dlc3_satellite_pontoon_14`, doubled directory) exactly. |

Two `.wavc` records stay unnamed: `patch_win64/game4` `016DE9D1` (bracketed between
`sound/dialogue/ara/mission_mm320_dial_gameplay_090.wavc` and `…_gameplay_start05.wavc`, but no
numeric or known-basename candidate hashes to it) and `archives_win64/game67` `966DB7BC`, which is
the only entry in that archive and so has no neighbours at all.
