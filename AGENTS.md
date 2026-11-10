# Reglas para agentes de IA en el Portal Comunitario (`clusterurbano`)

Trabaja en español. Este repositorio mantiene el portal regional de la **Comunidad Urbana Copernicus Centroamérica**, el registro de repositorios autorizados (`data/projects.registry.json`), las semillas de arranque (`bootstrap/`), la agenda (`data/events.agenda.json`) y la generación de instantáneas derivadas del catálogo, Atlas y seguimiento.

## Invariantes

1. Mantén exactamente los ocho IDs iniciales: `pa-panama-oeste`, `sv-amss`, `cr-la-carpio`, `sv-la-union`, `gt-bethania`, `do-santiago`, `gt-salud-metropolitana` y `hn-distrito-central`.
2. `project.json` y `content/project.md` viven canónicamente en cada repositorio `urbano-{id}` una vez aprovisionado. No edites manualmente `data/projects.snapshot.json` ni `data/atlas.snapshot.json`.
3. No incorpores forks personales como iniciativas del catálogo regional.
4. Conserva la separación estricta entre tarea cerrada, PMV demostrable, revisión técnica, validación institucional y adopción.
5. Nunca publiques datos personales, secretos ni enlaces hacia insumos privados.

## Comandos de verificación obligatoria

```bash
python3 scripts/validate.py --source
python3 scripts/sync_catalog.py --offline
python3 scripts/export_progress.py --offline
python3 scripts/build_site.py --output site
python3 scripts/validate.py --site site
python3 -m unittest discover -s tests -v
```
