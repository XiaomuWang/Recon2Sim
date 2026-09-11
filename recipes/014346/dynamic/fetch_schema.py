import urllib.request,pathlib
p=pathlib.Path('dynamic_replay_014346/validation/OpenSCENARIO.xsd')
url='https://raw.githubusercontent.com/carla-simulator/scenario_runner/v0.9.15/srunner/openscenario/OpenSCENARIO.xsd'
with urllib.request.urlopen(url,timeout=30) as r:p.write_bytes(r.read())
print(p.stat().st_size)
