**NOVA** — un rogue-lite spatial qui tourne sur une calculatrice NumWorks *et*
sur PC. Même jeu, deux éditions : 32 Ko de tas MicroPython d'un côté, pygame de
l'autre.

## Télécharger

| | |
|---|---|
| **`NOVA-windows.exe`** | Windows, un seul fichier. Double-clic, rien à installer. |
| **`NOVA-linux`** | Linux, un seul fichier. `chmod +x NOVA-linux && ./NOVA-linux` |
| **`nova-numworks.zip`** | L'édition calculatrice : les cinq fichiers à coller dans [workshop.numworks.com](https://workshop.numworks.com), plus les instructions. |

Depuis les sources : `pc/play.sh` (ou `pc/play.cmd`) installe et lance tout seul.

## Ce qu'apporte la 1.1

### Les boss sont devenus des combats

Cinq boss, cinq mécaniques, et un vocabulaire commun : **murs à un seul trou**,
spirales tournantes, **peignes de rayons** qui balaient l'arène, pluie, et des
**canons destructibles sur les murs** — parce qu'un combat avec un coin sûr est
un combat qu'on gagne en s'y asseyant.

Rien n'est aléatoire : même spirale à chaque tour, toujours exactement un trou,
rayon fixé là où il visait au début de la charge. Dense, mais fait pour être lu.

Et surtout, ils **respirent** : une tempête de 3 à 4,4 s, puis une fenêtre où
tout se tait, signalée par quatre coins cyan. Sans cette pause le combat n'était
pas plus dur, juste plus long — 60 secondes d'esquive à grignoter le boss entre
deux frôlements.

| | avant | 1.1 |
|---|---|---|
| Dégâts pris par boss | 0,6 | **5,4** |
| Combats finis sans une égratignure | 57 % | **15 %** |

Un boss est aussi **intouchable pendant sa carte de présentation**. Il retenait
son tir ; le joueur non, et 5 à 25 % de sa coque partaient avant qu'il ait le
droit de répondre.

### La carte est enfin un choix

Les nœuds spéciaux étaient posés par colonne entière : toutes les routes
croisaient le marchand *et* l'atelier, et le dernier nœud avant le boss rendait
la coque à neuf. Un atelier n'apparaît plus que dans **54 % des secteurs**, sur
une seule branche, **jamais avant le boss** — et quand marchand et atelier sont
tous les deux là, ils sont dans la même colonne : cristaux **ou** coque.

### Le son

Le tir est automatique, donc il sonne pendant toute la partie. Il est
**14 dB plus discret** et tourne sur trois hauteurs, pour ne jamais rejouer deux
fois le même échantillon. `M` fait le tour de trois réglages — tout, **canon
coupé**, silence — parce que vouloir se passer du canon n'est pas vouloir se
passer du son.

### Le reste

- **Toutes les résolutions horizontales**, sans bandes noires : 1080p,
  3440×1440, 1366×768. Zoom toujours entier, arène de taille fixe.
- **Manettes** : sticks, croix, branchement à chaud, deux manettes en coop,
  clavier et manette actifs en même temps.
- **Scripts d'installation** `.sh` / `.cmd` qui installent pygame-ce et lancent.
- Musique chiptune synthétisée au démarrage, une boucle par secteur. Aucun
  fichier audio dans le dépôt.
- **Une graine reproduit une partie.** Elle ne le faisait pas : la même graine
  gagnait puis perdait deux fois, et tous les chiffres d'équilibrage mesuraient
  du bruit.

## Difficulté mesurée

Sur 24 graines, avec un pilote automatique à réaction parfaite et sans mémoire
des motifs — un humain est l'inverse :

| | Cadet | Pilote | As |
|---|---|---|---|
| Parties gagnées | 13/24 | 14/24 | 6/24 |

Cadet et Pilote sont à égalité pour ce pilote-là, et c'est la limite de la
mesure plutôt qu'un défaut du jeu : ce que Cadet offre, c'est surtout de la
coque en plus, et un robot qui se fait très peu toucher ne la dépense jamais.
Un humain la sentira.

Détail par boss, banc de mesure et raisonnement complet dans
[`pc/README.md`](../pc/README.md).

## Licence

MIT.
