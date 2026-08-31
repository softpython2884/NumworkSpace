# Optimisation

Le point n°1 du cahier des charges. Voici ce qui a été fait, pourquoi, et ce que
ça donne mesuré.

## Ce que la machine impose

| Contrainte | Valeur | Conséquence |
|---|---|---|
| Écran | 320×222, module `kandinsky` | `fill_rect`, `set_pixel`, `draw_string`. **Pas de sprite, pas de blit, pas de double tampon** |
| Tas Python | **32 Ko** | Contient le bytecode *et* tous les objets runtime |
| Stockage scripts | **32 Ko** au total | Le jeu doit tenir dedans, avec le reste |
| Interpréteur | MicroPython 1.17 | Accès global = recherche dans un dict ; accès local = index dans un tableau |
| Entrées | `ion.keydown(k)` | Scrutation pure, pas d'événements, pas de répétition auto |
| Fichiers | aucun (`os` absent) | Pas de sauvegarde possible |
| Réseau | aucun | Pas de multi en ligne |

## Les dix techniques

### 1. Rendu par rectangles sales — on n'efface jamais l'écran

C'est la décision qui structure tout le reste. Repeindre l'écran chaque image
coûterait 71 040 pixels. À la place, chaque objet mobile s'efface à sa position
courante puis se redessine à la nouvelle : **2 appels par objet**, quelle que
soit la taille de l'écran.

Mesuré : une image repeint entre **923 et 3 344 pixels**, soit 1,3 % à 4,7 % de
l'écran.

### 2. Effacer tout, puis dessiner tout

Dans l'ordre : effacer chaque entité → mettre à jour → dessiner chaque entité.
Les deux phases ne sont pas fusionnées, parce qu'un objet dessiné avant qu'un
autre ne se soit effacé par-dessus lui produit un scintillement à chaque image.

### 3. Pools compactés, zéro allocation en combat

Projectiles, ennemis, ramassages et explosions vivent dans des pools de taille
fixe alloués une seule fois. Les entités vivantes occupent les slots `0..n-1`, si
bien que les boucles parcourent `range(n)` **sans test « est-elle vivante ? »**.
Une entité qui meurt est remplacée par la dernière et `n` décroît.

Rien n'est alloué ni libéré pendant un combat, donc **le ramasse-miettes ne se
déclenche jamais en pleine image** — c'est le premier tueur de fluidité en
MicroPython.

### 4. Boucles à l'envers

Toutes les boucles de mise à jour descendent, `i = n-1` vers `0`. Conséquence :
l'entité déplacée dans le slot `i` lors d'une suppression vient toujours d'un
slot **déjà traité**. Aucune entité n'est sautée, aucune n'est mise à jour deux
fois. En montant, il faudrait un `continue` qui retraiterait le slot.

### 5. Listes parallèles d'entiers, pas d'objets

`ex[i]` est une indexation. Un attribut de classe est une recherche de dict plus
un en-tête d'objet qu'on ne peut pas se permettre sur 32 Ko. Aucune classe,
aucun dictionnaire, aucune fermeture dans le jeu.

### 6. Liaison locale des fonctions chaudes

```python
fr = fill_rect
for i in range(nb):
    fr(bx[i], by[i], 2, 6, BLK)
```

En MicroPython, lire une globale traverse un dict ; lire une locale indexe un
tableau. Sur une fonction appelée jusqu'à 30 fois par image, ce n'est pas de la
micro-optimisation.

### 7. Entiers uniquement, jamais de trigonométrie

Aucun flottant dans la boucle de jeu. La visée des ennemis remplace un `atan2`
par un décalage :

```python
d = (plx[0] + 7 - cx) >> 5     # -2..2 de dérive horizontale
```

Le générateur aléatoire est un xorshift 16 bits dont toutes les valeurs
intermédiaires restent sous 2¹⁶, pour que MicroPython ne bascule jamais en
entiers longs (ce qui allouerait). Période vérifiée : 65 535, distribution
uniforme.

### 8. HUD redessiné champ par champ, seulement s'il change

`draw_string` repeint une bande de 10×18 pixels **par caractère** : c'est l'appel
le plus cher du jeu. Chaque champ du HUD garde sa dernière valeur affichée et ne
se redessine que si elle a bougé.

### 9. Champ d'étoiles groupé par couche

Trois couches de parallaxe avançant d'un pixel toutes les 1, 2 et 3 images. Une
étoile qui ne bouge pas cette image **ne coûte rien du tout** — d'où le
regroupement par couche plutôt qu'une position sous-pixel par étoile.

Effet de bord utile : les étoiles se redessinent en permanence, donc celles
qu'un vaisseau a effacées en passant se réparent toutes seules.

### 10. Limiteur d'image, jamais de rattrapage

```python
d = tnext - time.monotonic()
if d > 0: time.sleep(d)
else:     tnext = t + FRAME    # en retard : on ne rattrape pas
```

Le jeu tourne à la même vitesse sur tous les modèles. Si une image déborde, on ne
tente pas de rattraper — ça téléporterait les entités les unes à travers les
autres.

## La chaîne de build

`tools/build.py` transforme `src/nova.py` (lisible, commenté) en `dist/nova.py`
(ce qu'on colle dans la machine), en trois passes :

1. **Suppression** des commentaires et docstrings via `tokenize`, par plages de
   texte — jamais par expression régulière, qui ne distingue pas un commentaire
   d'un `#` dans une chaîne.
2. **Renommage** des identifiants, les plus courts pour les plus fréquents.
3. **Réindentation** à un espace par niveau, et compactage des espaces autour des
   opérateurs.

| | Octets |
|---|---:|
| `src/nova.py` | 46 022 |
| `dist/nova.py` | **17 444** |
| Gain | 62 % |
| Part du stockage NumWorks | 53 % |

### Comment on sait que le build est correct

Trois filets, dans cet ordre :

1. **`tools/lint_globals.py`** vérifie qu'aucune locale ni aucun paramètre ne
   masque un nom de module. Le renommage se fait par orthographe, un symbole par
   nom : cette garantie est ce qui le rend légitime. (Le linter a trouvé un vrai
   `UnboundLocalError` et deux paramètres qui masquaient des fonctions.)
2. **Comparaison structurelle** : l'AST avant et après doit être identique aux
   noms près, constantes comprises.
3. **`tests/run_all.py` rejoue toute la suite sur `dist/nova.py`.**

Le troisième filet n'est pas du zèle. Une première version du minifieur laissait
les identifiants d'un caractère intacts tout en réattribuant ces mêmes lettres à
d'autres symboles : deux variables distinctes fusionnaient silencieusement. La
forme de l'AST était **inchangée**, donc la vérification structurelle ne voyait
rien. Seule l'exécution du build a levé l'erreur. Le minifieur renomme désormais
tous les identifiants et vérifie que le renommage est injectif et disjoint des
noms conservés.

## Ce que le clavier a dicté

La matrice 9×6 n'a pas de diode. Trois touches dont deux partagent une ligne et
deux une colonne font apparaître une quatrième touche que personne n'a pressée.

C'est ce qui a fixé le schéma de contrôle : **tir automatique** et déplacement
horizontal seul, soit deux touches par joueur, plus une touche d'overdrive
partagée. `tests/test_controls.py` énumère les 12 combinaisons que deux joueurs
peuvent produire et vérifie qu'aucune ne peut créer de fantôme — le test
contrôle aussi son propre détecteur sur un trio connu comme mauvais.

```
P1 gauche  (0,0)      P2 gauche  (6,0)      overdrive EXE  (8,4)
P1 droite  (0,3)      P2 droite  (6,2)      solo OK        (0,4)
```

`KEY_BACK` n'est volontairement jamais utilisé : Epsilon peut interrompre le
script dessus.
