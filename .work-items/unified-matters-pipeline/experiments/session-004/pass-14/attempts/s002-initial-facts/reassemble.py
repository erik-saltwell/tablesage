"""Reassemble pass 14 Session 002 facts from the saved per-thread responses after a targeted retry."""
import importlib.util
import json
from pathlib import Path

p = Path('.work-items/unified-matters-pipeline/experiments/session-004/pass-14').resolve()
spec = importlib.util.spec_from_file_location('pass14', p / 'run14.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
r.r2.use_session('002')
out = p / 'runs/s002-step3'
threads = r.r2.load_threads('s002-step2')
results = {t['id']: json.loads((out / 'records' / f"step3_{t['id']}.raw.json").read_text())
           for t in threads['threads'] if r.r2.needs_facts(t)}
r.write_facts(out, 's002-step1', 's002-step2', threads, results)

# Metadata repair: resource_subject only applies to could_use facts (it drives resource deduplication and nothing
# else). Clear a shared-subject label the model put on another kind; raw responses stay unchanged.
path = out / 'thread_facts.json'
data = json.loads(path.read_text())
cleared = []
for f in data['facts']:
    if f['kind'] != 'could_use' and f.get('resource_subject'):
        cleared.append({'fact': f['id'], 'thread': f['thread'], 'kind': f['kind'], 'label': f['resource_subject']})
        f['resource_subject'] = ''
path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
(out / 'metadata-repair.json').write_text(json.dumps(cleared, indent=2, ensure_ascii=False))
print('Cleared resource_subject on non-resource facts:', cleared)
problems = r.check_classification('s002-step3')
assert not problems, problems
print('Reassembled all saved responses with the targeted retries; classifications valid.')
