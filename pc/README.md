# NOVA — édition PC

La version pygame de [NOVA](../README.md). Même jeu, mêmes règles, mais sans les
32 Ko de RAM qui ont forcé la version calculatrice à tout élaguer.

![Combat](../docs/img/pc-03-fight.png)

## Lancer

```bash
pip install pygame
python3 nova.py
```

| Option | |
|---|---|
| `--scale N` | Taille de fenêtre, 1 à 6 (défaut 3 → 1440×810) |
| `--fullscreen` | Démarre en plein écran |
| `--no-crt` | Coupe les scanlines |

En jeu : `F11` plein écran · `F1` filtre CRT · `+`/`-` taille de fenêtre.

## Contrôles

| | Joueur 1 | Joueur 2 (coop) |
|---|---|---|
| Se déplacer | flèches **ou** WASD | WASD |
| Tirer | automatique | automatique |
| Bombe | `Espace` ou `Maj` | partagée |
| Menus | flèches + `Entrée` | |

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
| Boss | un pattern | **3 phases**, enrage au bout de 40 s |
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
    sector.py        génération et rendu de la carte
    run.py           l'état d'une partie
    ui.py            menus, panneaux, HUD
    game.py          machine à états et boucle principale
  tests/             suite headless
  tools/shots.py     rend les captures d'écran
```

## Tests

Tout tourne sans écran (`SDL_VIDEODRIVER=dummy`), donc en intégration continue :

```bash
python3 tests/run_all.py     # runs complets + budget d'image
python3 tools/shots.py       # régénère les captures
```

`test_run.py` joue de vraies parties à travers la vraie machine à états — mêmes
événements clavier, mêmes combats, rien n'est simulé sauf l'écran. Il valide
aussi qu'aucun écran ne peut mener à une impasse.

Mesures actuelles :

| | |
|---|---|
| Taux de victoire (bot) | Cadet 7/8 · **Pilote 4/8** · As 1/8 |
| Durée d'une partie gagnée | 9 à 11 min de combat |
| Coût d'une image (p99) | **1,35 ms** sur un budget de 16,7 ms |

Le pilote automatique a une information parfaite et des réflexes parfaits mais
une stratégie naïve : un humain fera moins bien, ce qui est le bon sens de
l'erreur pour un contrôle de difficulté.

## Licence

MIT, comme le reste du dépôt.
