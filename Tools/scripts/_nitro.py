"""FSB sample details for nitro targets + Batmobile source prep info."""
import wave

from fsb5 import FSB5

bank = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank", "rb").read()
fsb = FSB5(bank[bank.find(b"FSB5"):])
print("samples:", len(fsb.samples))
for i in (56, 150, 355):
    s = fsb.samples[i]
    print("%d %s freq=%s ch=%s nsamples=%s datalen=%d" %
          (i, s.name, s.frequency, s.channels, s.samples, len(s.data)))
for tag in ["EC2FD42B", "E7BD5AD0", "jc3_batmobile_start", "jc3_batmobile_loop"]:
    p = ("Working/Audio/hashid/%s.wav" % tag) if tag[0] in "E" else ("Working/Audio/bml/%s.wav" % tag)
    w = wave.open(p, "rb")
    print("%-22s %dch %dHz %.2fs" % (tag, w.getnchannels(), w.getframerate(), w.getnframes() / w.getframerate()))
    w.close()
