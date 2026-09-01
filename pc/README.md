# NOVA — édition PC

La version pygame de [NOVA](../README.md). Même jeu, mêmes règles, mais sans les
32 Ko de RAM qui ont forcé la version calculatrice à tout élaguer.

![Combat](../docs/img/pc-03-fight.png)

## Lancer

**Le plus simple** — installe tout et démarre, en une commande :

| | |
|---|---|
| Windows | double-clic sur **`play.cmd`** |
| Linux / macOS | **`./play.sh`** |

Le script trouve Python, crée un environnement isolé dans `pc/.venv`, installe
les dépendances et lance le jeu. Les fois suivantes, il démarre directement.

Il installe **pygame-ce** en priorité — le fork communautaire publie des paquets
pour les nouvelles versions de Python des mois avant pygame classique, ce qui
évite l'erreur de compilation habituelle sur un Python tout frais. Même
`import pygame`, et si pygame-ce n'est pas disponible il retombe sur pygame.

**À la main**, si tu préfères :

```bash
pip install pygame-ce numpy   # ou: pip install pygame numpy
python3 nova.py
```

## Créer un exécutable

| | |
|---|---|
| Windows | **`build_exe.cmd`** → `dist\NOVA.exe` |
| Linux / macOS | **`./build_exe.sh`** → `dist/NOVA` |

Un seul fichier, icône incluse, aucune installation de Python requise pour y
jouer. Il n'y a pas de compilation croisée : un `.exe` Windows doit être
construit sur Windows.

![Icône](assets/nova.png)

| Option | |
|---|---|
| `--scale N` | Force un zoom entier (par défaut : choisi selon l'écran) |
| `--fullscreen` | Démarre en plein écran |
| `--no-crt` | Coupe les scanlines |
| `--no-sound` | Démarre en muet |

En jeu : `F11` plein écran · `F1` filtre CRT · `M` son (3 crans) ·
`+`/`-` taille · la fenêtre est redimensionnable à la souris.

## Résolutions

Le jeu s'adapte à n'importe quelle résolution, **sans bandes noires**. Le zoom
est toujours un **entier** — un pixel de jeu reste un carré net — et le canvas
prend ensuite autant de pixels de jeu qu'il en faut pour remplir l'écran.

| Écran | Zoom | Canvas | Arène |
|---|---|---|---|
| 1920×1080 | ×4 | 480×270 | 480×244 |
| 2560×1440 | ×5 | 512×288 | 480×244 |
| **3440×1440** (21:9) | ×5 | 688×288 | 480×244 |
| 1920×1200 (16:10) | ×4 | 480×300 | 480×244 |
| 1366×768 | ×3 | 455×256 | 455×230 |
| 3840×2160 | ×8 | 480×270 | 480×244 |

**L'arène, elle, ne change pas.** Sur un shmup vertical, la largeur du terrain
*est* un réglage de difficulté : donner 40 % de place en plus à quelqu'un en
ultrawide, c'est lui donner un autre jeu, plus facile. L'arène garde donc une
taille fixe, centrée, et le canvas supplémentaire devient du décor — champ
d'étoiles, rails, et un panneau latéral qui affiche l'équipement du vaisseau.

![Ultrawide](../docs/img/pc-res-ultrawide.png)

*3440×1440. L'arène est cadrée par ses rails, les marges portent le loadout à
gauche et le secteur à droite.*

Sur un écran étroit (1366×768), l'arène se réduit pour tenir, et il n'y a
simplement pas de marges.

## Son

Tout est **synthétisé au démarrage** — ondes carrées, triangles et bruit avec
enveloppes, comme une NES. Aucun fichier audio dans le dépôt : 20 sons —
24 échantillons, le canon en ayant trois — et cinq boucles de musique,
construits en **0,03 seconde**.

À écouter : [`docs/nova-sound-demo.wav`](../docs/nova-sound-demo.wav) — les
20 effets puis un extrait de musique.

| | |
|---|---|
| Armes | tir simple et tir large (3+ canons), chacun en trois hauteurs, tir ennemi |
| Impacts | touche, explosion, explosion de boss |
| Vaisseau | dégât, déflecteur qui encaisse, déflecteur rechargé, bombe |
| Butin | cristal, réparation |
| Interface | navigation, validation, refus, achat, saut |
| Jingles | alerte boss, secteur terminé, fin de partie |

La musique change à chaque secteur : basse triangle et arpège carré, gamme et
tempo propres à chacun, structure tirée de la graine de la partie.

### Le canon

Le tir est automatique : il sonne six à dix fois par seconde, pendant toute la
partie. C'est le seul son du jeu qui se comporte comme une boucle, et deux
choses le rendent fatigant — le volume, et la **répétition à l'identique**.

Les deux sont traitées. Le canon est **14 dB plus discret** qu'avant (0,037×
l'énergie par tir), ce qui le place sous tous les autres effets sauf l'impact,
et il tourne sur **trois hauteurs** : tenir le tir ne rejoue jamais deux fois
le même échantillon.

| Effet | RMS |
|---|---|
| Alerte boss | 0,164 |
| Tir ennemi | 0,042 |
| Explosion | 0,041 |
| **Tir joueur** | **0,016** |

### `M` : trois crans, pas deux

Vouloir couper le canon n'est pas vouloir le silence. `M` fait donc le tour :

    SOUND ON  →  GUNS MUTED  →  SOUND OFF  →  SOUND ON

`GUNS MUTED` ne touche **que** notre propre canon. Le tir ennemi, les impacts
et l'alerte de boss restent : ce sont des informations, pas de la décoration —
les couper rendrait le jeu plus difficile. L'état choisi s'affiche à l'écran,
parce qu'on ne peut pas entendre la différence entre « moins » et « rien ».

Sans numpy, ou sur une machine sans carte son, le jeu démarre en silence
plutôt que de planter.

## Contrôles

| | Joueur 1 | Joueur 2 (coop) |
|---|---|---|
| Se déplacer | flèches **ou** WASD | WASD |
| Tirer | automatique | automatique |
| Bombe | `Espace` ou `Maj` | partagée |
| Menus | flèches + `Entrée` | |

### Manette

Branchée avant ou pendant la partie, ça marche : stick gauche ou croix
directionnelle pour se déplacer, bouton du bas ou gâchette pour la bombe, et la
navigation des menus suit. Les manettes sont attribuées dans l'ordre de
branchement — la première au joueur 1, la seconde au joueur 2.

**Clavier et manette restent actifs en même temps.** En coop, l'un peut tenir
une manette pendant que l'autre joue au clavier, ce qui est la façon dont ces
choses se jouent vraiment sur un canapé.

Contrairement à la calculatrice — dont le clavier matriciel sans diodes
interdisait plus de deux touches — le vaisseau se déplace ici en **8 directions**.
Le tir reste automatique : c'est l'identité du jeu, et ça laisse les deux mains
pour esquiver.

## Ce que la version PC récupère

Tout ce que les 32 Ko avaient coûté :

| | Calculatrice | PC |
|---|---|---|
| Carte de secteur | un menu à 3 routes | **le graphe complet, avec diagonales** |
| Améliorations | 8 | **12** |
| Difficultés | une seule | **3** (Cadet / Pilote / As) |
| Événements | ✗ | **6**, avec choix et conséquences |
| Ramassage de cristaux | crédité à la mort | **butin à ramasser**, aimantable |
| Explosions | ✗ | particules, débris, screen shake |
| Boss | un pattern | **5 boss différents**, un par secteur |
| Étoiles | 2 couches, 12 étoiles | 3 couches, 140 étoiles |

Plus, en propre à cette version : sprites pixel art dessinés (au lieu de trois
rectangles par vaisseau), traînées de réacteur, flash blanc à l'impact,
hit-stop sur les dégâts, filtre CRT optionnel.

| | |
|---|---|
| ![Carte](../docs/img/pc-02-map.png) | ![Boss](../docs/img/pc-04-boss.png) |
| La carte de secteur, enfin dessinée | Boss en phase 2 |
| ![Marchand](../docs/img/pc-05-trader.png) | ![CRT](../docs/img/pc-03-fight-crt.png) |
| Le marchand dit ce qu'il vend | Le filtre CRT, `F1` |

## Le bestiaire

Il grandit jusqu'au bout. Avant, c'était `min(2 + secteur, 5)` : tout était
débloqué dès le secteur 3, donc les secteurs 4 et 5 n'introduisaient plus rien
et le dernier tiers d'une partie n'était que le premier tiers avec des nombres
plus gros.

```
secteur 1  GRUNT, WEAVER      secteur 4  + TANK
secteur 2  + RUSHER           secteur 5  + SPINNER
secteur 3  + TURRET, LANCER   le Vide    + PHANTOM
```

Les trois derniers prennent chacun une mécanique à un boss et la boulonnent sur
quelque chose de mortel. C'est tout l'intérêt : un boss t'apprend une attaque
une fois, puis l'attaque revient sur un vaisseau que tu peux abattre.

![Les ennemis tardifs](../docs/img/pc-foes.png)

| | |
|---|---|
| **LANCER** | Le **rayon** de LANCE. Il vise, charge 0,85 s, tire. Le rayon reste verrouillé là où il visait — et le tuer pendant la charge emporte le rayon avec lui. Une priorité de cible, pas une fatalité. |
| **SPINNER** | Les anneaux de SENTINEL. Le seul ennemi du bestiaire qui ne se soucie pas d'où tu es, ce qui le rend gênant à côté de tous ceux qui te visent. |
| **PHANTOM** | Le Vide seulement. **Dash arrière et latéral**, déclenché par le fait que tu sois aligné dessous — donc se garer en dessous et tenir la gâchette, ce que la cadence de tir du Vide t'a appris à faire, est exactement ce qui échoue. |

La densité aussi : le budget passe de `+10` à `+13` par secteur, plafond de 104
à 150. Mais le vrai frein était ailleurs — un **plafond fixe de 14 ennemis
simultanés**, inchangé depuis le secteur 1. Il monte maintenant avec le secteur,
jusqu'à 20.

## Les boss

Le premier jet PC avait un seul boss reskinné par secteur : le combat censé
être la conclusion d'un secteur était le même combat à chaque fois. Chacun a
maintenant sa propre mécanique.

![Les cinq boss](../docs/img/pc-bosses.png)

| | |
|---|---|
| **SENTINEL** | Éventails, puis des **murs avec un seul trou**, puis une spirale par-dessus. Le boss qui enseigne le vocabulaire des quatre autres. |
| **HIVE MOTHER** | Ouvre ses baies et lâche des escortes, arme les **canons muraux**, et fait pleuvoir depuis le haut. |
| **LANCE** | Un rayon, puis deux, puis un **peigne de quatre** qui balaie l'arène d'un bord à l'autre. La colonne sûre finit toujours par ne plus l'être. |
| **BULWARK** | Un cœur derrière deux **modules destructibles** qui tirent en rafales. Tant qu'un module tient, le cœur ne prend qu'un quart des dégâts — la barre passe au bleu pour le dire. Casse-les et le cœur cesse de se retenir. |
| **WARDEN** | Tout à la fois : canons muraux dès le début, rayons en phase 2, baies ouvertes en phase 3, modules toujours dans le chemin. |

Ils partagent un corps — dérive, points de vie, phases selon la coque restante.
Ce qui change est une seule méthode, `act`, dispatchée une fois par image : le
seul endroit où vit la personnalité d'un boss.

### Dense, mais pas injuste

Aucun de ces motifs n'est aléatoire. Une spirale est la même spirale à chaque
tour, un mur a toujours exactement un trou, un rayon est fixé là où il visait
au début de la charge. C'est la différence entre difficile et injuste : le
motif est fait pour être lu et traversé, pas subi. Trois choses existent
uniquement pour ça — la boîte de collision du vaisseau fait 6×9 dans un sprite
de 13×17, un coup à la coque offre 1,4 seconde d'invulnérabilité, et la bombe
nettoie l'écran.

### Le rythme : tempête, puis fenêtre

Le premier jet de ces boss ne s'arrêtait jamais de tirer. C'était l'erreur.
Sans fenêtre pour riposter, un combat cesse d'être quelque chose qu'on lit et
devient de l'arithmétique : **60 secondes** d'esquive à grignoter le boss entre
deux frôlements. Mesuré.

Ils respirent maintenant. Chaque boss alterne une **tempête** (3 à 4,4 s selon
la phase) et une **fenêtre** (1,7 à 1,1 s) pendant laquelle tout se tait —
boss, modules et canons muraux compris. Quatre coins cyan apparaissent autour
du boss pour la signaler ; un cadre complet voudrait dire « blindé », alors la
fenêtre a sa propre forme.

Le résultat mesuré au moment de ce changement : le combat tombe de 60 à
**45 secondes**, les dégâts encaissés de 7,4 à 4,5 points de coque, et la
tempête peut être bien plus méchante qu'elle n'aurait osé l'être sans la pause.

### Le bouclier d'entrée

Un boss retient son tir le temps de sa carte de présentation. Le joueur, lui,
ne retient rien : un vaisseau garé dessous place tous ses tirs. Mesuré, avant
correction — **5 à 25 % de la coque du boss partaient avant qu'il ait agi**,
25 % avec un vaisseau d'origine au secteur 1, moins avec des canons maxés
seulement parce que les points de vie du boss suivent l'armement apporté.

Des dégâts gratuits contre quelque chose qui ne peut pas répondre, ce n'est pas
une récompense d'habileté, c'est un trou dans les règles. Le boss est donc
intouchable pendant toute cette fenêtre — la constante est de 2 s et le combat
l'élargit à la durée de la carte, parce qu'un bouclier qui expire pendant que le
boss retient encore son tir ne fait que déplacer le trou une seconde plus loin.
Les modules sont couverts aussi, sinon l'astuce se déplaçait simplement sur
BULWARK et WARDEN.

Il se dessine en **cercle**. Le cadre veut déjà dire « modules qui blindent le
cœur » et les coins cyan « en train de venter » : trois états qui changent ce
que font tes tirs, trois formes.

### Des canons sur les murs

Le boss tient le milieu de l'écran. Sans les canons muraux, les bords sont
l'endroit où l'on va pour être tranquille — et un combat avec un coin sûr est
un combat qu'on gagne en s'y asseyant. Ils sont **destructibles**, donc nettoyer
un côté est un vrai choix à faire avec les secondes où l'on ne tire pas sur le
boss, et ils **s'arment visiblement** pendant une seconde avant leur premier
tir : un projectile venu du hors-champ n'est pas un motif, c'est une embuscade.

Chaque combat s'ouvre sur une carte qui nomme le boss et dit ce qu'il fait : un
combat qu'on n'a jamais vu ne devrait pas commencer par une surprise qu'on ne
pouvait pas lire.

## La carte : un choix, pas un couloir

Un secteur est un graphe à embranchements, et pendant un moment il n'en avait
que l'apparence. Le générateur remplissait des **colonnes entières** : la
colonne 4 était toujours un marchand, la colonne 6 toujours un atelier de
réparation. Quelle que soit la route prise, on croisait les deux — et le
dernier nœud avant le boss rendait la coque à neuf. On pouvait jouer un secteur
n'importe comment et affronter le seigneur de guerre à pleine vie de toute
façon. Rien de ce qui arrivait en chemin ne comptait.

Les nœuds spéciaux sont maintenant posés **un par un**, pas par colonne :

| | avant | maintenant |
|---|---|---|
| Ateliers par secteur | 1,87 | **0,54** |
| Secteurs qui en proposent un | 100 % | **54 %** |
| Toutes les routes en croisent un | 100 % | **12 %** |
| Atelier juste avant le boss | 100 % | **0 %** |

Quand les deux sont présents, **le marchand et l'atelier sont dans la même
colonne, sur deux lignes différentes** : on a l'un ou l'autre, et le choix a
réellement été fait une colonne plus tôt, en prenant la ligne qui pouvait
atteindre celui qu'on voulait. Cristaux ou coque.

La dernière colonne avant le boss est toujours une patrouille ou une patrouille
d'élite. Quelle que soit la route, la dernière chose avant le boss coûte
quelque chose.

En échange, un atelier vaut le détour : il rend **45 % de la barre** au lieu
d'un forfait de 5 points, et si la coque est déjà pleine l'équipage revend le
blindage en trop.

### L'attrition, et pourquoi elle n'existait pas

En cherchant pourquoi on arrivait toujours au boss à pleine vie, la mesure a
donné une réponse inattendue : **une patrouille rapportait −0,13 point de
coque**. Négatif. On finissait un combat en meilleur état qu'on ne l'avait
commencé.

Deux fuites, toutes deux invisibles sans compter :

- chaque ennemi tué avait **9 %** de chances de lâcher un correctif de coque.
  À dix-huit morts par combat, cela soignait plus que le combat ne coûtait.
  Ramené à 3 %.
- **NANOREPAIR** soignait à chaque nœud, par niveau. Le Vide n'a pas de fin,
  donc cette réparation non plus : au niveau 3 elle surpassait tout ce que le
  jeu pouvait infliger. Ce n'est pas une amélioration, c'est un interrupteur.
  Elle soigne maintenant une fois par secteur.

### Les difficultés séparent enfin

Autre chose que la mesure a trouvée : la difficulté se réglait surtout par le
**nombre** d'ennemis — or un ennemi est aussi du butin. As envoyait 35 %
d'ennemis en plus, donc 35 % de cristaux en plus, donc un meilleur vaisseau, et
gagnait plus souvent que Cadet. Le curseur se battait contre lui-même.

Resserrer l'écart n'a pas suffi, et il a fallu une deuxième mesure pour le voir :
avec 0,85 d'ennemis, **Cadet mesurait plus dur que Pilote** — 12 victoires
contre 13, des combats de boss plus longs (57,8 s contre 48,0) et plus de dégâts
encaissés (5,4 contre 4,8), tout en tirant moins vite. Moins d'ennemis, moins de
cristaux, un moins bon vaisseau, un combat plus long.

Les trois niveaux envoient maintenant **exactement le même nombre d'ennemis** et
se séparent sur la **cadence de tir** — qui ne rend rien au joueur — et sur la
profondeur de la barre de coque, qui est volontairement large : un boss capable
de prendre un tiers de la coque en une erreur a besoin d'une coque avec laquelle
on peut se permettre des erreurs. Sinon « difficile » veut seulement dire « le
premier coup termine la partie », ce qui n'est pas de la difficulté, c'est de la
fragilité.

## Structure

```
pc/
  nova.py            point d'entrée
  nova/
    data.py          palette, sprites (en texte), tables, événements
    art.py           construit les surfaces, teinte les ennemis par secteur
    entities.py      vaisseaux, tirs, butin — tout en pixels par seconde
    combat.py        la scène de combat
    fx.py            particules, shake, flash, étoiles, overlay CRT
    audio.py         synthèse chiptune : ondes, enveloppes, catalogue, musique
    boss.py          les cinq boss, leurs rayons et leurs modules
    gamepad.py       manettes : sticks, croix, boutons, branchement à chaud
    sector.py        génération et rendu de la carte
    run.py           l'état d'une partie
    ui.py            menus, panneaux, HUD
    game.py          machine à états et boucle principale
  assets/nova.ico    icône de l'exécutable (générée)
  play.sh play.cmd   installe et lance
  build_exe.sh/.cmd  construit l'exécutable
  nova.spec          recette PyInstaller
  tests/             suite headless
  tools/shots.py     rend les captures d'écran
  tools/balance.py   mesure la carte, le bestiaire et les combats
  tools/shots_foes.py captures des ennemis tardifs
  tools/make_icon.py dessine l'icône
```

## Tests

Tout tourne sans écran (`SDL_VIDEODRIVER=dummy`), donc en intégration continue :

```bash
python3 tests/run_all.py     # runs complets + budget d'image
python3 tools/balance.py     # carte et difficulté, chiffrées
python3 tools/shots.py       # régénère les captures
```

`test_run.py` joue de vraies parties à travers la vraie machine à états — mêmes
événements clavier, mêmes combats, rien n'est simulé sauf l'écran. Il valide
aussi qu'aucun écran ne peut mener à une impasse.

`test_gamepad.py` pilote la vraie logique de manette avec un faux périphérique :
axes, croix, boutons, transitions de menu, débranchement. Aucune manette ne peut
être branchée en CI, et un mapping testé uniquement à la main est un mapping qui
casse en silence — celui-ci a d'ailleurs trouvé un vrai conflit, le bouton Est
étant à la fois « valider » et « annuler ».

`test_audio.py` attrape un piège discret : un nom d'effet mal orthographié est
**silencieux, pas une erreur** — `play("expode")` ne fait rien, pour toujours,
et personne ne le remarque. Le test enregistre chaque son demandé pendant une
partie et exige que les deux ensembles coïncident dans les deux sens ; un effet
construit mais jamais déclenché est aussi une anomalie. Les sons rares
(réparation, déflecteur, refus d'achat, fin de partie) sont provoqués
explicitement, sinon le résultat dépendrait de la graine. Les noms de canon
étant des alias — `play("shoot")` atteint l'une des trois variantes — la
comparaison passe par `audio.gun_variants`, ce qui vérifie du même coup que la
rotation les atteint **toutes**.

Le même test exerce les trois crans de `M` : que `GUNS MUTED` fasse taire le
canon, qu'il ne fasse taire *que* lui, et que `SOUND OFF` fasse taire le reste.
Il vérifie aussi que deux tirs sur la même image ne donnent qu'un son — le
cas de la coop, et le piège des variantes : si l'anti-répétition est indexée
sur la variante choisie plutôt que sur le nom demandé, deux joueurs qui tirent
ensemble tombent sur deux variantes différentes et le canon double de volume
exactement là où il est déjà le plus présent. Les trois régressions (un cran
qui ne coupe rien, une rotation qui saute une variante, l'anti-répétition mal
indexée) ont été introduites volontairement pour vérifier que le test les voit.

### Une graine ne reproduisait rien

Le pire défaut trouvé pendant cette passe ne faisait planter personne. La même
graine, lancée trois fois de suite : **gagnée, perdue au secteur 4, perdue au
secteur 5**.

Les motifs de boss et le comportement des ennemis tiraient leur hasard du
`random` du module, pas du générateur de la partie. Rien ne plantait, aucun test
ne tombait — le jeu n'était simplement pas reproductible. Ce qui veut dire que
le banc d'équilibrage rapportait du bruit d'un lancement à l'autre comme si
c'était l'effet d'un changement, et qu'une graine dans un rapport de bug ne
reproduisait rien du tout.

Tout ce qui décide de l'issue d'un combat passe maintenant par le RNG de la
partie : dérive du boss, phase des spirales, trou des murs, pluie, ordre des
peignes de rayons, côté des canons muraux, décalage des modules, position et
cadence des ennemis, dispersion du butin. Les particules, le shake et le champ
d'étoiles restent volontairement sur le générateur global : ils ne peuvent
changer aucune issue.

`test_determinism.py` prend l'empreinte d'une patrouille et des cinq boss, joués
deux fois depuis la même graine avec la même séquence d'entrées, en **perturbant
volontairement le générateur global entre les deux** pour qu'un tirage qui fuit
ne puisse pas retomber juste par hasard. Sa première version passait alors que
le bug était réintroduit exprès : elle ne suivait que le boss du secteur 2, et
HIVE MOTHER n'a pas de murs. En suivant les cinq, le même bug fait tomber
SENTINEL, BULWARK et WARDEN.

Son garde-fou — une graine différente doit changer l'empreinte — a lui aussi dû
être assoupli. L'ouverture de LANCE ne tire qu'un seul dé, le sens de sa dérive,
donc quatre graines d'affilée peuvent légitimement donner le même combat. Exiger
qu'une graine précise diffère testait la graine, pas le jeu.

### Le pilote automatique est un instrument, et il a fallu le réparer

La première version était un champ de répulsion : additionner un vecteur qui
s'éloigne de chaque projectile proche, et suivre la somme. Ça marche contre du
tir visé et échoue complètement contre tout ce dont un motif de bullet hell est
fait. Un mur avec un trou le pousse **le long** du mur au lieu de le pousser
dans le trou ; une spirale l'entoure, les vecteurs s'annulent, il s'arrête et
meurt.

Mesurer la difficulté des boss avec ce pilote-là, c'était mesurer à quel point
un motif est illisible pour une mauvaise heuristique — et la première chose
qu'il aurait conseillée, c'est de supprimer les bonnes attaques.

Il esquive maintenant comme une personne : pour chacune des neuf directions du
stick, calculer à quelle distance passerait le projectile le plus menaçant, et
prendre la meilleure. Le point d'approche est calculé proprement, position
relative contre vitesse relative, parce qu'un projectile proche mais qui
s'éloigne n'est pas une menace et qu'un projectile lointain qui converge en est
une.

Validation : sur le jeu **inchangé**, l'ancien pilote faisait 7/4/1 et le
nouveau fait **7/6/5**. Il n'est jamais moins bon, et il est beaucoup plus fort
là où l'ancien perdait contre des motifs qu'il ne savait tout simplement pas
lire. Ce qui veut dire au passage que l'ancien équilibrage mesurait en partie
l'incompétence du robot.

Il a une information parfaite, des réflexes parfaits, et **aucune mémoire** :
il n'apprend jamais qu'un motif se répète. Un bon humain est moins bon sur le
premier point et bien meilleur sur le second, ce qui est à peu près la bonne
erreur à avoir quand les chiffres servent à régler la difficulté.

Mesures actuelles :

Toutes sur 24 graines, sur une version où une graine **reproduit** vraiment une
partie (voir plus bas — pendant un moment ce n'était pas le cas, et les chiffres
publiés mesuraient du bruit) :

| | |
|---|---|
| Taux de victoire (bot) | Cadet 18/24 · **Pilote 12/24** · As 3/24 |
| Coque à l'entrée du boss | **75 %** de la barre (89 % avant) |
| Dégâts pris par boss | **3,6** points de coque (0,6 avant) |
| Combats de boss sans une égratignure | **17 %** (57 % avant) |
| Durée d'un combat de boss | **45 s** (30 s avant) |
| Durée d'une partie gagnée | 13 à 16 min de combat |
| Coût d'une image (p99) | **1,76 ms** sur un budget de 16,7 ms |
| Pire cas mesuré | WARDEN phase 3 en coop, **305 entités** à l'écran |
| Construction des sons | 24 échantillons en **0,03 s** au démarrage |

L'échelle est monotone — 75 %, 50 %, 13 % — et elle ne l'a été qu'à partir du
moment où les secteurs tardifs ont eu de quoi remplir l'écran. Avant, Cadet et
Pilote finissaient à égalité (13 contre 14) : ce que Cadet donne, c'est surtout
de la coque en plus, et un pilote qui se fait peu toucher ne la dépense jamais.
Des combats plus denses lui donnent enfin quelque chose à en faire.

**La coque à l'entrée du boss est passée de 89 % à 75 %**, et c'est le chiffre
qui répond vraiment à « on arrive toujours au boss à pleine vie ». Rendre les
ateliers rares n'y suffisait pas : encore fallait-il que le chemin coûte quelque
chose.

Et boss par boss, au niveau Pilote — c'est le tableau qui a servi à régler la
difficulté, parce qu'une moyenne sur cinq boss cache exactement ce qu'on veut
savoir : est-ce que le *premier* boss rencontré est un combat ou une formalité ?

| Boss | Dégâts pris | Durée | Sans une égratignure |
|---|---:|---:|---:|
| S1 SENTINEL | 2,2 | 31 s | 12 % |
| S2 HIVE MOTHER | 3,3 | 56 s | 33 % |
| S3 LANCE | 3,5 | 44 s | 5 % |
| S4 BULWARK | 3,9 | 47 s | 24 % |
| S5 WARDEN | 6,1 | 49 s | 7 % |

2,2 → 3,3 → 3,5 → 3,9 → 6,1 : une rampe propre, ce qu'aucune des passes
précédentes n'avait obtenu.

HIVE MOTHER, le boss du secteur 2, mesurait **1,0 point de dégâts et la moitié
de ses combats sans une égratignure** avant cette passe — de loin le plus faible
des cinq, sur le boss que la plupart des gens rencontrent en deuxième.

## Licence

MIT, comme le reste du dépôt.
