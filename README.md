# Comunidad Urbana Copernicus Centroamérica (`clusterurbano`)

Portal regional del **Clúster de Asentamientos Humanos · Fase II**. Conecta las ocho iniciativas de Centroamérica y República Dominicana, el catálogo del **Atlas Urbano Regional**, el seguimiento de compromisos y la agenda de la jornada presencial de San Salvador (10–12 de noviembre de 2026).

## Construcción y previsualización local

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate.py --source
python3 scripts/sync_catalog.py --offline
python3 scripts/export_progress.py --offline
python3 scripts/build_site.py --output site
python3 scripts/validate.py --site site
python3 -m http.server 8000 --directory site
```

## Sincronización remota desde repositorios canónicos

Cuando los repositorios `urbano-{id}` están verificados en `data/projects.registry.json` con `source_mode: "canonical"`:

```bash
python3 scripts/sync_catalog.py --online
python3 scripts/export_progress.py
python3 scripts/build_site.py --output site
```
