"""Patch the G2-33 tracker row: escape the anchor pipes, replace exactly that one line."""
import io

ROW = "tmp/freebuff/g2_33_row.txt"
BACKLOG = "GRAB_BACKLOG.md"
ANCHOR_RAW = "`|sportsmuscle_LOD1|wheel_f_l|Wheel_Frnt_Left_Disc|Wheel_Frnt_Left_Disc_LIG`"
ANCHOR_ESC = "`\\|sportsmuscle_LOD1\\|wheel_f_l\\|Wheel_Frnt_Left_Disc\\|Wheel_Frnt_Left_Disc_LIG`"

row = io.open(ROW, encoding="utf-8").read().strip("\r\n")
if ANCHOR_RAW in row:
    row = row.replace(ANCHOR_RAW, ANCHOR_ESC)

unescaped = row.count("|") - row.count("\\|")
assert unescaped == 4, f"row has {unescaped} unescaped pipes, expected 4"

text = io.open(BACKLOG, encoding="utf-8", newline="").read()
old = "| G2-33 | todo | |"
assert text.count(old) == 1, text.count(old)
text = text.replace(old, row, 1)
io.open(BACKLOG, "w", encoding="utf-8", newline="").write(text)

lines = io.open(BACKLOG, "rb").read().split(b"\n")
print("replaced. lines:", len(lines))
for i, ln in enumerate(lines):
    if ln.startswith(b"| G2-33 |"):
        print("line", i + 1, "pipes:", ln.count(b"|"), "crlf:", ln.endswith(b"\r"))
        break
print("still-todo rows:", sum(1 for ln in lines if ln.startswith(b"| G2-33 | todo")))
