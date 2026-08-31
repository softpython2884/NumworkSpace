# Game design

## L'objectif

Un jeu qu'on lance quand on a une heure devant soi, qui ne lasse pas.

Une heure, ce n'est pas *une partie d'une heure*. C'est une **session** d'une
heure : quatre ou cinq parties de douze à quinze minutes qui s'enchaînent, chacune
différente de la précédente. C'est le modèle rogue-lite, et il convient
particulièrement à une calculatrice — on joue par à-coups, on peut s'arrêter
entre deux nœuds.

Mesuré sur des parties simulées : **7,5 minutes de combat pur** par partie, soit
douze à quinze minutes une fois comptés la carte, le marchand et les événements.

## Ce que le matériel a décidé à notre place

Trois contraintes ont façonné le design bien plus que mes préférences.

**Pas de communication entre calculatrices.** Aucune API réseau en Python sur
Epsilon. Le multi ne peut donc être que local. D'où la **coop en écran partagé**
sur le même clavier — et les **graines** : ton adversaire entre le même code et
affronte exactement les mêmes vagues, vous comparez les scores. C'est du versus
compétitif sur une machine sans radio.

**Pas de système de fichiers.** Aucune sauvegarde possible. C'est pourquoi la
progression tient dans une seule partie et que la rejouabilité vient de la
variété des builds, pas d'un déblocage persistant.

**Un clavier sans anti-ghosting.** Le tir automatique et le déplacement
horizontal ne sont pas un choix esthétique : à trois touches simultanées, la
matrice invente des appuis. Deux touches par joueur, c'est la limite sûre. Le
bénéfice inattendu : le jeu se joue d'une main, et c'est bien plus agréable sur
un clavier de calculatrice que n'importe quel schéma à quatre directions.

## La boucle

```
                    ┌──────────────────────────┐
                    │      CARTE DE SECTEUR    │
                    │   tu choisis ta route    │
                    └────────────┬─────────────┘
                                 │
       ┌──────────┬──────────────┼──────────┬──────────────┐
       ▼          ▼              ▼          ▼              ▼
   PATROUILLE   ÉLITE        ÉVÉNEMENT   MARCHAND      ATELIER
   cristaux   amélioration   choix       achats        +4 coque
       │        gratuite     à 2 options   │              │
       └──────────┴──────────────┴──────────┴──────────────┘
                                 │
                                 ▼
                            BOSS de secteur
                                 │
                     ┌───────────┴───────────┐
                     ▼                       ▼
              secteur suivant          après le 5ᵉ : LE VIDE
                                       (sans fin, pour le score)
```

## La carte de secteur

Huit colonnes, trois lignes, générée en avant depuis le nœud d'entrée : chaque
nœud placé est **atteignable par construction**, sans passe de connectivité.

Le rythme est garanti sur toutes les routes :

| Colonne | 0 | 1 | 2 | 3 | **4** | 5 | **6** | 7 |
|---|---|---|---|---|---|---|---|---|
| Contenu | entrée | combat | libre | libre | **marchand** | libre | **atelier** | **boss** |

Cette règle est née d'une mesure, pas d'une intuition. Les premières simulations
mouraient toutes au secteur 1 ; le journal a montré que certaines routes
atteignaient le boss **sans avoir croisé un seul marchand**, donc sans une seule
amélioration. Forcer une colonne entière de marchands et une d'ateliers a fait
passer le taux de victoire de 12 % à 50 % sans toucher à un seul chiffre de
difficulté.

`tests/test_map.py` génère 400 cartes et vérifie qu'aucune route n'échappe à
cette règle, qu'aucun nœud n'est orphelin, et que la largeur moyenne atteignable
reste autour de 1,5 ligne sur 3 — assez pour que le choix de route en soit un.

## Les ennemis

| Type | Comportement | PV | Points |
|---|---|---:|---:|
| **Grunt** | descend droit, tire rarement | 1 | 10 |
| **Weaver** | zigzag, rebondit sur les bords, ne tire pas | 1 | 15 |
| **Turret** | s'ancre en haut et bombarde | 3 | 25 |
| **Rusher** | plonge vite, ne tire pas | 1 | 20 |
| **Tank** | lent, salves de deux, encaisse | 6 | 40 |
| **Boss** | balaie l'écran, salves de trois, **descend** | ∝ | 500 |

Les types se débloquent au fil des secteurs : le premier n'oppose que des grunts
et des weavers.

### Deux ennemis ont été redessinés par les tests

**La tourelle bloquait le jeu.** Elle s'ancrait et campait indéfiniment ; un
joueur qui se contentait d'esquiver ne terminait jamais le combat. Sur 120
combats simulés, **82 ne se terminaient pas**. Sur une calculatrice il n'y a pas
d'échappatoire : c'était un blocage définitif dès le secteur 2. Correctif : son
point d'ancrage **descend** d'un pixel toutes les deux images. Elle a toujours le
temps de te bombarder, mais elle finit toujours par te tomber dessus ou sortir
par le bas.

**Le boss descend aussi.** Même raison, poussée plus loin : dans le Vide, les
dégâts du joueur plafonnent (trois niveaux maximum par amélioration) alors que la
réserve de PV du boss, elle, continuait de grimper. Passé un certain seuil, le
combat devenait impossible **et interminable**. Maintenant le boss avance d'un
pixel toutes les dix images : soit tu le tues, soit il t'écrase. Une partie se
termine par une mort, jamais par une impasse.

## Les améliorations

Douze améliorations, trois niveaux chacune, toutes encodées en douze entiers —
ce qui rend un build à la fois rapide à appliquer et minuscule en mémoire.

| | | | |
|---|---|---|---|
| Cadence de tir | Dégâts | Canons multiples | Propulseurs |
| Vitesse des tirs | Munitions perforantes | Déflecteur | Rayon tracteur |
| Cellule d'overdrive | Blindage | Récupérateur | Nanoréparation |

Chaque niveau supplémentaire de la même amélioration coûte moitié plus cher, ce
qui pousse à diversifier plutôt qu'à empiler.

## Difficulté

Trois réglages, qui ne sont pas trois chemins de code mais **trois nombres** :
coque de départ, pourcentage appliqué au budget de menace, et accélération du tir
ennemi.

| | Coque | Menace | Tir ennemi | Taux de victoire simulé |
|---|---:|---:|---:|---:|
| **Cadet** | 14 | 68 % | — | 90 % |
| **Pilote** | 10 | 112 % | +4 | 50 % |
| **As** | 7 | 160 % | +9 | 30 % |

Ces taux viennent de `tests/test_balance.py`, qui joue de vraies parties avec un
pilote automatique qui esquive les tirs, ramasse les cristaux et vise les
ennemis. Ce pilote a une information parfaite et des réflexes parfaits, mais une
stratégie naïve : un humain sur un clavier de calculatrice fera moins bien.
Pilote à 50 % pour le robot, c'est un vrai défi pour une personne.

Le budget de menace est **plafonné**. Sans plafond, le Vide rendait les vagues
plus *longues* au lieu de plus *dures* — un combat de trois minutes est épuisant,
pas excitant. Passé le plafond, la difficulté monte par les points de vie et la
cadence de tir.

## Coop

Deux vaisseaux, une coque, un score. Le vaisseau 1 est cyan, le 2 est violet.

La première version était **plus difficile que le solo** : deux vaisseaux, c'est
deux cibles pour une seule barre de vie, et la puissance de feu doublée
raccourcit les combats sans réduire les dégâts encaissés. La coop part donc avec
six points de coque supplémentaires. C'est le genre de chose qu'on ne voit pas en
lisant le code et qui saute aux yeux en simulant.

## Ce qui n'a pas été retenu

**Un Doom / raycaster.** Techniquement possible, honnêtement non jouable : un DDA
en Python pur plus 80 colonnes de `fill_rect` donnent 3 à 6 images par seconde.
Une démo qui impressionne cinq minutes, pas un jeu où l'on passe une heure.

**Un système de codes de reprise** (mot de passe façon Game Boy pour reprendre
une partie). Concevable — 12 chiffres suffiraient à encoder secteur, coque,
cristaux et build — mais saisir douze chiffres au pavé numérique est fastidieux,
et une partie de douze minutes n'a pas vraiment besoin d'être reprise. Le
stockage libre est là si l'envie revient : le build n'occupe que 53 % du budget.
