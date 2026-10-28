#!/usr/bin/env python3
"""Select gap-one code-table targets from a local census CSV, without network I/O."""
import argparse,csv,datetime,json,sys

def select(rows):
 out=[];seen=set()
 for row in rows:
  r={x:int(row[x])for x in ('q','n','k','lower','upper')}
  if r['q']not in (3,4,5,7,8,9)or not 1<=r['k']<=r['n']or not 1<=r['lower']<=r['upper']<=r['n']:raise ValueError('invalid census bounds')
  key=tuple(r[x]for x in ('q','n','k'))
  if key in seen:raise ValueError('duplicate target')
  seen.add(key)
  if r['upper']-r['lower']==1:out.append(r)
 return sorted(out,key=lambda r:(r['n'],r['k'],r['q']))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('csv');p.add_argument('--read-date',required=True);p.add_argument('--limit',type=int,default=20);a=p.parse_args()
 try:
  datetime.date.fromisoformat(a.read_date);rows=select(csv.DictReader(open(a.csv)));counts={str(q):sum(r['q']==q for r in rows)for q in (3,4,5,7,8,9)}
  print(json.dumps({'read_date':a.read_date,'counts':counts,'first_targets':rows[:a.limit]},indent=2))
 except (ValueError,KeyError,OSError)as e:print(str(e),file=sys.stderr);return 1
 return 0
if __name__=='__main__':sys.exit(main())
