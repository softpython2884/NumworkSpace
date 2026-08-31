# NOVA - space rogue-lite for NumWorks. MIT licence.
# Generated from src/ by tools/build.py -- do not edit.
from kandinsky import fill_rect,draw_string,set_pixel
from ion import keydown
import ion
import time
i=320
aY=222
q=18
P=222
ag=208
ak=14
aE=10
p=(0,0,0)
F=(255,255,255)
t=(128,140,160)
at=(38,44,58)
H=(60,235,255)
aj=(255,150,30)
Z=(255,70,70)
Q=(80,255,130)
U=(255,225,60)
am=(200,120,255)
ax=(H,Q,am,aj,Z)
bL=((96,104,134),(228,234,255))
aa=[0]*24
ba=ion.KEY_LEFT
bb=ion.KEY_RIGHT
bc=ion.KEY_UP
aZ=ion.KEY_DOWN
bE=ion.KEY_FOUR
bF=ion.KEY_SIX
av=ion.KEY_OK
au=ion.KEY_EXE
cp=ion.KEY_BACKSPACE
bG=(bc,aZ,ba,bb,av,au,cp)
E=0
R=1
z=2
S=3
T=4
N=5
ar=6
J=7
n=8
B=9
cD=10
aF=11
W=12
aD=13
a=[0]*14
a[aF]=1
az=0
aG=1
al=2
bi=3
bh=4
bf=5
bg=6
ay=7
k=[0]*8
C=(
("RAPID FIRE",az,30,"SHOOT 2 FRAMES SOONER"),
("HEAVY ROUNDS",aG,34,"+1 DAMAGE PER SHOT"),
("SPREAD BARREL",al,46,"+1 CANNON, WIDER ARC"),
("THRUSTERS",bi,24,"+1 PIXEL OF SPEED"),
("PIERCING AMMO",bh,54,"SHOTS PASS THROUGH KILLS"),
("OVERDRIVE CELL",bf,40,"+1 BOMB PER NODE"),
("HULL PLATING",bg,44,"+2 MAX HULL, HEALS 2"),
("SCAVENGER",ay,30,"+1 CRYSTAL PER KILL"),
)
O=5
I=b"\x0a\x0a\x0c\x08\x10\x30"
V=b"\x08\x08\x0a\x0a\x0c\x16"
bA=b"\x01\x01\x03\x01\x06\x01"
bB=b"\x02\x03\x05\x04\x08\x64"
bC=b"\x02\x02\x00\x05\x01\x00"
aX=b"\x6e\x00\x37\x00\x46\x22"
bK=(b"\x00\x00\x0a\x03\x03\x03\x04\x03\x04\x06\x02\x02"
b"\x00\x01\x03\x05\x07\x01\x03\x05\x03\x00\x04\x08"
b"\x00\x00\x0c\x05\x02\x05\x08\x03\x04\x08\x04\x02"
b"\x00\x00\x08\x03\x02\x03\x04\x04\x03\x07\x02\x03"
b"\x00\x00\x10\x06\x02\x06\x0c\x04\x06\x0a\x04\x02"
b"\x00\x00\x30\x0a\x06\x0a\x24\x08\x12\x12\x0c\x04")
bJ=b"\x06\x00\x02\x03\x04\x03\x06\x03\x00\x06\x0e\x04"
be=(((0,0),),((-5,0),(5,0)),((-5,-1),(0,0),(5,1)),
((-6,-2),(-2,0),(2,0),(6,2)))
def ch(M):
 a[aF]=(M&0xFFFF)or 1
def s(h):
 e=a[aF]
 e^=(e<<7)&0xFFFF
 e^=e>>9
 e^=(e<<8)&0xFFFF
 a[aF]=e
 return e%h
def bw(D,b,e,f,l):
 ac=fill_rect
 ac(e+D[b],f+D[b+1],D[b+2],D[b+3],l)
 ac(e+D[b+4],f+D[b+5],D[b+6],D[b+7],l)
 ac(e+D[b+8],f+D[b+9],D[b+10],D[b+11],l)
def af(M,e,f,l=F,bj=p):
 draw_string(M,e,f,l,bj)
def m(M,f,l=F,bj=p):
 draw_string(M,(i-10*len(M))>>1,f,l,bj)
def aW():
 fill_rect(0,0,i,aY,p)
def ae(cw,ci):
 aW()
 fill_rect(0,0,i,3,ci)
 m(cw,8,ci)
def cq():
 for u in bG:
  if keydown(u):
   return True
 return False
def aq():
 while cq():
  time.sleep(0.02)
 while True:
  for u in bG:
   if keydown(u):
    return u
  time.sleep(0.02)
A=[-1,-1,-1,""]
def bX():
 A[0]=-1
 A[1]=-1
 A[2]=-1
 A[3]=""
 fill_rect(0,0,i,q,p)
 fill_rect(0,q-1,i,1,at)
def bW(aA):
 ah=a[E]
 if A[0]!=ah:
  A[0]=ah
  ao=a[R]
  af("%2d"%ah,2,0,Q if ah*3>ao*2 else(U if ah*3>ao else Z))
 if A[1]!=a[N]:
  A[1]=a[N]
  af("*%d"%a[N],30,0,aj)
 if A[2]!=a[S]:
  A[2]=a[S]
  af("%06d %04d"%(a[S],a[z]),74,0,F)
 if A[3]!=aA:
  A[3]=aA
  af(aA,246,0,t)
