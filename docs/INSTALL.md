# Installation

## Sur une vraie NumWorks

1. Ouvre <https://my.numworks.com/python> et connecte-toi à ton compte NumWorks.
2. Crée un script nommé **`nova.py`**.
3. Colle le contenu intégral de [`dist/nova.py`](../dist/nova.py).
   ⚠️ Prends bien `dist/`, pas `src/` : la source lisible fait 46 Ko et ne rentre
   pas dans les 32 Ko de la machine.
4. Branche la calculatrice en USB et clique sur **Envoyer le script**.
5. Sur la calculatrice : **Python** → `nova` → `EXE`.

Le jeu démarre directement sur l'écran-titre.

## Vérifier que ça rentre

```bash
python3 tools/build.py
```

```
minified  :  17444 bytes  dist/nova.py
NumWorks script storage: 32768 bytes total for all scripts
this script uses 53.2% of it, 15324 bytes to spare
```

Les 32 Ko sont partagés par **tous** tes scripts. Si l'envoi échoue, supprime
d'autres scripts de la calculatrice.

## Dépannage

**« Le script ne démarre pas / erreur de mémoire »**
Le tas Python fait 32 Ko et contient le bytecode *plus* les objets. Supprime les
autres scripts et relance. Sur les modèles les plus anciens (N0100), la marge est
plus mince.

**« Ça rame »**
Le jeu est plafonné à 25 images par seconde et ne tente jamais de rattraper son
retard : sur une machine plus lente il ralentit proprement au lieu de saccader.
Vérifie qu'aucun autre script volumineux n'occupe la mémoire.

**« La touche RETOUR quitte le jeu »**
C'est voulu — `KEY_BACK` n'est jamais lue par le jeu, parce qu'Epsilon peut
interrompre un script Python dessus. La pause est sur **retour arrière**
(`BACKSPACE`).

**« En coop, le vaisseau part tout seul »**
Vérifie que tu utilises bien `4` et `6` pour le joueur 2. D'autres touches
peuvent créer des appuis fantômes sur la matrice sans diodes du clavier.

## Développer sans calculatrice

Le dépôt contient un émulateur headless de `kandinsky` et `ion` :

```bash
python3 tests/run_all.py       # toute la suite, sur la source et sur le build
python3 tests/test_balance.py  # simule des parties complètes, mesure l'équilibrage
python3 tools/screenshot.py    # rend de vraies scènes de jeu en PNG
```

Aucune dépendance : uniquement la bibliothèque standard Python 3.

Pour tester avec un affichage réel sur PC, le module
[Kandinsky-Numworks](https://github.com/ZetaMap/Kandinsky-Numworks) de ZetaMap
(`pip install kandinsky`, nécessite SDL2) ouvre une fenêtre qui émule l'écran.
Il n'est pas utilisé ici parce qu'il lui faut un affichage, ce qui l'exclut de
l'intégration continue.
