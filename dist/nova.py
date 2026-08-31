# NOVA - space rogue-lite for NumWorks. MIT licence.
# Generated from src/ by tools/build.py -- do not edit.
from novad import(p,ar,N,O,P,aD,z,H,at,V,I,
Q,t,aY,R,E,bE,bF,au,ba,av,bb,J,n,B,W,aj,
aE,bJ,ak,ag,Z,a,S,ax,T,bK,aa,bL,q,ay,k,
bi,am,i,F,U,m,fill_rect,bW,bX,keydown,aq,
ae,s,set_pixel,bw,ch,time,aW)
from novae import(v,g,w,bd,aw,X,Y,o,bM,bU,ap,
ce)
from novaf import bN,bR,bS,cj
from novag import bP,bz
bD=0.04
cl=b"\x01\x02\x03\x02\x05"
def cf(aH,L,aI):
 ac=fill_rect
 for b in range(0,a[J]*4,4):
  ac(v[b],v[b+1],2,6,p if aI else U)
 for b in range(0,a[n]*6,6):
  d=g[b+2]
  if aI:
   ac(g[b],g[b+1],I[d],V[d]+2,p)
  else:
   bw(bK,d*12,g[b],g[b+1],Z if d==O else aH)
 for b in range(0,a[B]*4,4):
  ac(w[b],w[b+1],3,5,p if aI else aj)
 for c in range(2):
  if Y[c]:
   if aI:
    ac(o[c],ag,ak,aE,p)
   elif not X[c]or L&2:
    bw(bJ,0,o[c],ag,H if c==0 else am)
def cu(ca):
 a[J]=0
 a[n]=0
 a[B]=0
 aW()
 bX()
 for c in range(0,24,2):
  aa[c]=s(i)
  aa[c+1]=q+s(P-q)
 j=a[T]
 aH=ax[j%5]
 aJ=ca==5
 bk=1
 ab=15+j*9+a[W]*3
 if ab>84:
  ab=84
 if ca==1:
  ab=(ab*7)//5
 if aJ:
  ab=0
  bk=bM(j)
  g[0:6]=(136,q+4,O,bk,1,30)
  a[n]=1
 bt=2+j
 if bt>5:
  bt=5
 aA="BOSS"if aJ else("S%d-%d"%(j+1,a[W]+1))
 bl=4+j*3
 bx=30
 L=0
 by=time.monotonic()
 bV=True
 while True:
  L+=1
  cf(aH,L,1)
  ai=set_pixel
  for c in range(0,24,2):
   f=aa[c+1]
   ai(aa[c],f,p)
   if c&2 or L&1:
    f+=1
    if f>=P:
     f=q
     aa[c]=s(i)
    aa[c+1]=f
   ai(aa[c],f,bL[1 if c&2 else 0])
  an=keydown
  ai=5+k[bi]
  if an(ba):
   y=o[0]-ai
   o[0]=y if y>0 else 0
  if an(bb):
   y=o[0]+ai
   o[0]=y if y<i-ak else i-ak
  if Y[1]:
   if an(bE):
    y=o[1]-ai
    o[1]=y if y>0 else 0
   if an(bF):
    y=o[1]+ai
    o[1]=y if y<i-ak else i-ak
  cd=an(au)or(not Y[1]and an(av))
  if cd and not bV and a[N]>0:
   ce()
  bV=cd
  bN()
  bS(L,bl)
  bR()
  cj()
  if ab>0:
   bx-=1
   if bx<=0 and a[n]<bd-1:
    d=s(bt)
    ab-=cl[d]
    bx=bU(d,j)
  cf(aH,L,0)
  if aJ and a[n]:
   h=(180*g[3])//bk
   fill_rect(70,20,h,3,Z)
   fill_rect(70+h,20,180-h,3,at)
  bW(aA)
  if a[E]<=0:
   return False
  if a[n]==0 and(aJ or(ab<=0 and a[B]==0)):
   return True
  d=time.monotonic()
  x=by-d
  if x>0:
   time.sleep(x)
   by+=bD
  else:
   by=d+bD
def cA():
 aW()
 for cE in range(44):
  set_pixel(s(i),26+s(aY-26),(120,130,165))
 fill_rect(0,34,i,2,H)
 fill_rect(0,72,i,2,H)
 m("N O V A",46,F)
 m("A ROGUE-LITE FOR NUMWORKS",76,t)
 return 1+ap(["SOLO","CO-OP  2 PLAYERS"],[H,am],118,
 ["ARROWS MOVE, FIRE IS AUTO, EXE BOMBS",
 "P1 ARROWS, P2 KEYS 4 AND 6"])
def cz(bs):
 for c in range(8):
  k[c]=0
 a[R]=12+(6 if bs>1 else 0)
 a[E]=a[R]
 a[z]=0
 a[S]=0
 a[T]=0
 a[aD]=0
 a[ar]=2
 Y[1]=1 if bs>1 else 0
 o[0]=90 if bs>1 else 153
 o[1]=216
 for c in range(2):
  aw[c]=4
  X[c]=0
 ch(int(time.monotonic()*977))
 while True:
  a[W]=0
  while a[W]<7:
   u=bP()
   a[W]+=1
   a[N]=a[ar]
   if u==2:
    bz(0)
   elif u==3:
    ae("REPAIR BAY",Q)
    a[E]=min(a[R],a[E]+5)
    m("HULL RESTORED",90,Q)
    m("OK",180,t)
    aq()
   else:
    if not cu(u):
     return False
    if u:
     bz(1)
    else:
     a[z]+=6+k[ay]*3
  a[T]+=1
  j=a[T]
  if j==5:
   a[aD]=1
  ae("VICTORY"if j==5 else"SECTOR CLEARED",ax[(j-1)%5])
  m("THE VOID HAS NO EDGE"if j>=5 else
  ("ENTERING SECTOR %d"%(j+1)),88,am if j>=5 else F)
  m("SCORE %06d"%a[S],116,U)
  m("OK",180,t)
  aq()
def cx():
 while True:
  ck=cz(cA())
  j=a[T]
  ae("RUN COMPLETE"if ck else"SHIP LOST",Q if ck else Z)
  m(("VOID DEPTH %d"%(j-4))if j>4 else
  ("SECTOR %d"%(j+1)),60,am if j>4 else F)
  m("SCORE %06d"%a[S],86,U)
  if a[aD]:
   m("CAMPAIGN CLEARED",136,Q)
  m("OK TO CONTINUE",186,t)
  aq()
cx()
