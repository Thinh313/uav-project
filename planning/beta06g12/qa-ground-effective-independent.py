"""Independent effective-entry regression. Synthetic clock/UI/journal only."""
from pathlib import Path
import ast, hashlib, importlib.util, json, os, sys, types
from unittest.mock import patch

P = Path(__file__).resolve().parent
R = P.parents[1]
F = R / 'planning/beta06g11'
digest = lambda data: hashlib.sha256(data).hexdigest()
sha = lambda path: digest(path.read_bytes())
freeze = json.loads((R / 'evidence/beta06/generation11/native-helper-freeze01.json').read_bytes())
old, candidate, writer = F / 'qa-ground-soak.py', P / 'qa-ground-soak.py', P / 'qa-native-budget.py'
def namespace(source):
    for a,z in [('beta06g11','beta06g12'),('generation11','generation12'),('GENERATION11','GENERATION12'),('host-app11','host-app12'),('g11_','g12_'),('aeris_g11_clock','aeris_g12_clock'),('G11','G12'),("'22'","'24'"),("'23'","'25'"),('22|23','24|25'),('ROOT_LIVE22','ROOT_LIVE24'),('root-controller22','root-controller24'),('EMULATOR22','EMULATOR24'),('BOOT22','BOOT24'),('BOOT23','BOOT25'),('BEFORE23','BEFORE25'),('closure22','closure24'),('attempt23','attempt25'),('Boot22','Boot24'),('Boot23','Boot25'),('g12_frozen_root_controller_live22','g12_frozen_root_controller_live24')]:source=source.replace(a,z)
    return source
source_rows=[]
for path,h in freeze['files'].items():
    if not path.startswith('planning/beta06g11/qa-'):continue
    prior=R/path;current=R/path.replace('beta06g11','beta06g12').replace('qa-root-live22.py','qa-root-live24.py')
    assert sha(prior)==h
    expected=namespace(prior.read_text())
    if prior.name=='qa-ground-soak.py':expected=expected.replace('import hashlib,json,math,time,importlib.util,sys,re','import os,hashlib,json,math,time,importlib.util,sys,re',1)
    assert current.read_text()==expected,str(current)
    if current.suffix=='.py':
        nums=lambda text:[n.value for n in ast.walk(ast.parse(text))if isinstance(n,ast.Constant)and type(n.value)in(int,float,complex)]
        assert nums(prior.read_text())==nums(current.read_text()),str(current)
    source_rows.append({'path':str(current.relative_to(R)),'sha256':sha(current),'proof':'EXACT_NAMESPACE_ONLY_EXCEPT_GROUND_OS_IMPORT; NUMERIC_AST_IDENTICAL'})
provider=R/'pilot/beta06g12/clock_basis.py'
assert sha(provider)=='40fba1dc750f09ba042668c916547f88ef59eb05c0c9de2f07bd8defcb5bda17'
assert len(source_rows)==20

assert candidate.read_bytes() == namespace(old.read_text()).encode().replace(
    b'import hashlib,json,math,time,importlib.util,sys,re\n',
    b'import os,hashlib,json,math,time,importlib.util,sys,re\n', 1)
for path in (old,):
    assert sha(path) == freeze['files'][str(path.relative_to(R))]
tree = ast.parse(candidate.read_text())
for node in tree.body:
    if isinstance(node, ast.Import):
        node.names = [name for name in node.names if name.name != 'os']
assert ast.dump(tree, include_attributes=False) == ast.dump(ast.parse(namespace(old.read_text())), include_attributes=False)

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

assert 'g12_native_writer' not in sys.modules
b = load('g12_native_writer', writer)
original = load('qa_ground_original', old)
fixed = load('qa_ground_candidate', candidate)
assert fixed.b is b and original.b is not b
controller=load('qa_g12_controller_defaults',P/'qa-root-controller.py')
ui_module=load('qa_g12_ui_defaults',P/'qa-ui.py')
runtime=load('qa_g12_runtime_defaults',P/'qa-runtime.py')
assert b.host_clock is controller.b.host_clock is controller.g.host_clock is ui_module.b.host_clock is runtime.b.host_clock
assert fixed.collect.__kwdefaults__['clock'] is controller.Controller.__init__.__kwdefaults__['clock'] is runtime.validate_parent_permit.__kwdefaults__['clock'] is b.host_clock.now_s
assert ui_module.receipt_observation.__defaults__[1] is b.host_clock.now_s
assert 'aeris_g12_clock' in sys.modules and Path(b.host_clock.__file__).resolve()==provider.resolve()
seen=[]
try:ui_module.receipt_observation(99,reader=lambda:seen.append(1),clock=lambda:100,pause=lambda _:None)
except AssertionError as exc:assert 'DEADLINE' in str(exc)
else:raise AssertionError('EXPIRED_RECEIPT_DEFAULT_GATE_ACCEPTED')
assert not seen

clock = [1000.0]
boot = '11111111-2222-3333-4444-555555555555'
writes, calls = [], []

def sink(path, report, *, maximum, kind):
    assert Path(path).parent == P and kind == 'ground' and maximum == 256 * 2**10
    raw = (json.dumps(report, indent=2, allow_nan=False) + '\n').encode()
    assert len(raw) <= maximum
    with Path(path).open('xb') as out:
        out.write(raw); out.flush(); os.fsync(out.fileno())
    writes.append({'path': str(Path(path).relative_to(R)), 'bytes': len(raw), 'sha256': digest(raw)})

def sentinel(_):
    calls.append('journal')
    raise AssertionError('QA_SENTINEL_NO_UI_OR_NETWORK')

fake = types.SimpleNamespace(observation=lambda: (_ for _ in ()).throw(AssertionError('NO_UI_EXPECTED')))
with patch.dict(os.environ, {'BETA06_HOST_BOOT_UUID': boot}), patch.object(b, 'write_json', side_effect=sink):
    for module, name, expected in ((original, 'qa-effective-original01', NameError),
                                   (fixed, 'qa-effective-refusal01', AssertionError)):
        with patch.object(module, 'E', P), patch.object(module, 'journal_rows', side_effect=sentinel):
            try:
                module.collect(name, P / 'qa-effective-clock01.jsonl', clock=lambda: clock[0], pause=lambda _: None, ui=fake)
                raise RuntimeError('EXPECTED_REFUSAL_ABSENT')
            except expected as error:
                assert str(error) == ("name 'os' is not defined" if module is original else 'QA_SENTINEL_NO_UI_OR_NETWORK')
        if module is original:
            assert not calls and not writes
    assert calls == ['journal'] and len(writes) == 1
refusal = json.loads((P / 'qa-effective-refusal01-ground-soak.json').read_bytes())
assert refusal['status'] == 'REFUSED_GROUND_ADMISSION_NO_AP' and refusal['hostBootId'] == boot

# Reuse retained synthetic rows and fixture constructors, not Builder assertions.
# The actual parser, chain, renewals, sample_decision and collect remain unmodified.
fixture = R / 'planning/ground11fix/test-effective-collector.py'
nodes = [n for n in ast.parse(fixture.read_text()).body
         if isinstance(n, ast.FunctionDef) and n.name in ('observation', 'state')]
assert len(nodes) == 2
observations = [0]
context = {'clock': clock, 'observations': observations, 'config': 'mock-config', 'viewer': 'viewer-mock-clock'}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(fixture), 'exec'), context)
raw = (R / 'planning/ground11fix/mock-clock01.jsonl').read_bytes()
assert digest(raw) == 'b636646d74d0af9e02aa666b3cfd2dd5c58f32389c9de0e25524e2c7103ced89'
rows = raw.splitlines(keepends=True)
assert len(rows) == 9
journal = P / 'qa-effective-clock01.jsonl'
with journal.open('xb') as out:
    out.write(b''.join(rows[:3]))
emitted = set()

def advance(seconds):
    assert seconds == .5
    clock[0] += seconds
    for threshold, offset in ((1030, 3), (1060, 6)):
        if clock[0] >= threshold and threshold not in emitted:
            emitted.add(threshold)
            with journal.open('ab') as out:
                out.write(b''.join(rows[offset:offset+3]))

ui = types.SimpleNamespace(observation=context['observation'], q=types.SimpleNamespace(state=context['state']))
with patch.dict(os.environ, {'BETA06_HOST_BOOT_UUID': boot}), patch.object(b, 'write_json', side_effect=sink), patch.object(fixed, 'E', P):
    result = fixed.collect('qa-effective-success01', journal, clock=lambda: clock[0], pause=advance, ui=ui)
assert result['status'] == 'PASS_GROUND_INTERVAL_NOT_AP_AUTHORITY'
assert result['observedPythonSpanS'] == 75 and len(result['samples']) == observations[0] == 151
assert len(result['renewalEvidence']['viewer']) == len(result['renewalEvidence']['publisher']) == 2
assert result['apStarts'] == 0 and result['clockBasis'] == b.host_clock.BASIS and result['hostBootId'] == boot
assert journal.read_bytes() == raw
for path in (old,):
    assert sha(path) == freeze['files'][str(path.relative_to(R))]
report = {'status': 'PASS_EFFECTIVE_NEW_G12_GROUND_COLLECT_AND_SOURCE_MOCK_ONLY', 'groups': 6,
          'checks': ['Exact sole import delta and identical function AST', 'Original effective collect NameError before sentinel or writer',
                     'Corrected effective collect sentinel refusal persists bounded finally report',
                     'Corrected synthetic75s,151 real sample decisions and actual chain/renewal predicates'],
          'sourceInvariance': source_rows, 'canonicalProviderSha256': sha(provider), 'effectiveCurrentClockDefaultIdentity': True, 'expiredReceiptReaderCalls': 0, 'inheritedClockNumericProof': {'path':'evidence/beta06/generation11/qa-clock-integration-independent01.json','sha256':sha(R/'evidence/beta06/generation11/qa-clock-integration-independent01.json'),'scope':'Mixed-basis/boot/backward and225/240/90 cases reused only after exact current namespace-source/numeric-AST invariance; current imports/defaults exercised here; Native current child proof separate.'}, 'originalSha256': sha(old), 'proposalSha256': sha(candidate), 'frozenWriterSha256': sha(writer),
          'qaRecipeSha256': sha(Path(__file__)), 'builderFixtureRecipeSha256': sha(fixture),
          'loading': 'Exact current G12 writer preloaded and used by current collector; original G11 reuses its separate frozen writer (constructor fails before writer). Explicit fake clock/UI/pause and test output sink. Builder synthetic fixture rows/observation constructors reused; Builder assertions not reused.',
          'syntheticJournalSha256': sha(journal), 'outputs': writes, 'actualRuntimeEffects': 0,
          'G11SourceChanged': False, 'G12EffectiveCollectorExecutedWithMocks': True, 'productRuntimeLaunched': False, 'cleanup': 'No scratch directories created or removed; bounded synthetic proof files retained.',
          'limits': 'No actual75s, UI/network/Android/SITL, FPS, payload, restart or persistence acceptance. Other guard branches not re-certified. G12 actual acceptance NOT_RUN.'}
out = R / 'evidence/beta06/generation12/qa-ground-effective-independent01.json'
with out.open('x') as handle:
    json.dump(report, handle, indent=2); handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
print(json.dumps({'path': str(out.relative_to(R)), 'sha256': sha(out), 'status': report['status'], 'groups': 6}))
