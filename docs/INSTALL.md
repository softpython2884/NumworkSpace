# Installation

## Sur une vraie NumWorks

Le jeu est en **cinq scripts**. MicroPython compile un module d'un seul bloc et
garde tout son arbre syntaxique en mémoire : c'est le plus gros module qui fixe
le pic, pas le total. D'un seul tenant, le jeu déclenche `MemoryError` avant même
de démarrer.

1. Ouvre <https://my.numworks.com/python> et connecte-toi.
2. Crée ces cinq scripts, en collant le contenu du fichier correspondant :

   | Script à créer | Contenu |
   |---|---|
   | `novad.py` | `dist/novad.py` |
   | `novae.py` | `dist/novae.py` |
   | `novaf.py` | `dist/novaf.py` |
   | `novag.py` | `dist/novag.py` |
   | `nova.py` | `dist/nova.py` |

   ⚠️ Prends bien `dist/`, pas `src/` : la source lisible fait 25 Ko et ne rentre
   pas.
   ⚠️ Les noms doivent être exacts — les scripts s'importent entre eux.
3. Branche la calculatrice en USB, envoie les scripts.
4. Sur la calculatrice : **Python** → **`nova`** → `EXE`.

Seul `nova` se lance ; les quatre autres se chargent tout seuls.

## Vérifier que ça rentre

Compter les octets ne suffit pas : les 32 Ko de tas contiennent le bytecode, les
objets, **et l'arbre syntaxique du module en cours de compilation**. Le dépôt
mesure donc pour de vrai, sur le vrai interpréteur :

```bash
tools/mp/build.sh          # compile MicroPython 1.17, une fois (~15 s)
python3 tools/memcheck.py  # cherche le plus petit tas qui charge le jeu
```

```
minimum heap: 47K   (budget 48K sur ce build 64 bits, device 32K)
```

Le build local est en 64 bits, donc ses pointeurs sont deux fois plus larges que
ceux du ARM de la calculatrice ; le budget de 48 Ko tient compte de cet écart.

## Dépannage

**« MemoryError au lancement »**
Le tas fait 32 Ko et contient le bytecode *plus* les objets. Supprime les autres
scripts de la calculatrice et relance. Vérifie surtout que tu as bien collé les
**cinq** scripts séparément, et pas tout dans un seul fichier.

**« ImportError: no module named novad »**
Un des scripts manque ou est mal nommé. Les cinq noms doivent être exacts.

**« Ça rame »**
Le jeu est plafonné à 25 images par seconde et ne tente jamais de rattraper son
retard : sur une machine plus lente il ralentit proprement au lieu de saccader.

**« La touche RETOUR quitte le jeu »**
C'est voulu — `KEY_BACK` n'est jamais lue, parce qu'Epsilon peut interrompre un
script Python dessus.

**« En coop, le vaisseau part tout seul »**
Vérifie que tu utilises bien `4` et `6` pour le joueur 2. D'autres touches
peuvent créer des appuis fantômes sur la matrice sans diodes.

## Développer sans calculatrice

```bash
python3 tests/run_all.py       # toute la suite, sur la source et sur le build
python3 tests/test_balance.py  # simule des parties, mesure l'équilibrage
python3 tools/screenshot.py    # rend de vraies scènes de jeu en PNG
```

Aucune dépendance : uniquement la bibliothèque standard Python 3. Seul
`tools/memcheck.py` demande gcc et git, pour compiler MicroPython.

Pour tester avec un affichage réel sur PC, le module
[Kandinsky-Numworks](https://github.com/ZetaMap/Kandinsky-Numworks) de ZetaMap
(`pip install kandinsky`, nécessite SDL2) ouvre une fenêtre qui émule l'écran.
Il n'est pas utilisé ici parce qu'il lui faut un affichage, ce qui l'exclut de
l'intégration continue.
