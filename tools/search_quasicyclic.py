#!/usr/bin/env python3
"""Bounded prime-field quasi-cyclic search. Output is a candidate, never a record."""
import argparse,itertools,json,random,time

def search(q,m,blocks,trials,seed):
 if q not in (3,5,7)or m<1 or blocks<2 or trials<1 or q**m>100000:raise ValueError('unsupported parameters or word budget')
 rng=random.Random(seed);best=None;t0=time.monotonic()
 for _ in range(trials):
  seeds=[[rng.randrange(q)for _ in range(m)]for _ in range(blocks-1)]
  G=[]
  for i in range(m):G.append([int(i==j)for j in range(m)]+[row[(j-i)%m]for row in seeds for j in range(m)])
  distance=blocks*m
  for u in itertools.product(range(q),repeat=m):
   if any(u):distance=min(distance,sum(sum(u[i]*G[i][j]for i in range(m))%q!=0 for j in range(blocks*m)))
  if best is None or distance>best['d']:best=dict(q=q,n=blocks*m,k=m,d=distance,generator=[''.join(map(str,row))for row in G],construction='systematic identity plus circulant blocks',seed=seed)
 return {'status':'numerical-search-candidate; independent checkers pending','trials':trials,'words_per_trial':q**m,'seconds':time.monotonic()-t0,'candidate':best}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name,default in [('q',3),('m',2),('blocks',3),('trials',8),('seed',20261028)]:p.add_argument('--'+name,type=int,default=default)
 a=p.parse_args();print(json.dumps(search(a.q,a.m,a.blocks,a.trials,a.seed),indent=2))
