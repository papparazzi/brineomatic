"""Write the JLCPCB gerber + drill zip for Rev D with the options that made gerbers-rev_d_step23.zip (this script reproduces that zip
byte for byte apart from the date lines): Protel file extensions, no X2 attributes, no netlist attributes, solder mask subtracted from
the silkscreen, Excellon in mm with decimal coordinates, plated and non-plated holes in separate files. No job file, no drill map.
kicad-cli is taken from the KICAD_CLI environment variable, else from the macOS application folder (as make_jlc.py).
usage: make_gerbers.py <pcb> <out.zip>"""
import sys, os, subprocess, tempfile, zipfile
CLI = os.environ.get('KICAD_CLI') or os.path.expanduser('~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
LAYERS = 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'
pcb, out = sys.argv[1:3]
with tempfile.TemporaryDirectory() as d:
    subprocess.run([CLI, 'pcb', 'export', 'gerbers', '--no-x2', '--no-netlist', '--subtract-soldermask', '-l', LAYERS, '-o', d + os.sep, pcb], check=True, capture_output=True)
    subprocess.run([CLI, 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-units', 'mm', '--excellon-zeros-format', 'decimal',
                    '--excellon-separate-th', '-o', d + os.sep, pcb], check=True, capture_output=True)
    files = sorted(f for f in os.listdir(d) if not f.endswith('.gbrjob'))
    assert len(files) == 13, files
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in files: z.write(os.path.join(d, f), f)
print(out, len(files), 'files:', ' '.join(files))
