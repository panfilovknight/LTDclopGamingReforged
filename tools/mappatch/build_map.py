"""Build the Reforged branch of Legion TD Mega klopGaming from the classic 1.1.26 map.

Usage:
  python build_map.py SOURCE.w3x OUT.w3x --version R1.0 --code 20100

The version code is written to the replay as gamecache "dr.x" / "EOG" / "ver",
next to the winner mask "EOG" / "Win1", so the ladder can reject old versions.
Code scheme: 2MMmm (2 = Reforged branch, MM = major, mm = minor).
"""
import argparse
import os
import re
import tempfile

import mpq

OLD_NAME = b'Legion TD |cffff0000Mega|r 1x1 |cff32cd32klopGaming|r v1.1.26'


def patch_script(j, name, version, code):
    def rep(old, new, count=1):
        nonlocal j
        if j.count(old) != count:
            raise ValueError('expected %d x %r, found %d' % (count, old, j.count(old)))
        j = j.replace(old, new)

    store = re.compile(rb'(call StoreInteger\(SZw,"EOG","Win2",MEw\)(\r?\n))')
    if len(store.findall(j)) != 1:
        raise ValueError('EOG store not found')
    j = store.sub(lambda m: m.group(1) + b'set SZw=Jf' + m.group(2)
                  + b'call StoreInteger(SZw,"EOG","ver",' + code + b')' + m.group(2), j)
    sync = re.compile(rb'(call SyncStoredInteger\(SZw,"EOG","Win1"\)(\r?\n))(endif)')
    if len(sync.findall(j)) != 2:
        raise ValueError('EOG sync not found')
    j = sync.sub(lambda m: m.group(1) + b'call SyncStoredInteger(SZw,"EOG","ver")' + m.group(2) + m.group(3), j)

    rep(b'// Legion TD Mega 1x1 klopGaming v1.1.26', b'// Legion TD Mega Reforged klopGaming v' + version)
    rep(b'set S="1.1.26"', b'set S="' + version + b'"')
    rep(OLD_NAME, name, 2)
    rep(b'F9 -> 1.1.26 Changelog', b'F9 -> ' + version + b' Changelog')
    rep(b'call QuestSetDescription(bj_lastCreatedQuest,"|cffAA3333klopGaming 1.1.26|r\\n',
        b'call QuestSetDescription(bj_lastCreatedQuest,"|cffAA3333klopGaming Reforged ' + version
        + b'|r\\n- Separate Reforged branch based on 1.1.26, with its own version numbering.'
        + b'\\n- Ladder: the map version is saved to the replay together with the game result.'
        + b'\\n\\n|cffAA3333klopGaming 1.1.26|r\\n')
    return j


def patch_w3i(w, name):
    end = w.index(b'\0', 12)
    if w[12:end] != OLD_NAME:
        raise ValueError('unexpected map name in w3i: %r' % w[12:end])
    return w[:12] + name + w[end:]


def patch_hm3w(full, name):
    head = full[:512]
    end = head.index(b'\0', 8)
    if head[8:end] != OLD_NAME:
        raise ValueError('unexpected map name in HM3W header')
    new = head[:8] + name + head[end:end + 9]
    return new + b'\0' * (512 - len(new)) + full[512:]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source')
    p.add_argument('out')
    p.add_argument('--version', default='R1.0')
    p.add_argument('--code', default='20100')
    a = p.parse_args()
    version = a.version.encode()
    name = b'Legion TD |cffff0000Mega|r Reforged |cff32cd32klopGaming|r v' + version

    full = open(a.source, 'rb').read()
    with tempfile.TemporaryDirectory() as tmp:
        files = mpq.read_files(a.source, ['war3map.j', 'war3map.w3i'], os.path.join(tmp, 'inner.mpq'))
    j = patch_script(files['war3map.j'], name, version, a.code.encode())
    w = patch_w3i(files['war3map.w3i'], name)
    out = mpq.replace_files(patch_hm3w(full, name), {'war3map.j': j, 'war3map.w3i': w})
    open(a.out, 'wb').write(out)
    print('built', a.out, len(out), 'bytes')


if __name__ == '__main__':
    main()
