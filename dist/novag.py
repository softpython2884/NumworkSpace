# NOVA - space rogue-lite for NumWorks. MIT licence.
# Generated from src/ by tools/build.py -- do not edit.
from novad import(z,H,at,Q,t,R,E,W,aj,Z,a,
ax,T,C,k,F,U,m,ae,af)
from novae import bm,bp,ap,cc
cm=("PATROL","ELITE PATROL","TRADER","REPAIR BAY","","WARLORD")
cn=(t,aj,U,Q,t,Z)
co=("CRYSTALS, AND A LITTLE TROUBLE","HARDER. IT PAYS IN UPGRADES",
"SPEND YOUR CRYSTALS HERE","REPAIR 5 HULL, FREE","",
"THE SECTOR BOSS. GOOD LUCK.")
def bP():
 h=a[W]
 if h>=6:
  return 5
 aS=[0,1,2]if h&1 else[0,1,3]
 ae("SECTOR %d   NODE %d"%(a[T]+1,h+1),ax[a[T]%5])
 m("%04d CRYSTALS   HULL %d/%d"%(a[z],a[E],a[R]),44,t)
 return aS[ap([cm[d]for d in aS],[cn[d]for d in aS],100,
 [co[d]for d in aS])]
def bz(aN):
 aP=cc()
 if not aP:
  return
 while True:
  aQ=[]
  aK=[]
  aO=[]
  for c in aP:
   G=bm(c)
   bO=aN or a[z]>=G
   aQ.append("%-16s%s %s"%(C[c][0],""if aN else"%3d"%G,
   "*"*k[C[c][1]]))
   aK.append(H if aN else(U if bO else at))
   aO.append(C[c][3]if bO else"NEED %d CRYSTALS"%G)
  if aN:
   ae("SALVAGE",H)
   m("CHOOSE ONE",34,t)
   bp(C[aP[ap(aQ,aK,90,aO)]][1])
   return
  aQ.append("LEAVE")
  aK.append(F)
  aO.append("BACK TO THE JUMP MENU")
  ae("TRADER",U)
  af("%04d"%a[z],8,30,H)
  l=ap(aQ,aK,70,aO)
  if l==3:
   return
  c=aP[l]
  G=bm(c)
  if a[z]>=G and k[C[c][1]]<3:
   a[z]-=G
   bp(C[c][1])
