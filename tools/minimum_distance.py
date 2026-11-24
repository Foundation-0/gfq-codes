#!/usr/bin/env python3
"""Exact bounded minimum-distance checker. Exhaustive, not a fast search tool."""
import argparse,itertools,json,sys
DEFAULT={4:[1,1,1],8:[1,1,0,1],9:[2,2,1]}
class Field:
 def __init__(self,q,modulus=None):
  if q not in (3,4,5,7,8,9):raise ValueError('unsupported field')
  self.q=q;self.p=2 if q in (4,8) else 3 if q==9 else q
  self.m=1 if q in (3,5,7) else 3 if q==8 else 2
  self.mod=list(modulus or DEFAULT.get(q,[]))
  if self.m>1:
   if len(self.mod)!=self.m+1 or self.mod[-1]!=1 or any(type(v)is not int or not 0<=v<self.p for v in self.mod):raise ValueError('invalid monic modulus')
   # Every reducible degree 2 or 3 polynomial has a root in its prime field.
   if any(sum(c*pow(x,i,self.p)for i,c in enumerate(self.mod))%self.p==0 for x in range(self.p)):raise ValueError('reducible modulus')
 def digits(self,x):
  out=[]
  for _ in range(self.m):out.append(x%self.p);x//=self.p
  return out
 def pack(self,v):return sum(c*self.p**i for i,c in enumerate(v))
 def add(self,a,b):return self.pack([(x+y)%self.p for x,y in zip(self.digits(a),self.digits(b))])
 def neg(self,a):return self.pack([(-x)%self.p for x in self.digits(a)])
 def mul(self,a,b):
  if self.m==1:return a*b%self.p
  v=[0]*(2*self.m-1)
  for i,x in enumerate(self.digits(a)):
   for j,y in enumerate(self.digits(b)):v[i+j]=(v[i+j]+x*y)%self.p
  for i in range(len(v)-1,self.m-1,-1):
   for j in range(self.m):v[i-self.m+j]=(v[i-self.m+j]-v[i]*self.mod[j])%self.p
  return self.pack(v[:self.m])
 def inv(self,a):
  if not a:raise ValueError('zero inverse')
  return next(x for x in range(1,self.q)if self.mul(a,x)==1)
def rank(rows,F):
 a=[r[:]for r in rows];pivot=0
 for col in range(len(a[0])):
  j=next((j for j in range(pivot,len(a))if a[j][col]),None)
  if j is None:continue
  a[pivot],a[j]=a[j],a[pivot];iv=F.inv(a[pivot][col]);a[pivot]=[F.mul(v,iv)for v in a[pivot]]
  for j in range(len(a)):
   if j!=pivot:
    c=F.neg(a[j][col]);a[j]=[F.add(x,F.mul(c,y))for x,y in zip(a[j],a[pivot])]
  pivot+=1
  if pivot==len(a):break
 return pivot
def check(data,max_words=1000000):
 q,n,k,d=(data[x]for x in ('q','n','k','d'))
 if any(type(x)is not int for x in (q,n,k,d))or not 1<=k<=n or not 1<=d<=n:raise ValueError('invalid parameters')
 F=Field(q,data.get('modulus'));g=data['generator']
 if not isinstance(g,list)or len(g)!=k or any(not isinstance(s,str)or len(s)!=n or any(c not in '012345678'[:q]for c in s)for s in g):raise ValueError('invalid generator matrix')
 a=[[int(c)for c in s]for s in g];r=rank(a,F)
 if r!=k:raise ValueError('generator rank differs from k')
 if q**k>max_words:raise ValueError('word budget exceeded; no distance certified')
 best=n
 for msg in itertools.product(range(q),repeat=k):
  if not any(msg):continue
  word=[0]*n
  for coeff,row in zip(msg,a):word=[F.add(x,F.mul(coeff,y))for x,y in zip(word,row)]
  best=min(best,sum(x!=0 for x in word))
 if best!=d:raise ValueError(f'claimed distance {d}, computed {best}')
 return {'q':q,'n':n,'rank':r,'distance':best,'words_enumerated':q**k}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('file');p.add_argument('--max-words',type=int,default=1000000);a=p.parse_args()
 try:print(json.dumps(check(json.load(open(a.file)),a.max_words)))
 except (ValueError,KeyError,TypeError,OSError,StopIteration)as e:print(str(e),file=sys.stderr);return 1
 return 0
if __name__=='__main__':sys.exit(main())
