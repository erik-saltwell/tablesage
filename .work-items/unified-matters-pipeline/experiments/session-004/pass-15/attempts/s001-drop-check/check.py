"""Call step 6 repeatedly on pass 14's recorded Session 001 input, with pass 14's and pass 15's prompts, and record which open IDs each output drops."""
import asyncio, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
P15 = HERE.parents[1]; P14 = P15.parent / "pass-14"
sys.argv = ["x"]; sys.path.insert(0, str(P15))
import run15 as m
from tablesage_tools.llm import call_llm
m.r2.load_credentials()
user = (P14 / "runs/s001/records/step6.user.md").read_text()
want = sorted(f for sec in json.loads((P14 / "runs/s001/selection.json").read_text())["open"] for f in sec["facts"])
async def one(pas, folder, n):
    system = (folder / "system.md").read_text(); schema = json.loads((folder / "schema.json").read_text())
    raw = await call_llm(system, user, m.r2.MODEL, response_format=schema, timeout=m.r2.TIMEOUT, prompt_name=f"drop_check_{pas}_{n}",
                         model_options={"reasoning_effort": "high", "drop_params": False})
    (HERE / f"{pas}-{n}.json").write_text(raw)
    got = sorted(x["id"] for x in json.loads(raw)["open"])
    return pas, n, sorted(set(want) - set(got))
async def main():
    jobs = [one(p, f / "prompts/step6_writing", n) for p, f in (("pass14", P14), ("pass15", P15)) for n in (1, 2, 3)]
    res = await asyncio.gather(*jobs, return_exceptions=True)
    for r in res: print(r)
    (HERE / "results.json").write_text(json.dumps([r if not isinstance(r, Exception) else repr(r) for r in res], indent=1))
asyncio.run(main())
