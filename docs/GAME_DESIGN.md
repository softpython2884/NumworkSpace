# Game design

## L'objectif

Un jeu qu'on lance quand on a une heure devant soi, qui ne lasse pas.

Une heure, ce n'est pas *une partie d'une heure*. C'est une **session** d'une
heure : quatre ou cinq parties de douze à quinze minutes qui s'enchaînent,
chacune différente. C'est le modèle rogue-lite, et il convient particulièrement
à une calculatrice — on joue par à-coups, on peut s'arrêter entre deux nœuds.

Mesuré sur des parties simulées : **7 minutes de combat pur** par partie, soit
douze à quinze minutes une fois comptés les menus.

## Ce que le matériel a décidé à notre place

**Pas de communication entre calculatrices.** Aucune API réseau en Python sur
Epsilon. Le multi ne peut donc être que local, d'où la **coop en écran partagé**
sur le même clavier.

**Pas de système de fichiers.** Aucune sauvegarde possible. La progression tient
dans une seule partie, et la rejouabilité vient de la variété des builds.

**Un clavier sans anti-ghosting.** Le tir automatique et le déplacement
horizontal ne sont pas un choix esthétique : à trois touches simultanées, la
matrice invente des appuis. Bénéfice inattendu : le jeu se joue d'une main.

**32 Ko de tas.** Celle-là a coûté le plus cher — voir plus bas.

## La boucle

```
   ┌──────────────────────────────┐
   │        CHOIX DU SAUT         │   trois routes, sept nœuds par secteur
   └──────────────┬───────────────┘
        ┌─────────┼─────────┬──────────────┐
        ▼         ▼         ▼              ▼
    PATROUILLE  ÉLITE    MARCHAND    ATELIER DE RÉPARATION
     cristaux  upgrade    achats          +5 coque
        └─────────┴─────────┴──────────────┘
                       │
                       ▼
                BOSS de secteur
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   secteur suivant           après le 5ᵉ : LE VIDE
                             (sans fin, pour le score)
```

Chaque saut propose **patrouille**, **patrouille d'élite**, et selon la parité du
nœud un **marchand** ou un **atelier**. La décision — soigner, acheter, ou
pousser pour du butin — est la même à chaque fois, et c'est elle qui compte.

## Les ennemis

| Type | Comportement | PV | Points |
|---|---|---:|---:|
| **Grunt** | descend droit, tire rarement | 1 | 10 |
| **Weaver** | zigzag, rebondit sur les bords, ne tire pas | 1 | 15 |
| **Turret** | s'ancre en haut et bombarde | 3 | 25 |
| **Rusher** | plonge vite, ne tire pas | 1 | 20 |
| **Tank** | lent, encaisse | 6 | 40 |
| **Boss** | balaie l'écran, salves de trois, **descend** | ∝ | 500 |

Les types se débloquent au fil des secteurs : le premier n'oppose que des grunts
et des weavers.

### Deux ennemis ont été redessinés par les tests

**La tourelle bloquait le jeu.** Elle s'ancrait et campait indéfiniment ; un
joueur qui se contentait d'esquiver ne terminait jamais le combat. Sur 120
combats simulés, **82 ne se terminaient pas** — un blocage définitif dès le
secteur 2, sans échappatoire sur une calculatrice. Correctif : son point
d'ancrage **descend** d'un pixel toutes les deux images.

**Le boss descend aussi.** Dans le Vide, les dégâts du joueur plafonnent (trois
niveaux maximum par amélioration) alors que la réserve de PV du boss continuait
de grimper : le combat devenait impossible **et interminable**. Maintenant il
avance d'un pixel toutes les dix images — soit tu le tues, soit il t'écrase. Une
partie se termine par une mort, jamais par une impasse.

Ses points de vie s'ajustent aussi à la puissance de feu réellement embarquée :
`30 + secteur × 4 + dps × 7`. Un montant fixe donnerait huit secondes avec un
build complet et deux minutes sans.

## Les améliorations

Huit améliorations, trois niveaux chacune, encodées en huit entiers.

| | | | |
|---|---|---|---|
| Cadence de tir | Dégâts | Canons multiples | Propulseurs |
| Munitions perforantes | Cellule d'overdrive | Blindage | Récupérateur |

Chaque niveau supplémentaire de la même amélioration coûte moitié plus cher, ce
qui pousse à diversifier plutôt qu'à empiler. **Le marchand affiche sous la ligne
sélectionnée ce que fait l'amélioration** et, si elle est trop chère, combien il
manque.

## Équilibrage

`tests/test_balance.py` joue de vraies parties avec un pilote automatique qui
esquive les tirs, prend l'atelier quand il est blessé et vise les ennemis. Ce
pilote a une information parfaite et des réflexes parfaits, mais une stratégie
naïve : un humain sur un clavier de calculatrice fera moins bien.

Réglage actuel : le bot gagne **6 parties sur 8**, atteint le secteur 4,2 en
moyenne, pour 7 minutes de combat. Pour une personne, cela vise un taux de
réussite autour du tiers.

La coop part avec six points de coque supplémentaires : deux vaisseaux, c'est
deux cibles pour une seule barre de vie, et sans cet ajustement la coop était
**plus difficile que le solo** — ce qui ne se voit pas en lisant le code, mais
saute aux yeux en simulant.

## Ce que les 32 Ko ont coûté

La première version tenait dans un seul fichier de 17 Ko et **ne démarrait pas**.
Ramener le jeu dans le budget a demandé de retirer, dans cet ordre de préférence
inverse :

| Retiré | Pourquoi c'était le moins grave |
|---|---|
| Le champ d'étoiles à trois couches | Remplacé par deux couches en ligne, six lignes de code, effet quasi identique |
| Quatre améliorations (déflecteur, rayon tracteur, railgun, nanoréparation) | Chacune demandait sa propre machinerie dans la boucle de combat |
| Les explosions | Joli, mais un pool complet pour un flash de trois images |
| Le ramassage des cristaux | La chasse au butin était bonne ; le pool qui la portait ne rentrait pas. Les cristaux se créditent à la mort |
| Les trois niveaux de difficulté | Un seul réglage, calibré sur le milieu |
| **La carte de secteur dessinée** | Remplacée par un menu de trois routes. C'est la perte la plus nette : le graphe était le point fort visuel. Mais la décision qu'il servait — soigner, acheter ou pousser — est intacte |

Ce qui a été gardé sans compromis : le combat complet (cinq types d'ennemis, un
boss par secteur, tir auto, canons multiples, overdrive), la coop deux joueurs,
le marchand avec ses descriptions, et la progression sans fin.

## Ce qui n'a jamais été retenu

**Un Doom / raycaster.** Techniquement possible, honnêtement injouable : un DDA
en Python pur plus 80 colonnes de `fill_rect` donnent 3 à 6 images par seconde.

**Un système de codes de reprise.** Concevable, mais saisir douze chiffres au
pavé numérique est fastidieux, et une partie de douze minutes n'a pas besoin
d'être reprise.
