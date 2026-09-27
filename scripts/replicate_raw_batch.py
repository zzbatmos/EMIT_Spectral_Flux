"""Resume raw-data reproduction for the 577 historical saved cases.

Configurable independent processes; EMIT cubes are held only in memory and discarded.
Cached CERES hourly files are protected by per-file process locks.
"""
import argparse
import contextlib
import datetime as dt
import json
import fcntl
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import time
import traceback

import earthaccess
from replicate_raw_case import ROOT,run_case,manifest_name,retry

LPFS=None
ASDCFS=None


def init():
 global LPFS,ASDCFS
 with (ROOT/'.cache/earthdata-auth.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  if not retry(lambda:earthaccess.login(strategy='netrc',persist=False),tries=5).authenticated:raise RuntimeError('Auth failed')
  LPFS=retry(lambda:earthaccess.get_s3_filesystem(provider='LPCLOUD'),tries=5)
  ASDCFS=retry(lambda:earthaccess.get_s3_filesystem(provider='LARC_CLOUD'),tries=5)


def worker(timestamp):
 out=ROOT/'outputs/raw_reproduction'/timestamp;out.mkdir(parents=True,exist_ok=True)
 start=time.monotonic()
 with (out/'run.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
  try:
   _,report=run_case(timestamp,LPFS,ASDCFS,False)
   fail=[k for k,v in report['fields'].items() if not v.get('allclose_rtol1e-5_atol1e-4',False)]
   return {'timestamp':timestamp,'status':'done','validation_failed_fields':fail,'elapsed_seconds':time.monotonic()-start}
  except Exception as exc:
   traceback.print_exc()
   return {'timestamp':timestamp,'status':'error','error':str(exc),'elapsed_seconds':time.monotonic()-start}


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workers',type=int,default=4);p.add_argument('--limit',type=int);args=p.parse_args()
 files=sorted((ROOT/'Qianqian/Flux_Comparison_Surface_Reflectance_Data').glob('*.pkl'))
 stamps=[f.stem.rsplit('_',1)[-1] for f in files]
 if args.limit:stamps=stamps[:args.limit]
 for ts in stamps:
  for product in ['RAD','OBS']:manifest_name(ts,product)
 pending=[];status=[]
 for ts in stamps:
  d=ROOT/'outputs/raw_reproduction'/ts
  if (d/'provenance.json').exists() and (d/'validation.json').exists():
   v=json.loads((d/'validation.json').read_text());fail=[k for k,x in v['fields'].items() if not x.get('allclose_rtol1e-5_atol1e-4',False)]
   status.append({'timestamp':ts,'status':'resumed','validation_failed_fields':fail})
  else:pending.append(ts)
 print(f'{len(stamps)} cases; {len(status)} complete; {len(pending)} pending',flush=True)
 target=ROOT/'outputs/raw_reproduction/batch_status.json'
 def save():
  target.write_text(json.dumps({'updated_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'target_cases':len(stamps),'cases':status},indent=2))
 save()
 with ProcessPoolExecutor(max_workers=args.workers,mp_context=mp.get_context('spawn'),initializer=init) as pool:
  tasks={pool.submit(worker,ts):ts for ts in pending}
  for future in as_completed(tasks):
   row=future.result();status.append(row);save()
   print(f"{len(status)}/{len(stamps)} {row['timestamp']} {row['status']} validation={row.get('validation_failed_fields',row.get('error'))}",flush=True)
 print('Batch complete',flush=True)


if __name__=='__main__':main()
