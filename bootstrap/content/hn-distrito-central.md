# Distrito Central: brecha catastral y ciudad construida

La iniciativa propone comparar la ciudad construida con el catastro del Distrito Central para localizar diferencias, priorizar actualización y levantamientos y preparar un método que otros municipios puedan adaptar.

## Propósito

La información catastral puede quedar rezagada respecto de edificaciones y ocupaciones existentes. La AMDC necesita medir esa diferencia de manera sistemática para orientar actualización, regularización y mejoramiento de barrios.

Contar con indicadores trazables y un kit replicable que conecte el trabajo municipal con el Atlas Municipal del MDC y el Atlas Urbano de la UNAH.

## Instituciones participantes

- Alcaldía Municipal del Distrito Central (AMDC)
- Universidad Nacional Autónoma de Honduras (UNAH)
- Secretaría de Gobernación, Justicia y Descentralización (SEGOB)

## Integrantes del equipo

- **Mario Baide** · Profesor Investigador, UNAH
- **Mario Matamoros** · Profesor Investigador, UNAH
- **Jonathan Ramirez** · Analista en Planificación Urbana, AMDC
- **Ana Maritza Irías** · SEGOB

## Territorio

Zona piloto: toda la mancha urbana consolidada del Municipio del Distrito Central, es decir, Tegucigalpa y Comayagüela.

El polígono de la mancha urbana se genera con el script (GHSL y Dynamic World) y se homologa con el perímetro urbano delimitado por la AMDC.

## Usuario y decisión

AMDC: Dirección de Ordenamiento Territorial (responsable del Atlas Municipal), Catastro Municipal y la unidad de acceso a la tierra y regularización.

Instituto de la Propiedad (regularización y titulación) y SEGOB (asistencia técnica a municipios).

UNAH (Atlas Urbano).

Etapa de réplica: toda la población, con énfasis en las personas y organizaciones interesadas en temas urbanos.

¿Dónde y en qué magnitud difiere la ciudad construida de la ciudad catastrada? A partir de esa respuesta:
Priorizar sectores para la actualización catastral y el levantamiento en campo.
Identificar y caracterizar asentamientos informales para la regularización de la tenencia y el mejoramiento integral de barrios.
Detectar a tiempo nuevas ocupaciones, en especial en laderas, quebradas y suelo no urbanizable.
Estimar la base tributaria no registrada y orientar la inversión municipal en servicios.

## Producto mínimo viable previsto

Un script parametrizado para la mancha urbana consolidada del MDC, una primera comparación con el catastro autorizado, indicadores por colonia o celda de 250 m y una prueba de réplica en un segundo municipio.

Alcance sujeto a acuerdo y revisión con el equipo. La disponibilidad de la demostración y la aceptación del producto se informarán con evidencia.

## Método previsto y datos

Se propone comparar la ciudad construida observable con datos globales con la ciudad registrada en el catastro municipal. El flujo combina Sentinel-2/Dynamic World, Sentinel-1, GHSL, Open Buildings y Copernicus DEM con parcelario, colonias, zonificación y amenazas de AMDC. Los indicadores de brecha se plantean por colonia o celda, con revisión institucional de las tipologías y publicación agregada; el kit deberá poder adaptarse posteriormente a otro municipio.

## Contribución prevista al Atlas

Capas e indicadores agregados de brecha catastral, huella urbana y tipología revisada, publicados de forma compatible en el Atlas Municipal del MDC y el Atlas Urbano de la UNAH.

## Estado de la documentación

Existe un perfil de proyecto y los materiales enumerados en la sección de documentación. El estado operativo, la revisión técnica y la validación institucional deben confirmarse por separado.

## Participación

El repositorio oficial de esta iniciativa se encuentra activo y abierto a la colaboración técnica. Las personas e instituciones participantes trabajan sobre una copia personal (*fork*) vinculada en Google Antigravity, integran capas geoespaciales en `geovisor/capas/` o ejecutan el ejercicio práctico en Google Colab / Google Earth Engine, y envían sus mejoras mediante una solicitud de cambios (*Pull Request*) para revisión técnica antes de su publicación.

## Precedencia documental e identificación

**Perfil documental que orienta esta iniciativa:** *Brecha catastral y asentamientos informales en el Municipio del Distrito Central: herramienta geoespacial replicable para los municipios de Honduras* (revisión actualizada `S24` del 12 de octubre de 2026).

**Articulación del expediente:** El ámbito operativo cubre la mancha urbana consolidada de Tegucigalpa y Comayagüela en el Municipio del Distrito Central (`S24`), mientras que el perfil preliminar focalizado en el centro histórico (`S25`) se conserva como antecedente.
