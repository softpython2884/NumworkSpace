# NOVA - space rogue-lite for NumWorks. MIT licence.
# Generated from src/ by tools/build.py -- do not edit.
from novad import(O,P,aX,V,bC,I,J,n,B,a,q,k,az,
i,s)
from novae import(v,g,w,aw,X,Y,o,aM,bo,bq,br,ad,
cg)
def cr(e,f,ct,cy):
 K=(a[n]-1)*6
 while K>=0:
  d=g[K+2]
  aV=g[K+1]
  if f<aV+V[d]and f+6>aV:
   aU=g[K]
   if e<aU+I[d]and e+2>aU:
    g[K+3]-=ct
    if g[K+3]<=0:
     bo(K,d,aU,aV)
    if not cy:
     return True
  K-=6
 return False
def bN():
 b=(a[J]-1)*4
 while b>=0:
  f=v[b+1]-11
  if f<q:
   ad(v,b,4,J)
  else:
   v[b+1]=f
   e=v[b]+v[b+2]
   v[b]=e
   bT=v[b+3]
   if cr(e,f,bT%100,bT>99):
    ad(v,b,4,J)
  b-=4
def cB(d,e,f,l):
 if l<14:
  l=14
 aL=e+(I[d]>>1)
 bn=f+V[d]
 x=(o[0]+7-aL)>>5
 if x>2:
  x=2
 elif x<-2:
  x=-2
 if d==O:
  aM(aL-18,bn,-1,4)
  aM(aL+18,bn,1,4)
 aM(aL,bn,x,4)
 return l
def bS(L,bl):
 b=(a[n]-1)*6
 while b>=0:
  d=g[b+2]
  e=g[b]
  f=g[b+1]+bC[d]
  if d==1:
   e+=g[b+4]
   if e<0 or e>i-I[d]:
    g[b+4]=-g[b+4]
    e=0 if e<0 else i-I[d]
  elif d==2:
   if f<g[b+4]:
    f+=2
   elif L&1:
    g[b+4]+=1
  elif d==O:
   e+=g[b+4]
   if e<4 or e>i-52:
    g[b+4]=-g[b+4]
   if not L%10:
    f+=1
  g[b]=e
  g[b+1]=f
  if f>P:
   ad(g,b,6,n)
  else:
   if aX[d]:
    l=g[b+5]-1
    if l<=0:
     l=cB(d,e,f,aX[d]-bl-s(20))
    g[b+5]=l
   r=bq(e,f,I[d],V[d])
   if r>=0:
    br(r)
    if d!=O:
     ad(g,b,6,n)
  b-=6
def bR():
 b=(a[B]-1)*4
 while b>=0:
  f=w[b+1]+w[b+3]
  e=w[b]+w[b+2]
  if f>P or e<0 or e>i:
   ad(w,b,4,B)
  else:
   w[b+1]=f
   w[b]=e
   r=bq(e,f,3,5)
   if r>=0:
    br(r)
    ad(w,b,4,B)
  b-=4
def cj():
 bv=9-(k[az]<<1)
 if bv<3:
  bv=3
 for r in range(2):
  if Y[r]:
   if X[r]:
    X[r]-=1
   l=aw[r]-1
   if l<=0:
    cg(r)
    l=bv
   aw[r]=l
