import importlib.util
import json
from pathlib import Path

p=Path('.work-items/unified-matters-pipeline/experiments/session-004/pass-12').resolve();spec=importlib.util.spec_from_file_location('pass12',p/'run12.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.r2.use_session('002');out=p/'runs/s002-step3';threads=r.r2.load_threads('s002-step2');results={}
for t in threads['threads']:
 if r.r2.needs_facts(t):results[t['id']]=json.loads((out/'records'/f"step3_{t['id']}.raw.json").read_text())
r.write_facts(out,'s002-step1','s002-step2',threads,results)
problems=r.check_classification('s002-step3')
assert not problems,problems
print('Reassembled all valid saved responses with the targeted replacement; classifications valid.')
