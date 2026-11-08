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
| `jc3_fsb5_token.filelist` | `.wavc` payloads are a 16-byte prefix + FMOD **FSB5**; the FSB5 name table holds one **language-invariant** token per take (`a1630394639`). The Japanese (`BEA6350C`, game64) and English (`82088DE4`, game56) copies of `mission_mm110_dial_defendtheplane_090.wavc` carry that token, and so does the unnamed `archives_win64/game67` `966DB7BC`. The basename is therefore known; hashing `sound/dialogue/<lang>/` + basename against `966DB7BC` hits only `pol`, a 1-entry Polish language shard. |

| `jc3_mm320_sams01.filelist` | The **last** unnamed record, `patch_win64/game4` `016DE9D1` (84,720 B, one-sample FSB5 v1, 11,025 Hz mono, 243,648 samples = 22.100 s, token `1606523576`). Its token maps to **no** named file in any language — a unique orphan, so the Polish lever cannot be used — and it is bracketed at `sound/dialogue/ara/mission_mm320_dial_gameplay_090.wavc` < it < `…_gameplay_start05.wavc`. The basename inside that bracket is a **word** take, which the earlier numeric sweep could not reach: the 11,591 take suffixes and 796 word tokens of every named dialogue take, crossed with `01…09`/`alt` variants, give exactly one hash hit out of 514,994 candidates, `mission_mm320_dial_gameplay_sams01`. English ships `sams02`/`sams03` and no `sams01`, which is why the take has no sibling copy. Evidence: `derived_016de9d1.json`; re-proved by `Tools/scripts/g2_last_entry.py --check` (13/13). |

**Status: every archive entry is named** — `INDEX.json` reports 81,953 / 81,953 and 0 unnamed,
91 of them from this directory (88 navmesh tiles, 1 `.hmddsc`, 1 Polish `.wavc`, 1 Arabic `.wavc`).
