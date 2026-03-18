# API avec Docker

## Prérequis

Installer Docker

## Comment lancer l'api avec Docker

`cd api`

Copier le contenu _.env.exemple_ dans un nouveau fichier _.env.prod_

Si besoin, remplacer le contenu des variables

`npm run docker:up`

## Comment stoper l'api sur le Docker

`npm run docker:down`

# API en dev (avec node)

## Prerequis

Installer Node

Installer MongoDB

## Comment lancer l'API avec node

`cd api`

`npm i`

Copier le contenu _.env.exemple_ dans un nouveau fichier _.env.dev_

Si besoin, remplacer le contenu des variables

`npm run dev`

## Comment stoper l'api sur node

_CTRL+C_ dans le même terminal
