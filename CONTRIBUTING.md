# Guía de contribución al Portal Comunitario (`clusterurbano`)

## ¿Qué cambios pertenecen a este repositorio?

- Mejoras de diseño, accesibilidad, filtros, buscador y documentación transversal del portal.
- Actualización del registro de repositorios canónicos verificados (`data/projects.registry.json`).
- Acuerdos colectivos de la Comunidad de Práctica, recursos compartidos y curaduría del Atlas Urbano Regional.

> **Nota:** Para editar el alcance, metodología, código o capas del Geovisor GeoLibre de una iniciativa específica, haz fork y envía una Pull Request directamente al repositorio `urbano-{id}` de esa iniciativa.

## Comprobación local antes de enviar una Pull Request

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate.py --source
python3 scripts/sync_catalog.py --offline
python3 scripts/build_site.py --output site
python3 scripts/validate.py --site site
python3 -m unittest discover -s tests -v
```
