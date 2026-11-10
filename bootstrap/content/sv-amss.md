# AMSS: expansión urbana y transformación del suelo

## Integrantes del equipo técnico (OPAMSS)

- **Fabio Gracias** ([@fabiogracias1979-svg](https://github.com/fabiogracias1979-svg))
- **Fernando Aguilar** ([@fernando70](https://github.com/fernando70))
- **Tatiana Miranda**

La iniciativa integra información de expansión urbana, permisos de construcción y valores del suelo para examinar las transformaciones del Área Metropolitana de San Salvador y apoyar sus instrumentos de planificación y gestión territorial.

## Propósito

El AMSS necesita información actualizada e integrada para reconocer dónde y cómo se expande la ciudad y relacionar esos cambios con la normativa, la inversión y el valor del suelo.

Mejorar la lectura de las tipologías de expansión y de la dinámica de inversión, con información útil para planificación, control del desarrollo y gestión del suelo.

## Instituciones participantes

- Oficina de Planificación del Área Metropolitana de San Salvador (OPAMSS)
- Ministerio de Gobernación y Desarrollo Territorial
- Instituto Holandés para la Democracia Multipartidaria (NIMD)

## Territorio

Área Metropolitana de San Salvador (AMSS) - Zona núcleo/urbana (AMSS) - 14 DISTRITOS.

## Usuario y decisión

Principalmente la Subdirección de Planificación, Subdirección de Control de Desarrollo Urbano, Inteligencia Territorial y departamento de información del Ministerio de Gobernación.

Evaluar la conveniencia de las diferentes tipologías de expansión urbana en el territorio, permitiendo identificar las fortalezas y riesgos de inversión que estas conllevan e identificar las oportunidades de mejora para los criterios de planificación urbana , los instrumentos de gestión del suelo y los procesos de utilización de la data de los permisos de construcción de manera que permita comprender mejor la dinámica de inversión territorial

## Producto mínimo viable previsto

Un primer script reproducible, una capa demostrativa de expansión urbana, un flujo de integración con información de permisos y valores del suelo, y un prototipo de tablero para los 14 distritos del AMSS.

Alcance sujeto a acuerdo y revisión con el equipo. La disponibilidad de la demostración y la aceptación del producto se informarán con evidencia.

## Método previsto y datos

Se propone integrar información de trámites y permisos con cambios de huella urbana observados por satélite y referencias de precios del suelo. El flujo previsto incluye normalización espacial, consultas en PostgreSQL/PostGIS, procesamiento en Earth Engine e interpolación de precios con evaluación del error. La publicación de registros institucionales depende de sus condiciones de acceso.

## Contribución prevista al Atlas

Capas de expansión urbana e indicadores territoriales por distrito, asociados a periodos y a rangos de valor del suelo con metodología y límites de interpretación.

## Estado de la documentación

Existe un perfil de proyecto y los materiales enumerados en la sección de documentación. El estado operativo, la revisión técnica y la validación institucional deben confirmarse por separado.

## Participación

El repositorio oficial de esta iniciativa se encuentra activo y abierto a la colaboración técnica. Las personas e instituciones participantes trabajan sobre una copia personal (*fork*) vinculada en Google Antigravity, integran capas geoespaciales en `geovisor/capas/` o ejecutan el ejercicio práctico en Google Colab / Google Earth Engine, y envían sus mejoras mediante una solicitud de cambios (*Pull Request*) para revisión técnica antes de su publicación.

## Precedencia documental e identificación

**Perfil documental que orienta esta iniciativa:** *Monitoreo de las dinámicas de expansión urbana y transformación del suelo para la planificación y la gestión sostenible del AMSS* (perfil actualizado `S10` — versión `AV_02` de OPAMSS).

**Articulación del expediente:** Se toma como referencia operativa la versión actualizada `AV_02` (`S10`), conservando la formulación preliminar `AV_01` (`S09`) como antecedente y la matriz de historias de usuario y tareas Scrum (`S11`) como base del backlog técnico.
