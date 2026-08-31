# NOVA - space rogue-lite for NumWorks. MIT licence.
# Generated from src/ by tools/build.py -- do not edit.
from novad import(p,ar,N,O,P,z,V,bA,bB,I,t,
R,E,aZ,au,av,bc,J,n,B,aE,ag,a,S,C,be,
q,bf,aG,ay,bg,k,bh,az,al,i,F,m,
fill_rect,aq,s,af)
bH=12
bd=12
bI=16
v=[0]*(bH*4)
g=[0]*(bd*6)
w=[0]*(bI*4)
o=[40,240]
aw=[0,0]
X=[0,0]
Y=[1,0]
def ad(G,b,aC,bQ):
 h=a[bQ]-1
 a[bQ]=h
 ao=h*aC
 if b!=ao:
  G[b:b+aC]=G[ao:ao+aC]
def aM(e,f,aB,y):
 h=a[B]
 if h<bI:
  w[h*4:h*4+4]=(e,f,aB,y)
  a[B]=h+1
def bq(e,f,aC,ah):
 if f+ah>ag and f<ag+aE:
  for c in range(2):
   if Y[c]and not X[c]:
    bY=o[c]+4
    if e<bY+6 and e+aC>bY:
     return c
 return-1
def br(r):
 a[E]-=1
 X[r]=45
def cg(r):
 x=1+k[aG]+(100 if k[bh]else 0)
 for cb in be[k[al]if k[al]<4 else 3]:
  h=a[J]
  if h>=bH:
   return
  v[h*4:h*4+4]=(o[r]+6+cb[0],ag-6,cb[1],x)
  a[J]=h+1
def bm(c):
 return C[c][2]+(C[c][2]*k[C[c][1]])//2
def cc():
 aT=[]
 d=0
 while len(aT)<3 and d<30:
  d+=1
  c=s(8)
  if c not in aT and k[C[c][1]]<3:
   aT.append(c)
 return aT
def bp(aB):
 k[aB]+=1
 if aB==bg:
  a[R]+=2
  a[E]+=2
 elif aB==bf:
  a[ar]+=1
  a[N]+=1
def bU(d,j):
 h=a[n]
 G=-2+(s(2)<<2)if d==1 else q+20+s(50)
 g[h*6:h*6+6]=(4+s(i-I[d]-8),q-V[d],d,
 bA[d]+(j>>1),G,20+s(40))
 a[n]=h+1
 x=16+s(22)-j*2
 return x if x>7 else 7
def ce():
 a[N]-=1
 fill_rect(0,q,i,P-q,F)
 fill_rect(0,q,i,P-q,p)
 a[B]=0
 b=(a[n]-1)*6
 while b>=0:
  g[b+3]-=4
  if g[b+3]<=0:
   bo(b,g[b+2],g[b],g[b+1])
  b-=6
def bM(j):
 bu=9-(k[az]<<1)
 if bu<3:
  bu=3
 h=len(be[k[al]if k[al]<4 else 3])
 return 30+j*4+(1+k[aG])*h*25//bu*7
def ap(bZ,cs,cC,cv):
 c=0
 h=len(bZ)
 while True:
  for aR in range(h):
   f=cC+aR*21
   M=aR==c
   fill_rect(16,f,288,19,t if M else p)
   af(bZ[aR],22,f,p if M else cs[aR],t if M else p)
  fill_rect(0,196,i,22,p)
  m(cv[c],198,t)
  u=aq()
  if u==bc:
   c=h-1 if c==0 else c-1
  elif u==aZ:
   c=0 if c==h-1 else c+1
  elif u==av or u==au:
   return c
def bo(K,d,aU,aV):
 a[S]+=bB[d]*5
 a[z]+=(6 if d==O else 1)*(2+k[ay])
 ad(g,K,6,n)
