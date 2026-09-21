#!/bin/sh
mkdocs build --clean
rsync -av --delete site/ rya:/var/www/html/hilfe/
