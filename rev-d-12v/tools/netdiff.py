#!/usr/bin/env python3
"""Compare two KiCad XML netlists (baseline vs new). Reports parts added/removed/changed
and, per net, pins gained/lost. Net names are matched by name; for nets that exist in only one
netlist it prints their pin sets so renamed nets can be reviewed by eye.
usage: netdiff.py baseline.xml new.xml [--ignore REF,REF ...]"""
import sys, xml.etree.ElementTree as ET
def load(p):
    t=ET.parse(p).getroot()
    comps={}
    for c in t.find('components'):
        ref=c.get('ref'); f={x.get('name'):x.text for x in (c.find('fields') or [])}
        comps[ref]=dict(value=c.findtext('value'),fp=(c.findtext('footprint') or '').split(':')[-1],lcsc=f.get('LCSC',''))
    nets={}
    for n in t.find('nets'):
        pins={(x.get('ref'),x.get('pin')) for x in n}
        nets[n.get('name')]=pins
    return comps,nets
def main():
    a,b=sys.argv[1],sys.argv[2]
    ign=set(sys.argv[sys.argv.index('--ignore')+1].split(',')) if '--ignore' in sys.argv else set()
    ca,na=load(a); cb,nb=load(b)
    print('PARTS removed:',sorted(set(ca)-set(cb)-ign))
    print('PARTS added  :',sorted(set(cb)-set(ca)))
    for r in sorted(set(ca)&set(cb)):
        if ca[r]!=cb[r]: print(f'  CHANGED {r}: {ca[r]["value"]}/{ca[r]["lcsc"]} -> {cb[r]["value"]}/{cb[r]["lcsc"]} ({ca[r]["fp"]}->{cb[r]["fp"]})')
    print('\nNETS with pin changes (ignoring pins on removed/added parts shown separately):')
    for n in sorted(set(na)|set(nb)):
        pa,pb=na.get(n,set()),nb.get(n,set())
        lost=sorted(p for p in pa-pb if p[0] not in ign)
        gain=sorted(pb-pa)
        if lost or gain: print(f'  {n}: -{lost} +{gain}')
if __name__=='__main__': main()
