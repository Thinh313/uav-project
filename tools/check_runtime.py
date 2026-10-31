"""Fail loud if captured simulator/protocol inputs change."""
import pathlib,hashlib,json,subprocess
root=pathlib.Path(__file__).resolve().parents[1]
inputs=json.loads((root/'evidence/flight01/public-inputs.json').read_text())
for rec in inputs:
 p=root/rec['path'];assert p.is_file(),f'Missing pinned input: {p}'
 assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['sha256'],f'Pinned input changed: {p}'
before=(root/'services/mavlink-definitions.mjs').read_bytes()
subprocess.run(['python3','tools/generate_mavlink.py','--check'],cwd=root,check=True,capture_output=True)
assert (root/'services/mavlink-definitions.mjs').read_bytes()==before,'Generated protocol changed'
print(json.dumps({'input_hashes':len(inputs),'generated_dialect_deterministic':True,'simulation_binary_version':(root/'runtime/sitl/firmware-version.txt').read_text().strip()}))
