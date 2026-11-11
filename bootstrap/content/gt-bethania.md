# Bethania (Nueva León de Judá): modelo de elevación, mapa de pendientes y riesgo por techo de vivienda

**Integrante del equipo técnico:** Rafael Ruiz Urizar

La iniciativa organiza e integra en un geovisor interactivo la cartografía microurbana y la evaluación de riesgo del asentamiento **Nueva León de Judá** (Zona 7, colonia Bethania, Ciudad de Guatemala), delimitando la zona de estudio mediante un **recuadro envolvente generado a partir de la capa de predios** (`lotes_leondejuda.shp`, **7.15 ha**) y articulando:
1. Un **Modelo Digital de Elevación (DEM de 0.5 m)** interpolado a partir de las curvas de nivel de 1 m (`1,320.55 – 1,436.00 m s. n. m.`).
2. Un **Mapa de Pendientes y Zonificación de Amenaza por Ladera** (`<12°` Bajo, `12°–22°` Medio, `22°–32°` Alto, `>32°` Muy Alto / Escarpe de barranco).
3. Las huellas de **Techos de Vivienda (`124 techos`, `4,752.27 m²`)** obtenidas de **Google-Microsoft Open Buildings** y complementadas con restitución sobre la **ortofoto RPAS (`~2.4 cm/px`)**, clasificando cada techo y cada uno de los **105 predios** por su **nivel de riesgo multicriterio** (pendiente, servidumbre de líneas de alta tensión, descarga de aguas al barranco y vulnerabilidad constructiva).

## Propósito

La Unidad de Catastro de UDEVIPO requiere información espacial de alta precisión sobre viviendas, techos, lotes, pendientes de barranco y restricciones por líneas de alta tensión en **Nueva León de Judá** para identificar unidades habitacionales expuestas a amenazas y priorizar estudios geotécnicos y decisiones sobre obras de protección o escrituración.

## Instituciones participantes

- UDEVIPO (Unidad para el Desarrollo de Vivienda Popular)
- Municipalidad de Guatemala

## Territorio y delimitación de la zona de estudio

- **Ámbito focalizado:** Asentamiento **Nueva León de Judá**, Zona 7, colonia Bethania, Ciudad de Guatemala.
- **Delimitación por recuadro predial:** Polígono rectangular (`220.3 m × 324.3 m`, **7.15 ha**, centro en `-90.520353, 14.668426`) generado a partir del cuadro delimitador (*bounding box*) de la capa de predios (`lotes_leondejuda.shp`) más un margen técnico de 12 metros.
- **Superficie predial y techada:** **105 lotes catastrados** (**8,089.32 m²** = **0.81 ha** netas en Sectores A=50, B=32, C=22 y 1 sin sector) y **124 techos de vivienda** (**4,752.27 m²** techados: 105 en el asentamiento y 19 en el entorno inmediato dentro del recuadro).

## Capas publicadas en el Geovisor de Nueva León de Judá

1. **Modelo Digital de Elevación TIN 0.5 m (`modelo_elevacion_leondejuda_cog.tif` / `.webp`):** Superficie continua de elevación (`1,320.55 m` a `1,436.00 m s. n. m.`) interpolada mediante red irregular de triángulos (TIN Delaunay de 102,836 facetas) a partir de las curvas de nivel de 1 m, con sombreado analítico de relieve (*hillshade*).
2. **Mapa continuo de pendientes (`mapa_pendientes_leondejuda_cog.tif` / `.webp`) y Zonificación vectorial (`zonas_riesgo_pendiente_leondejuda.geojson`):** Clasificación morfométrica del terreno en cuatro niveles de riesgo por pendiente:
   - **Bajo (`< 12°` / `< 21%`):** `4,564.6 m²` (`0.46 ha` · `6.4%` del recuadro)
   - **Medio (`12° – 22°` / `21% – 40%`):** `3,356.9 m²` (`0.34 ha` · `4.7%`)
   - **Alto (`22° – 32°` / `40% – 62%`):** `7,824.5 m²` (`0.78 ha` · `11.0%`)
   - **Muy Alto / Crítico (`> 32°` / `> 62%`):** `55,661.4 m²` (`5.57 ha` · `77.9%` correspondiente a las laderas pronunciadas del barranco).
3. **Ortofoto RPAS de alta resolución (`ortofoto_leondejuda_cog.tif` / `.webp`):** Mosaico aerofotogramétrico de dron (~2.4 cm/píxel, `8087 × 6644 px`).
4. **Techos de vivienda clasificados por nivel de riesgo (`techos_vivienda_riesgo_leondejuda.geojson`):** **124 techos** (113 obtenidos de **Google-Microsoft Open Buildings** y 11 restituidos sobre la ortofoto RPAS en lotes donde el satélite no separó la cubierta) coloreados según su nivel de riesgo multicriterio:
   - 🟥 **Riesgo Muy Alto:** **24 techos** (18 en lotes del asentamiento + 6 en laderas del entorno)
   - 🟧 **Riesgo Alto:** **70 techos** (60 en lotes del asentamiento + 10 en el entorno)
   - 🟨 **Riesgo Medio:** **19 techos** (19 en lotes del asentamiento)
   - 🟩 **Riesgo Bajo:** **11 techos** (8 en lotes del asentamiento + 3 en plataforma superior)
5. **Catastro de predios enriquecido (`lotes_leondejuda.geojson`):** Los **105 predios** con su elevación media, pendiente media y máxima, estado de ocupación, drenajes, intersección con alta tensión y nivel de riesgo predial (**Muy Alto: 18**, **Alto: 60**, **Medio: 19**, **Bajo: 8**).
6. **Líneas de alta tensión (`lineas_alta_tension_leondejuda.geojson`):** 3 polígonos (**4,303.51 m²**) del corredor eléctrico que intersecta **39 lotes**.
7. **Curvas de nivel cada 1 m (`curvas_nivel_leondejuda.geojson`):** 536 curvas topográficas (`1,308–1,439 m s. n. m.`).
8. **Recuadro delimitador de la zona de estudio (`recuadro_zona_estudio_leondejuda.geojson`):** Polígono rectangular de **7.15 ha** derivado de la envolvente predial.

## Resumen cuantitativo del análisis integrado

| Componente / Indicador | Resultado en Nueva León de Judá |
| :--- | :--- |
| **Recuadro de zona de estudio** | `220.3 m × 324.3 m` (**7.15 ha**) derivado de `lotes_leondejuda.shp` (+12 m de margen) |
| **Modelo Digital de Elevación (DEM 0.5 m)** | Cota mínima: **1,320.55 m** · Cota máxima: **1,436.00 m** · Cota media: **1,381.57 m s. n. m.** |
| **Mapa de Pendientes (0.5 m)** | Pendiente media: **39.38°** (`90.0%`) · Máxima en escarpe: **72.68°** |
| **Superficie por clase de pendiente** | **Bajo (`<12°`):** `0.46 ha` (6.4%) · **Medio (`12–22°`):** `0.34 ha` (4.7%) · **Alto (`22–32°`):** `0.78 ha` (11.0%) · **Muy Alto (`>32°`):** `5.57 ha` (77.9%) |
| **Techos de vivienda analizados** | **124 techos** (**4,752.27 m²**): **113** de *Google-Microsoft Open Buildings* + **11** restituidos por RPAS |
| **Techos por nivel de riesgo** | 🟥 **Muy Alto:** **24** · 🟧 **Alto:** **70** · 🟨 **Medio:** **19** · 🟩 **Bajo:** **11** |
| **Predios catastrados (105 lotes) por riesgo** | 🟥 **Muy Alto:** **18** · 🟧 **Alto:** **60** · 🟨 **Medio:** **19** · 🟩 **Bajo:** **8** |
| **Intersección con líneas de alta tensión** | **39 predios** intersectan el corredor eléctrico (4,303.51 m² en 3 polígonos) |

## Precedencia documental e identificación

- **Perfil documental que orienta esta iniciativa:** *Asentamientos en alto riesgo — Zona 7, colonia Bethania, Guatemala* (ficha técnica `S20` de UDEVIPO).
- **Insumos geoespaciales procesados (`S20-LDJ`):** Levantamiento del asentamiento **Nueva León de Judá** (`lotes_leondejuda.shp`, `lineasdealtatension_leondejuda.shp`, `leóndejuda_curvas_clip.shp`, `leon_de_juda.tif`) e integración con **Google-Microsoft Open Buildings**.
