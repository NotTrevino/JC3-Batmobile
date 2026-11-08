# Existing JC3 community format writers — check before building our own

STATUS: done — desk survey, read-only. No executable was downloaded or run; no file was written to a game
install or dropzone; the only binary touched was `D:/Games/Just Cause 3/fmod_studio_F.dll`, opened read-only for
string/export names. Question: for writers (a)–(f) in the brief, does a public tool already do the job, what does
it write, which JC3 version does it target, what licence, and does it cover our case?

Labels: **decoded** = read from a file/page at the cited location; **derived** = computed from decoded facts with
the rule stated; **UNKNOWN** = not established, with what was tried.

---

## 0. Short answer

| # | writer we need | public tool that writes it? | covers our case? |
|---|---|---|---|
| a | Scaleform GFx (`ui/hud.gfx`) | **yes, general-purpose**: JPEXS FFDec (`-replace` / `-importScript` / `-swf2xml` → `-xml2swf`, `-header -set gfx`) | **partly** — it can recompile an AS3 edit into a `.gfx`, but AS3 editing is flagged experimental, JC3's AVM2 GFx v0f compatibility is unproven, and nobody has documented a modified `hud.gfx` loading from the dropzone |
| b | ADF append (camera shake) | **yes for instances/array elements of existing types**: Gibbed `ConvertAdf`, tim42 fork, Neam's Modified Gibbed's Tools (XML round trip) | **partly** — appending an instance is supported as a hand-edit recipe; **adding a new type is explicitly forbidden** ("type-definitions … DO NOT TOUCH") |
| c | FMOD bank: add samples/events | **no** — Fmod Bank Tools only swaps payloads of the same duration; no FEV/FSB5 *authoring* tool found | **no** |
| d | `.effc` add an emitter | **no JC3/APEX tool found** | repo already has a value-edit writer; **array/instance growth is unproven** |
| e | `.physicsc` add a hull / hinge | **no JC3/APEX tool found**; generic HavokLib can serialise packfiles but not the JC3 wrapper | repo already has hull-replace and hinge-append prototypes; **no external or in-game proof** |
| f | `keymap_gamepad.bin` editor | **no** — the community edits a text `kepmap.txt` in the save folder instead | **no** |

Consequence for ROADMAP §4: **RB-6 is too strong** (a GFx writer exists; the open fact is JC3 load/AVM2, not
authored bytes). **RB-8 is right about the banks** (FEV v56/b50, no project) but the installed DLL is FMOD
**Studio**, not FMOD Ex — the two facts coexist and the consumer is UNKNOWN. **RB-10 is partly out of date**: ADF
append, `.effc` value edits and `.physicsc` hull/hinge writes are already in this repo; what is genuinely missing
is ADF *new type* append and `.effc` *growth*.

---

## 1. Findings per writer

### (a) Scaleform GFx writer — recompile `ui/hud.gfx` after an AS3 edit

**Tool: JPEXS Free Flash Decompiler (FFDec).**
URL: <https://github.com/jindrapetrik/jpexs-decompiler> (wiki: <https://github.com/jindrapetrik/jpexs-decompiler/wiki/Commandline-arguments>)

What it writes (decoded from the CLI reference page, v26.4.0):

- `-replace <infile> <outfile> (<characterId>|<scriptName>) <importDataFile> …` — "Replaces the data of the
  specified BinaryData, Image, Shape, Text, Font, Sound tag **or Script**", and for AS3 the imported entity may
  be a P-Code body. This is a recompile path for an AS3 edit into the same movie.
- `-importScript <infile> <outfile> <scriptsfolder>` — bulk AS3 import.
- `-swf2xml` / `-xml2swf` — whole-movie round trip through XML; `-header -set gfx true` writes the GFx header
  flag; `-compress`, `-decompress`, `-dumpSWF`, `-dumpAS3` exist for inspection.
- The code itself has a GFx save path: `SWF.java` — `public void saveTo(OutputStream os, boolean gfx, boolean includeImported)` and the signature table includes `"GFX" // Uncompressed ScaleForm GFx` and `"CFX" // Compressed ScaleForm GFx`
  (<https://github.com/jindrapetrik/jpexs-decompiler/blob/master/libsrc/ffdec_lib/src/com/jpexs/decompiler/flash/SWF.java>).

Game version targeted: **none** — generic SWF/GFX. The wiki Features page lists "GFx ScaleForm files support
(*.GFX)" (<https://github.com/jindrapetrik/jpexs-decompiler/wiki/Features>).

Licence (decoded from the repository README): "FFDec Application is licensed under the GNU GPL v3
(GPL-3.0-or-later) licence".

Limits that matter to us (decoded quotes from the FAQ, <https://github.com/jindrapetrik/jpexs-decompiler/wiki/FAQ>):

- "Direct editation of AS is experimental - it might damage your SWF file."
- "GFX files usually store all images externally and there are only external file names stored in the GFX file.
  Make sure you have all the necessary image files the GFX need in the GFX directory…" — so a repack must keep
  the movie's texture references intact (JC3 streams art from `.tfc`; see `Working/HUD/CLUSTER.md` row
  "afterburner").
- An old GFX import bug (#1727) was fixed only in nightly 2131, so use a current build:
  <https://www.free-decompiler.com/flash/issues/1727-import-swf-xml-error>.

Other GFx writers seen:

| tool | writes | licence | covers us? |
|---|---|---|---|
| Adobe **GFxExporter** (Flash CS extension) | `.swf` → `.gfx` | proprietary, part of discontinued Autodesk Gameware (PCGamingWiki: "On July 12, 2017, Autodesk has discontinued Autodesk Gameware, including Scaleform GFx", <https://www.pcgamingwiki.com/wiki/Scaleform_GFx>) | no — not obtainable, and needs a FLA/AS3 project |
| FFDec in other game communities (KH3, Hitman) | edited GFX in place, then repacked by the game's own tool | — | technique, not a JC3 tool: <https://github.com/KH3-Modding-Org/OpenKH3Modding/blob/main/Tutorials/Scaleform%20Quick%20Guide.md>, <https://github.com/glacier-modding/glaciermodding.org/blob/main/docs/modding/hitman/guides/scaleform/fontreplacement.md> |

**Does anyone document loading a modified `hud.gfx` from the JC3 dropzone?** No — **UNKNOWN / no evidence found.**
Searched: Just Cause Wiki `Modifying (JC3)` (its tool table lists no Scaleform or HUD tool at all), Just Cause 3
Nexus top/all-time and "mods of the month", VideoGameMods JC3, Steam guides/discussions, GitHub. The only JC3
HUD mod found is Nexus `No-HUD-No-Effects`, which "Utilizes ShaderToggler to make the HUD & Effects togglable"
(<https://www.nexusmods.com/justcause3/mods/40>) — a ReShade shader toggle, i.e. it deliberately does **not**
touch `hud.gfx`. The wiki's dropzone rule is generic: "any files you place in here will overwrite the default
files the game comes with… Just Cause 3 also cares about file paths"
(<https://justcause.fandom.com/wiki/Modifying_(JC3)>) — it is not evidence that `ui/hud.gfx` is honoured.
Repo agrees it is unproven: `Working/Roadmap/hud_cam_lights_fx.md` NEW-HUD-4 (U5/U6) and
`RB/HUD.md`: "`ui/hud.gfx` was read, not replaced".

### (b) ADF writer — append a new type or instance (camera shake)

**Tool: Gibbed's Just Cause 3 Tools (`ConvertAdf`).**
URL: <https://github.com/gibbed/Gibbed.JustCause3> (local copy in `Tools/Gibbed`, source in `Tools/GibbedSrc`).

- Git-tag/commit: original, 2015-era JC3; 19 commits; Zlib licence (decoded from `license.txt` in the repo:
  "Permission is granted to anyone to use this software for any purpose…").
- Writes: ADF ⇄ XML. The fork in the repo states it adds "A (working) and generic ADF serializer and
  deserializer" (`Tools/Gibbed/README.md`), i.e. XML → `.adf`, not just a reader.

**Tool: tim42's fork** — "A (working) and generic ADF serializer and deserializer", "fixes bugs from the
original", Zlib + modifications by Timothée Feuillet. <https://github.com/tim42/gibbed-justcause3-tools-fork>
(index: <https://eonzenx.github.io/apex-resource-index/tools/just_cause_3_tools_fork>).

**Tool: Neam's Modified Gibbed's Tools** — the one the community actually uses for stat files.
URL: <https://videogamemods.com/vgm/justcause3/mods/modified-gibbeds-tools> (v1, 2016-03-31, updated 2016-06-06,
JC3 + Sky Fortress/MLA era).

Decoded quotes that answer the "append" question:

- "For most of the ADF files (.*tunec, .onlinec, …) the conversion to and from the xml file should work."
- `<type-definitions WARNING="DO NOT TOUCH …">` (the page's own emphasis, ellipsis mine) — "touching — or even
  looking at — the content of the type-definitions tag will most likely break everything."
- "You can add new elements / remove elements to/from any Array elements. (but NOT InlineArrays)"
- "If you plan to add an array, you have to search for the greatest ID (they may not be in the correct order),
  add one and voilà, you've got you're new ID."
- "First order <member> must have an ID." / "Arrays are typed. Please use the correct one."
- "InlineArrays are evils. Please don't mess with them."

So: **new instance of an existing type / new array element = supported as a documented hand-edit; new type =
not supported by any tool found.** Licence: the page says "read the LICENSE.txt and README.txt files in the
archive" — **UNKNOWN** (archive not downloaded, per the brief).

**Tool: UnknownMiscreant's JC3 tools (jc3tools.7z)** — linked from Luke JC's guide, hosted on a Discord CDN
(<https://lukejcdotcom.wordpress.com/2019/12/27/just-cause-modding-getting-started>). No public repository; the
JC4 successor is marked "status/private" (<https://eonzenx.github.io/apex-resource-index/tools/ashen_just_cause_4_tools>).
Decoded caveats: the JC4 page says "AvalancheData - ADF converter… **Very broken**. Only able to convert some ADF
files to XML atm"; Luke JC says of the JC3 set: "unknown's set every value to zero on repack due to a bug in those
tools", which is why Naem's tools are used for stat files. Licence **UNKNOWN** (private binaries).

**Tool: deca** (kk49) — MIT, <https://github.com/kk49/deca>. ADF row: "**Extractable, Parsed**", with "Missing
code for types that have hardcoded parsers in EXE(?)"; no ADF writer at all. Its "Basic rebuilding of archive
files" is archive-level, "Set pieces do not".

**Tool: Apex Tools (EonZeNx)** — <https://github.com/EonZeNx/apex-tools>. File-type table: "ADF | 4 | **WIP**",
"Releases: Initial release planned once full Just Cause 3 support is achieved". No LICENSE file in the repo
listing at the time checked → licence **UNKNOWN**. Not usable today.

Verdict for camera shake: if the shake object is an instance of a class **already present in the target ADF file**,
it can be appended today with Neam's XML recipe (new array element / new instance ID) or with this repo's
`adf_append.py`. If it needs a **new class in the type dictionary**, no public tool does it, and the only known
tool says don't touch that block.

### (c) FMOD bank writer — add samples or events

**Which format is right?** The project's note is right: **FMOD Designer/Ex FEV v56 build 50 with an embedded
FSB5**, decoded from the banks themselves — `Research/JC3Grab/JC3_AUDIO.md`: "Every JC3 sound bank here is a
**FMOD Designer/Ex event bank** (RIFF `FEV `, `FMT ` version 56 build 50), not an FMOD Studio bank: the event
graph and one FSB5 sample bank share one file"; table row: container `RIFF`/`FEV `, `FMT ` version 56 build 50;
samples `SND ` → `FSB5` v1, 649 samples.

**Why the DLL name misleads.** Decoded from the installed binary `D:/Games/Just Cause 3/fmod_studio_F.dll`
(5,230,592 B, 2017-02-04), read-only `grep -a`:

- exports include `FMOD_Studio_System_Create`, `FMOD_Studio_EventDescription_Create`, `FMOD_System_Create`
  (the Studio 1.x API);
- strings: `FMOD Studio` ×2, `FMOD Ex` ×0, `FSB4`, `FSB5`, `FSBANK`;
- no `EventSystem_Create` export (the FMOD Ex/Designer API) was found.

Derived: the shipped runtime is **FMOD Studio 1.x**, while the shipped *data* is FEV v56. How a Studio runtime
consumes an FEV event bank is **UNKNOWN** (there is also `jc3AudioDSP_MultibandCompressor_SSE_F.dll` in the root,
so Avalanche ships its own DSP layer; whether JC3 reads the FEV sections itself, or links a renamed Ex runtime,
would need the EXE's import table — not read here). Either way the **bank bytes are FEV**, so the authoring
question is unchanged.

**Tool: Fmod Bank Tools** (Wouldubeinta).
URL: <https://github.com/Wouldubeinta/Fmod-Bank-Tools> (CLI: <https://github.com/Wouldubeinta/Fmod-Bank-Tools-CLI>).
Licence: **GPL-3.0**. Versions current to 2026 (2.2.4.32); generic FMOD, not JC3-specific.

Decoded quotes (<https://github.com/Wouldubeinta/Fmod-Bank-Tools/blob/master/README.md>):

- "Extracts and Rebuilds Fmod .bank files."
- "To rebuild the bank files, you will need to replace the wav files with your own that has the same file type,
  bitrate etc. **THE DURATION MUST BE SAME OR LESS THAN ORIGINAL AUDIO.**"
- Encrypted banks need a password `.txt` beside the bank; the tool then decrypts/re-encrypts.

It also has a known bank-version/size failure mode (issue #13: "there could be a issue with that bank version.
There is a lot of different bank versions out there, so it's hard to have support for all";
<https://github.com/Wouldubeinta/Fmod-Bank-Tools/issues/13>). This is the same ceiling B-11 already works under:
payload swap only.

**Tool: fsbank / fsbankcl** (FMOD's official FSB builder) — builds an `.fsb` from WAVs; used by the newer
`FSB-BANK-Extractor-Rebuilder` (GPL-3.0): "Uses the official FMOD tool fsbankcl.exe to generate FSB files
compatible with the original" (<https://github.com/IZH318/FSB-BANK-Extractor-Rebuilder>). It builds **sample
banks**, not the FEV event graph — adding a *new event* still needs the FEV.

**Tool: FMOD Designer 2010** — the only thing that builds a FEV, and only from an `.fdp` project. Decoded from the
FMOD forums (<https://qa.fmod.com/t/fev-editing/11224>): "The FEV/FSB are the compiled output for the game,
generated from the FDP (FMOD Designer Project) file. You need to locate the FDP used to generate the FEV/FSB…".
And FMOD Studio cannot do it: "FMOD Studio cannot export FSB/FEV files or save the project as a FDP"
(<https://qa.fmod.com/t/how-do-i-create-fsb-files-with-fmod-studio/11683>). No `.fdp` ships with JC3 (repo search:
no project file), so **event authoring is blocked at the source, not at the tool**.

Coverage of our case: sample replacement **yes** (same-length, which B-11 already exploits); adding a sample or an
event **no**.

### (d) `.effc` writer — add an emitter

**No public JC3/APEX `.effc` tool found.** Absence evidence (decoded from each source's own format/tool tables):

- Just Cause Wiki `Modifying (JC3)` tool table: no effects tool (<https://justcause.fandom.com/wiki/Modifying_(JC3)>).
- deca's file-type table lists `CFX` (Scaleform) but no `effc`/effect type (<https://github.com/kk49/deca/blob/main/README.md>).
- Apex Tools format table: IRTPC, RTPC, AAF, SARC, ADF, TAB/ARC, DDSC/AVTX — no effects format
  (<https://github.com/EonZeNx/apex-tools>).
- Searches for "effc Just Cause", "Avalanche effect file format", "add emitter JC3" returned nothing on-topic.

Searched: wiki, Nexus JC3, VGM, GitHub, Steam. Verdict: **UNKNOWN whether any private tool exists**; none public.

**In-repo capability (decoded, `Working/Effects/EFFC_WRITER.md`):** 95 `.effc` files decoded with **0 decode
failures**; strict round trip byte-identical 88/95, **carry round trip 95/95**; "edited copy re-read + reverted |
PASS", with a real value edit (`EmitterTemplates[0].MaxParticles` 60 → 317) read back. So the repo can **write
`.effc` values**; it has not demonstrated **growing an array or adding a template**, and `bm_fx.py`'s B-08 output
(`Working/Effects/bm_fx_edits.json`) is an edit of the donor's existing graph, not new emitters.

### (e) Havok `.physicsc` writer — append a hull or hinge

**No public JC3 `.physicsc` tool found.** Generic Havok libraries exist but do not cover the JC3 container:

- **HavokLib** (PredatorCZ, GPL-3.0): "an independent Havok packfile serialize and XML store library", "Havok
  5.0.0 - 2017", but "**Binary exporting is an experimental feature for now**", and the listed supported classes
  are `hkaSkeleton` / `hkRootLevelContainer` (animation), not `hkpLimitedHingeConstraintData`
  (<https://github.com/PredatorCZ/HavokLib>). kk49's fork is what deca uses
  (<https://github.com/kk49/HavokLib>).
- JC3 wraps Havok in its own header: the wiki's JC2 sibling page describes the same family as "a proprietary
  Havok format wrapped in a JC2-specific header" (<https://justcause.fandom.com/wiki/Per-mesh_physics_attributes>),
  which is why a raw HavokLib packfile is not loadable.
- The wiki's `Modifying (JC3)` tool table lists nothing for collision or physics.

**In-repo capability (decoded, `Research/JC3Grab/PHYSICS_WRITE.md`):** donor `.physicsc` re-emitted byte-for-byte
(340,368 B identical, all 54 hulls), remap stress +16 B on all 430 objects PASS, scaled hull PASS, and a
**size-changing hull replace** (704 B slot ← 1776 B hull) PASS with 0 shape-check violations. `bm_physicsc_hinges.py`
then "append[s] the two Batmobile hinges to a COPY" as two 304-byte `hkpLimitedHingeConstraintData` objects at
constraint indices 11/12, and a report exists (`tmp/freebuff/reports/physicsc-append-hinges.md`). So the repo has a
prototype writer; **no in-game proof** (blocked by the test ban / P1), and no second implementation to check it
against.

### (f) `keymap_gamepad.bin` editor

**No tool found.** The community does not edit the `.bin`; it edits a text file in the save folder:

- "Go to C:\Users\*YOUR USER NAME*\Documents\Square Enix\Just Cause 3\Saves … Open 'kepmap.txt' in notepad or your
  favorite editor … Search for DETONATE_EXPLOSIVE … Below DETONATE_EXPLOSIVE should be `"key": "PC_F"`"
  (<https://steamcommunity.com/app/225540/discussions/0/485623406960065017>).
- And it may not even be read: "Seems like since the latest patch JC3 will write to
  \Documents\Square Enix\Just Cause 3\Saves\/kepmap.txt, but won't read from it."
  (<https://steamcommunity.com/app/225540/discussions/0/405693392927110932>).
- PCGamingWiki notes the UI keeps showing default prompts after remapping
  (<https://www.pcgamingwiki.com/wiki/Just_Cause_3>) — consistent with a client-side text remap, not a shipped
  keymap asset edit.

The wiki's tool table lists no input/keymap tool. **UNKNOWN** whether `kepmap.txt` covers gamepad bindings at all
(the quoted edits are keyboard scancodes/`PC_*` names).

**In-repo capability:** `Tools/scripts/jc3_input.py` **reads** all four keymap files with a byte-accounting oracle
(blocks tile exactly; 131/145 gamepad bindings base/patch), and `Research/JC3Grab/INPUT.md` decodes the binding
model. No writer exists, in the repo or in the community.

---

## 2. Already in repo (names only)

`Tools/`: `Blender` (empty), `Deca`, `Gibbed`, `Gibbed-patched`, `GibbedSrc`, `jc3-console-thingy-src`, `JCMR`,
`JCMR-src`, `names`, `scripts`, `Universal-Modder`, `vgmstream-win64`.

`Tools/scripts/` relevant to these six writers:

- ADF: `adf_append.py`, `adfdump.py`, `jc3adf.py`, `jc3_entity.py`, `_adftypes.py`.
- effc/effects: `effc_writer.py`, `jc3fx.py`, `bm_fx.py`, `t17_fx.py`, `fx9_haze.py`, `fx13_casings.py`.
- physics/collision: `jc3hkx.py`, `bm_physicsc_hinges.py`, `bm_collision.py`, `bm_colhull.py`, `bm_colmesh.py`,
  `jc3_constraint_axes.py`, `jc3_constraint_code.py`, `joint_fields.py`, `physics_stations.py`.
- audio: `jc3audio.py`, `bm_audio.py`, `_fev.py`, `_fev2.py`, `_fbank.py`, `_fbank2.py`, `_fsb.py`,
  `_fsbnames.py`, `_fbfs.py`, `_bank_parse.py`, `_bank_carve.py`, `_bank_convert.py`, `_wem_*.py`.
- HUD/Scaleform: `bmak_hud.py`, `bmak_hud_cluster.py`, `bmak_hud_inventory.py`, `hud_spec.py`,
  `hud_cluster_elements.py`, `hud_radar_recheck.py`, `jc3hudwpn.py`, `t19_hud.py`, `qa1_hud.py` — **readers only**.
- input: `jc3_input.py`, `jc3_input_d11.py`, `grab_keyboard_bindings.py`, `grab_controls*.py` — **reader only**.
- third-party binaries: `Tools/Gibbed/*` (`ConvertAdf`, `ConvertRBM`, `ConvertTexture`, `Pack`, `SmallPack`,
  `SmallUnpack`, `Unpack`, `DLCPacker`, `HashName`, `QueryHashList`, `Batch`, `GenerateName`, `RebuildFileLists`),
  `Tools/GibbedSrc/*` (+ `patched-adf-reader.patch`), `Tools/Deca/*`, `Tools/Universal-Modder/*`,
  `Tools/JCMR/jc-model-renderer.exe`, `Tools/vgmstream-win64/*`.

Missing from every list above: a SWF/GFx **writer**, an **FEV/FSB5 writer**, a **keymap writer**, an ADF
**type-dictionary** writer.

---

## 3. Gaps that remain truly unsolved (after crediting the tools above)

1. **GFx: JC3 load + AVM2 compatibility, not byte authoring.** FFDec can recompile a script into a `.gfx`
   (`-replace … <scriptName>`), so "no writer exists" is false. What is unproven: (i) whether JC3's Scaleform
   loader accepts a FFDec-written AVM2 GFx v0f file (repo `CLUSTER.md`: BmAK movie and JC3 `hud.gfx` are both
   "AVM2 GFx v0f", so it is plausible but unmeasured), (ii) whether a private `ui/hud.gfx` is loaded at all
   (no community report exists), (iii) whether external art paths survive the repack.
2. **ADF: a new *type* in the dictionary.** No public tool will grow `<type-definitions>`; Neam's page forbids
   it. Appending an instance/array element of an existing class is solved; camera shake must reuse an existing
   class or this stays blocked.
3. **FMOD: new events and new samples.** No FEV authoring without an `.fdp`; Fmod Bank Tools is swap-only and
   duration-capped; fsbank builds FSBs, not events. Only an FSB5/EVTS writer (or a re-created FDP) closes this.
4. **`.effc`: growing the graph.** The repo writer proves value edits; adding an `EmitterTemplate` (array count,
   instance table, string/type references) is unproven and has no community precedent.
5. **`.physicsc`: independent verification.** The repo can append a hull or hinge object; nothing external can
   read the result and no in-game contact test has run (P1). Treat the hinge append as a prototype until then.
6. **`keymap_gamepad.bin`: writer + game reading it.** No tool anywhere; even the text route is reported as
   write-only since a 2016 patch, and gamepad coverage of `kepmap.txt` is UNKNOWN.

---

## 4. Recommended 5-minute experiment per gap

Each is offline and read-only against the game; the oracle would fail if the claim were wrong. None launches JC3.

**E-a — GFx: does a FFDec re-save of `ui/hud.gfx` stay byte-stable apart from the edit?**
`ffdec -dumpSWF` the game's `ui/hud.gfx` and one BmAK movie; compare the GFx/AVM2 header words and tag set.
Then `ffdec -decompress ui/hud.gfx out.swf` and `ffdec -header -set gfx true out.swf back.gfx`, and diff `back.gfx`
against the source. *Oracle:* tag list and AS3 script count identical, and the diff touches only the header/compression
bytes. If that passes, one `-replace` of a single text string is a viable HUD edit; if the re-save already differs
structurally, stop and rethink. (This is the unrun U6 check already in `Working/Roadmap/hud_cam_lights_fx.md`.)

**E-b — ADF: append one instance of an existing class and re-read it.**
Take a donor `.epe` that already contains a camera-shake instance; in Neam/Gibbed XML duplicate the instance with a
new array ID (the documented recipe), convert back, and run `adfdump.py` / `ConvertAdf` on the result. *Oracle:*
the new instance is present with every field, the untouched control file still re-emits identically, and the
`<type-definitions>` block is unchanged. If the class does not already exist in that file, the experiment is over:
the gap is real.

**E-c — FMOD: settle the runtime and test one added FSB5 sample.**
(i) `grep -a -o "FMOD_Studio_[A-Za-z_]*\|EventSystem_Create" JustCause3.exe` to see which API the EXE imports —
one minute, and it decides whether the FEV is read by Avalanche code or a legacy Ex runtime.
(ii) In a private copy of the smallest bank, duplicate the smallest sample record and fix the FSB5 offset table by
+one entry; read it with `vgmstream-cli -m`. *Oracle:* `stream count` rises by one and the duplicate decodes with the
same length. That tests an FSB5 "add sample" writer without touching the FEV.

**E-d — `.effc`: grow one array by one element.**
Copy `effects/cinematic/mm150_ember_camera.effc`, add a second `EmitterTemplates` element (copy the existing one,
bump the array count and any instance/type indices), then run `effc_writer.py` decode on the copy. *Oracle:* the
decoder reports 2 templates with all fields, the edited file re-encodes byte-for-byte, and the untouched control
still round-trips 95/95. If the count is stored anywhere the writer does not model, this fails loudly — which is the
answer we need before writing emitter-growth code.

**E-e — `.physicsc`: append a duplicate hull object, not a new class.**
Copy `Working/Collision/batmobile.physicsc`, duplicate one hull object and its array entry, then
`jc3hkx.py check --all`. *Oracle:* 0 shape-check violations and the file still ends exactly at the last object.
If that passes, the remaining risk is only whether JC3 reads the file at all — P1's contact-gap probe.

**E-f — keymap: add one binding whose action string already exists.**
Rebuild the patched `settings/keymap_gamepad.bin` with one extra binding that reuses an action string already in
the pool (e.g. `LTRIGGER` → an existing vehicle action), so the string pool and its dedup do not change; run
`jc3_input.py --check` on the new file. *Oracle:* the byte-accounting tiles exactly to EOF, bindings = 146, and the
base/patch diff shows exactly the one added binding. That is the minimal writer prover; honouring it is P2.

---

## 5. Method, sources, UNKNOWNs

Read-only. Web pages opened: Just Cause Wiki `Modifying (JC3)`, `Current Tools` (redirects to `Modifying (JC2)`),
`Per-mesh physics attributes`; github.com/gibbed/Gibbed.JustCause3; github.com/tim42 (via deca README);
videogamemods.com Modified Gibbed's Tools and Ashen JC4 tools; github.com/kk49/deca (+README), github.com/PredatorCZ/HavokLib,
github.com/kk49/HavokLib; github.com/EonZeNx/apex-tools (+ apex-resource-index pages); github.com/Wouldubeinta/Fmod-Bank-Tools
(+CLI, issue #13), Fmod Bank Tools Nexus page; github.com/IZH318/FSB-BANK-Extractor-Rebuilder; qa.fmod.com threads
11224, 11683, 23724; github.com/jindrapetrik/jpexs-decompiler (README, Features, FAQ, Commandline-arguments, SWF.java);
PCGamingWiki Just Cause 3 and Scaleform GFx; Nexus JC3 mods 40, 27, top/mod-of-month lists; Steam threads on
`kepmap.txt`; Luke JC "Getting started"; eonzenx apex-resource-index tool index.

Local reads: `ROADMAP.md` §4, `Tools/` and `Tools/scripts/` listings, `Tools/Gibbed/README.md`,
`Tools/GibbedSrc/README.md` + patch, `Research/JC3Grab/JC3_AUDIO.md`, `Research/JC3Grab/PHYSICS_WRITE.md`,
`Research/JC3Grab/INPUT.md`, `Research/specs/B-11.md`, `Working/Effects/EFFC_WRITER.md`, `Working/HUD/CLUSTER.md`,
`Working/Roadmap/hud_cam_lights_fx.md`, `Working/Effects/bm_fx_edits.json`, script headers/docstrings.

UNKNOWNs still open after this check:

- Exact licence of Neam's Modified Gibbed's Tools and of UnknownMiscreant's JC3/Ashen tools — both ship licence
  text inside an archive that was not downloaded (brief: no downloads).
- Licence of EonZeNx/apex-tools — no LICENSE file in the repository listing at the time checked.
- Which FMOD API consumes the FEV banks in JC3 (Studio DLL exported symbols vs FEV data is a contradiction that
  only the EXE import table or live attach settles).
- Whether any *private* tool (JC3 Discord, UnknownMiscreant, Ashen) writes FEV events, `.effc` graphs or
  `.physicsc` objects; the public record does not say. What was tried: VGM pages, apex-resource-index, deca's docs,
  GitHub code search results, and the quoted Discord-CDN links (not opened).
- Whether `kepmap.txt` carries gamepad bindings (quoted threads only show `PC_*` keyboard names).
- Whether JC3 loads a private `ui/hud.gfx` from the dropzone: no report found in any source above; only P3 can answer it.

No script was produced: this brief is a source survey, its output is this report, and every claim above is either a
quoted page with its URL or a quoted file with its path.
