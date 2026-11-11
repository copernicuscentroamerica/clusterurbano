# Bethania (Nueva León de Judá): huella urbana, catastro predial y evaluación territorial del riesgo

**Integrante del equipo técnico:** Rafael Ruiz Urizar

La iniciativa organiza e integra en un geovisor interactivo la cartografía de detalle del asentamiento **Nueva León de Judá** (Zona 7, colonia Bethania, Ciudad de Guatemala), delimitando una zona de estudio acotada mediante un **recuadro envolvente generado a partir de la capa de predios** (`lotes_leondejuda.shp`) y articulando la ortofoto de dron (RPAS), la franja de servidumbre de líneas de alta tensión y las curvas de nivel a cada 1 metro para apoyar decisiones institucionales sobre obras de protección o escrituración.

## Propósito

La Unidad de Catastro de UDEVIPO requiere información espacial de alta precisión sobre viviendas, lotes, pendientes de barranco y restricciones por líneas de alta tensión en **Nueva León de Judá** para identificar predios expuestos a amenazas y priorizar estudios complementarios.

Facilitar el análisis de gabinete sobre los **105 predios catastrados** y orientar la priorización de verificaciones técnicas antes de adoptar decisiones administrativas o constructivas sobre cada lote.

## Instituciones participantes

- UDEVIPO (Unidad para el Desarrollo de Vivienda Popular)
- Municipalidad de Guatemala

## Territorio y delimitación de la zona de estudio

- **Ámbito focalizado:** Asentamiento **Nueva León de Judá**, Zona 7, colonia Bethania, Ciudad de Guatemala.
- **Delimitación por recuadro predial:** El área de estudio se acota mediante un polígono rectangular (`220.3 m × 324.3 m`, superficie de **7.15 ha**, centro en `-90.520353, 14.668426`) calculado directamente a partir del cuadro delimitador (*bounding box*) de la capa de predios (`lotes_leondejuda.shp`) con un margen técnico de encuadre de 12 metros.
- **Superficie predial neta:** **8,089.32 m²** (**0.81 ha**) distribuidos en **105 lotes** organizados en tres sectores: **Sector A** (50 lotes), **Sector B** (32 lotes), **Sector C** (22 lotes) y 1 lote sin sector asignado.

## Usuario y decisión

**Usuario principal:** Unidad de Catastro (UDEVIPO).

**Decisión que apoya:** Definir qué lotes del asentamiento Nueva León de Judá se encuentran afectados por la servidumbre de líneas de alta tensión o por condiciones críticas de ladera y drenaje, para fundamentar decisiones de obras de protección, mitigación o procesos de escrituración.

## Producto mínimo viable implementado en el Geovisor

El Geovisor interactivo de **Nueva León de Judá** integra cinco capas geoespaciales reproyectadas a `EPSG:4326`:

1. **Recuadro de zona de estudio (`recuadro_zona_estudio_leondejuda.geojson`):** Marco rectangular de 7.15 ha derivado de la envolvente de la capa de predios.
2. **Ortofoto RPAS de alta resolución (`ortofoto_leondejuda_cog.tif` / `.webp`):** Mosaico aerofotogramétrico de dron (~2.4 cm/píxel, `8087 × 6644 px` en su resolución nativa) que permite inspeccionar techos, accesos peatonales y taludes.
3. **Predios y lotes catastrados (`lotes_leondejuda.geojson`):** 105 polígonos prediales con numeración de lote, sector (`A`, `B`, `C`), estado de ocupación (**92 ocupados**, **8 desocupados**, **5 sin dato**), niveles de construcción y condiciones sanitarias (`desfogue_a`, `aguas_gris`, `aguas_pluv`), diferenciando visualmente los lotes que intersectan el corredor eléctrico.
4. **Líneas de alta tensión (`lineas_alta_tension_leondejuda.geojson`):** 3 polígonos que conforman la franja de servidumbre eléctrica (**4,303.51 m²**), la cual intersecta espacialmente **39 de los 105 predios** (19 en el Sector A, 16 en el Sector B y 4 en el Sector C).
5. **Curvas de nivel cada 1 m (`curvas_nivel_leondejuda.geojson`):** 536 curvas topográficas (normales cada 1 m y directoras cada 5 m) recortadas al recuadro de estudio, abarcando cotas entre **1,308 m y 1,439 m s. n. m.** a lo largo de la ladera del barranco.

## Resumen cuantitativo de las capas integradas

| Indicador / Capa en Nueva León de Judá | Valor / Detalle técnico |
| :--- | :--- |
| **Recuadro de zona de estudio** | `220.3 m × 324.3 m` (**7.15 ha**) derivado de `lotes_leondejuda.shp` (+12 m de margen) |
| **Total de predios levantados** | **105 lotes** (**8,089.32 m²** = **0.81 ha** netas) |
| **Distribución por sector** | Sector A: **50** · Sector B: **32** · Sector C: **22** · Sin sector: **1** |
| **Estado de ocupación** | Ocupados: **92** · Desocupados: **8** · Sin dato (NA): **5** |
| **Intersección con líneas de alta tensión** | **39 predios** intersectan el corredor eléctrico (4,303.51 m² en 3 polígonos) |
| **Desfogue de aguas negras (`desfogue_a`)** | Drenaje: **45** · Fosa séptica: **19** · Al barranco: **17** · Pozo ciego: **10** · NA: **14** |
| **Desfogue de aguas grises (`aguas_gris`)** | Drenaje: **47** · Al barranco: **40** · NA: **17** · No: **1** |
| **Relieve (curvas de nivel cada 1 m)** | **536 curvas** dentro del recuadro, entre **1,308 m y 1,439 m s. n. m.** (desnivel de 131 m) |
| **Ortofoto de dron (RPAS)** | `leon_de_juda.tif` (`8087 × 6644 px`, ~2.4 cm/px) publicada en COG y WebP |

## Contribución al Atlas Urbano Regional

El producto publicado en el Atlas documenta la caracterización predial y microtopográfica del asentamiento Nueva León de Judá, combinando levantamiento catastral, fotogrametría con dron e identificación de restricciones físicas (servidumbre de alta tensión y descarga de aguas hacia las laderas del barranco).

## Participación

El repositorio oficial de esta iniciativa se encuentra activo y abierto a la colaboración técnica. Las personas e instituciones participantes pueden consultar y descargar las capas en `geovisor/capas/`, abrir el proyecto directamente en GeoLibre Studio o enviar mejoras mediante una solicitud de cambios (*Pull Request*).

## Precedencia documental e identificación

- **Perfil documental que orienta esta iniciativa:** *Asentamientos en alto riesgo — Zona 7, colonia Bethania, Guatemala* (ficha técnica `S20` de UDEVIPO).
- **Insumos geoespaciales procesados (`S20-LDJ`):** Levantamiento del asentamiento **Nueva León de Judá** (`lotes_leondejuda.shp`, `lineasdealtatension_leondejuda.shp`, `leóndejuda_curvas_clip.shp` y `leon_de_juda.tif`).
