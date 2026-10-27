import re, sys
from pathlib import Path
from collections import defaultdict

NOTAS = {"DO": 0, "RE": 2, "MI": 4, "FA": 5, "SOL": 7, "LA": 9, "SI": 11}
SEMITONOS = [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12]
PAT = re.compile(r"^(?P<inst>[A-Za-z]+)_(?P<nota>DO|RE|MI|FA|SOL|LA|SI)(?P<alt>#|b)?(?P<oct>\d)\.wav$", re.I)

carpeta = Path(sys.argv[1] if len(sys.argv) > 1 else "storage/audio")
midis = defaultdict(set)
ignorados = []

for f in sorted(carpeta.rglob("*.wav")):
    m = PAT.match(f.name)
    if not m:
        ignorados.append(f.name)
        continue
    base = NOTAS[m["nota"].upper()]
    alt = 1 if m["alt"] == "#" else (-1 if m["alt"] == "b" else 0)
    midis[m["inst"].capitalize()].add(12 * (int(m["oct"]) + 1) + base + alt)

for inst, s in sorted(midis.items()):
    print(f"\n== {inst}: {len(s)} notas, MIDI {min(s)} a {max(s)}")
    print("MIDI existentes:", sorted(s))
    for semi in SEMITONOS:
        raices = sorted(r for r in s if (r + semi) in s)
        print(f"  intervalo de {semi:2d} semitonos: {len(raices):2d} raíces posibles {raices}")
    todas = sorted(r for r in s if all((r + x) in s for x in SEMITONOS))
    print("  raíces válidas para TODOS los intervalos:", todas)

print("\nArchivos ignorados (nombre no reconocido):", ignorados)
