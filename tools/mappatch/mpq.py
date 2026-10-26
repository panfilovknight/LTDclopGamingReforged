"""Minimal MPQ (v1) helpers for Warcraft III maps.

Reading goes through mpyq. Writing replaces existing files in place: the new
data is appended, the block table entry is repointed and the tables are moved
to the end. This works on maps without a (listfile).
"""
import struct
import zlib

import mpyq

FLAG_EXISTS_COMPRESSED = 0x80000200


def _crypt_table():
    seed = 0x00100001
    table = {}
    for i in range(256):
        idx = i
        for _ in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            hi = (seed & 0xFFFF) << 16
            seed = (seed * 125 + 3) % 0x2AAAAB
            lo = seed & 0xFFFF
            table[idx] = hi | lo
            idx += 256
    return table


CT = _crypt_table()


def hash_string(s, hash_type):
    s1, s2 = 0x7FED7FED, 0xEEEEEEEE
    for ch in s.upper():
        v = ord(ch)
        s1 = CT[(hash_type << 8) + v] ^ ((s1 + s2) & 0xFFFFFFFF)
        s2 = (v + s1 + s2 + (s2 << 5) + 3) & 0xFFFFFFFF
    return s1


def _crypt(data, key, decrypt):
    s1, s2 = key, 0xEEEEEEEE
    out = bytearray()
    for (v,) in struct.iter_unpack('<I', data):
        s2 = (s2 + CT[0x400 + (s1 & 0xFF)]) & 0xFFFFFFFF
        r = v ^ ((s1 + s2) & 0xFFFFFFFF)
        out += struct.pack('<I', r)
        plain = r if decrypt else v
        s1 = ((((~s1) << 0x15) + 0x11111111) | (s1 >> 0x0B)) & 0xFFFFFFFF
        s2 = (plain + s2 + (s2 << 5) + 3) & 0xFFFFFFFF
    return bytes(out)


def encrypt(data, key):
    return _crypt(data, key, decrypt=False)


def decrypt(data, key):
    return _crypt(data, key, decrypt=True)


def find_header(full):
    """Return the offset of the real MPQ header (protected maps carry a fake one at 0)."""
    pos = full.find(b'MPQ\x1a')
    while pos >= 0:
        if struct.unpack('<I', full[pos + 4:pos + 8])[0] == 32:
            return pos
        pos = full.find(b'MPQ\x1a', pos + 1)
    raise ValueError('no MPQ header found')


def read_files(path, names, tmp_path):
    """Read files from a map by name. Writes the bare archive to tmp_path for mpyq."""
    full = open(path, 'rb').read()
    open(tmp_path, 'wb').write(full[find_header(full):])
    archive = mpyq.MPQArchive(tmp_path, listfile=False)
    return {n: archive.read_file(n) for n in names}


def _pack(raw, sector):
    count = (len(raw) + sector - 1) // sector
    sectors = []
    for i in range(count):
        chunk = raw[i * sector:(i + 1) * sector]
        z = b'\x02' + zlib.compress(chunk, 9)
        sectors.append(z if len(z) < len(chunk) else chunk)
    offsets = [(count + 1) * 4]
    for s in sectors:
        offsets.append(offsets[-1] + len(s))
    return struct.pack('<%dI' % (count + 1), *offsets) + b''.join(sectors)


def replace_files(full, replacements):
    """Return new map bytes with files (name -> bytes) replaced. Files must already exist."""
    base = find_header(full)
    _, _, _, fmt, shift, hto, bto, hte, bte = struct.unpack('<4sIIHHIIII', full[base:base + 32])
    sector = 512 << shift
    arc = full[base:]
    ht_raw = arc[hto:hto + hte * 16]
    ht = decrypt(ht_raw, hash_string('(hash table)', 3))
    bt = bytearray(decrypt(arc[bto:bto + bte * 16], hash_string('(block table)', 3)))
    body = bytearray(arc[:hto])
    for name, raw in replacements.items():
        a, b = hash_string(name, 1), hash_string(name, 2)
        idx = None
        for i in range(hte):
            ha, hb, _, _, bi = struct.unpack('<IIHHI', ht[i * 16:i * 16 + 16])
            if ha == a and hb == b:
                idx = bi
                break
        if idx is None:
            raise KeyError(name)
        flags = struct.unpack('<I', bt[idx * 16 + 12:idx * 16 + 16])[0]
        if flags != FLAG_EXISTS_COMPRESSED:
            raise ValueError('%s: unsupported flags %#x' % (name, flags))
        packed = _pack(raw, sector)
        bt[idx * 16:idx * 16 + 16] = struct.pack('<IIII', len(body), len(packed), len(raw), FLAG_EXISTS_COMPRESSED)
        body += packed
    new_hto = len(body)
    body += ht_raw
    new_bto = len(body)
    body += encrypt(bytes(bt), hash_string('(block table)', 3))
    body[0:32] = struct.pack('<4sIIHHIIII', b'MPQ\x1a', 32, len(body), fmt, shift, new_hto, new_bto, hte, bte)
    return full[:base] + bytes(body)
