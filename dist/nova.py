# NOVA - space rogue-lite for NumWorks. MIT licence.
# Generated from src/nova.py by tools/build.py -- do not edit.
# https://github.com/softpython2884/NumworkSpace
from kandinsky import fill_rect,draw_string,set_pixel
from ion import keydown
import ion
import time
bP=ion.KEY_LEFT
cI=ion.KEY_RIGHT
bQ=ion.KEY_UP
bO=ion.KEY_DOWN
dF=ion.KEY_FOUR
dG=ion.KEY_SIX
aK=ion.KEY_OK
at=ion.KEY_EXE
bq=ion.KEY_BACKSPACE
n=320
bo=222
bp=18
H=bp
af=bo
L=af-14
q=(0,0,0)
D=(255,255,255)
r=(110,120,140)
G=(40,46,60)
x=(0,230,255)
au=(255,150,0)
V=(255,60,60)
C=(60,255,120)
W=(255,235,60)
O=(190,100,255)
dw=(80,140,255)
bU=(x,C,O,au,V)
cy=1
def ex(p):
 global cy
 cy=(p&0xFFFF)or 1
def m(aF):
 global cy
 b=cy
 b^=(b<<7)&0xFFFF
 b^=b>>9
 b^=(b<<8)&0xFFFF
 cy=b
 return b%aF
aV=12
ag=12
aW=16
br=6
aL=14
ax=[0]*aV;ay=[0]*aV;bu=[0]*aV;bv=[0]*aV
A=0
Z=[0]*ag;aa=[0]*ag;Q=[0]*ag
Y=[0]*ag;P=[0]*ag;ba=[0]*ag
k=0
aB=[0]*aW;aC=[0]*aW;bx=[0]*aW;by=[0]*aW
v=0
aG=[0]*br;aH=[0]*br;bd=[0]*br
E=0
bf=[0]*aL;bJ=[0]*aL;cA=[0]*aL
eC=0
cP=1
dP=2
eD=3
dO=4
aw=5
dD=(
((0,2,10,4),(3,0,4,8)),
((0,0,10,3),(3,3,4,5)),
((0,0,12,6),(4,6,4,4)),
((2,0,4,10),(0,6,8,4)),
((0,0,16,8),(2,8,12,4)),
((0,0,48,14),(8,14,32,8)),
)
ar=(10,10,12,8,16,48)
aU=(8,8,10,10,12,22)
dB=(1,1,3,1,6,60)
cF=(10,15,25,20,40,500)
bX=0
bV=1
aY=2
cW=3
cS=4
cV=5
bZ=6
cU=7
cR=8
cT=9
bW=10
bY=11
cQ=12
l=[0]*cQ
M=(
("RAPID FIRE",bX,30),
("HEAVY ROUNDS",bV,35),
("SPREAD BARREL",aY,45),
("THRUSTERS",cW,25),
("RAILGUN",cS,25),
("PIERCING AMMO",cV,55),
("DEFLECTOR",bZ,50),
("TRACTOR BEAM",cU,20),
("OVERDRIVE CELL",cR,40),
("HULL PLATING",cT,45),
("SCAVENGER",bW,30),
("NANOREPAIR",bY,40),
)
o=[40,240]
ct=[40,240]
T=[1,0]
cr=[0,0]
aR=[0,0]
bF=[0,0]
ap=[0,0]
av=14
aX=10
dN=((5,0,4,4),(0,4,14,4),(2,8,10,2))
dA=(14,10,7)
dy=(68,112,160)
dz=(0,4,9)
cE=("CADET","PILOT","ACE")
aA=1
i=10
z=10
u=0
ad=0
w=0
ah=2
cd=2
es=1
dq=0
ce=0
U=8
s=3
bS=0
bt=1
cN=2
cL=3
cM=4
bR=5
S=[-1]*(U*s)
co=[0]*(U*s)
J=0
aE=1
def eE(b,c,aq,bz):
 fill_rect(b,c,aq,bz,q)
def dt(ew,b,c,d):
 I=fill_rect
 for g in ew:
  I(b+g[0],c+g[1],g[2],g[3],d)
def B(p,b,c,d=D,ca=q):
 draw_string(p,b,c,d,ca)
def j(p,c,d=D,ca=q):
 draw_string(p,(n-10*len(p))>>1,c,d,ca)
def bk():
 fill_rect(0,0,n,bo,q)
def cZ(b,c,aq,bz,bw,dl,d):
 if dl<=0:
  return
 R=(aq*bw)//dl
 if R<0:
  R=0
 elif R>aq:
  R=aq
 fill_rect(b,c,R,bz,d)
 fill_rect(b+R,c,aq-R,bz,G)
ci=-1
cj=-1
ch=-1
cg=-1
ck=""
def df():
 global ci,cj,ch,cg,ck
 ci=-1;cj=-1;ch=-1;cg=-1;ck=""
 fill_rect(0,0,n,bp,q)
 fill_rect(0,bp-1,n,1,G)
def ee(bg):
 global ci,cj,ch,cg,ck
 if ci!=i:
  ci=i
  d=C if i*3>z*2 else(W if i*3>z else V)
  cZ(2,4,56,10,i,z,d)
 if cg!=ah:
  cg=ah
  for a in range(4):
   fill_rect(63+a*9,5,7,8,au if a<ah else G)
 if cj!=ad:
  cj=ad
  B("%06d"%ad,104,0,D)
 if ch!=u:
  ch=u
  B("%04d"%u,178,0,x)
 if ck!=bg:
  ck=bg
  B(bg,246,0,r)
bT=((55,60,80),(120,130,160),(225,230,255))
def ey():
 for a in range(aL):
  bf[a]=m(n)
  bJ[a]=H+m(af-H)
  cA[a]=a%3
def cC():
 bH=set_pixel
 for a in range(aL):
  bH(bf[a],bJ[a],bT[cA[a]])
def ez(al):
 bH=set_pixel
 for a in range(aL):
  bC=cA[a]
  if bC==2 or(bC==1 and not al&1)or(bC==0 and not al%3):
   c=bJ[a]
   bH(bf[a],c,q)
   c+=1
   if c>=af:
    c=H
    bf[a]=m(n)
   bJ[a]=c
   bH(bf[a],c,bT[bC])
bs=5
bm=[0]*bs;bn=[0]*bs;aT=[0]*bs
F=0
def aM(b,c,p):
 global F
 if F<bs:
  bm[F]=b;bn[F]=c;aT[F]=p
  F+=1
def dh(a):
 global A
 A-=1
 if a!=A:
  ax[a]=ax[A];ay[a]=ay[A];bu[a]=bu[A];bv[a]=bv[A]
def bB(a):
 global k
 k-=1
 if a!=k:
  Z[a]=Z[k];aa[a]=aa[k];Q[a]=Q[k]
  Y[a]=Y[k];P[a]=P[k];ba[a]=ba[k]
def di(a):
 global v
 v-=1
 if a!=v:
  aB[a]=aB[v];aC[a]=aC[v];bx[a]=bx[v];by[a]=by[v]
def dj(a):
 global E
 E-=1
 if a!=E:
  aG[a]=aG[E];aH[a]=aH[E];bd[a]=bd[E]
def ds(e,b,c,ab,cn):
 global k
 if k<ag:
  Z[k]=b;aa[k]=c;Q[k]=e
  Y[k]=cn;P[k]=ab;ba[k]=20+m(40)
  k+=1
def aS(b,c,bj,K):
 global v
 if v<aW:
  aB[v]=b;aC[v]=c;bx[v]=bj;by[v]=K
  v+=1
def cB(b,c,h):
 global E
 if E<br:
  aG[E]=b;aH[E]=c;bd[E]=h
  E+=1
cO=(
((0,0),),
((-5,0),(5,0)),
((-5,-1),(0,0),(5,1)),
((-6,-2),(-2,0),(2,0),(6,2)),
)
def eu(f):
 global A
 cf=1+l[bV]
 eq=l[cV]
 for dm in cO[l[aY]if l[aY]<4 else 3]:
  if A>=aV:
   return
  ax[A]=o[f]+6+dm[0]
  ay[A]=L-6
  bu[A]=dm[1]
  bv[A]=cf+(100 if eq else 0)
  A+=1
cH=0.04
dC=(2,2,2,5,1,0)
dE=(110,0,55,0,70,34)
def da(dk,bA):
 global A,k,v,E,F,i,u,ad,ah
 A=k=v=E=F=0
 bk()
 df()
 ey()
 cC()
 dQ=bU[w%5]
 aZ=dk==bR
 dX=dk==bt
 ai=((14+w*9+bA*3)*dy[aA])//100
 if ai>84:
  ai=84
 if dX:
  ai=(ai*7)//5
 cc=0
 if aZ:
  ai=0
  cw=9-(l[bX]<<1)
  if cw<3:
   cw=3
  dV=(1+l[bV])*len(cO[l[aY]if l[aY]<4 else 3])*25//cw
  cc=30+w*4+dV*7
  ds(aw,136,H+4,1,cc)
 dx=(1,2,3,2,5)
 cs=2+w
 if cs>5:
  cs=5
 bg="BOSS"if aZ else("S%d-%d"%(w+1,bA+1))
 be=30
 al=0
 et=dz[aA]+w*3
 bK=time.monotonic()
 do=True
 while True:
  al+=1
  ao=keydown
  bI=5+l[cW]
  if ao(bP):
   K=o[0]-bI
   o[0]=K if K>0 else 0
  if ao(cI):
   K=o[0]+bI
   o[0]=K if K<n-av else n-av
  if T[1]:
   if ao(dF):
    K=o[1]-bI
    o[1]=K if K>0 else 0
   if ao(dG):
    K=o[1]+bI
    o[1]=K if K<n-av else n-av
   cq=ao(at)
  else:
   cq=ao(at)or ao(aK)
  ea=cq and not do
  do=cq
  if ao(bq):
   if eo()==0:
    return False
   bk();df();cC()
   bK=time.monotonic()
  if ea and ah>0:
   ah-=1
   fill_rect(0,H,n,af-H,(255,255,255))
   fill_rect(0,H,n,af-H,q)
   cC()
   v=0
   a=k-1
   while a>=0:
    Y[a]-=4
    if Y[a]<=0:
     ad+=cF[Q[a]]
     aM(Z[a],aa[a],4)
     bB(a)
    a-=1
  ez(al)
  I=fill_rect
  for a in range(A):
   I(ax[a],ay[a],2,6,q)
  for a in range(k):
   e=Q[a]
   I(Z[a],aa[a],ar[e],aU[e]+2,q)
  for a in range(v):
   I(aB[a],aC[a],3,5,q)
  for a in range(E):
   I(aG[a],aH[a],5,5,q)
  for a in range(F):
   I(bm[a],bn[a],12,12,q)
  for a in range(2):
   if T[a]:
    I(ct[a],L,av,aX,q)
  a=A-1
  dT=9+(l[cS]<<1)
  while a>=0:
   c=ay[a]-dT
   if c<H:
    dh(a)
    a-=1
    continue
   ay[a]=c
   b=ax[a]+bu[a]
   ax[a]=b
   db=bv[a]
   cf=db%100
   y=k-1
   dc=False
   while y>=0:
    bi=aa[y]
    if c<bi+aU[Q[y]]and c+6>bi:
     bh=Z[y]
     if b<bh+ar[Q[y]]and b+2>bh:
      Y[y]-=cf
      if Y[y]<=0:
       e=Q[y]
       ad+=cF[e]
       aM(bh,bi,3 if e!=aw else 8)
       if e==aw:
        for cX in range(5):
         cB(bh+8+m(32),bi+8,0)
       elif m(10)<6:
        cB(bh+3,bi+3,1 if m(8)==0 else 0)
       bB(y)
      else:
       aM(b-4,c-4,1)
      if db<100:
       dc=True
       break
    y-=1
   if dc:
    dh(a)
   a-=1
  a=k-1
  while a>=0:
   e=Q[a]
   b=Z[a]
   c=aa[a]
   if e==cP:
    b+=P[a]
    if b<0 or b>n-ar[e]:
     P[a]=-P[a]
     b=0 if b<0 else n-ar[e]
    c+=2
   elif e==dP:
    if c<P[a]:
     c+=2
    elif al&1:
     P[a]+=1
   elif e==aw:
    b+=P[a]
    if b<4 or b>n-52:
     P[a]=-P[a]
    if not al%10:
     c+=1
   else:
    c+=dC[e]
   Z[a]=b
   aa[a]=c
   if c>af:
    bB(a)
    a-=1
    continue
   R=dE[e]
   if R:
    d=ba[a]-1
    if d<=0:
     d=R-et-m(20)
     if d<14:
      d=14
     az=b+(ar[e]>>1)
     aN=c+aU[e]
     t=(o[0]+7-az)>>5
     if t>2:
      t=2
     elif t<-2:
      t=-2
     if e==aw:
      aS(az-18,aN,-1,4)
      aS(az,aN,t,4)
      aS(az+18,aN,1,4)
     elif e==dO:
      aS(az-6,aN,t-1,3)
      aS(az+6,aN,t+1,3)
     else:
      aS(az,aN,t,4)
    ba[a]=d
   ed=aU[e]
   if c+ed>L and c<L+aX:
    eB=ar[e]
    for f in range(2):
     if T[f]and not ap[f]:
      am=o[f]+4
      if b<am+6 and b+eB>am:
       dg(f)
       if e!=aw:
        Y[a]=0
        aM(b,c,3)
        bB(a)
       break
   a-=1
  a=v-1
  while a>=0:
   c=aC[a]+by[a]
   b=aB[a]+bx[a]
   if c>af or b<0 or b>n:
    di(a)
    a-=1
    continue
   aC[a]=c
   aB[a]=b
   if c+5>L and c<L+aX:
    for f in range(2):
     if T[f]and not ap[f]:
      am=o[f]+4
      if b<am+6 and b+3>am:
       dg(f)
       di(a)
       break
   a-=1
  a=E-1
  while a>=0:
   c=aH[a]+2
   b=aG[a]
   if l[cU]and c>H+40:
    cb=o[0]
    if T[1]and abs(o[1]-b)<abs(cb-b):
     cb=o[1]
    t=cb+4-b
    if t>1:
     b+=2
    elif t<-1:
     b-=2
   if c>af:
    dj(a)
    a-=1
    continue
   aH[a]=c
   aG[a]=b
   for f in range(2):
    if T[f]and c+5>L and c<L+aX:
     am=o[f]
     if b<am+av and b+5>am:
      if bd[a]:
       if i<z:
        i+=1
      else:
       u+=2+l[bW]
       ad+=5
      dj(a)
      break
   a-=1
  a=F-1
  while a>=0:
   aT[a]-=1
   if aT[a]<=0:
    F-=1
    if a!=F:
     bm[a]=bm[F];bn[a]=bn[F];aT[a]=aT[F]
   a-=1
  cv=9-(l[bX]<<1)
  if cv<3:
   cv=3
  for f in range(2):
   if not T[f]:
    continue
   if ap[f]:
    ap[f]-=1
   d=cr[f]-1
   if d<=0:
    eu(f)
    d=cv
   cr[f]=d
   if l[bZ]and not aR[f]:
    bF[f]-=1
    if bF[f]<=0:
     aR[f]=1
  if ai>0:
   be-=1
   if be<=0 and k<ag-1:
    e=m(cs)
    ai-=dx[e]
    aq=ar[e]
    cn=dB[e]+(w>>1)
    ab=-2+(m(2)<<2)if e==cP else H+20+m(50)
    ds(e,4+m(n-aq-8),H-aU[e],ab,cn)
    be=16+m(22)-w*2
    if be<7:
     be=7
  for a in range(A):
   I(ax[a],ay[a],2,6,W)
  for a in range(k):
   e=Q[a]
   dt(dD[e],Z[a],aa[a],V if e==aw else dQ)
  for a in range(v):
   I(aB[a],aC[a],3,5,au)
  for a in range(E):
   I(aG[a],aH[a],5,5,C if bd[a]else x)
  for a in range(F):
   p=aT[a]
   I(bm[a]+4-p,bn[a]+4-p,p<<1,p<<1,D if p>2 else au)
  for a in range(2):
   if T[a]:
    b=o[a]
    ct[a]=b
    if not ap[a]or al&2:
     dt(dN,b,L,x if a==0 else O)
     if l[bZ]and aR[a]:
      I(b-1,L+aX,av+2,1,dw)
  if aZ and k:
   cZ(70,bp+2,180,4,Y[0],cc,V)
  ee(bg)
  if i<=0:
   return False
  if not aZ and ai<=0 and k==0 and v==0:
   return True
  if aZ and k==0:
   for cX in range(8):
    cB(60+m(200),H+40+m(60),0)
   return True
  e=time.monotonic()
  t=bK-e
  if t>0:
   time.sleep(t)
   bK+=cH
  else:
   bK=e+cH
def dg(f):
 global i
 if aR[f]:
  aR[f]=0
  bF[f]=170
  ap[f]=20
  aM(o[f],L-4,4)
  return
 i-=1
 ap[f]=45
 aM(o[f],L-4,5)
cJ=(bQ,bO,bP,cI,aK,at,bq)
def cY():
 for h in cJ:
  if keydown(h):
   return True
 return False
def aD():
 while cY():
  time.sleep(0.02)
 while True:
  for h in cJ:
   if keydown(h):
    return h
  time.sleep(0.02)
def eo():
 fill_rect(60,80,200,62,G)
 fill_rect(62,82,196,58,q)
 j("PAUSED",92,D)
 j("OK  RESUME",112,r)
 while True:
  h=aD()
  if h==aK or h==at or h==bq:
   return 1
  if h==bP:
   return 0
dL=("X","!","$","?","+","@")
cK=(r,au,W,x,C,V)
dM=("PATROL","ELITE","TRADER","SIGNAL","REPAIR","WARLORD")
def em(d):
 if d==1:
  return bS
 if d==4:
  return cN
 if d==6:
  return cM
 g=m(100)
 if g<46:
  return bS
 if g<70:
  return bt
 return cL
def eb():
 global J,aE
 for a in range(U*s):
  S[a]=-1
  co[a]=0
 S[1]=bS
 J=0
 aE=1
 bw=[1]
 for d in range(1,U-1):
  bD=[]
  for g in bw:
   for cX in range(1+m(2)):
    aQ=g+m(3)-1
    if aQ<0:
     aQ=0
    elif aQ>=s:
     aQ=s-1
    if aQ not in bD:
     bD.append(aQ)
  for g in bD:
   S[d*s+g]=em(d)
  bw=bD
 S[(U-1)*s+1]=bR
dJ=14
dH=38
dK=52
dI=44
def cp(d,g):
 return(dJ+d*dH,dK+g*dI)
def ef(bl,ae,bM,aJ,d):
 bN=(bl+bM)>>1
 fill_rect(bl,ae,bN-bl,2,d)
 if aJ!=ae:
  fill_rect(bN,ae if aJ>ae else aJ,2,abs(aJ-ae)+2,d)
 fill_rect(bN,aJ,bM-bN,2,d)
def dW(dr):
 bk()
 B("SECTOR %d"%(w+1),6,2,bU[w%5])
 B("%04d"%u,178,2,x)
 B("HULL %d"%i,240,2,C if i>2 else V)
 for d in range(U-1):
  for g in range(s):
   if S[d*s+g]<0:
    continue
   bl,ae=cp(d,g)
   for cu in range(s):
    if S[(d+1)*s+cu]<0 or abs(cu-g)>1:
     continue
    bM,aJ=cp(d+1,cu)
    eg=(d==J and g==aE)
    ef(bl+20,ae+9,bM,aJ+9,D if eg else G)
 for d in range(U):
  for g in range(s):
   e=S[d*s+g]
   if e<0:
    continue
   b,c=cp(d,g)
   de=(d==J and g==aE)
   ep=(d==J+1 and g==dr)
   if co[d*s+g]:
    fill_rect(b,c,20,20,G)
    B(".",b+5,c,r,G)
   else:
    dR=D if ep else(G if not de else r)
    fill_rect(b,c,20,20,dR)
    fill_rect(b+2,c+2,16,16,q)
    B(dL[e],b+5,c+1,cK[e],q)
   if de:
    fill_rect(b+4,c+22,12,3,x)
 cz=S[(J+1)*s+dr]if J+1<U else-1
 fill_rect(0,170,n,bo-170,q)
 j("UP/DOWN + OK",172,r)
 if cz>=0:
  j(dM[cz],196,cK[cz])
def dU():
 bc=[]
 for g in range(s):
  if abs(g-aE)<=1 and S[(J+1)*s+g]>=0:
   bc.append(g)
 if not bc:
  return-1
 a=0
 while True:
  dW(bc[a])
  h=aD()
  if h==bQ and a>0:
   a-=1
  elif h==bO and a<len(bc)-1:
   a+=1
  elif h==aK or h==at:
   return bc[a]
def dn(aF):
 bE=[]
 dv=0
 while len(bE)<aF and dv<40:
  dv+=1
  a=m(len(M))
  if a not in bE and l[M[a][1]]<3:
   bE.append(a)
 return bE
def dp(a):
 return M[a][2]+(M[a][2]*l[M[a][1]])//2
def ac(cl,du):
 bk()
 fill_rect(0,0,n,3,du)
 j(cl,10,du)
def bb(N,X,ae):
 a=0
 aF=len(N)
 while True:
  for y in range(aF):
   c=ae+y*22
   fill_rect(20,c,280,20,r if y==a else q)
   B(N[y],28,c+1,q if y==a else X[y],
   r if y==a else q)
  h=aD()
  if h==bQ:
   a=aF-1 if a==0 else a-1
  elif h==bO:
   a=0 if a==aF-1 else a+1
  elif h==aK or h==at:
   return a
def ev():
 global u,i,z
 an=dn(3)
 while True:
  N=[]
  X=[]
  for a in an:
   eh=l[M[a][1]]
   ab=dp(a)
   N.append("%-15s%3d%s"%(M[a][0],ab,"*"*eh))
   X.append(W if u>=ab else G)
  N.append("%-15s %2d"%("REPAIR HULL",18))
  X.append(C if u>=18 and i<z else G)
  N.append("LEAVE")
  X.append(D)
  ac("TRADER",W)
  B("%04d"%u,178,30,x)
  d=bb(N,X,60)
  if d==len(N)-1:
   return
  if d==len(N)-2:
   if u>=18 and i<z:
    u-=18
    i+=2
    if i>z:
     i=z
   continue
  a=an[d]
  ab=dp(a)
  if u>=ab and l[M[a][1]]<3:
   u-=ab
   dd(M[a][1])
def dd(bj):
 global z,i,cd,ah
 l[bj]+=1
 if bj==cT:
  z+=2
  i+=2
 elif bj==cR:
  cd+=1
  ah+=1
def cx(dS):
 an=dn(3)
 if not an:
  return
 if not dS:
  an=an[:2]
 ac("SALVAGE",x)
 j("CHOOSE ONE",34,r)
 N=[]
 X=[]
 for a in an:
  N.append("%-16s%s"%(M[a][0],"*"*l[M[a][1]]))
  X.append(x)
 d=bb(N,X,70)
 dd(M[an[d]][1])
cG=(
("DERELICT HULK","IT IS VENTING ATMOSPHERE","SALVAGE",1,26,"MOVE ON",0,8),
("DISTRESS BEACON","THE SIGNAL LOOPS","ANSWER",3,0,"IGNORE",0,10),
("FUEL DEPOT","ABANDONED, MOSTLY","SIPHON",0,22,"REPAIR HERE",2,3),
("DRIFTING ENGINEER","SHE WANTS PASSAGE","TAKE HER IN",5,0,"REFUSE",0,14),
("ASTEROID FIELD","DENSE, AND VERY QUIET","CUT THROUGH",1,30,"GO AROUND",4,0),
("VOID SHRINE","PILGRIMS TRADED HERE","OFFER 25",6,25,"STEAL",3,0),
)
def dZ(bA):
 global u,i,z
 aj=cG[m(len(cG))]
 ac(aj[0],O)
 j(aj[1],40,r)
 d=bb([aj[2],aj[5]],[O,O],90)
 aO,aI=(aj[3],aj[4])if d==0 else(aj[6],aj[7])
 if aO==0:
  u+=aI
  ak("+%d CRYSTALS"%aI,x)
 elif aO==1:
  if m(10)<6:
   u+=aI
   ak("+%d CRYSTALS"%aI,x)
  else:
   i-=2
   ak("HULL BREACH  -2",V)
 elif aO==2:
  i=min(z,i+aI)
  ak("HULL REPAIRED",C)
 elif aO==3:
  ak("AMBUSH!",V)
  return da(bt,bA)
 elif aO==5:
  ak("SHE OWES YOU ONE",O)
  cx(False)
 elif aO==6:
  if u>=aI:
   u-=aI
   z+=2
   i+=2
   ak("MAX HULL +2",C)
  else:
   ak("NOT ENOUGH",G)
 return True
def ak(ek,d):
 fill_rect(0,150,n,24,q)
 j(ek,152,d)
 time.sleep(1.1)
cD=(ion.KEY_ZERO,ion.KEY_ONE,ion.KEY_TWO,ion.KEY_THREE,ion.KEY_FOUR,
ion.KEY_FIVE,ion.KEY_SIX,ion.KEY_SEVEN,ion.KEY_EIGHT,ion.KEY_NINE)
def en(cl,ej):
 ac(cl,x)
 j("TYPE DIGITS, OK TO START",40,r)
 p=""
 while True:
  fill_rect(60,90,200,24,G)
  B(p+"_",68,92,D,G)
  while True:
   cm=-1
   for t in range(10):
    if keydown(cD[t]):
     cm=t
     break
   if cm>=0:
    if len(p)<ej:
     p+=chr(48+cm)
    break
   if keydown(bq):
    p=p[:-1]
    break
   if keydown(aK)or keydown(at):
    return int(p)if p else 0
   time.sleep(0.02)
  while cY()or[1 for t in range(10)if keydown(cD[t])]:
   time.sleep(0.02)
def eA():
 global aA
 while True:
  bk()
  for a in range(40):
   set_pixel(m(n),30+m(bo-30),bT[m(3)])
  fill_rect(0,40,n,3,x)
  j("N O V A",52,D)
  fill_rect(0,74,n,3,x)
  j("A ROGUE-LITE FOR NUMWORKS",80,r)
  d=bb(["SOLO","CO-OP  2 PLAYERS","SEEDED RUN",
  "DIFFICULTY  "+cE[aA],"CONTROLS"],
  [x,O,W,au,r],108)
  if d==0:
   return 1,time.monotonic().__int__()&0xFFFF
  if d==1:
   return 2,time.monotonic().__int__()&0xFFFF
  if d==2:
   return 1,en("SEEDED RUN",5)&0xFFFF
  if d==3:
   aA=(aA+1)%3
  else:
   ec()
def ec():
 ac("CONTROLS",r)
 B("P1      LEFT / RIGHT ARROWS",14,40,x)
 B("P2      KEYS 4 AND 6",14,62,O)
 B("FIRE    AUTOMATIC",14,84,W)
 B("BOMB    EXE  (SOLO: ALSO OK)",14,106,au)
 B("PAUSE   BACKSPACE",14,128,r)
 j("CLEAR 5 SECTORS TO WIN",168,D)
 j("OK",194,r)
 aD()
def dY(bL):
 ac("RUN COMPLETE"if bL else"SHIP LOST",C if bL else V)
 if w>=5:
  j("VOID DEPTH %d"%(w-4),60,O)
 else:
  j("SECTOR %d"%(w+1),60,D)
 j("SCORE %06d"%ad,84,W)
 j("SEED %05d  %s"%(dq,cE[aA]),108,r)
 if ce:
  j("CAMPAIGN CLEARED",136,C)
 j("OK TO CONTINUE",190,r)
 aD()
def el(aP,bG):
 global i,z,u,ad,w,ah,cd,es,dq
 global cy,ce
 for a in range(cQ):
  l[a]=0
 z=dA[aA]+(6 if aP>1 else 0)
 i=z
 u=0
 ad=0
 w=0
 ce=0
 ah=2
 cd=2
 es=aP
 dq=bG
 ex(bG)
 T[0]=1
 T[1]=1 if aP>1 else 0
 o[0]=90 if aP>1 else 153
 o[1]=216
 for a in range(2):
  ct[a]=o[a]
  cr[a]=4
  aR[a]=0
  bF[a]=0
  ap[a]=0
def er():
 global w,J,aE,ah,i,u,ce
 while True:
  eb()
  while True:
   g=dU()
   if g<0:
    break
   J+=1
   aE=g
   h=S[J*s+aE]
   co[J*s+aE]=1
   ah=cd
   if l[bY]and i<z:
    i=min(z,i+l[bY])
   if h==cN:
    ev()
   elif h==cM:
    ac("REPAIR BAY",C)
    i=min(z,i+4)
    j("HULL RESTORED",90,C)
    j("OK",180,r)
    aD()
   elif h==cL:
    if not dZ(J):
     return False
   else:
    if not da(h,J):
     return False
    if h==bt:
     cx(False)
    elif h==bR:
     cx(True)
    else:
     u+=6+l[bW]*3
   if J>=U-1:
    break
  w+=1
  if w==5:
   ce=1
   ac("VICTORY",C)
   j("FIVE SECTORS CLEARED",62,C)
   j("SCORE %06d"%ad,86,W)
   j("THE VOID HAS NO EDGE",112,O)
   if bb(["ENTER THE VOID","END RUN HERE"],[O,D],146)==1:
    return True
  else:
   ac("SECTOR CLEARED",bU[(w-1)%5])
   j("ENTERING SECTOR %d"%(w+1),90,D)
   j("OK",180,r)
   aD()
def ei():
 while True:
  aP,bG=eA()
  el(aP,bG)
  bL=er()
  dY(bL)
ei()
