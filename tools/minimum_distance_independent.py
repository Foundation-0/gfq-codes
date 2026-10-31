#!/usr/bin/env python3
"""Independent exact distance by zero-coordinate subspaces, no other imports."""
import argparse,itertools,json,sys

def operations(q,mod):
 p,m={3:(3,1),4:(2,2),5:(5,1),7:(7,1),8:(2,3),9:(3,2)}[q]
 modulus=mod or {4:[1,1,1],8:[1,1,0,1],9:[2,2,1]}.get(q)
 if m>1:
  if not isinstance(modulus,list)or len(modulus)!=m+1 or modulus[-1]!=1 or any(type(x)is not int or not 0<=x<p for x in modulus):raise ValueError('invalid modulus')
  if any(sum(c*x**i for i,c in enumerate(modulus))%p==0 for x in range(p)):raise ValueError('reducible modulus')
 def parts(x):return [(x//p**i)%p for i in range(m)]
 add=[[sum(((a+b)%p)*p**i for i,(a,b)in enumerate(zip(parts(x),parts(y))))for y in range(q)]for x in range(q)]
 mul=[]
 for x in range(q):
  row=[]
  for y in range(q):
   c=[0]*(2*m-1)
   for i,a in enumerate(parts(x)):
    for j,b in enumerate(parts(y)):c[i+j]+=a*b
   for i in reversed(range(m,len(c))):
    v=c[i]%p
    for j in range(m):c[i-m+j]-=v*modulus[j]
   row.append(sum((v%p)*p**i for i,v in enumerate(c[:m])))
  mul.append(row)
 return add,mul

def check(d,budget=1000000):
 q,n,k,claimed=[d[x]for x in ('q','n','k','d')]
 if any(type(x)is not int for x in (q,n,k,claimed))or q not in (3,4,5,7,8,9)or not 1<=k<=n or not 1<=claimed<=n:raise ValueError('invalid parameters')
 g=d['generator']
 if not isinstance(g,list)or len(g)!=k or any(not isinstance(r,str)or len(r)!=n or any(c not in '012345678'[:q]for c in r)for r in g):raise ValueError('invalid matrix')
 g=[[int(c)for c in r]for r in g];add,mul=operations(q,d.get('modulus'))
 neg=[next(v for v in range(q)if add[v][x]==0)for x in range(q)]
 inv=[None]+[next(v for v in range(1,q)if mul[v][x]==1)for x in range(1,q)]
 def rnk(columns):
  # Constraints on the message: one row per coordinate required to be zero.
  a=[[g[i][j]for i in range(k)]for j in columns];rank=0
  for col in range(k):
   piv=next((j for j in range(rank,len(a))if a[j][col]),None)
   if piv is None:continue
   a[rank],a[piv]=a[piv],a[rank];v=inv[a[rank][col]];a[rank]=[mul[v][x]for x in a[rank]]
   for j in range(rank+1,len(a)):
    c=neg[a[j][col]];a[j]=[add[x][mul[c][y]]for x,y in zip(a[j],a[rank])]
   rank+=1
  return rank
 if rnk(range(n))!=k:raise ValueError('rank differs from k')
 examined=0
 # A nonzero message vanishes on S iff those column constraints have rank<k.
 for zeros in range(n-1,-1,-1):
  for cols in itertools.combinations(range(n),zeros):
   examined+=1
   if examined>budget:raise ValueError('subset budget exceeded; no distance certified')
   if rnk(cols)<k:
    distance=n-zeros
    if distance!=claimed:raise ValueError(f'claimed {claimed}, computed {distance}')
    return {'rank':k,'distance':distance,'subsets_examined':examined}
 raise ValueError('no support found')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('file');p.add_argument('--max-subsets',type=int,default=1000000);a=p.parse_args()
 try:print(json.dumps(check(json.load(open(a.file)),a.max_subsets)))
 except (ValueError,KeyError,TypeError,OSError,StopIteration)as e:print(str(e),file=sys.stderr);return 1
 return 0
if __name__=='__main__':sys.exit(main())
