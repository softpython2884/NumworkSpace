# Optimisation

Le point n°1 du cahier des charges. Voici ce qui a été fait, pourquoi, et ce que
ça donne mesuré.

## La leçon principale : compter les octets ne sert à rien

La première version faisait **17 444 octets** dans un seul fichier, soit 53 % du
stockage de la NumWorks. Elle semblait confortable. Elle a donné un
`MemoryError` au lancement.

La raison : les 32 Ko de tas Python ne contiennent pas le *fichier*, ils
contiennent le bytecode compilé, tous les objets du runtime, **et l'arbre
syntaxique complet du module pendant sa compilation**. MicroPython parse un
module d'un seul bloc, et cet arbre pèse plusieurs fois la taille de la source.

Mesuré sur le vrai interpréteur (`tools/memcheck.py`) :

| Version | Octets livrés | Tas nécessaire | Verdict |
|---|---:|---:|---|
| 1 fichier | 17 444 | **159 Ko** | `MemoryError` |
| 5 modules équilibrés | 11 500 | **47 Ko** | passe |

Le passage de 159 à 47 Ko ne vient qu'à 34 % de la réduction de code. Le reste
vient de la **découpe** et de l'**ordre de chargement**.

## Comment mesurer, plutôt que deviner

`tools/mp/build.sh` compile MicroPython 1.17 — exactement la version qu'embarque
Epsilon. `tools/memcheck.py` fait tourner le jeu dessus et cherche par
dichotomie le plus petit tas capable de le charger.

C'est l'outil qui manquait la première fois. Il est désormais dans le dépôt, et
c'est lui qui a la dernière parole, pas la taille des fichiers.

Il a aussi fallu qu'il tourne. Le port unix de MicroPython 1.17 réclame par
défaut deux sous-modules git — axtls pour `ussl`, berkeley-db pour `btree` — que
`git clone --depth 1` ne rapporte pas : en local le tas de travail les avait,
en CI le build échouait dès la première seconde, et la mesure était sautée sans
que personne le remarque. Epsilon n'embarque ni l'un ni l'autre, alors le build
les désactive : la compilation passe de « à réparer à la main » à quinze
secondes, et la mesure tourne à chaque commit.

Et une fois qu'elle a tourné, elle a annoncé **50 Ko** là où la même commande
en annonçait 47 sur cette machine. Le jeu n'y était pour rien : la sonde
insérait le dossier de travail dans `sys.path`, en absolu. Sur un runner GitHub
ce chemin est plus long ; quelques centaines d'octets de plus au départ, une
allocation de l'analyseur qui franchit une frontière de bloc, et le minimum
mesuré saute de 3 Ko. Un banc de mesure dont la réponse dépend de l'endroit où
le dépôt est cloné ne mesure pas le programme. La sonde tourne désormais avec
le dossier de travail pour répertoire courant — `sys.path` de MicroPython
commence déjà par `''` — et ne manipule plus aucun chemin : 47 Ko, quelle que
soit la profondeur du clone.

Le build local est en 64 bits, donc ses pointeurs sont deux fois plus larges que
ceux du ARM 32 bits de la calculatrice ; l'arbre syntaxique, qui est presque
entièrement fait de pointeurs, coûte environ 1,6 fois plus ici. Le budget de
48 Ko utilisé par `memcheck` tient compte de cet écart et garde de la marge.

## Ce qui fait vraiment le pic

Trois découvertes, toutes contre-intuitives, toutes mesurées :

**1. C'est le plus gros module qui compte, pas le total.** Le pic vaut à peu
près `résident déjà chargé + 12 × taille du module en cours`. Découper un jeu de
11 Ko en modules de 2 à 3 Ko divise le pic par trois sans retirer une ligne.

**2. Le module racine est compilé en premier, avec un tas vide.** C'est donc lui
qui peut être le plus gros. Chaque module chargé ensuite dispose de moins de
place que le précédent, donc les tailles doivent décroître dans l'ordre de
chargement. Déplacer une seule fonction (`paint`) vers la racine a fait tomber
le pic de 50 à 46 Ko.

**3. `from X import *` coûte cher.** Il recopie tous les noms publics du module
source dans le dict de globals de l'importateur. Sur cinq modules, cela faisait
plusieurs centaines d'entrées inutiles. `tools/fiximports.py` calcule, module par
module, les noms réellement utilisés et réécrit les imports en liste explicite :
**5,5 Ko de tas récupérés**, sans toucher au jeu.

Une quatrième piste s'est révélée fausse et mérite d'être notée : la profondeur
d'imbrication semblait exploser le coût. Aplatir les fonctions les plus
imbriquées (14 niveaux → 8) n'a rien changé. C'est bien la taille du module qui
domine.

## Les techniques de rendu

### Rectangles sales — on n'efface jamais l'écran

Repeindre l'écran chaque image coûterait 71 040 pixels. À la place, chaque objet
mobile s'efface à sa position courante puis se redessine : **2 appels par objet**.

Mesuré : une image repeint entre **902 et 2 966 pixels**, soit 1,3 % à 4,2 %.

### Effacer tout, puis dessiner tout, et dans cet ordre

`paint(acc, frame, bl)` fait les deux passes avec le même code : `bl=1` efface,
`bl=0` dessine. Les deux ne sont pas fusionnées, parce qu'un objet dessiné avant
qu'un autre ne se soit effacé par-dessus lui produit un scintillement.

Cette passe d'effacement doit aussi tourner **avant** la lecture du clavier. Une
régression l'avait placée après : le vaisseau s'effaçait à sa nouvelle position
et laissait l'ancienne peinte, traçant une barre continue à l'écran. Aucun test
de performance ne l'a vue — seule une capture d'écran l'a révélée.

### Pools compactés, zéro allocation en combat

Projectiles, ennemis et tirs vivent dans des listes plates de taille fixe :
l'entité `i` occupe `[i*w, i*w+w)`. Les vivantes occupent les slots `0..n-1`, si
bien que les boucles parcourent `range(n)` **sans test « est-elle vivante ? »**,
et supprimer une entité est **une seule affectation de tranche** au lieu de six.

Rien n'est alloué ni libéré pendant un combat : **le ramasse-miettes ne se
déclenche jamais en pleine image**.

### Boucles à l'envers

Toutes les boucles de mise à jour descendent. L'entité déplacée lors d'une
suppression vient donc toujours d'un slot **déjà traité** : aucune n'est sautée,
aucune n'est traitée deux fois.

### Le reste

- **Listes plates d'entiers**, jamais d'objets : `E[o+1]` est une indexation, un
  attribut de classe est une recherche de dict.
- **Liaison locale** des fonctions chaudes (`fr = fill_rect`) : lire une globale
  traverse un dict, lire une locale indexe un tableau.
- **Entiers uniquement** : la visée ennemie remplace un `atan2` par
  `(PX[0] + 7 - cx) >> 5`.
- **Xorshift 16 bits** dont toutes les valeurs restent sous 2¹⁶, pour que
  MicroPython ne bascule jamais en entiers longs (ce qui allouerait). Période
  vérifiée : 65 535, distribution uniforme.
- **Tables en `bytes`** : un tuple de six entiers, c'est six pointeurs plus un
  en-tête ; une chaîne de six octets, c'est six octets.
- **HUD champ par champ**, redessiné seulement quand la valeur change :
  `draw_string` repeint une bande de 10×18 pixels **par caractère**.
- **Limiteur d'image sans rattrapage** : si une image déborde, on ne tente pas de
  rattraper — ça téléporterait les entités les unes à travers les autres.

Résultat : **92 appels de dessin** au pire cas mesuré, contre un budget de ~240.

## La chaîne de build

`tools/build.py` transforme `src/` (lisible, commenté) en `dist/` : suppression
des commentaires et docstrings par plages de texte via `tokenize`, renommage des
identifiants (les plus courts aux plus fréquents, **de façon cohérente entre
modules**), réindentation à un espace.

| | Octets |
|---|---:|
| `src/` | 25 012 |
| `dist/` | **11 500** |
| Gain | 54 % |

### Comment on sait que le build est correct

1. **`tools/lint_globals.py`** vérifie qu'aucune locale ni aucun paramètre ne
   masque un nom de module — c'est ce qui rend le renommage par orthographe
   légitime. Il a trouvé un vrai `UnboundLocalError` et deux paramètres qui
   masquaient des fonctions.
2. **`tools/fiximports.py`** refuse un module qui utilise un nom défini **plus
   tard** dans la chaîne : Python ne s'en plaindrait qu'à l'exécution de la
   ligne, potentiellement en pleine partie.
3. **Comparaison structurelle** : l'AST avant et après minification doit être
   identique aux noms près, constantes comprises.
4. **`tests/run_all.py` rejoue toute la suite sur `dist/`.**

Le quatrième filet n'est pas du zèle. Une version du minifieur laissait les
identifiants d'un caractère intacts tout en réattribuant ces mêmes lettres à
d'autres symboles : deux variables distinctes fusionnaient silencieusement. La
forme de l'AST était **inchangée**, donc la vérification structurelle ne voyait
rien. Seule l'exécution du build a levé l'erreur.

## Ce que le clavier a dicté

La matrice 9×6 n'a pas de diode. Trois touches dont deux partagent une ligne et
deux une colonne font apparaître une quatrième touche que personne n'a pressée.

D'où le **tir automatique** et le déplacement horizontal seul : deux touches par
joueur, plus une touche d'overdrive partagée.
`tests/test_controls.py` énumère les 12 combinaisons que deux joueurs peuvent
produire et vérifie qu'aucune ne peut ghoster — le test contrôle aussi son
propre détecteur sur un trio connu comme mauvais.

```
P1 gauche  (0,0)      P2 gauche  (6,0)      overdrive EXE  (8,4)
P1 droite  (0,3)      P2 droite  (6,2)      solo OK        (0,4)
```
