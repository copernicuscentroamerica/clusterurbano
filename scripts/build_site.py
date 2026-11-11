#!/usr/bin/env python3
"""
Generador estático determinista del Portal Comunitario (clusterurbano).
Construye Inicio, Proyectos, fichas proyectos/{id}/, Ejercicio práctico (/ejercicio/),
Atlas, fichas atlas/{product_id}/, Seguimiento, Comunidad, Recursos, Agenda (+ .ics) y 404.html.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from markdown_lite import render_markdown
from site_common import (
    TEMPLATE_VERSION,
    THEME_VERSION,
    SiteContext,
    badge_html,
    compute_site_context,
    esc,
    format_spanish_date,
    render_hero_team,
    render_project_institutions_band,
    render_regional_institutional_band,
    render_team_section_html,
    render_upper_institutional_bar,
)

ROOT = Path(__file__).resolve().parent.parent

SHORT_CARD_TITLES: dict[str, str] = {
    "pa-panama-oeste": "Panamá Oeste · Expansión urbana y ocupación informal",
    "sv-amss": "San Salvador (AMSS) · Expansión urbana y suelo",
    "cr-la-carpio": "La Carpio (San José) · Plan Maestro de Intervención",
    "sv-la-union": "Conchagua y La Unión · Asentamientos costeros",
    "gt-bethania": "Bethania (Guatemala) · Huella urbana y riesgo",
    "do-santiago": "Santiago · Escenarios de riesgo y PMOT",
    "gt-salud-metropolitana": "Guatemala Metropolitana · Clima urbano y salud",
    "hn-distrito-central": "Distrito Central · Brecha catastral y huella urbana",
}


def render_link_or_pending(url: str | None, active_label: str, pending_label: str, btn_class: str = "btn btn-outline", declared_only: bool = False) -> str:
    if url and url.startswith("https://"):
        suffix = " (referencia declarada)" if declared_only else " ↗"
        return (
            f'<a class="{btn_class}" href="{html.escape(url, quote=True)}" '
            f'target="_blank" rel="noopener noreferrer">{html.escape(active_label + suffix)}</a>'
        )
    return f'<span class="btn-disabled" role="status">{html.escape(pending_label)}</span>'


def render_hub_shell(
    *,
    ctx: SiteContext,
    registry: dict[str, Any],
    page_title: str,
    active_nav: str,
    hero_html: str,
    body_html: str,
    include_maplibre: bool = False,
    snapshot_generated_at: str | None = None,
) -> str:
    robots_meta = (
        '<meta name="robots" content="noindex, nofollow">'
        if ctx.effective_mode != "canonical"
        else '<meta name="robots" content="index, follow">'
    )

    work_banner_html = ""
    if ctx.effective_mode != "canonical":
        hub_site = registry.get("hub", {}).get("website")
        canon_link = (
            f' · <a href="{html.escape(hub_site, quote=True)}">Abrir portal canónico</a>'
            if hub_site
            else ""
        )
        work_banner_html = f"""
        <div class="work-banner" role="region" aria-label="Aviso de versión de trabajo">
          <div class="container">
            <span>Vista de trabajo del Portal Comunitario · Modo: <code>{esc(ctx.effective_mode)}</code>.</span>
            <span>La versión oficial se publica desde el repositorio canónico verificado{canon_link}</span>
          </div>
        </div>
        """

    nav_items = [
        ("inicio", "Inicio", ctx.site_url("")),
        ("proyectos", "Proyectos", ctx.site_url("proyectos/")),
        ("ejercicio", "Empieza aquí · Ejercicio", ctx.site_url("ejercicio/")),
        ("atlas", "Atlas", ctx.site_url("atlas/")),
        ("seguimiento", "Seguimiento", ctx.site_url("seguimiento/")),
        ("comunidad", "Comunidad", ctx.site_url("comunidad/")),
        ("recursos", "Recursos", ctx.site_url("recursos/")),
        ("agenda", "Agenda", ctx.site_url("agenda/")),
    ]
    nav_lis = []
    for key, label, href in nav_items:
        cur = ' aria-current="page"' if key == active_nav else ""
        nav_lis.append(f'<li><a href="{html.escape(href, quote=True)}"{cur}>{html.escape(label)}</a></li>')

    maplibre_head = ""
    maplibre_scripts = ""
    if include_maplibre:
        maplibre_head = (
            '<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" crossorigin="anonymous">'
        )
        maplibre_scripts = (
            '<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js" crossorigin="anonymous"></script>\n'
            f'  <script src="{html.escape(ctx.site_url("assets/js/geovisor.js"), quote=True)}?v=2.0.2"></script>'
        )

    hub_repo_url = (
        f"https://github.com/{registry['hub']['repository']}"
        if registry.get("hub", {}).get("repository")
        else None
    )
    hub_repo_html = (
        f'<a href="{html.escape(hub_repo_url, quote=True)}" target="_blank" rel="noopener noreferrer">GitHub ({esc(registry["hub"]["repository"])}) ↗</a>'
        if hub_repo_url
        else "<span>Repositorio central: en preparación</span>"
    )

    sync_label = format_spanish_date(snapshot_generated_at, "Semillas iniciales del paquete")
    upper_bar_html = render_upper_institutional_bar(
        ctx,
        "<strong>Comunidad Urbana Copernicus Centroamérica</strong> · Clúster de Asentamientos Humanos · Fase II",
        f"Última sincronización: <strong>{esc(sync_label)}</strong> · {hub_repo_html}",
    )
    regional_band_html = render_regional_institutional_band(ctx, extra_class="is-footer-band")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(page_title)} · Comunidad Urbana Copernicus Centroamérica</title>
  <meta name="description" content="Comunidad de Práctica del Clúster de Asentamientos Humanos Copernicus Centroamérica · Fase II. Proyectos, ejercicio práctico Colab/GEE, geovisores GeoLibre, seguimiento y Atlas Urbano Regional.">
  {robots_meta}
  <link rel="stylesheet" href="{html.escape(ctx.site_url('assets/css/styles.css'), quote=True)}?v=2.0.4">
  {maplibre_head}
</head>
<body>
  <a class="skip-link" href="#contenido-principal">Saltar al contenido principal</a>
  {work_banner_html}
  {upper_bar_html}
  <header class="site-header">
    <div class="container header-inner">
      <a class="brand" href="{html.escape(ctx.site_url(''), quote=True)}">
        <span class="brand-mark" aria-hidden="true">CU</span>
        <span class="brand-text">
          <span class="brand-title">Comunidad Urbana Copernicus Centroamérica</span>
          <span class="brand-subtitle">Clúster de Asentamientos Humanos · Fase II</span>
        </span>
      </a>
      <button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="menu-hub">
        Menú ☰
      </button>
      <nav id="menu-hub" class="site-nav" data-site-nav aria-label="Navegación principal del portal">
        <ul>
          {"".join(nav_lis)}
        </ul>
      </nav>
    </div>
  </header>

  {hero_html}

  <main id="contenido-principal">
    <div class="container">
      {body_html}
    </div>
  </main>

  {regional_band_html}
  <footer class="site-footer">
    <div class="container footer-grid">
      <div>
        <p class="footer-title">Comunidad Urbana Copernicus Centroamérica</p>
        <p>Clúster de Asentamientos Humanos · Fase II. Espacio regional que articula iniciativas institucionales, métodos reproducibles en Google Colab y Google Earth Engine, geovisores basados en GeoLibre y el Atlas Urbano Regional (Tema común: <code>{esc(THEME_VERSION)}</code>).</p>
      </div>
      <div>
        <p class="footer-title">Secciones del portal</p>
        <p>
          <a href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">Proyectos</a> ·
          <a href="{html.escape(ctx.site_url('ejercicio/'), quote=True)}">Ejercicio Colab / GEE</a> ·
          <a href="{html.escape(ctx.site_url('atlas/'), quote=True)}">Atlas Urbano Regional</a> ·
          <a href="{html.escape(ctx.site_url('seguimiento/'), quote=True)}">Seguimiento</a> ·
          <a href="{html.escape(ctx.site_url('comunidad/'), quote=True)}">Comunidad</a> ·
          <a href="{html.escape(ctx.site_url('recursos/'), quote=True)}">Recursos</a> ·
          <a href="{html.escape(ctx.site_url('agenda/'), quote=True)}">Agenda San Salvador</a>
        </p>
      </div>
      <div>
        <p class="footer-title">Fuentes de verdad y trazabilidad</p>
        <p>Cada iniciativa mantiene su manifiesto canónico <code>project.json</code>, su identidad local <code>branding/project-branding.json</code> y su propio geovisor en su repositorio independiente. Este portal consulta registros autorizados y distingue datos declarados, propuestas y asuntos por confirmar.</p>
      </div>
    </div>
  </footer>

  <script src="{html.escape(ctx.site_url('assets/js/ui.js'), quote=True)}?v=2.0.4"></script>
  {maplibre_scripts}
</body>
</html>
"""


def build_project_card_html(ctx: SiteContext, item: dict[str, Any]) -> str:
    p = item["project"]
    pid = p["id"]
    country_code = p["country"]["code"]
    country_name = p["country"]["name"]
    tags = p.get("tags", [])
    tags_attr = "|".join(tags)
    inst_list = p["institutional_use"].get("institutions", [])
    primary_inst = inst_list[0] if inst_list else "Institución por confirmar"
    inst_str = ", ".join(inst_list)
    short_title = SHORT_CARD_TITLES.get(pid, p["title"])
    search_blob = f"{pid} {short_title} {p['title']} {country_name} {p['territory']['label']} {inst_str} {' '.join(tags)}"

    detail_href = html.escape(ctx.site_url(f"proyectos/{pid}/"), quote=True)
    site_link = p["links"].get("website")
    ext_site_btn = (
        f'<a class="btn btn-outline btn-xs" href="{html.escape(site_link.rstrip("/") + "/aplicacion/", quote=True)}" target="_blank" rel="noopener noreferrer">Abrir Geovisor ↗</a>'
        if site_link and site_link.startswith("https://")
        else '<span class="badge badge-pendiente">Sitio propio en preparación</span>'
    )
    tags_html = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags)

    # Miniaturas de logos aprobados del proyecto o sus instituciones participantes (máx. 3)
    branding = item.get("branding")
    logo_imgs: list[str] = []
    if isinstance(branding, dict):
        pl = branding.get("project_logo")
        if isinstance(pl, dict) and pl.get("logo_path"):
            lsrc = ctx.site_url(f"assets/img/projects/{pid}/{pl['logo_path']}")
            lalt = esc(pl.get("alt_text") or pl.get("name"))
            logo_imgs.append(f'<img src="{html.escape(lsrc, quote=True)}" alt="{lalt}" height="24" style="height:24px;width:auto;max-width:74px;object-fit:contain;display:block;background:#FFFFFF;padding:2px 5px;border:1px solid #E2E8F4;border-radius:4px;" loading="lazy">')
        for b_inst in sorted(branding.get("institutions", []), key=lambda x: (int(x.get("order", 99)), str(x.get("id", "")))):
            if len(logo_imgs) >= 3:
                break
            if isinstance(b_inst, dict) and b_inst.get("logo_path"):
                lsrc = ctx.site_url(f"assets/img/projects/{pid}/{b_inst['logo_path']}")
                lalt = esc(b_inst.get("alt_text") or b_inst.get("name"))
                logo_imgs.append(f'<img src="{html.escape(lsrc, quote=True)}" alt="{lalt}" height="24" style="height:24px;width:auto;max-width:74px;object-fit:contain;display:block;background:#FFFFFF;padding:2px 5px;border:1px solid #E2E8F4;border-radius:4px;" loading="lazy">')

    logos_strip_right = f'<div class="card-inst-strip-logos" style="display:flex;align-items:center;gap:0.35rem;flex-wrap:wrap;">{"".join(logo_imgs)}</div>' if logo_imgs else ""
    team_names = [esc(m.get("name", "")) for m in (p.get("team") or []) if isinstance(m, dict) and m.get("name")]
    team_card_html = (
        f'<p style="font-size:0.84rem;color:var(--c-brand-blue);margin:0 0 0.25rem;">'
        f'<strong>Equipo técnico:</strong> {", ".join(team_names)}</p>'
        if team_names else ""
    )

    return f"""
    <article class="card" data-filter-item
             data-country="{esc(country_code)}"
             data-tag="{esc(tags_attr)}"
             data-pmv="{esc(p['pmv']['scope_status'])}"
             data-search-text="{esc(search_blob)}">
      <div style="display:flex;flex-wrap:wrap;justify-content:space-between;gap:0.4rem;">
        <span class="badge badge-country">{esc(country_name)} ({esc(country_code)})</span>
        <div style="display:flex;flex-wrap:wrap;gap:0.3rem;">
          {badge_html(p['status'].get('development'), 'Desarrollo')}
          {badge_html(p['pmv']['scope_status'], 'PMV')}
        </div>
      </div>
      <h3><a href="{detail_href}" style="color:var(--c-brand-blue);text-decoration:none;">{esc(short_title)}</a></h3>
      <div class="card-inst-strip">
        <div class="card-inst-strip-text">
          <strong>Institución principal</strong>
          <span>{esc(primary_inst)}</span>
        </div>
        {logos_strip_right}
      </div>
      {team_card_html}
      <p style="font-size:0.85rem;color:var(--c-text-muted);"><strong>Territorio:</strong> {esc(p['territory']['label'])}</p>
      <p>{esc(p['summary'])}</p>
      <div class="tag-list">{tags_html}</div>
      <div class="card-footer">
        <a class="btn btn-teal btn-xs" href="{detail_href}">Conocer proyecto →</a>
        {ext_site_btn}
      </div>
    </article>
    """


def build_home_page(
    ctx: SiteContext,
    registry: dict[str, Any],
    catalog_snap: dict[str, Any],
    atlas_snap: dict[str, Any],
    agenda_doc: dict[str, Any],
) -> str:
    projects_items = catalog_snap.get("projects", [])
    n_initiatives = len(projects_items)
    countries = sorted({it["project"]["country"]["code"] for it in projects_items})
    n_countries = len(countries)
    all_groups = sorted({g for it in projects_items for g in it["project"].get("source_groups", [])})
    n_atlas = len(atlas_snap.get("products", []))

    map_points = []
    for it in projects_items:
        p = it["project"]
        pid = p["id"]
        gv = it.get("geovisor_summary") or {}
        center = gv.get("center", [-84.0, 13.5])
        insts = p["institutional_use"].get("institutions", [])
        map_points.append(
            {
                "id": pid,
                "country_code": p["country"]["code"],
                "country_name": p["country"]["name"],
                "short_name": SHORT_CARD_TITLES.get(pid) or gv.get("short_name") or p["title"],
                "territory_label": p["territory"]["label"],
                "institution": insts[0] if insts else "Por confirmar",
                "center": center,
                "detail_url": ctx.site_url(f"proyectos/{pid}/"),
            }
        )
    safe_points_json = json.dumps(map_points, ensure_ascii=False).replace("</", "<\\/")

    cards_html = "".join(build_project_card_html(ctx, it) for it in projects_items)

    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <span class="badge badge-lime">Comunidad de Práctica Regional</span>
          <span class="badge badge-country">Jornada Presencial San Salvador · 10–12 nov 2026</span>
        </div>
        <h1>Información territorial que apoya decisiones urbanas</h1>
        <p class="hero-lead">La comunidad reúne iniciativas de Centroamérica y República Dominicana que emplean información geoespacial y observación de la Tierra para abordar retos de los asentamientos humanos. Este espacio conecta proyectos, laboratorios en Google Colab y Google Earth Engine, avances y contribuciones al Atlas Urbano Regional.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">Explorar proyectos</a>
          <a class="btn btn-teal" href="#solicitar-asesoria">Solicitar asesoría técnica</a>
          <a class="btn btn-outline-light" href="{html.escape(ctx.site_url('ejercicio/'), quote=True)}">Ejercicio Colab / GEE</a>
          <a class="btn btn-outline-light" href="{html.escape(ctx.site_url('atlas/'), quote=True)}">Consultar el Atlas</a>
          <a class="btn btn-outline-light" href="{html.escape(ctx.site_url('seguimiento/'), quote=True)}">Seguimiento y tablero</a>
        </div>
      </div>
    </section>
    """

    body = f"""
    <section class="stats-strip" aria-label="Resumen calculado del catálogo inicial">
      <div class="stat-card">
        <div class="stat-value">{n_initiatives}</div>
        <div class="stat-label">Iniciativas consolidadas en repositorios independientes</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{n_countries}</div>
        <div class="stat-label">Países participantes ({esc(', '.join(countries))})</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{len(all_groups)}</div>
        <div class="stat-label">Grupos documentales de origen integrados (1 y 9 unificados en Panamá Oeste)</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{n_atlas}</div>
        <div class="stat-label">Contribuciones previstas registradas para el Atlas Urbano Regional</div>
      </div>
    </section>

    <section class="section">
      <div class="card" style="border-left:4px solid var(--c-teal);background:var(--c-surface);">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.75rem;">
          <div>
            <span class="badge badge-ok">Recorrido práctico de principio a fin</span>
            <h2 style="margin:0.3rem 0;">¿Participas en un equipo técnico? Empieza tu primer análisis y despliega tu capa</h2>
            <p style="margin:0;color:var(--c-text-muted);font-size:0.92rem;">Ejecuta el ejercicio de <strong>Mancha Urbana con Sentinel-2</strong> en <strong>Google Colab</strong> o en <strong>Google Earth Engine</strong> usando la <strong>misma cuenta de Google</strong> con la que ingresas a <strong>Google Antigravity</strong>, e integra tus resultados en el Geovisor de tu proyecto.</p>
          </div>
          <div style="display:flex;gap:0.6rem;flex-wrap:wrap;">
            <a class="btn btn-primary btn-xs" href="{html.escape(ctx.site_url('ejercicio/'), quote=True)}">Abrir guía del ejercicio →</a>
            <a class="btn btn-outline btn-xs" href="{html.escape(ctx.site_url('assets/descargas/Manual_Guia_Antigravity_Proyectos_Copernicus.docx'), quote=True)}" download>Descargar Manual Word v1.1</a>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="section-header">
        <h2>Distribución territorial referencial de las iniciativas</h2>
        <span class="badge badge-declarado">Ubicaciones referenciales según cada perfil</span>
      </div>
      <div class="hub-map-card">
        <div class="geovisor-toolbar" style="border-radius:0;">
          <div style="display:flex;flex-wrap:wrap;align-items:center;gap:0.45rem;">
            <strong style="font-size:0.82rem;">🛰️ Catálogo Copernicus (23 capas):</strong>
            <select id="hub-basemap-select" aria-label="Seleccionar mapa base o producto Copernicus" style="padding:0.25rem 0.5rem;border-radius:4px;border:1px solid rgba(255,255,255,0.4);font-size:0.78rem;background:#FFFFFF;color:var(--c-brand-blue);font-weight:600;max-width:340px;">
              <optgroup label="1. Modelo Digital de Elevación Oficial Copernicus DEM (GLO-30 · 30 m)">
                <option value="copernicus-dem-glo30">Copernicus DEM GLO-30 (30 m · Elevación Hipsométrica + Sombreado)</option>
                <option value="copernicus-dem-hillshade">Copernicus DEM GLO-30 (30 m · Sombreado de Relieve / Hillshade)</option>
                <option value="copernicus-dem-viridis">Copernicus DEM GLO-30 (30 m · Hipsometría Viridis + Curvas de Nivel)</option>
              </optgroup>
              <optgroup label="2. Cobertura Terrestre y Mancha Urbana 10 m (Sentinel-1 + Sentinel-2)">
                <option value="esa-worldcover-2021">ESA WorldCover 10 m (2021 v200 · Mancha Urbana y Cobertura)</option>
                <option value="esa-worldcover-2020">ESA WorldCover 10 m (2020 v100 · Mancha Urbana y Cobertura)</option>
                <option value="s2-lulc-2023">Uso y Cobertura del Suelo Sentinel-2 10 m (Año 2023 · 9 clases)</option>
                <option value="s2-lulc-2020">Uso y Cobertura del Suelo Sentinel-2 10 m (Año 2020 · 9 clases)</option>
                <option value="s2-lulc-2017">Uso y Cobertura del Suelo Sentinel-2 10 m (Año 2017 · Línea base)</option>
              </optgroup>
              <optgroup label="3. Índices Espectrales y Bandas Copernicus Sentinel-2 L2A (10 m / 20 m)">
                <option value="s2-l2a-ndvi">Sentinel-2 L2A · Índice de Vegetación Urbana (NDVI · 10 m)</option>
                <option value="s2-l2a-ndbi">Sentinel-2 L2A · Índice de Edificación / Área Construida (NDBI · 20 m)</option>
                <option value="s2-l2a-ndwi">Sentinel-2 L2A · Índice de Humedad Superficial (NDWI · 20 m)</option>
                <option value="s2-l2a-falsecolor">Sentinel-2 L2A · Falso Color Infrarrojo (B08-B04-B03 · 10 m)</option>
                <option value="s2-l2a-swir">Sentinel-2 L2A · SWIR Urbano (B12-B8A-B04 · 20 m)</option>
              </optgroup>
              <optgroup label="4. Radar de Apertura Sintética Copernicus Sentinel-1 SAR RTC (10 m · Sin Nubes)">
                <option value="s1-rtc-falsecolor">Copernicus Sentinel-1 SAR RTC (10 m · Compuesto Urbano VV+VH)</option>
                <option value="s1-rtc-vv">Copernicus Sentinel-1 SAR RTC (10 m · Polarización VV Escala de Grises)</option>
              </optgroup>
              <optgroup label="5. Agua Superficial e Inundaciones (JRC Comisión Europea / Copernicus)">
                <option value="jrc-gsw-occurrence">JRC Agua Superficial · Ocurrencia Histórica e Inundación (1984–2021)</option>
                <option value="jrc-gsw-extent">JRC Agua Superficial · Extensión Máxima de Agua / Inundación</option>
              </optgroup>
              <optgroup label="6. Mosaicos Anuales Ópticos Copernicus Sentinel-2 Cloudless (2018–2024)">
                <option value="sentinel2-2024">Copernicus Sentinel-2 Cloudless (Mosaico 2024 · EOX)</option>
                <option value="sentinel2-2023">Copernicus Sentinel-2 Cloudless (Mosaico 2023 · EOX)</option>
                <option value="sentinel2-2022">Copernicus Sentinel-2 Cloudless (Mosaico 2022 · EOX)</option>
                <option value="sentinel2-2021">Copernicus Sentinel-2 Cloudless (Mosaico 2021 · EOX)</option>
                <option value="sentinel2-2020">Copernicus Sentinel-2 Cloudless (Mosaico 2020 · EOX)</option>
                <option value="sentinel2-2019">Copernicus Sentinel-2 Cloudless (Mosaico 2019 · EOX)</option>
                <option value="sentinel2-2018">Copernicus Sentinel-2 Cloudless (Mosaico 2018 · EOX)</option>
              </optgroup>
              <optgroup label="7. Mapas Base Vectoriales y Referencia Cartográfica">
                <option value="carto-positron" selected>Mapa Claro Vectorial (OpenFreeMap)</option>
                <option value="osm-standard">OpenStreetMap Estándar</option>
                <option value="carto-dark">Modo Oscuro Vectorial (OpenFreeMap)</option>
                <option value="esri-imagery">Imagen Satelital de Alta Resolución (Esri)</option>
              </optgroup>
            </select>
            <button type="button" class="btn btn-outline-light btn-xs" data-hub-basemap-quick="copernicus-dem-glo30">⛰️ DEM GLO-30</button>
            <button type="button" class="btn btn-outline-light btn-xs" data-hub-basemap-quick="esa-worldcover-2021">🏙️ WorldCover 10m</button>
            <button type="button" class="btn btn-outline-light btn-xs" data-hub-basemap-quick="s2-lulc-2023">🏙️ LULC 2023</button>
            <button type="button" class="btn btn-outline-light btn-xs" data-hub-basemap-quick="s2-l2a-ndvi">🌿 NDVI</button>
            <button type="button" class="btn btn-outline-light btn-xs" data-hub-basemap-quick="s2-l2a-ndbi">🏗️ NDBI</button>
            <button type="button" class="btn btn-outline-light btn-xs" data-hub-basemap-quick="s1-rtc-falsecolor">📡 Radar S1</button>
            <button type="button" class="btn btn-outline-light btn-xs" data-hub-basemap-quick="jrc-gsw-occurrence">🌊 JRC Agua</button>
            <button type="button" class="btn btn-outline-light btn-xs" data-hub-basemap-quick="sentinel2-2024">🛰️ S2 2024</button>
            <button type="button" class="btn btn-teal btn-xs" data-hub-basemap-quick="carto-positron">🗺️ Vectorial</button>
          </div>
          <div class="geovisor-toolbar-actions">
            <button type="button" id="hub-toggle-fullscreen" class="btn btn-primary btn-xs">⛶ Pantalla completa</button>
          </div>
        </div>
        <div id="hub-basemap-legend" style="padding:0.35rem 0.9rem;background:#1A2766;color:#E8ECF8;font-size:0.76rem;border-bottom:1px solid rgba(255,255,255,0.12);">
          🗺️ Mapa base vectorial de referencia cartográfica (OpenFreeMap / OpenStreetMap)
        </div>
        <div id="hub-regional-map" class="hub-map-canvas" role="region" aria-label="Mapa regional orientativo de las ocho iniciativas"></div>
        <div style="padding:0.65rem 1rem;background:var(--c-surface-alt);font-size:0.82rem;color:var(--c-text-muted);">
          <strong>Nota cartográfica:</strong> Los marcadores señalan únicamente el centroide o ámbito referencial declarado en cada ficha de proyecto para facilitar la navegación; no representan resultados analíticos ni límites oficiales validados. Cada iniciativa cuenta con su propio geovisor basado en GeoLibre con mosaicos abiertos de Copernicus Sentinel-2 Cloudless (2018–2024) y Relieve Copernicus DEM.
        </div>
      </div>
      <script id="hub-map-points" type="application/json">{safe_points_json}</script>
    </section>

    <section class="section">
      <div class="section-header">
        <h2>Cartera inicial de iniciativas ({n_initiatives})</h2>
        <a class="btn btn-outline btn-xs" href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">Filtrar y buscar en catálogo →</a>
      </div>
      <div class="grid-3">
        {cards_html}
      </div>
    </section>

    <section class="section" id="solicitar-asesoria" aria-labelledby="titulo-solicitar-asesoria">
      <div class="card" style="border-top:4px solid var(--c-brand-blue);border-left:4px solid var(--c-accent-yellow);padding:1.5rem;">
        <div class="section-header" style="margin-bottom:0.85rem;">
          <div>
            <span class="badge badge-lime">Mesa de ayuda y mentoría regional</span>
            <h2 id="titulo-solicitar-asesoria" style="margin:0.35rem 0 0.2rem;">Solicitar asesoría técnica o acompañamiento metodológico</h2>
            <p style="margin:0;color:var(--c-text-muted);font-size:0.94rem;">Describe el problema técnico, metodológico o geoespacial que tu equipo necesita resolver. El formulario estructura tu solicitud para registrarla directamente en el repositorio de tu proyecto (vinculada al tablero de <a href="{html.escape(ctx.site_url('seguimiento/'), quote=True)}">Seguimiento Regional</a>) y genera al instante un prompt técnico para avanzar en <strong>Google Antigravity</strong>.</p>
          </div>
        </div>

        <div class="grid-2" data-advisory-form-root style="align-items:start;gap:1.35rem;">
          <form id="form-asesoria-equipos" onsubmit="return false;" style="display:flex;flex-direction:column;gap:0.85rem;background:var(--c-bg);padding:1.15rem;border:1px solid var(--c-border);border-radius:var(--radius-md);">
            <div class="grid-2" style="gap:0.75rem;">
              <div class="filter-field">
                <label for="adv-project">1. Iniciativa / Proyecto del equipo *</label>
                <select id="adv-project" data-adv-project required>
                  <option value="pa-panama-oeste" data-repo="copernicuscentroamerica/urbano-pa-panama-oeste">Panamá · Panamá Oeste (urbano-pa-panama-oeste)</option>
                  <option value="pa-colon" data-repo="copernicuscentroamerica/clusterurbano">Panamá · Colón (pa-colon)</option>
                  <option value="sv-amss" data-repo="copernicuscentroamerica/urbano-sv-amss">El Salvador · AMSS OPAMSS (urbano-sv-amss)</option>
                  <option value="cr-la-carpio" data-repo="copernicuscentroamerica/urbano-cr-la-carpio">Costa Rica · La Carpio (urbano-cr-la-carpio)</option>
                  <option value="sv-la-union" data-repo="copernicuscentroamerica/urbano-sv-la-union">El Salvador · La Unión Sur (urbano-sv-la-union)</option>
                  <option value="gt-bethania" data-repo="copernicuscentroamerica/urbano-gt-bethania">Guatemala · Bethania (urbano-gt-bethania)</option>
                  <option value="do-santiago" data-repo="copernicuscentroamerica/urbano-do-santiago">Rep. Dominicana · Santiago (urbano-do-santiago)</option>
                  <option value="gt-salud-metropolitana" data-repo="copernicuscentroamerica/urbano-gt-salud-metropolitana">Guatemala · Salud Metropolitana (urbano-gt-salud-metropolitana)</option>
                  <option value="hn-distrito-central" data-repo="copernicuscentroamerica/urbano-hn-distrito-central">Honduras · Distrito Central (urbano-hn-distrito-central)</option>
                  <option value="regional-general" data-repo="copernicuscentroamerica/clusterurbano">Consulta transversal regional (clusterurbano)</option>
                </select>
              </div>
              <div class="filter-field">
                <label for="adv-author">2. Nombre e institución solicitante *</label>
                <input id="adv-author" type="text" data-adv-author placeholder="Ej. Ana Maritza Irías · SEGOB / UNAH" required>
              </div>
            </div>

            <div class="grid-2" style="gap:0.75rem;">
              <div class="filter-field">
                <label for="adv-category">3. Área temática de la asesoría *</label>
                <select id="adv-category" data-adv-category>
                  <option value="Procesamiento satelital (Sentinel-2 / DEM / LST en GEE o Colab)">Procesamiento satelital (Sentinel-2 / DEM / LST en GEE o Colab)</option>
                  <option value="Cruce espacial, SIG y datos locales (Catastro, censos, amenazas)">Cruce espacial, SIG y datos locales (Catastro, censos, amenazas)</option>
                  <option value="Publicación y estilo de capas en el Geovisor GeoLibre">Publicación y estilo de capas en el Geovisor GeoLibre</option>
                  <option value="Flujo Git, Fork, Pull Request o configuración en Antigravity">Flujo Git, Fork, Pull Request o configuración en Antigravity</option>
                  <option value="Delimitación del PMV, indicadores y criterios de aceptación">Delimitación del PMV, indicadores y criterios de aceptación</option>
                  <option value="Estandarización de metadatos para el Atlas Urbano Regional">Estandarización de metadatos para el Atlas Urbano Regional</option>
                </select>
              </div>
              <div class="filter-field">
                <label for="adv-priority">4. Nivel de urgencia / impacto en el PMV *</label>
                <select id="adv-priority" data-adv-priority>
                  <option value="Media" data-label="prioridad:media">Prioridad Media · Orientación metodológica o revisión</option>
                  <option value="Alta" data-label="prioridad:alta">Prioridad Alta · Paso técnico detenido en el equipo</option>
                  <option value="Crítica (Bloqueo)" data-label="prioridad:alta">Bloqueo Crítico · Impide avanzar en el entregable del PMV</option>
                </select>
              </div>
            </div>

            <div class="filter-field">
              <label for="adv-problem">5. Problema específico que quieren resolver *</label>
              <textarea id="adv-problem" rows="4" data-adv-problem placeholder="Describe con claridad qué problema técnico, metodológico o territorial busca resolver tu equipo y en qué paso se encuentran..." style="width:100%;padding:0.6rem 0.75rem;border:1px solid var(--c-border-strong);border-radius:var(--radius-sm);font-family:inherit;font-size:0.9rem;" required></textarea>
            </div>

            <div class="filter-field">
              <label for="adv-context">6. Insumos, pruebas realizadas o enlace a tu fork / script (opcional)</label>
              <textarea id="adv-context" rows="2" data-adv-context placeholder="Ej. Probamos el filtro SCL en GEE sobre el AOI municipal, pero tenemos dudas con el umbral de NDBI o la proyección del GeoJSON..." style="width:100%;padding:0.55rem 0.75rem;border:1px solid var(--c-border-strong);border-radius:var(--radius-sm);font-family:inherit;font-size:0.88rem;"></textarea>
            </div>

            <div class="filter-field">
              <label for="adv-expected">7. Resultado concreto esperado de la asesoría *</label>
              <input id="adv-expected" type="text" data-adv-expected placeholder="Ej. Definir el umbral óptimo, validar el cruce espacial y publicar la capa resultante en geovisor/capas/">
            </div>

            <div style="display:flex;flex-wrap:wrap;gap:0.6rem;padding-top:0.35rem;">
              <a id="adv-submit-github" data-adv-submit-github class="btn btn-primary btn-xs" href="https://github.com/copernicuscentroamerica/urbano-pa-panama-oeste/issues/new?template=02-bloqueo-apoyo.yml" target="_blank" rel="noopener noreferrer">1. Registrar solicitud en GitHub Issues ↗</a>
              <a id="adv-submit-discussion" data-adv-submit-discussion class="btn btn-teal btn-xs" href="https://github.com/copernicuscentroamerica/clusterurbano/discussions/new?category=ayuda-tecnica-y-mentoria" target="_blank" rel="noopener noreferrer">2. Publicar en Foro de Mentoría ↗</a>
              <button type="button" class="btn btn-outline btn-xs" data-copy-target="adv-markdown-preview">3. Copiar ficha para chat / correo</button>
            </div>
          </form>

          <div style="display:flex;flex-direction:column;gap:0.9rem;">
            <div class="card" style="background:#F8FAFF;border:1px solid var(--c-border);padding:1rem;">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;margin-bottom:0.45rem;">
                <span class="badge badge-declarado">Trazabilidad automática</span>
                <small style="color:var(--c-text-muted);font-weight:600;" data-adv-target-repo-label>Destino: copernicuscentroamerica/urbano-pa-panama-oeste</small>
              </div>
              <h3 style="margin:0 0 0.35rem;font-size:1rem;">Vista previa del ticket estructurado</h3>
              <p style="margin:0 0 0.55rem;font-size:0.83rem;color:var(--c-text-muted);">Al pulsar <strong>Registrar solicitud en GitHub Issues</strong>, se abrirá el repositorio oficial de tu proyecto con esta estructura lista para enviar y vinculada al tablero de seguimiento:</p>
              <pre id="adv-markdown-preview" data-adv-markdown-preview style="margin:0;max-height:210px;overflow:auto;font-size:0.78rem;background:#0C1659;color:#FFFFFF;padding:0.75rem;border-radius:6px;white-space:pre-wrap;"></pre>
            </div>

            <div class="card" style="background:#FFFDF2;border:1px solid #E6C750;padding:1rem;">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;margin-bottom:0.45rem;">
                <span class="badge badge-lime">Asistencia inmediata con IA</span>
                <button type="button" class="btn btn-outline btn-xs" data-copy-target="adv-antigravity-prompt">Copiar prompt para Antigravity</button>
              </div>
              <h3 style="margin:0 0 0.35rem;font-size:1rem;">Prompt sugerido para tu agente en Google Antigravity</h3>
              <p style="margin:0 0 0.55rem;font-size:0.83rem;color:var(--c-text-muted);">Mientras el equipo de facilitación atiende tu solicitud, pega este prompt en el chat de <strong>Antigravity</strong> dentro de tu repositorio local para recibir apoyo técnico inmediato:</p>
              <pre id="adv-antigravity-prompt" data-adv-antigravity-prompt style="margin:0;max-height:175px;overflow:auto;font-size:0.78rem;background:#000A62;color:#FFFFFF;padding:0.75rem;border-radius:6px;white-space:pre-wrap;"></pre>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="grid-3">
        <article class="card">
          <span class="badge badge-lime">10–12 de noviembre de 2026</span>
          <h3>Encuentro presencial en San Salvador</h3>
          <p>{esc(agenda_doc.get('event_name'))}. Tres días de delimitación de PMV, laboratorios técnicos, mentorías y acuerdos regionales con cierre público en Parque Cuscatlán.</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="{html.escape(ctx.site_url('agenda/'), quote=True)}">Consultar horario (UTC−06:00)</a>
          </div>
        </article>
        <article class="card">
          <span class="badge badge-declarado">Seguimiento y apoyos</span>
          <h3>Tablero compartido y trazabilidad</h3>
          <p>Las tareas técnicas viven en el repositorio de cada iniciativa y se articulan con el tablero público GitHub Project #1, distinguiendo el avance operativo de la validación del PMV.</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="{html.escape(ctx.site_url('seguimiento/'), quote=True)}">Ir a Seguimiento</a>
          </div>
        </article>
        <article class="card">
          <span class="badge badge-propuesta">Colaboración abierta</span>
          <h3>Antigravity, Colab, GEE y Geovisor GeoLibre</h3>
          <p>Cada participante trabaja desde su fork personal, procesa imágenes Sentinel-2 en Google Colab o Google Earth Engine y despliega sus capas en el Geovisor de su iniciativa.</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="{html.escape(ctx.site_url('ejercicio/'), quote=True)}">Ir al ejercicio paso a paso</a>
          </div>
        </article>
      </div>
    </section>
    """

    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Inicio",
        active_nav="inicio",
        hero_html=hero,
        body_html=body,
        include_maplibre=True,
        snapshot_generated_at=catalog_snap.get("generated_at"),
    )


def build_proyectos_catalog_page(ctx: SiteContext, registry: dict[str, Any], catalog_snap: dict[str, Any]) -> str:
    items = catalog_snap.get("projects", [])
    countries = sorted({(it["project"]["country"]["code"], it["project"]["country"]["name"]) for it in items})
    tags = sorted({t for it in items for t in it["project"].get("tags", [])})

    country_opts = '<option value="all">Todos los países (6)</option>' + "".join(
        f'<option value="{esc(code)}">{esc(name)} ({esc(code)})</option>' for code, name in countries
    )
    tag_opts = '<option value="all">Todos los temas</option>' + "".join(
        f'<option value="{esc(t)}">{esc(t)}</option>' for t in tags
    )
    cards_html = "".join(build_project_card_html(ctx, it) for it in items)

    hero = """
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <span class="badge badge-lime">Catálogo regional</span>
        </div>
        <h1>Iniciativas del Clúster de Asentamientos Humanos</h1>
        <p class="hero-lead">Ocho iniciativas en seis países generadas desde sus manifiestos estructurados, conservando estados reales de alcance, demostración y validación.</p>
      </div>
    </section>
    """

    body = f"""
    <section class="section" data-catalog-projects>
      <div class="filter-bar" role="search" aria-label="Filtrar proyectos">
        <div class="filter-field" style="flex:2;">
          <label for="f-proj-q">Buscar por título, territorio o institución</label>
          <input id="f-proj-q" type="search" placeholder="Ej. Panamá, OPAMSS, La Carpio, catastro, riesgo..." data-filter-search>
        </div>
        <div class="filter-field">
          <label for="f-proj-country">País</label>
          <select id="f-proj-country" data-filter-select="country">{country_opts}</select>
        </div>
        <div class="filter-field">
          <label for="f-proj-tag">Tema</label>
          <select id="f-proj-tag" data-filter-select="tag">{tag_opts}</select>
        </div>
        <div>
          <button type="button" class="btn btn-outline" data-filter-reset>Restablecer</button>
        </div>
      </div>

      <p style="font-size:0.88rem;color:var(--c-text-muted);margin-bottom:1rem;" data-filter-count>{len(items)} de {len(items)} registros mostrados</p>

      <div class="callout callout-warn hidden" data-filter-empty>
        <strong>No se encontraron iniciativas con los criterios seleccionados</strong>
        <span>Prueba con otro término o restablece los filtros para volver a mostrar las ocho iniciativas.</span>
      </div>

      <div class="grid-3">
        {cards_html}
      </div>
    </section>
    """

    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Proyectos",
        active_nav="proyectos",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=catalog_snap.get("generated_at"),
    )


def build_hub_project_detail_page(
    ctx: SiteContext,
    registry: dict[str, Any],
    reg_entry: dict[str, Any],
    item: dict[str, Any],
    atlas_products: list[dict[str, Any]],
    snapshot_generated_at: str | None,
) -> str:
    p = item["project"]
    pid = p["id"]
    content_md = item["content_markdown"]
    proposed_slug = f"{reg_entry['proposed_owner']}/{reg_entry['proposed_repository']}"
    effective_slug = reg_entry.get("repository") or proposed_slug
    canon_repo_url = p["links"].get("repository") or f"https://github.com/{effective_slug}"
    proj_site_url = p["links"].get("website")

    has_decl_demo = any(
        st.get("pointer") == "/links/demo" and st.get("status") == "declarado"
        for st in p.get("provenance", {}).get("statements", [])
    )

    site_btn = render_link_or_pending(
        proj_site_url.rstrip("/") + "/aplicacion/" if proj_site_url else None,
        "Abrir Geovisor GeoLibre de la iniciativa",
        "Sitio independiente en preparación",
        "btn btn-primary",
    )
    repo_btn = render_link_or_pending(
        canon_repo_url,
        "Ver repositorio canónico en GitHub",
        f"Repositorio en preparación (propuesto: {reg_entry['proposed_repository']})",
        "btn btn-outline-light",
    )
    demo_btn = (
        render_link_or_pending(
            p["links"].get("demo"),
            "Abrir demostrador externo",
            "",
            "btn btn-outline-light",
            declared_only=has_decl_demo and p["status"].get("demo") != "disponible",
        )
        if p["links"].get("demo")
        else ""
    )

    ac_rows = "".join(
        f"<tr><td><code>{esc(ac['id'])}</code></td><td>{esc(ac['description'])}</td><td>{badge_html(ac['status'])}</td></tr>"
        for ac in p["pmv"].get("acceptance_criteria", [])
    )
    lim_li = "".join(f"<li>{esc(l)}</li>" for l in p.get("limitations", []))

    atlas_links = []
    for ap in atlas_products:
        ahref = html.escape(ctx.site_url(f"atlas/{ap['id']}/"), quote=True)
        atlas_links.append(f'<li><a href="{ahref}"><strong>{esc(ap["title"])}</strong></a> ({esc(ap["publication_status"])})</li>')

    if item.get("sync_state") == "ok":
        sync_badge = '<span class="badge badge-ok">Datos sincronizados</span>'
    elif item.get("sync_state") == "stale":
        sync_badge = '<span class="badge badge-propuesta">Copia en caché (stale)</span>'
    else:
        sync_badge = '<span class="badge badge-pendiente">Semilla inicial</span>'

    fork_snippet = f"""gh repo fork {effective_slug} --clone=false
git clone https://github.com/TU_USUARIO_GITHUB/{reg_entry['proposed_repository']}.git
cd {reg_entry['proposed_repository']}
git remote add upstream https://github.com/{effective_slug}.git"""

    fork_url = f"{canon_repo_url.rstrip('/')}/fork"
    new_task_url = f"{canon_repo_url.rstrip('/')}/issues/new?template=tarea_pmv.yml"
    support_url = f"{canon_repo_url.rstrip('/')}/issues/new?template=bloqueo_apoyo.yml"
    pr_url = f"{canon_repo_url.rstrip('/')}/pulls"
    collab_page_url = (proj_site_url.rstrip("/") + "/colaborar/") if proj_site_url else ctx.site_url("ejercicio/")

    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <a href="{html.escape(ctx.site_url('proyectos/'), quote=True)}" style="color:#FFFFFF;font-weight:600;">← Catálogo de proyectos</a>
          <span class="badge badge-lime">{esc(p['country']['name'])}</span>
          <span class="badge badge-country">ID: {esc(pid)} · Grupos: {esc(', '.join(str(g) for g in p['source_groups']))}</span>
          {sync_badge}
        </div>
        <h1>{esc(p['title'])}</h1>
        {render_hero_team(p)}
        <p class="hero-lead">{esc(p['summary'])}</p>
        <div class="hero-actions">
          {site_btn}
          {repo_btn}
          <a class="btn btn-teal" href="{html.escape(ctx.site_url('ejercicio/'), quote=True)}">Ejercicio Colab / GEE →</a>
          {demo_btn}
        </div>
      </div>
    </section>
    """

    body = f"""
    <section class="status-strip" aria-label="Estados de la iniciativa">
      <div class="status-cell"><div class="status-cell-label">Alcance PMV</div>{badge_html(p['pmv']['scope_status'])}</div>
      <div class="status-cell"><div class="status-cell-label">Desarrollo</div>{badge_html(p['status']['development'])}</div>
      <div class="status-cell"><div class="status-cell-label">Demostración</div>{badge_html(p['status']['demo'])}</div>
      <div class="status-cell"><div class="status-cell-label">Revisión técnica</div>{badge_html(p['status']['technical_review']['state'])}</div>
      <div class="status-cell"><div class="status-cell-label">Validación institucional</div>{badge_html(p['status']['institutional_validation']['state'])}</div>
      <div class="status-cell"><div class="status-cell-label">Adopción</div>{badge_html(p['status']['adoption']['state'])}</div>
    </section>

    <section class="section">
      <div class="card" style="border-left:4px solid var(--c-brand-blue);">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.6rem;">
          <div>
            <h2 style="margin:0 0 0.25rem;">Trabajar en esta iniciativa · Accesos directos</h2>
            <p style="margin:0;font-size:0.88rem;color:var(--c-text-muted);">Usa estos enlaces para abrir tu copia personal (<em>fork</em>), añadir o actualizar logos institucionales, ejecutar el ejercicio en Google Colab o Google Earth Engine, registrar tareas o enviar un Pull Request.</p>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:0.45rem;">
            <a class="btn btn-teal btn-xs" href="{html.escape(fork_url, quote=True)}" target="_blank" rel="noopener noreferrer">1. Crear copia personal (Fork) ↗</a>
            <a class="btn btn-outline btn-xs" href="{html.escape(collab_page_url, quote=True)}" target="_blank" rel="noopener noreferrer">2. Guía de incorporación y logos ↗</a>
            <a class="btn btn-outline btn-xs" href="{html.escape(ctx.site_url('ejercicio/'), quote=True)}">3. Ejercicio Colab / GEE</a>
            <a class="btn btn-outline btn-xs" href="{html.escape(new_task_url, quote=True)}" target="_blank" rel="noopener noreferrer">4. Crear tarea PMV ↗</a>
            <a class="btn btn-outline btn-xs" href="{html.escape(support_url, quote=True)}" target="_blank" rel="noopener noreferrer">5. Solicitar apoyo / bloqueo ↗</a>
            <a class="btn btn-outline btn-xs" href="{html.escape(pr_url, quote=True)}" target="_blank" rel="noopener noreferrer">6. Pull Requests ↗</a>
          </div>
        </div>
      </div>
    </section>

    {render_team_section_html(p)}

    <section class="section">
      <div class="grid-2">
        <div class="prose">
          {render_markdown(content_md)}
        </div>
        <div style="display:flex;flex-direction:column;gap:1.2rem;">
          <article class="card">
            <h3>Metadatos de origen y sincronización</h3>
            <p><strong>Estado en catálogo:</strong> {sync_badge}</p>
            <p><strong>Repositorio oficial:</strong> <code>{esc(item.get('source_repository'), 'Semilla local bootstrap')}</code></p>
            <p><strong>Revisión SHA verificada:</strong> <code>{esc((item.get('source_commit') or '')[:12] or None, 'N/A (bootstrap)')}</code></p>
            <p><strong>Última lectura desde el portal:</strong> {esc(format_spanish_date(item.get('fetched_at')))}</p>
            <p><strong>Última actualización declarada (<code>governance.content_updated_at</code>):</strong> {esc(format_spanish_date(item.get('content_updated_at'), 'Fecha de actualización aún no informada por el equipo'))}</p>
          </article>

          <article class="card">
            <h3>Contribución prevista al Atlas</h3>
            <ul>{"".join(atlas_links) if atlas_links else "<li>En definición</li>"}</ul>
          </article>

          <article class="card">
            <h3>Colaborar desde Google Antigravity (Fork / Clone)</h3>
            <p style="font-size:0.86rem;">Para aportar cambios o desplegar capas en el Geovisor de este equipo, crea un fork del repositorio específico de esta iniciativa:</p>
            <pre id="fork-{esc(pid)}" class="code-block"><code>{html.escape(fork_snippet)}</code></pre>
            <div class="card-footer">
              <button type="button" class="btn btn-outline btn-xs" data-copy-target="fork-{esc(pid)}">Copiar comandos</button>
              <a class="btn btn-teal btn-xs" href="{html.escape(ctx.site_url('ejercicio/'), quote=True)}">Ver ejercicio práctico →</a>
            </div>
          </article>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>Criterios de aceptación propuestos del PMV</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>Descripción</th><th>Estado</th></tr></thead>
          <tbody>{ac_rows}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <div class="callout callout-warn">
        <strong>Limitaciones y cautelas documentadas en el manifiesto</strong>
        <ul>{lim_li}</ul>
      </div>
    </section>

    {render_project_institutions_band(
        ctx,
        item.get("branding"),
        p,
        colaborar_href=(proj_site_url.rstrip("/") + "/colaborar/#anadir-actualizar-logos") if proj_site_url else None,
        logo_url_prefix=f"assets/img/projects/{pid}/",
    )}
    """

    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title=p["title"],
        active_nav="proyectos",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=snapshot_generated_at,
    )


def build_ejercicio_page(ctx: SiteContext, registry: dict[str, Any], catalog_snap: dict[str, Any]) -> str:
    colab_url = "https://colab.research.google.com/github/copernicuscentroamerica/clusterurbano/blob/main/web/assets/descargas/mancha_urbana_sentinel2_vmod01.ipynb"
    nb_dl = html.escape(ctx.site_url("assets/descargas/mancha_urbana_sentinel2_vmod01.ipynb"), quote=True)
    pptx_dl = html.escape(ctx.site_url("assets/descargas/scrum_aplicacion_geoespacial_Sesion_7_Previa_Encuentro.pptx"), quote=True)
    docx_dl = html.escape(ctx.site_url("assets/descargas/Manual_Guia_Antigravity_Proyectos_Copernicus.docx"), quote=True)

    colab_vectorize_snippet = """# Celda opcional al final de Google Colab: exportar mancha urbana a GeoJSON (EPSG:4326)
import geopandas as gpd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape

tif_path = f"salida_{CIUDAD_SLUG}_{ANIO}/construido_{CIUDAD_SLUG}_{ANIO}.tif"
with rasterio.open(tif_path) as src:
    arr = src.read(1)
    mask = arr == 1
    geoms = [
        {"geometry": shape(geom), "properties": {"clase": "construido", "anio": int(ANIO), "fuente": "Sentinel-2 L2A RF"}}
        for geom, val in shapes(arr, mask=mask, transform=src.transform)
        if val == 1
    ]
    gdf = gpd.GeoDataFrame.from_features(geoms, crs=src.crs).to_crs("EPSG:4326")
    # Filtrar polígonos menores a 500 m2 para aligerar la capa web
    gdf = gdf[gdf.to_crs(epsg=3857).area >= 500]
    out_geojson = f"salida_{CIUDAD_SLUG}_{ANIO}/mancha_urbana_{CIUDAD_SLUG}_{ANIO}.geojson"
    gdf.to_file(out_geojson, driver="GeoJSON")
    print("GeoJSON listo para geovisor/capas/:", out_geojson, "Polígonos:", len(gdf))"""

    gee_script_snippet = """// ============================================================================
// EJERCICIO PRÁCTICO EN GOOGLE EARTH ENGINE (GEE)
// Detección de Mancha Urbana con Sentinel-2 SR Harmonized (12 predictores + RF)
// Funciona con la MISMA cuenta de Google que usas en Google Antigravity y Colab
// ============================================================================

// 1. Definir Área de Estudio (ejemplo: Panamá Oeste - Arraiján / La Chorrera)
// Puedes cambiar las coordenadas al centroide de tu iniciativa (AMSS, La Carpio, etc.)
var centro = ee.Geometry.Point([-79.7553, 8.9451]);
var aoi = centro.buffer(8000).bounds();
Map.centerObject(aoi, 12);

// 2. Filtrar colección COPERNICUS/S2_SR_HARMONIZED y enmascarar nubes con SCL
// Nota verificada: S2_SR_HARMONIZED inicia el 2017-03-28
var ANIO = 2025;
function maskS2SCL(img) {
  var scl = img.select('SCL');
  // Conservar únicamente clases limpias: 4 (vegetación), 5 (suelo desnudo), 6 (agua)
  var mask = scl.eq(4).or(scl.eq(5)).or(scl.eq(6));
  return img.updateMask(mask).divide(10000);
}

var s2Col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(aoi)
  .filterDate(ANIO + '-01-01', ANIO + '-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .map(maskS2SCL);

print('Escenas Sentinel-2 disponibles:', s2Col.size());
var comp = s2Col.median().clip(aoi);

// 3. Calcular índices espectrales urbanos y de vegetación
var ndvi = comp.normalizedDifference(['B8', 'B4']).rename('NDVI');
var ndbi = comp.normalizedDifference(['B11', 'B8']).rename('NDBI');
var ndwi = comp.normalizedDifference(['B3', 'B8']).rename('NDWI');
var bsi = comp.expression(
  '((B11 + B4) - (B8 + B2)) / ((B11 + B4) + (B8 + B2) + 1e-6)',
  {'B2': comp.select('B2'), 'B4': comp.select('B4'), 'B8': comp.select('B8'), 'B11': comp.select('B11')}
).rename('BSI');

// Textura espacial local 3x3 sobre NDVI y NDBI
var ndviStd = ndvi.reduceNeighborhood({reducer: ee.Reducer.stdDev(), kernel: ee.Kernel.square(1)}).rename('NDVI_std3x3');
var ndbiStd = ndbi.reduceNeighborhood({reducer: ee.Reducer.stdDev(), kernel: ee.Kernel.square(1)}).rename('NDBI_std3x3');

var stack = comp.select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12'])
  .addBands([ndvi, ndbi, ndwi, bsi, ndviStd, ndbiStd]);

// 4. Etiquetas de entrenamiento desde GHSL Built-Up Surface o Google Open Buildings
var ghsl = ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/2020').clip(aoi);
var label = ghsl.gt(20).rename('clase').uint8();

var muestras = stack.addBands(label).stratifiedSample({
  numPoints: 1500,
  classBand: 'clase',
  region: aoi,
  scale: 10,
  seed: 42,
  geometries: true
});

// 5. Entrenar clasificador Random Forest (150 árboles) y clasificar
var bandas = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12', 'NDVI', 'NDBI', 'NDWI', 'BSI', 'NDVI_std3x3', 'NDBI_std3x3'];
var rf = ee.Classifier.smileRandomForest(150).train({
  features: muestras,
  classProperty: 'clase',
  inputProperties: bandas
});

var clasificado = stack.select(bandas).classify(rf).rename('construido');
Map.addLayer(comp, {bands: ['B4', 'B3', 'B2'], min: 0.02, max: 0.30}, 'Sentinel-2 RGB');
Map.addLayer(clasificado.selfMask(), {palette: ['#d95f02']}, 'Mancha Urbana RF (10 m)');

// 6. Vectorizar polígonos construidos y exportar a Google Drive como GeoJSON (EPSG:4326)
var vectores = clasificado.selfMask().reduceToVectors({
  geometry: aoi,
  crs: 'EPSG:4326',
  scale: 20,
  geometryType: 'polygon',
  eightConnected: true,
  maxPixels: 1e9
});

Export.table.toDrive({
  collection: vectores,
  description: 'mancha_urbana_s2_' + ANIO + '_geojson',
  fileFormat: 'GeoJSON'
});

// 7. Exportar también el raster como Cloud Optimized GeoTIFF (COG)
Export.image.toDrive({
  image: clasificado.uint8(),
  description: 'construido_s2_' + ANIO + '_cog',
  region: aoi,
  scale: 10,
  crs: 'EPSG:4326',
  maxPixels: 1e9,
  formatOptions: {cloudOptimized: true}
});"""

    antigravity_prompt_snippet = """Acabo de ejecutar el ejercicio práctico de Mancha Urbana con Sentinel-2 (en Google Colab / Google Earth Engine) y descargué los archivos resultantes en mi computadora.
Por favor ayúdame a integrarlos en este repositorio siguiendo las reglas de gobernanza:
1. Verifica con `git remote -v` que estamos en mi fork personal y crea una rama nueva llamada `ejercicio/mancha-urbana-s2`.
2. Copia el archivo vectorial `mancha_urbana_*.geojson` (o el COG `construido_*.tif`) a la carpeta `geovisor/capas/`, comprobando que esté en coordenadas `EPSG:4326` y no contenga datos personales.
3. Registra la nueva capa en `geovisor/layers.json` con estado `en_revision`, estilo visible y una nota de cautela explicando que proviene del ejercicio supervisado con Sentinel-2 L2A (Random Forest, 10 m) sujeto a validación institucional.
4. Actualiza `governance.content_updated_at` en `project.json` con la fecha de hoy (y su entrada en `provenance.statements`) y añade en `content/metodologia.md` un resumen de las métricas obtenidas (F1, ROC-AUC, hectáreas detectadas).
5. Ejecuta `python scripts/build_site.py --output site`, `python scripts/validate.py --source` y `python scripts/validate.py --site site`, muéstrame `git status` y `git diff` para mi revisión antes de hacer commit."""

    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <span class="badge badge-lime">Guía de incorporación práctica · Sesión 7 y Taller Presencial</span>
          <span class="badge badge-country">Google Antigravity + Google Colab + Google Earth Engine</span>
        </div>
        <h1>Ejercicio práctico de principio a fin: Mancha Urbana con Sentinel-2</h1>
        <p class="hero-lead">Aprende el flujo completo de la Comunidad de Práctica: clona el repositorio de tu iniciativa en Google Antigravity, ejecuta el modelo de detección de mancha urbana en <strong>Google Colab</strong> o en <strong>Google Earth Engine</strong> usando tu <strong>misma cuenta de Google</strong>, despliega las capas resultantes en el Geovisor y envía tu primer Pull Request.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{html.escape(colab_url, quote=True)}" target="_blank" rel="noopener noreferrer">Abrir cuaderno en Google Colab ↗</a>
          <a class="btn btn-teal" href="{nb_dl}" download="mancha_urbana_sentinel2_vmod01.ipynb">Descargar .ipynb (Colab)</a>
          <a class="btn btn-outline-light" href="{pptx_dl}" download="scrum_aplicacion_geoespacial_Sesion_7_Previa_Encuentro.pptx">Descargar presentación Scrum (.pptx)</a>
          <a class="btn btn-outline-light" href="{docx_dl}" download="Manual_Guia_Antigravity_Proyectos_Copernicus.docx">Descargar Manual Word v1.1 (.docx)</a>
        </div>
      </div>
    </section>
    """

    body = f"""
    <div class="callout">
      <strong>Ventaja clave: una sola cuenta de Google para todo tu entorno de trabajo</strong>
      <span><strong>Google Antigravity</strong>, <strong>Google Colaboratory (Colab)</strong> y <strong>Google Earth Engine (GEE)</strong> son plataformas de Google. Puedes iniciar sesión en las tres con la <strong>misma cuenta de Google</strong> que utilizas en Antigravity, lo que te permite pasar del análisis satelital en la nube a la edición y publicación de tu repositorio sin configurar credenciales externas complejas.</span>
    </div>

    <section class="section">
      <h2>1. El recorrido completo de colaboración en 5 pasos</h2>
      <div class="grid-3">
        <article class="card">
          <span class="badge badge-country">Paso 1 · Preparar tu copia</span>
          <h3>Fork y clonación en Antigravity</h3>
          <p>Entra a la ficha de tu iniciativa en <a href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">Proyectos</a>, crea tu copia personal (<em>fork</em>) en GitHub y clónala en tu computadora desde Google Antigravity.</p>
        </article>
        <article class="card">
          <span class="badge badge-country">Paso 2 · Procesar imágenes</span>
          <h3>Ejecutar análisis en Colab o GEE</h3>
          <p>Con tu misma cuenta de Google, ejecuta el flujo de <strong>Mancha Urbana con Sentinel-2</strong> en Google Colab (Ruta A) o en Google Earth Engine (Ruta B) para la ciudad de tu proyecto.</p>
        </article>
        <article class="card">
          <span class="badge badge-country">Paso 3 · Integrar en Geovisor</span>
          <h3>Guardar en <code>geovisor/capas/</code></h3>
          <p>Descarga tu GeoJSON o GeoTIFF COG, colócalo en <code>geovisor/capas/</code> y pídele al agente de Antigravity que lo registre en <code>geovisor/layers.json</code> y actualice <code>proyecto.geolibre.json</code>.</p>
        </article>
        <article class="card">
          <span class="badge badge-country">Paso 4 · Validar y revisar</span>
          <h3>Ejecutar validadores y <code>git diff</code></h3>
          <p>Comprueba que <code>validate.py --source</code> y <code>validate.py --site site</code> terminen con <code>[OK]</code> y revisa tus cambios antes de subir tu rama a <code>origin</code>.</p>
        </article>
        <article class="card">
          <span class="badge badge-country">Paso 5 · Enviar y publicar</span>
          <h3>Pull Request y seguimiento regional</h3>
          <p>Abre tu Pull Request hacia el repositorio oficial, enlázalo a tu tarea en <a href="{html.escape(ctx.site_url('seguimiento/'), quote=True)}">Seguimiento</a> y comprueba la publicación en el Geovisor tras su aprobación.</p>
        </article>
        <article class="card">
          <span class="badge badge-ok">Marco ágil Scrum (Sesión 7)</span>
          <h3>Delimitación del PMV y Sprints</h3>
          <p>Consulta la presentación <em>Scrum para Aplicaciones Geoespaciales (Sesión 7 Previa al Encuentro)</em> para organizar historias de usuario (<code>US-GIS</code>), criterios de aceptación y entregables del taller.</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="{pptx_dl}" download="scrum_aplicacion_geoespacial_Sesion_7_Previa_Encuentro.pptx">Descargar presentación .pptx</a>
          </div>
        </article>
      </div>
    </section>

    <section class="section">
      <h2>2. Ruta A — Implementación paso a paso en Google Colab (Cuaderno Jupyter)</h2>
      <p>El cuaderno oficial <code>mancha_urbana_sentinel2_vmod01.ipynb</code> ejecuta un flujo reproducible de principio a fin utilizando escenas abiertas de <strong>Sentinel-2 L2A</strong> y aprendizaje automático (<em>Random Forest</em>) sin requerir llaves de API de pago.</p>

      <div class="table-wrap" style="margin:1rem 0;">
        <table>
          <thead>
            <tr>
              <th>Sección del cuaderno</th>
              <th>Qué hace técnicamente</th>
              <th>Parámetros o resultados clave</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Secciones 1 y 2</strong><br>Entorno y configuración</td>
              <td>Instala las librerías geoespaciales en la máquina virtual de Colab (<code>pystac-client</code>, <code>planetary-computer</code>, <code>odc-stac</code>, <code>rioxarray</code>, <code>scikit-learn</code>, <code>overturemaps</code>, <code>folium</code>) y define los parámetros de corrida.</td>
              <td><code>CIUDAD_OBJETIVO = "San Salvador"</code> (o tu ciudad), <code>ANIO = 2025</code>, <code>MAX_NUBES = 20</code>, <code>BUFFER_M = 10000</code>, <code>RESOLUCION = 10</code> m.</td>
            </tr>
            <tr>
              <td><strong>Sección 3</strong><br>Catálogo de ciudades de CA y RD</td>
              <td>Incluye un catálogo integrado de <strong>75 ciudades principales</strong> y un diccionario ampliado de <strong>779 poblados</strong> de Guatemala, El Salvador, Honduras, Nicaragua, Costa Rica, Panamá y República Dominicana.</td>
              <td>Construye automáticamente el recuadro delimitador (<em>bounding box</em>) en <code>EPSG:4326</code> y la proyección métrica UTM correspondiente.</td>
            </tr>
            <tr>
              <td><strong>Secciones 4 y 5</strong><br>Compuesto Sentinel-2 y 12 predictores</td>
              <td>Consulta el catálogo STAC de Sentinel-2 L2A, enmascara nubes, sombras y cirros usando la banda <code>SCL</code> (conservando clases limpias <code>4, 5, 6</code>), calcula la mediana anual y genera <strong>12 variables predictoras</strong>.</td>
              <td>6 bandas (<code>B02, B03, B04, B08, B11, B12</code>) + 4 índices (<code>NDVI, NDBI, NDWI, BSI</code>) + 2 texturas locales 3×3 (<code>NDVI_std3x3, NDBI_std3x3</code>).</td>
            </tr>
            <tr>
              <td><strong>Sección 6</strong><br>Etiquetas de edificaciones</td>
              <td>Descarga huellas de edificaciones abiertas desde <strong>Overture Maps</strong> (con respaldo automático en Microsoft/Google Open Buildings y OpenStreetMap) y las rasteriza a la grilla de 10 m.</td>
              <td>Máscara binaria de referencia (<code>1 = edificado</code>, <code>0 = no edificado</code>) para entrenamiento supervisado.</td>
            </tr>
            <tr>
              <td><strong>Secciones 7 y 8</strong><br>Random Forest y validación</td>
              <td>Toma una muestra estratificada balanceada, divide en entrenamiento (75 %) y prueba (25 %), entrena un <code>RandomForestClassifier</code> de 150 árboles y evalúa métricas independientes antes de predecir en toda el área.</td>
              <td>Genera matriz de confusión, precisión, exhaustividad, <strong>F1-Score</strong>, curva <strong>ROC-AUC</strong> e importancia de variables.</td>
            </tr>
            <tr>
              <td><strong>Secciones 9 y 10</strong><br>Mapas y exportación de archivos</td>
              <td>Despliega el mapa interactivo con control de capas y empaqueta todos los resultados en la carpeta <code>salida_{{ciudad}}_{{anio}}/</code> lista para descargar desde el panel izquierdo de archivos de Colab.</td>
              <td><code>probabilidad_{{ciudad}}_{{anio}}.tif</code> (0–100 %), <code>construido_{{ciudad}}_{{anio}}.tif</code> (binario), <code>resumen_{{ciudad}}_{{anio}}.csv</code> y gráficos <code>.png</code>.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h3>Cómo exportar también un polígono ligero <code>.geojson</code> desde Colab para carga directa en el Geovisor</h3>
      <p>Además de los archivos GeoTIFF (<code>.tif</code>), puedes añadir esta celda al final del cuaderno en Google Colab para vectorizar la mancha urbana detectada como archivo <code>.geojson</code> en <code>EPSG:4326</code> y cargarlo de forma nativa e inmediata en el mapa integrado del proyecto:</p>
      <pre id="code-colab-vec" class="code-block"><code>{html.escape(colab_vectorize_snippet)}</code></pre>
      <div style="display:flex;gap:0.6rem;flex-wrap:wrap;margin-top:0.5rem;">
        <button type="button" class="btn btn-outline btn-xs" data-copy-target="code-colab-vec">Copiar celda GeoJSON para Colab</button>
        <a class="btn btn-primary btn-xs" href="{html.escape(colab_url, quote=True)}" target="_blank" rel="noopener noreferrer">Abrir cuaderno en Google Colab ↗</a>
      </div>
    </section>

    <section class="section">
      <h2>3. Ruta B — Implementación equivalente en Google Earth Engine (GEE)</h2>
      <p>Si tu equipo trabaja con scripts en <strong>Google Earth Engine</strong> (como los casos de Panamá Oeste, AMSS, Distrito Central o Guatemala Metropolitana), puedes ejecutar el mismo análisis entrando a <a href="https://code.earthengine.google.com/" target="_blank" rel="noopener noreferrer">code.earthengine.google.com ↗</a> con la <strong>misma cuenta de Google</strong> que usas en Antigravity.</p>

      <div class="grid-2" style="margin-bottom:1rem;">
        <article class="card">
          <h3>Opción B1 · Editor de Código Web de GEE (JavaScript)</h3>
          <ol style="padding-left:1.2rem;font-size:0.9rem;">
            <li>Ingresa a <a href="https://code.earthengine.google.com/" target="_blank" rel="noopener noreferrer">code.earthengine.google.com ↗</a> con tu cuenta de Google.</li>
            <li>Pega el script de abajo en el panel central y ajusta las coordenadas de <code>centro</code> al ámbito de tu iniciativa (o usa tus polígonos piloto).</li>
            <li>Haz clic en <strong>Run</strong> para inspeccionar en el mapa el compuesto Sentinel-2 y la capa <code>Mancha Urbana RF (10 m)</code>.</li>
            <li>En la pestaña derecha <strong>Tasks</strong>, pulsa <strong>Run</strong> sobre <code>mancha_urbana_s2_2025_geojson</code> (vectorial para el visor integrado) y <code>construido_s2_2025_cog</code> (GeoTIFF optimizado para GeoLibre Studio) para descargarlos desde tu Google Drive.</li>
          </ol>
        </article>
        <article class="card">
          <h3>Opción B2 · API de Python de GEE desde Colab o Antigravity</h3>
          <ol style="padding-left:1.2rem;font-size:0.9rem;">
            <li>Tanto en Google Colab como en la terminal de Google Antigravity puedes autenticar Earth Engine con tu misma cuenta ejecutando:<br><code>import ee; ee.Authenticate(); ee.Initialize(project='tu-proyecto-cloud')</code></li>
            <li>Esto te permite combinar el catálogo masivo de GEE (<code>COPERNICUS/S2_SR_HARMONIZED</code>, <code>COPERNICUS/S1_GRD</code>, <code>GOOGLE/DYNAMICWORLD/V1</code>) con librerías de Python (<code>geopandas</code>, <code>scikit-learn</code>) y guardar el archivo directamente en <code>geovisor/capas/</code>.</li>
          </ol>
        </article>
      </div>

      <pre id="code-gee-script" class="code-block"><code>{html.escape(gee_script_snippet)}</code></pre>
      <div style="display:flex;gap:0.6rem;flex-wrap:wrap;margin-top:0.5rem;">
        <button type="button" class="btn btn-outline btn-xs" data-copy-target="code-gee-script">Copiar script para Google Earth Engine</button>
        <a class="btn btn-teal btn-xs" href="https://code.earthengine.google.com/" target="_blank" rel="noopener noreferrer">Abrir GEE Code Editor ↗</a>
      </div>
    </section>

    <section class="section">
      <h2>4. Cómo integrar los resultados en tu proyecto con Google Antigravity</h2>
      <p>Una vez que tengas los archivos generados por <strong>Google Colab</strong> o por <strong>Google Earth Engine</strong> en tu computadora, abre tu repositorio clonado en <strong>Google Antigravity</strong> y envíale la siguiente instrucción al agente de IA:</p>
      <pre id="prompt-ejercicio-agy" class="code-block"><code>{html.escape(antigravity_prompt_snippet)}</code></pre>
      <div style="display:flex;gap:0.6rem;flex-wrap:wrap;margin-top:0.5rem;">
        <button type="button" class="btn btn-primary btn-xs" data-copy-target="prompt-ejercicio-agy">Copiar prompt para Google Antigravity</button>
      </div>

      <div class="table-wrap" style="margin-top:1.25rem;">
        <table>
          <thead>
            <tr>
              <th>Archivo generado en el ejercicio</th>
              <th>Dónde colocarlo en tu repositorio</th>
              <th>Cómo se visualiza en el Geovisor del proyecto</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>mancha_urbana_{{ciudad}}_{{anio}}.geojson</code><br>(Polígonos vectoriales en <code>EPSG:4326</code>)</td>
              <td><code>geovisor/capas/</code> y registrado en <code>geovisor/layers.json</code></td>
              <td>Se dibuja <strong>automáticamente en el visor integrado (MapLibre)</strong> y también se empaqueta dentro de <code>proyecto.geolibre.json</code> para abrirse en <strong>GeoLibre Studio</strong>.</td>
            </tr>
            <tr>
              <td><code>construido_{{ciudad}}_{{anio}}.tif</code> o <code>probabilidad_{{ciudad}}_{{anio}}.tif</code><br>(GeoTIFF / COG)</td>
              <td><code>geovisor/capas/</code> (si ≤ 25 MB) o servicio HTTPS externo</td>
              <td>Aparece listado en la pestaña <strong><code>Carpeta repo</code></strong> del Geovisor; al pulsar <strong>Abrir en GeoLibre Studio ↗</strong> se transfiere mediante <code>?data=&lt;url&gt;</code> a <code>web.geolibre.app</code>.</td>
            </tr>
            <tr>
              <td><code>resumen_{{ciudad}}_{{anio}}.csv</code><br>(Métricas F1, ROC-AUC, área en ha)</td>
              <td>Documentado en <code>content/metodologia.md</code> y <code>content/pmv.md</code></td>
              <td>Se presenta en la ficha pública de la iniciativa con su nota metodológica y estado de revisión técnica (<code>en_revision</code>).</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    """

    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Ejercicio práctico: Mancha Urbana con Sentinel-2 (Colab + GEE + Antigravity)",
        active_nav="ejercicio",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=catalog_snap.get("generated_at"),
    )


def build_atlas_index_page(ctx: SiteContext, registry: dict[str, Any], atlas_snap: dict[str, Any], catalog_snap: dict[str, Any]) -> str:
    products = atlas_snap.get("products", [])
    proj_by_id = {it["project"]["id"]: it["project"] for it in catalog_snap.get("projects", [])}

    types = sorted({p["product_type"] for p in products})
    statuses = sorted({p["publication_status"] for p in products})
    type_opts = '<option value="all">Todos los tipos</option>' + "".join(f'<option value="{esc(t)}">{esc(t)}</option>' for t in types)
    st_opts = '<option value="all">Todos los estados</option>' + "".join(f'<option value="{esc(s)}">{esc(s)}</option>' for s in statuses)

    cards = []
    for ap in products:
        pid = ap["project_id"]
        p_info = proj_by_id.get(pid, {})
        c_name = p_info.get("country", {}).get("name", pid)
        c_code = p_info.get("country", {}).get("code", "")
        detail_href = html.escape(ctx.site_url(f"atlas/{ap['id']}/"), quote=True)
        search_txt = f"{ap['title']} {ap['summary']} {c_name} {ap['coverage']['label']} {ap.get('governance', {}).get('institution', '')}"
        cards.append(
            f"""
            <article class="card" data-filter-item
                     data-ptype="{esc(ap['product_type'])}"
                     data-pstatus="{esc(ap['publication_status'])}"
                     data-search-text="{esc(search_txt)}">
              <div style="display:flex;flex-wrap:wrap;gap:0.4rem;justify-content:space-between;">
                <span class="badge badge-country">{esc(c_name)} ({esc(c_code)})</span>
                {badge_html(ap['publication_status'], 'Catálogo')}
              </div>
              <h3><a href="{detail_href}" style="color:var(--c-navy);text-decoration:none;">{esc(ap['title'])}</a></h3>
              <p>{esc(ap['summary'])}</p>
              <p style="font-size:0.84rem;color:var(--c-text-muted);">
                <strong>Tipo:</strong> <code>{esc(ap['product_type'])}</code> ·
                <strong>Resolución:</strong> {esc(ap['coverage'].get('spatial_resolution'), 'Por definir')}
              </p>
              <div class="card-footer">
                <a class="btn btn-teal btn-xs" href="{detail_href}">Ver metadatos completos →</a>
                {badge_html(ap['validation']['state'], 'Validación')}
              </div>
            </article>
            """
        )

    hero = """
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <span class="badge badge-lime">Atlas Urbano Regional</span>
        </div>
        <h1>Catálogo de productos y contribuciones previstas</h1>
        <p class="hero-lead">Espacio común para documentar, revisar y enlazar capas, indicadores y visores de las iniciativas, conservando sus escalas, definiciones y limitaciones antes de realizar comparaciones regionales.</p>
      </div>
    </section>
    """

    body = f"""
    <div class="callout">
      <strong>Regla metodológica de comparabilidad regional</strong>
      <span>Dos indicadores solo son directamente comparables cuando comparten definición, unidad, periodo, cobertura y método de agregación documentados. Los registros en estado <em>Propuesto</em> representan contribuciones previstas por las fichas iniciales; no son productos validados ni publicados aún.</span>
    </div>

    <section class="section" data-catalog-atlas>
      <div class="filter-bar" role="search" aria-label="Filtrar catálogo del Atlas">
        <div class="filter-field" style="flex:2;">
          <label for="f-atlas-q">Buscar por territorio, institución o indicador</label>
          <input id="f-atlas-q" type="search" placeholder="Ej. huella urbana, brecha catastral, exposición, Santiago..." data-filter-search>
        </div>
        <div class="filter-field">
          <label for="f-atlas-type">Tipo de producto</label>
          <select id="f-atlas-type" data-filter-select="ptype">{type_opts}</select>
        </div>
        <div class="filter-field">
          <label for="f-atlas-st">Estado de publicación</label>
          <select id="f-atlas-st" data-filter-select="pstatus">{st_opts}</select>
        </div>
        <div>
          <button type="button" class="btn btn-outline" data-filter-reset>Restablecer</button>
        </div>
      </div>

      <p style="font-size:0.88rem;color:var(--c-text-muted);margin-bottom:1rem;" data-filter-count>{len(products)} de {len(products)} registros mostrados</p>

      <div class="callout callout-warn hidden" data-filter-empty>
        <strong>Sin coincidencias en el Atlas</strong>
        <span>Restablece los filtros para explorar todas las contribuciones previstas y publicadas.</span>
      </div>

      <div class="grid-2">
        {"".join(cards)}
      </div>
    </section>
    """

    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Atlas Urbano Regional",
        active_nav="atlas",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=atlas_snap.get("generated_at"),
    )


def build_atlas_detail_page(ctx: SiteContext, registry: dict[str, Any], ap: dict[str, Any], parent_proj: dict[str, Any] | None, snapshot_generated_at: str | None) -> str:
    pid = ap["project_id"]
    proj_href = html.escape(ctx.site_url(f"proyectos/{pid}/"), quote=True)
    proj_site_url = parent_proj["links"].get("website") if parent_proj else None
    geovisor_link = (
        f'<a class="btn btn-primary" href="{html.escape(proj_site_url.rstrip("/") + "/aplicacion/", quote=True)}" target="_blank" rel="noopener noreferrer">Abrir Geovisor GeoLibre del proyecto ↗</a>'
        if proj_site_url and proj_site_url.startswith("https://")
        else '<span class="btn-disabled">Geovisor remoto pendiente de publicación</span>'
    )

    outs = ap["outputs"]
    viewer_btn = render_link_or_pending(outs.get("viewer_url"), "Visor directo del producto", "Visor directo aún no publicado")
    dl_btn = render_link_or_pending(outs.get("download_url"), "Descargar producto", "Descarga aún no publicada")

    lim_li = "".join(f"<li>{esc(l)}</li>" for l in ap.get("limitations", [])) or "<li>Por detallar durante revisión técnica.</li>"

    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <a href="{html.escape(ctx.site_url('atlas/'), quote=True)}" style="color:#FFFFFF;font-weight:600;">← Catálogo del Atlas</a>
          {badge_html(ap['publication_status'], 'Publicación')}
          {badge_html(ap['validation']['state'], 'Validación')}
        </div>
        <h1>{esc(ap['title'])}</h1>
        <p class="hero-lead">{esc(ap['summary'])}</p>
        <div class="hero-actions">
          <a class="btn btn-teal" href="{proj_href}">Ver iniciativa responsable ({esc(pid)})</a>
          {geovisor_link}
        </div>
      </div>
    </section>
    """

    cov = ap["coverage"]
    temp = ap["temporal"]
    ind = ap["indicator"]
    gov = ap["governance"]
    lic = ap["license"]

    body = f"""
    <section class="section">
      <div class="table-wrap">
        <table>
          <tbody>
            <tr><th>Identificador de producto</th><td><code>{esc(ap['id'])}</code></td></tr>
            <tr><th>Iniciativa responsable</th><td><a href="{proj_href}"><code>{esc(pid)}</code> — {esc(parent_proj['title'] if parent_proj else pid)}</a></td></tr>
            <tr><th>Tipo de producto</th><td><code>{esc(ap['product_type'])}</code></td></tr>
            <tr><th>Cobertura territorial</th><td>{esc(cov['label'])}</td></tr>
            <tr><th>Resolución espacial / escala</th><td>{esc(cov.get('spatial_resolution'), 'Pendiente de confirmar')} (denominador de escala: {esc(cov.get('scale_denominator'), 'no aplica / por definir')})</td></tr>
            <tr><th>Periodo temporal</th><td>Inicio: {esc(temp.get('start'), 'Por confirmar')} · Fin: {esc(temp.get('end'), 'Por confirmar')} · Fecha referencia: {esc(temp.get('reference_date'), 'Por confirmar')}</td></tr>
            <tr><th>Indicador y unidad</th><td><strong>{esc(ind.get('name'), 'Por definir')}</strong> · Unidad: <code>{esc(ind.get('unit'), 'por definir')}</code></td></tr>
            <tr><th>Definición y regla de agregación</th><td>{esc(ind.get('definition'), '—')}<br><strong>Agregación:</strong> {esc(ind.get('aggregation'), '—')}</td></tr>
            <tr><th>Método y versión</th><td>{esc(ap['method'].get('description'), 'En documentación')} (versión: <code>{esc(ap['method'].get('version'), 'por definir')}</code>)</td></tr>
            <tr><th>Institución y mantenimiento</th><td>{esc(gov.get('institution'), 'Por confirmar')} · Responsable: {esc(gov.get('maintainer'), 'Responsable por confirmar')} · Frecuencia: {esc(gov.get('update_frequency'), 'Por confirmar')}</td></tr>
            <tr><th>Licencia y reutilización</th><td>{esc(lic.get('name'), 'Licencia pendiente de confirmar')} — {esc(lic.get('reuse_note'), 'Condiciones de reutilización por confirmar')}</td></tr>
          </tbody>
        </table>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:0.75rem;margin-top:1rem;">
        {viewer_btn}
        {dl_btn}
      </div>
    </section>

    <section class="section">
      <div class="callout callout-warn">
        <strong>Limitaciones y condiciones de interpretación</strong>
        <ul>{lim_li}</ul>
      </div>
    </section>
    """

    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title=ap["title"],
        active_nav="atlas",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=snapshot_generated_at,
    )


def build_seguimiento_page(
    ctx: SiteContext,
    registry: dict[str, Any],
    progress_snap: dict[str, Any],
    catalog_snap: dict[str, Any],
    board_cfg: dict[str, Any],
) -> str:
    overall = progress_snap.get("overall_state", "not_initialized")
    gen_at = format_spanish_date(progress_snap.get("generated_at"), "Seguimiento pendiente de primera sincronización")
    proj_titles = {it["project"]["id"]: SHORT_CARD_TITLES.get(it["project"]["id"], it["project"]["title"]) for it in catalog_snap.get("projects", [])}

    board_url = board_cfg.get("project_url")
    board_btn = render_link_or_pending(
        board_url,
        "Abrir tablero público GitHub Project #1",
        "Tablero GitHub Project en preparación",
        "btn btn-primary",
    )

    proj_rows = []
    all_tasks = []
    for p_entry in progress_snap.get("projects", []):
        pid = p_entry["project_id"]
        m = p_entry["metrics"]
        fmt = lambda v: "—" if v is None else str(v)
        proj_href = html.escape(ctx.site_url(f"proyectos/{pid}/"), quote=True)
        new_issue_href = f"https://github.com/copernicuscentroamerica/urbano-{pid}/issues/new?template=tarea_pmv.yml"
        sync_lbl = "Sincronizado" if p_entry["sync_state"] == "ok" else p_entry["sync_state"]
        proj_rows.append(
            f"<tr>"
            f'<td><a href="{proj_href}"><strong>{esc(proj_titles.get(pid, pid))}</strong></a><br><span style="font-size:0.78rem;color:var(--c-text-muted);"><code>{esc(pid)}</code> · <a href="{html.escape(new_issue_href, quote=True)}" target="_blank" rel="noopener noreferrer">Nueva tarea ↗</a></span></td>'
            f'<td><span class="badge badge-ok">{esc(sync_lbl)}</span></td>'
            f"<td><strong>{fmt(m['open_tasks'])}</strong></td>"
            f"<td>{fmt(m['in_review_tasks'])}</td>"
            f"<td>{fmt(m['completed_tasks'])}</td>"
            f"<td>{fmt(m['blocked_tasks'])}</td>"
            f"<td>{esc(format_spanish_date(p_entry.get('last_success_at'), '—'))}</td>"
            f"</tr>"
        )
        for t in p_entry.get("tasks", []):
            all_tasks.append(t)

    tasks_section = ""
    if all_tasks:
        t_cards = []
        for t in all_tasks:
            blk_badge = '<span class="badge badge-danger">Bloqueado</span>' if t.get("blocked") else ""
            prio_badge = f'<span class="badge badge-country">Prioridad: {esc(t["priority"])}</span>' if t.get("priority") else ""
            iter_badge = f'<span class="badge badge-declarado">{esc(t["iteration"])}</span>' if t.get("iteration") else ""
            wf_style = "ok" if t["workflow_status"] == "Terminado" else ("en_revision" if t["workflow_status"] in ("En curso", "En revisión") else "pendiente")
            ev_links = ""
            if t.get("evidence_urls"):
                ev_items = " · ".join(
                    f'<a href="{html.escape(u, quote=True)}" target="_blank" rel="noopener noreferrer">Evidencia {idx + 1} ↗</a>'
                    for idx, u in enumerate(t["evidence_urls"][:3])
                )
                ev_links = f'<p style="font-size:0.82rem;margin:0.25rem 0 0;"><strong>Evidencia vinculada:</strong> {ev_items}</p>'

            t_cards.append(
                f"""
                <article class="card" data-filter-item
                         data-tproj="{esc(t['project_id'])}"
                         data-tstatus="{esc(t['workflow_status'])}"
                         data-tblocked="{'si' if t.get('blocked') else 'no'}"
                         data-search-text="{esc(t['task_id'] + ' ' + t['title'] + ' ' + t['project_id'] + ' ' + (t.get('workflow_status') or ''))}">
                  <div style="display:flex;justify-content:space-between;gap:0.4rem;flex-wrap:wrap;">
                    <code>{esc(t['task_id'])}</code>
                    <span style="display:flex;gap:0.35rem;flex-wrap:wrap;">{badge_html(wf_style, t['workflow_status'])} {prio_badge} {iter_badge} {blk_badge}</span>
                  </div>
                  <h3><a href="{html.escape(t['issue_url'], quote=True)}" target="_blank" rel="noopener noreferrer">{esc(t['title'])} ↗</a></h3>
                  <p style="font-size:0.83rem;color:var(--c-text-muted);margin:0;">Iniciativa: <code>{esc(t['project_id'])}</code> · Issue: <code>{esc(t['issue_state'])}</code> · Actualizada: {esc(format_spanish_date(t['source_updated_at']))}</p>
                  {ev_links}
                </article>
                """
            )
        p_opts = '<option value="all">Todas las iniciativas (8)</option>' + "".join(
            f'<option value="{esc(p["project_id"])}">{esc(proj_titles.get(p["project_id"], p["project_id"]))}</option>'
            for p in progress_snap.get("projects", [])
        )
        tasks_section = f"""
        <section class="section" data-catalog-progress>
          <h2>Tarjetas operativas sincronizadas ({len(all_tasks)})</h2>
          <div class="filter-bar">
            <div class="filter-field" style="flex:2;">
              <label for="f-tsk-q">Buscar tarea por título o código</label>
              <input id="f-tsk-q" type="search" placeholder="Ej. Sentinel-2, KML, catastro, geovisor, TS-101..." data-filter-search>
            </div>
            <div class="filter-field">
              <label for="f-tsk-p">Iniciativa</label>
              <select id="f-tsk-p" data-filter-select="tproj">{p_opts}</select>
            </div>
            <div class="filter-field">
              <label for="f-tsk-st">Estado de flujo</label>
              <select id="f-tsk-st" data-filter-select="tstatus">
                <option value="all">Todos los estados</option>
                <option value="Por hacer">Por hacer</option>
                <option value="En curso">En curso</option>
                <option value="En revisión">En revisión</option>
                <option value="Terminado">Terminado</option>
              </select>
            </div>
            <div class="filter-field">
              <label for="f-tsk-b">Bloqueos</label>
              <select id="f-tsk-b" data-filter-select="tblocked">
                <option value="all">Todas</option>
                <option value="si">Solo con bloqueo</option>
              </select>
            </div>
            <button type="button" class="btn btn-outline" data-filter-reset>Restablecer</button>
          </div>
          <p style="font-size:0.88rem;color:var(--c-text-muted);margin-bottom:1rem;" data-filter-count>{len(all_tasks)} de {len(all_tasks)} tareas mostradas</p>
          <div class="grid-2">{"".join(t_cards)}</div>
        </section>
        """

    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <span class="badge badge-lime">Operación comunitaria</span>
          <span class="badge badge-ok">Datos sincronizados ({len(all_tasks)} tareas activas)</span>
        </div>
        <h1>Seguimiento de compromisos, tareas del PMV y bloqueos</h1>
        <p class="hero-lead">Vista pública sincronizada con los Issues de las 8 iniciativas y el tablero público regional <strong>GitHub Project #1</strong>. El cierre de una tarea técnica nunca se interpreta automáticamente como aceptación del PMV ni validación institucional.</p>
        <div class="hero-actions">
          {board_btn}
          <a class="btn btn-outline-light" href="https://github.com/copernicuscentroamerica/clusterurbano/issues/new?template=bloqueo_apoyo.yml" target="_blank" rel="noopener noreferrer">Reportar bloqueo o pedir apoyo ↗</a>
        </div>
      </div>
    </section>
    """

    body = f"""
    <div class="callout">
      <strong>Sincronización operativa verificada · Última actualización: {esc(gen_at)}</strong>
      <span>El exportador (<code>scripts/export_progress.py</code>) consulta los Issues de cada repositorio canónico <code>urbano-{{id}}</code> y los campos del tablero público <a href="https://github.com/users/copernicuscentroamerica/projects/1" target="_blank" rel="noopener noreferrer">GitHub Project #1 ↗</a> mediante GraphQL. Los cierres marcados como <code>not_planned</code> se excluyen del conteo de tareas terminadas.</span>
    </div>

    <section class="section">
      <h2>Resumen operativo por iniciativa</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Iniciativa</th>
              <th>Estado consulta</th>
              <th>Abiertas</th>
              <th>En revisión</th>
              <th>Terminadas</th>
              <th>Bloqueadas</th>
              <th>Última lectura válida</th>
            </tr>
          </thead>
          <tbody>{"".join(proj_rows)}</tbody>
        </table>
      </div>
    </section>

    {tasks_section}

    <section class="section">
      <h2>Fuente operativa de cada campo en el seguimiento</h2>
      <p>Para garantizar trazabilidad tanto si trabajas desde los Issues de tu repositorio como desde el tablero regional <strong>GitHub Project #1</strong>, cada atributo sigue una regla única y documentada:</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Campo en el portal</th>
              <th>Fuente principal en GitHub</th>
              <th>Respaldo automático (etiquetas / formulario)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Estado de flujo</strong> (<code>Por hacer</code>, <code>En curso</code>, <code>En revisión</code>, <code>Terminado</code>)</td>
              <td>Cierre de la Issue (<code>CLOSED</code> → <code>Terminado</code>) y columna <code>Status</code> en <strong>GitHub Project #1</strong></td>
              <td>Etiquetas en la Issue: <code>en-revision</code>, <code>en-curso</code> o <code>tipo:tarea</code></td>
            </tr>
            <tr>
              <td><strong>Condición de bloqueo</strong> (<code>Bloqueado</code>)</td>
              <td>Etiqueta <code>bloqueado</code> en la Issue (conservando su columna actual en el tablero para visibilizar dónde ocurrió el bloqueo)</td>
              <td>Formulario <em>Bloqueo o solicitud de apoyo</em></td>
            </tr>
            <tr>
              <td><strong>Prioridad e Iteración</strong> (<code>Alta</code>, <code>Media</code>, <code>Baja</code> / Sprint)</td>
              <td>Campos <code>Priority</code> e <code>Iteration</code> en <strong>GitHub Project #1</strong></td>
              <td>Etiquetas <code>prioridad:alta</code>, <code>prioridad:media</code>, <code>prioridad:baja</code> o campo <code>### Prioridad</code> del Issue Form</td>
            </tr>
            <tr>
              <td><strong>Evidencia verificable</strong></td>
              <td>Enlaces <code>https://</code> registrados en la sección <code>### Evidencia o enlace</code> del Issue Form</td>
              <td>Pull Requests o productos publicados en el repositorio canónico</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>¿Dónde registrar cada tarea o solicitud de apoyo?</h2>
      <div class="grid-3">
        <article class="card">
          <h3>1. Tareas técnicas del PMV</h3>
          <p>Se crean como Issues dentro del repositorio canónico de la iniciativa (<code>urbano-{{id}}</code>) usando el formulario <strong>Tarea del PMV</strong> y se vinculan al tablero regional.</p>
        </article>
        <article class="card">
          <h3>2. Bloqueos y mentoría técnica</h3>
          <p>Se registran con el formulario <strong>Bloqueo o solicitud de apoyo</strong> (etiqueta <code>bloqueado</code>), ya sea en el repositorio de tu iniciativa o en el portal central, con atención del Equipo de Facilitación Técnica.</p>
        </article>
        <article class="card">
          <h3>3. Compromisos regionales</h3>
          <p>Acuerdos transversales, calendario comunitario y coordinación del Atlas se registran en las Issues y Discussions del repositorio central <code>clusterurbano</code>.</p>
        </article>
      </div>
    </section>
    """

    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Seguimiento",
        active_nav="seguimiento",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=catalog_snap.get("generated_at"),
    )


def build_comunidad_page(ctx: SiteContext, registry: dict[str, Any], catalog_snap: dict[str, Any]) -> str:
    inst_by_country: list[tuple[str, str, list[str]]] = []
    for it in catalog_snap.get("projects", []):
        p = it["project"]
        inst_by_country.append(
            (p["country"]["name"], p["id"], p["institutional_use"].get("institutions", []))
        )

    inst_rows = []
    for cname, pid, insts in inst_by_country:
        href = html.escape(ctx.site_url(f"proyectos/{pid}/"), quote=True)
        inst_rows.append(
            f"<tr><td><strong>{esc(cname)}</strong></td><td><a href=\"{href}\"><code>{esc(pid)}</code></a></td>"
            f"<td>{esc('; '.join(insts) if insts else 'Por confirmar')}</td></tr>"
        )

    hub_repo = registry.get("hub", {}).get("repository") or "copernicuscentroamerica/clusterurbano"
    discussions_url = f"https://github.com/{hub_repo}/discussions"
    support_issue_url = f"https://github.com/{hub_repo}/issues/new?template=bloqueo_apoyo.yml"
    board_url = "https://github.com/users/copernicuscentroamerica/projects/1"

    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <span class="badge badge-lime">Comunidad de Práctica</span>
          <span class="badge badge-ok">Canales públicos activos</span>
        </div>
        <h1>Gobernanza colaborativa, canales de ayuda e intercambio regional</h1>
        <p class="hero-lead">Red interinstitucional y académica de Centroamérica y República Dominicana enfocada en desarrollar métodos abiertos, sostener productos territoriales útiles y nutrir el Atlas Urbano Regional.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{html.escape(discussions_url, quote=True)}" target="_blank" rel="noopener noreferrer">Abrir GitHub Discussions de la comunidad ↗</a>
          <a class="btn btn-teal" href="{html.escape(support_issue_url, quote=True)}" target="_blank" rel="noopener noreferrer">Solicitar apoyo técnico o reportar bloqueo ↗</a>
          <a class="btn btn-outline-light" href="{html.escape(board_url, quote=True)}" target="_blank" rel="noopener noreferrer">Ver tablero GitHub Project #1 ↗</a>
        </div>
      </div>
    </section>
    """

    body = f"""
    <section class="section">
      <h2>¿Dónde participar y dónde pedir apoyo técnico?</h2>
      <div class="grid-3">
        <article class="card" style="border-left:4px solid var(--c-teal);">
          <span class="badge badge-ok">Canal público activo</span>
          <h3>1. Foro regional (GitHub Discussions)</h3>
          <p>Espacio abierto para preguntas técnicas sobre Google Earth Engine, Google Colab, Sentinel-1/2 y GeoLibre, anuncios regionales y demostraciones de avances entre los seis países.</p>
          <div class="card-footer">
            <a class="btn btn-teal btn-xs" href="{html.escape(discussions_url, quote=True)}" target="_blank" rel="noopener noreferrer">Entrar a Discussions ↗</a>
            <a class="btn btn-outline btn-xs" href="https://github.com/copernicuscentroamerica/clusterurbano/discussions/1" target="_blank" rel="noopener noreferrer">Hilo de bienvenida #1 ↗</a>
          </div>
        </article>
        <article class="card" style="border-left:4px solid var(--c-navy);">
          <span class="badge badge-declarado">Atención de facilitación</span>
          <h3>2. Solicitar apoyo o reportar un bloqueo</h3>
          <p>Si encuentras un obstáculo con datos, validación de esquemas, permisos o despliegue en GeoLibre, abre un reporte con el formulario estructurado. <strong>Responsable de atención:</strong> Equipo de Facilitación Técnica y Administración del Clúster Urbano Copernicus.</p>
          <div class="card-footer">
            <a class="btn btn-primary btn-xs" href="{html.escape(support_issue_url, quote=True)}" target="_blank" rel="noopener noreferrer">Abrir solicitud de apoyo ↗</a>
          </div>
        </article>
        <article class="card" style="border-left:4px solid var(--c-lime);">
          <span class="badge badge-ok">Tablero público</span>
          <h3>3. Tablero GitHub Project #1 y Seguimiento</h3>
          <p>Consulta las tarjetas operativas de las ocho iniciativas tanto en el tablero público de GitHub Projects como en la vista consolidada del portal.</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="{html.escape(board_url, quote=True)}" target="_blank" rel="noopener noreferrer">Tablero GitHub Project #1 ↗</a>
            <a class="btn btn-outline btn-xs" href="{html.escape(ctx.site_url('seguimiento/'), quote=True)}">Vista en el portal →</a>
          </div>
        </article>
      </div>
    </section>

    <section class="section">
      <h2>Categorías activas en GitHub Discussions</h2>
      <p>Las categorías listadas a continuación corresponden exactamente a las habilitadas en el repositorio <code>copernicuscentroamerica/clusterurbano</code>:</p>
      <div class="grid-3">
        <div class="card">
          <span class="badge badge-country">Announcements</span>
          <h3>Anuncios y acuerdos</h3>
          <p>Hitos de la jornada presencial en San Salvador, convocatorias y acuerdos regionales.</p>
          <div class="card-footer"><a class="btn btn-outline btn-xs" href="{html.escape(discussions_url + '/categories/announcements', quote=True)}" target="_blank" rel="noopener noreferrer">Abrir Announcements ↗</a></div>
        </div>
        <div class="card">
          <span class="badge badge-country">Q&amp;A</span>
          <h3>Preguntas y respuestas técnicas</h3>
          <p>Consultas sobre Google Colab, Google Earth Engine, Sentinel-1/2, GeoLibre Studio y Google Antigravity.</p>
          <div class="card-footer"><a class="btn btn-outline btn-xs" href="{html.escape(discussions_url + '/categories/q-a', quote=True)}" target="_blank" rel="noopener noreferrer">Abrir Q&amp;A ↗</a></div>
        </div>
        <div class="card">
          <span class="badge badge-country">Show and tell</span>
          <h3>Avances y demostraciones</h3>
          <p>Comparte capturas de tus capas en el Geovisor, métricas del ejercicio con Sentinel-2 y avances del PMV.</p>
          <div class="card-footer"><a class="btn btn-outline btn-xs" href="{html.escape(discussions_url + '/categories/show-and-tell', quote=True)}" target="_blank" rel="noopener noreferrer">Abrir Show and tell ↗</a></div>
        </div>
        <div class="card">
          <span class="badge badge-country">General</span>
          <h3>Conversación general</h3>
          <p>Presentaciones de equipos institucionales, articulación entre países y coordinación de sesiones.</p>
          <div class="card-footer"><a class="btn btn-outline btn-xs" href="{html.escape(discussions_url + '/categories/general', quote=True)}" target="_blank" rel="noopener noreferrer">Abrir General ↗</a></div>
        </div>
        <div class="card">
          <span class="badge badge-country">Ideas</span>
          <h3>Propuestas comunitarias</h3>
          <p>Sugerencias de mejora para la plantilla común, nuevos indicadores y evolución del Atlas Urbano Regional.</p>
          <div class="card-footer"><a class="btn btn-outline btn-xs" href="{html.escape(discussions_url + '/categories/ideas', quote=True)}" target="_blank" rel="noopener noreferrer">Abrir Ideas ↗</a></div>
        </div>
        <div class="card">
          <span class="badge badge-country">Polls</span>
          <h3>Consultas rápidas</h3>
          <p>Votaciones breves para acordar horarios de mentorías y temas prioritarios de intercambio posjornada.</p>
          <div class="card-footer"><a class="btn btn-outline btn-xs" href="{html.escape(discussions_url + '/categories/polls', quote=True)}" target="_blank" rel="noopener noreferrer">Abrir Polls ↗</a></div>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>Instituciones participantes documentadas en los perfiles</h2>
      <p>Los nombres personales y correos privados se protegen por defecto y solo se publican con autorización expresa; aquí se listan las instituciones declaradas en las ocho iniciativas:</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>País</th><th>Iniciativa</th><th>Instituciones declaradas en el perfil</th></tr></thead>
          <tbody>{"".join(inst_rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Roles funcionales de la comunidad</h2>
      <div class="grid-2">
        <article class="card">
          <h3>Coordinación y administración</h3>
          <ul>
            <li><strong>Equipo de Facilitación Técnica y Coordinación:</strong> atiende solicitudes de apoyo, facilita acuerdos y mantiene sincronizado el tablero GitHub Project #1.</li>
            <li><strong>Administración técnica:</strong> gestiona permisos de repositorios, flujos de GitHub Pages y validación de esquemas.</li>
            <li><strong>Curaduría del Atlas:</strong> revisa consistencia de metadatos, unidades y advertencias de comparabilidad antes de publicar productos.</li>
          </ul>
        </article>
        <article class="card">
          <h3>Equipos de iniciativa y revisión</h3>
          <ul>
            <li><strong>Punto focal de iniciativa:</strong> cuida la coherencia de <code>project.json</code>, <code>content/project.md</code> y tareas del equipo.</li>
            <li><strong>Revisor técnico:</strong> comprueba reproducibilidad metodológica, código, CRS (<code>EPSG:4326</code>) y limitaciones antes de fusionar un Pull Request.</li>
            <li><strong>Referente institucional:</strong> examina pertinencia para la decisión pública y condiciones reales de adopción.</li>
          </ul>
        </article>
      </div>
    </section>

    <section class="section">
      <div class="callout callout-muted">
        <strong>Rutina de continuidad posjornada (Propuesta para acordar el jueves 12 de noviembre)</strong>
        <span>Se propone mantener actualizaciones breves por iniciativa (resultado, evidencia, siguiente compromiso y apoyo requerido), revisiones por ciclo de trabajo e intercambios temáticos regionales. Las fechas y responsables efectivos se registrarán únicamente tras su aprobación por los equipos.</span>
      </div>
    </section>
    """

    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Comunidad",
        active_nav="comunidad",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=catalog_snap.get("generated_at"),
    )


def build_recursos_page(ctx: SiteContext, registry: dict[str, Any], catalog_snap: dict[str, Any]) -> str:
    colab_url = "https://colab.research.google.com/github/copernicuscentroamerica/clusterurbano/blob/main/web/assets/descargas/mancha_urbana_sentinel2_vmod01.ipynb"
    nb_dl = html.escape(ctx.site_url("assets/descargas/mancha_urbana_sentinel2_vmod01.ipynb"), quote=True)
    pptx_dl = html.escape(ctx.site_url("assets/descargas/scrum_aplicacion_geoespacial_Sesion_7_Previa_Encuentro.pptx"), quote=True)
    docx_dl = html.escape(ctx.site_url("assets/descargas/Manual_Guia_Antigravity_Proyectos_Copernicus.docx"), quote=True)

    faqs = [
        (
            "¿Cómo encuentro mi iniciativa y su repositorio?",
            "Entra a la sección Proyectos, filtra por tu país o busca tu institución. Dentro de la ficha verás el identificador estable (ej. pa-panama-oeste), los botones de acción directa y los comandos exactos para clonar o hacer fork.",
        ),
        (
            "¿Cómo creo mi fork personal y configuro upstream sin confundir el portal?",
            "Haz fork únicamente del repositorio canónico de tu iniciativa (urbano-{id}), nunca del repositorio general clusterurbano si vas a editar tu proyecto. En tu clon local en Google Antigravity, 'origin' apunta a tu cuenta personal y 'upstream' apunta a copernicuscentroamerica/urbano-{id}.",
        ),
        (
            "¿Cómo despliego las capas que genere mi equipo en el Geovisor y en GeoLibre Studio?",
            "Coloca tus archivos en la carpeta geovisor/capas/ de tu repositorio (nunca en geovisor/data/). Si es un GeoJSON/TopoJSON/KML en EPSG:4326, regístralo también en geovisor/layers.json y ejecuta python scripts/build_site.py --output site para que se dibuje automáticamente en el visor integrado (MapLibre) y se empaquete en geovisor/proyecto.geolibre.json. Los formatos avanzados (.pmtiles, .tif/.tiff COG, .fgb, .parquet) se abren en GeoLibre Studio con un clic desde la pestaña 'Carpeta repo', y cualquier GeoJSON/KML local puede previsualizarse en la pestaña 'Archivo local'.",
        ),
        (
            "¿Puedo usar la misma cuenta de Google en Antigravity, Google Colab y Google Earth Engine?",
            "Sí. Las tres son herramientas de Google y comparten tu misma identidad de Google. Puedes ejecutar el cuaderno mancha_urbana_sentinel2_vmod01.ipynb en Google Colab o el script equivalente en Google Earth Engine y luego integrar las capas descargadas en tu repositorio local con el agente de Google Antigravity.",
        ),
        (
            "¿Cómo registro una tarea del PMV o un bloqueo?",
            "Abre la pestaña Issues del repositorio de tu iniciativa y elige el formulario 'Tarea del PMV' o 'Bloqueo o solicitud de apoyo'. Toda tarea se sincroniza con el tablero público GitHub Project #1 y con la sección Seguimiento del portal.",
        ),
        (
            "¿Cómo solicito una revisión técnica o validación institucional?",
            "Usa el formulario 'Solicitud de revisión' adjuntando el enlace HTTPS al producto, Pull Request o vista previa. Para que project.json cambie el estado a 'validado', el esquema exige URL HTTPS de evidencia, fecha ISO (YYYY-MM-DD) y nombre o rol del revisor.",
        ),
        (
            "¿Cómo propongo e incorporo un producto al Atlas Urbano Regional?",
            "Actualiza o añade un archivo JSON en atlas/products/ siguiendo schemas/atlas-product.schema.json (con publication_status en 'propuesto', 'en_preparacion', 'publicado' o 'retirado') y abre el formulario 'Contribución al Atlas' para curaduría.",
        ),
    ]

    faq_cards = []
    for q, a in faqs:
        faq_cards.append(
            f"""
            <article class="card" data-filter-item data-search-text="{esc(q + ' ' + a)}">
              <h3>{esc(q)}</h3>
              <p>{esc(a)}</p>
            </article>
            """
        )

    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <span class="badge badge-lime">Guías técnicas, manual v1.1 y descargas</span>
        </div>
        <h1>Recursos para desarrollo, Colab, GEE, GeoLibre y colaboración</h1>
        <p class="hero-lead">Materiales descargables, manual paso a paso con Google Antigravity, ejercicio reproducible con Sentinel-2 y documentación de formatos del Geovisor.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{docx_dl}" download="Manual_Guia_Antigravity_Proyectos_Copernicus.docx">Descargar Manual Guía v1.1 (.docx)</a>
          <a class="btn btn-teal" href="{html.escape(ctx.site_url('ejercicio/'), quote=True)}">Ir al Ejercicio Práctico Colab / GEE →</a>
        </div>
      </div>
    </section>
    """

    body = f"""
    <section class="section">
      <h2>Materiales de capacitación y ejercicio práctico (descarga directa)</h2>
      <div class="grid-3">
        <article class="card" style="border-left:4px solid var(--c-navy);">
          <span class="badge badge-ok">Manual oficial v1.1 (Word)</span>
          <h3>Manual Guía Paso a Paso con Google Antigravity</h3>
          <p>Guía completa para clonar tu repositorio desde un fork, usar prompts seguros con el agente de IA, ejecutar el ejercicio en Google Colab y Google Earth Engine, validar esquemas y revisar tu Pull Request. Incluye hoja de referencia rápida de 1 página.</p>
          <div class="card-footer">
            <a class="btn btn-primary btn-xs" href="{docx_dl}" download="Manual_Guia_Antigravity_Proyectos_Copernicus.docx">Descargar Manual (.docx)</a>
          </div>
        </article>

        <article class="card" style="border-left:4px solid var(--c-teal);">
          <span class="badge badge-ok">Cuaderno Jupyter (.ipynb)</span>
          <h3>Detección de Mancha Urbana con Sentinel-2 L2A</h3>
          <p>Cuaderno ejecutable en Google Colab con catálogo de 75 ciudades y 779 poblados de CA y RD, compuesto libre de nubes (<code>SCL</code>), 12 predictores espectrales/texturales y clasificación Random Forest entrenada con Overture Maps.</p>
          <div class="card-footer">
            <a class="btn btn-teal btn-xs" href="{html.escape(colab_url, quote=True)}" target="_blank" rel="noopener noreferrer">Abrir en Google Colab ↗</a>
            <a class="btn btn-outline btn-xs" href="{nb_dl}" download="mancha_urbana_sentinel2_vmod01.ipynb">Descargar .ipynb</a>
          </div>
        </article>

        <article class="card" style="border-left:4px solid var(--c-lime);">
          <span class="badge badge-declarado">Presentación Metodológica (.pptx)</span>
          <h3>Marco Scrum para Aplicaciones Geoespaciales (Sesión 7)</h3>
          <p>Presentación de la Sesión 7 previa al encuentro presencial: organización de sprints, historias de usuario (<code>US-GIS</code>), definición de terminado (DoD) y articulación con el ejercicio práctico.</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="{pptx_dl}" download="scrum_aplicacion_geoespacial_Sesion_7_Previa_Encuentro.pptx">Descargar .pptx</a>
          </div>
        </article>
      </div>
    </section>

    <section class="section">
      <h2>Comportamiento por formato en el Geovisor del proyecto y en GeoLibre Studio</h2>
      <p>Cada repositorio de iniciativa incluye dos modalidades complementarias de visualización: el <strong>visor integrado en la página (MapLibre GL JS)</strong> y la exportación o transferencia directa hacia <strong>GeoLibre Studio (<code>web.geolibre.app</code>)</strong>.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Formato</th>
              <th>Dónde se abre</th>
              <th>Pasos necesarios</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>.geojson</code>, <code>.json</code>, <code>.topojson</code>, <code>.kml</code></td>
              <td><strong>Directamente en el visor integrado de la página</strong> (MapLibre GL JS) y también en <strong>GeoLibre Studio</strong></td>
              <td>En la pestaña <strong>Carpeta repo</strong> (<code>geovisor/capas/</code>) pulsa <strong>+ Mapa</strong> para dibujarlo al instante, o arrástralo en la pestaña <strong>Archivo local</strong>. Si lo registras en <code>geovisor/layers.json</code> y ejecutas <code>build_site.py</code>, se carga por defecto y se incluye dentro de <code>geovisor/proyecto.geolibre.json</code>.</td>
            </tr>
            <tr>
              <td><code>.pmtiles</code>, <code>.tif</code>/<code>.tiff</code> (COG), <code>.fgb</code>, <code>.parquet</code>/<code>.geoparquet</code></td>
              <td><strong>En GeoLibre Studio</strong> (<code>web.geolibre.app</code>)</td>
              <td>Coloca el archivo en <code>geovisor/capas/</code> de tu repositorio. En la pestaña <strong>Carpeta repo</strong> pulsa <strong>Abrir en GeoLibre Studio ↗</strong>; el visor pasa automáticamente el parámetro <code>?data=&lt;url&gt;</code> para cargar la capa remota en GeoLibre Studio.</td>
            </tr>
            <tr>
              <td><code>.geolibre.json</code> (Proyecto completo v0.2.0)</td>
              <td><strong>En GeoLibre Studio</strong> (<code>web.geolibre.app/?url=...</code>)</td>
              <td>El generador <code>scripts/build_site.py</code> construye y valida automáticamente <code>geovisor/proyecto.geolibre.json</code> con <code>mapView</code>, <code>basemapStyleUrl</code>, estilos y capas GeoJSON embebidas. Pulsa <strong>Abrir proyecto en GeoLibre Studio ↗</strong> en la cabecera del visor.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Plataformas y herramientas técnicas verificadas</h2>
      <div class="grid-3">
        <article class="card">
          <span class="badge badge-ok">Geovisualización</span>
          <h3>GeoLibre Web &amp; MapLibre GL JS</h3>
          <p>Plataforma SIG ligera en navegador compatible con archivos de proyecto <code>.geolibre.json</code> (v0.2.0), GeoJSON, COG, PMTiles, FlatGeobuf y GeoParquet.</p>
          <div class="card-footer">
            <a class="btn btn-teal btn-xs" href="https://web.geolibre.app/" target="_blank" rel="noopener noreferrer">Abrir web.geolibre.app ↗</a>
            <a class="btn btn-outline btn-xs" href="https://github.com/opengeos/GeoLibre" target="_blank" rel="noopener noreferrer">GitHub GeoLibre ↗</a>
          </div>
        </article>

        <article class="card">
          <span class="badge badge-declarado">Observación de la Tierra</span>
          <h3>Copernicus Data Space &amp; openEO</h3>
          <p>Acceso oficial a colecciones Sentinel-1, Sentinel-2, Copernicus DEM y procesamiento reproducible mediante openEO.</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="https://dataspace.copernicus.eu/" target="_blank" rel="noopener noreferrer">Copernicus Data Space ↗</a>
            <a class="btn btn-outline btn-xs" href="https://openeo.dataspace.copernicus.eu/" target="_blank" rel="noopener noreferrer">openEO ↗</a>
          </div>
        </article>

        <article class="card">
          <span class="badge badge-declarado">Procesamiento en la nube</span>
          <h3>Google Colab, Earth Engine &amp; GHSL</h3>
          <p>Ejecución de cuadernos Python en Google Colab y scripts en Google Earth Engine con la misma cuenta de Google usada en Antigravity.</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="https://colab.research.google.com/" target="_blank" rel="noopener noreferrer">Google Colab ↗</a>
            <a class="btn btn-outline btn-xs" href="https://code.earthengine.google.com/" target="_blank" rel="noopener noreferrer">GEE Code Editor ↗</a>
          </div>
        </article>

        <article class="card">
          <span class="badge badge-propuesta">Plantilla oficial del clúster</span>
          <h3>Plantilla de iniciativa (<code>clusterurbano-proyecto-template</code>)</h3>
          <p>Estructura base independiente con contratos JSON Schema Draft 2020-12, generador Python, validación de <code>.geolibre.json</code> y geovisor preconfigurado.</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="https://github.com/copernicuscentroamerica/clusterurbano-proyecto-template" target="_blank" rel="noopener noreferrer">Plantilla en GitHub ↗</a>
          </div>
        </article>

        <article class="card">
          <span class="badge badge-declarado">Antecedente en la cuenta regional</span>
          <h3>Geovisor Mesoamérica y Clúster AFOLU</h3>
          <p>Recursos previos alojados en la cuenta <code>copernicuscentroamerica</code> como referencia comunitaria complementaria.</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="https://github.com/copernicuscentroamerica/geovisor" target="_blank" rel="noopener noreferrer">Repo Geovisor previo ↗</a>
            <a class="btn btn-outline btn-xs" href="https://copernicuscentroamerica.github.io/clusterafolu/" target="_blank" rel="noopener noreferrer">Portal AFOLU ↗</a>
          </div>
        </article>

        <article class="card">
          <span class="badge badge-declarado">Documentación GitHub</span>
          <h3>Flujo de Forks, Pull Requests y Pages</h3>
          <p>Guías oficiales de GitHub para trabajar con repositorios derivados de plantilla, sincronizar forks y publicar mediante GitHub Actions.</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo" target="_blank" rel="noopener noreferrer">Guía de Forks ↗</a>
          </div>
        </article>
      </div>
    </section>

    <section class="section" data-catalog-faq>
      <div class="section-header">
        <h2>Preguntas frecuentes y ayuda rápida</h2>
      </div>
      <div class="filter-bar" role="search" aria-label="Buscar en preguntas frecuentes">
        <div class="filter-field">
          <label for="f-faq-q">Buscar ayuda por palabra clave</label>
          <input id="f-faq-q" type="search" placeholder="Ej. fork, geovisor, capas, colab, gee, revisión, atlas..." data-filter-search>
        </div>
        <button type="button" class="btn btn-outline" data-filter-reset>Limpiar</button>
      </div>
      <div class="callout callout-warn hidden" data-filter-empty>
        <strong>No hay preguntas que coincidan con la búsqueda</strong>
        <span>Limpia el cuadro de texto para ver todas las guías frecuentes.</span>
      </div>
      <div class="grid-2">
        {"".join(faq_cards)}
      </div>
    </section>
    """

    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Recursos y FAQ",
        active_nav="recursos",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=catalog_snap.get("generated_at"),
    )


def build_agenda_page(ctx: SiteContext, registry: dict[str, Any], agenda_doc: dict[str, Any], catalog_snap: dict[str, Any]) -> str:
    by_day: dict[str, list[dict[str, Any]]] = {}
    day_labels: dict[str, str] = {}
    for ev in agenda_doc.get("scheduled_activities", []):
        d = ev["day_date"]
        by_day.setdefault(d, []).append(ev)
        day_labels[d] = ev["day_label"]

    tabs_html = ['<button type="button" class="day-tab is-active" data-day-tab="all" aria-selected="true">Los 3 días completos</button>']
    panels_html = []
    for d_key in sorted(by_day.keys()):
        short_btn = day_labels[d_key].split("—")[0].strip()
        tabs_html.append(f'<button type="button" class="day-tab" data-day-tab="{esc(d_key)}" aria-selected="false">{esc(short_btn)}</button>')
        rows = []
        for ev in by_day[d_key]:
            hm_start = ev["start"][11:16]
            hm_end = ev["end"][11:16]
            rows.append(
                f"<tr>"
                f"<td style=\"white-space:nowrap;\"><strong>{esc(hm_start)}–{esc(hm_end)}</strong><br><span style=\"font-size:0.74rem;color:var(--c-text-muted);\">UTC−06:00</span></td>"
                f"<td><strong>{esc(ev['title'])}</strong><br><span style=\"font-size:0.86rem;\">{esc(ev['description'])}</span></td>"
                f"<td>{esc(ev['location'])}</td>"
                f"<td><span class=\"badge badge-declarado\">{esc(ev['status'])}</span></td>"
                f"</tr>"
            )
        panels_html.append(
            f"""
            <div class="section" data-day-panel="{esc(d_key)}">
              <h2>{esc(day_labels[d_key])}</h2>
              <div class="table-wrap">
                <table>
                  <thead><tr><th>Horario (El Salvador)</th><th>Actividad y resultado operativo</th><th>Lugar</th><th>Estado</th></tr></thead>
                  <tbody>{"".join(rows)}</tbody>
                </table>
              </div>
            </div>
            """
        )

    prop_cards = []
    for prop in agenda_doc.get("continuity_proposals", []):
        prop_cards.append(
            f"""
            <article class="card">
              <div>{badge_html('propuesta', 'Estado: ' + prop['status'])}</div>
              <h3>{esc(prop['title'])}</h3>
              <p>{esc(prop['description'])}</p>
              <p style="font-size:0.84rem;color:var(--c-text-muted);"><strong>Fecha y hora:</strong> Pendiente de acordar · <strong>Lugar/canal:</strong> {esc(prop['location'])}</p>
            </article>
            """
        )

    ics_href = html.escape(ctx.site_url("agenda/jornada-copernicus-2026.ics"), quote=True)

    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <span class="badge badge-lime">San Salvador, El Salvador · 10 al 12 de noviembre de 2026</span>
          <span class="badge badge-country">Zona horaria: {esc(agenda_doc.get('timezone'))} (UTC{esc(agenda_doc.get('utc_offset'))})</span>
        </div>
        <h1>Agenda oficial de la jornada presencial y continuidad</h1>
        <p class="hero-lead">{esc(agenda_doc.get('event_name'))}. Todos los horarios se presentan en hora local de El Salvador sin desplazarse según el huso del navegador.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{ics_href}" download="jornada-copernicus-2026.ics">Descargar calendario (.ics)</a>
        </div>
      </div>
    </section>
    """

    body = f"""
    <div class="day-tabs" role="tablist" aria-label="Seleccionar día de la jornada">
      {"".join(tabs_html)}
    </div>

    {"".join(panels_html)}

    <section class="section">
      <h2>Próximos encuentros de continuidad (propuestas abiertas a acuerdo)</h2>
      <p>Estas actividades posteriores no tienen fechas asignadas hasta que la plenaria del jueves 12 de noviembre las acuerde:</p>
      <div class="grid-2">{"".join(prop_cards)}</div>
    </section>
    """

    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Agenda",
        active_nav="agenda",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=catalog_snap.get("generated_at"),
    )


def build_404_page(ctx: SiteContext, registry: dict[str, Any], snapshot_generated_at: str | None) -> str:
    hero = f"""
    <section class="hero">
      <div class="container">
        <h1>Página no encontrada (404)</h1>
        <p class="hero-lead">El enlace solicitado no corresponde a una ruta activa del Portal Comunitario.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{html.escape(ctx.site_url(''), quote=True)}">Ir a Inicio</a>
          <a class="btn btn-teal" href="{html.escape(ctx.site_url('ejercicio/'), quote=True)}">Ir al Ejercicio Práctico</a>
          <a class="btn btn-outline-light" href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">Explorar las 8 iniciativas</a>
        </div>
      </div>
    </section>
    """
    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="404 Página no encontrada",
        active_nav="",
        hero_html=hero,
        body_html="<section class='section'><p>Utiliza la barra superior para acceder al catálogo de proyectos, el ejercicio práctico en Google Colab y Google Earth Engine, el Atlas Urbano Regional, el seguimiento o la agenda.</p></section>",
        snapshot_generated_at=snapshot_generated_at,
    )


def write_deterministic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Construye el sitio estático del portal clusterurbano.")
    parser.add_argument("--output", type=str, default="site", help="Directorio de salida (por defecto: site).")
    parser.add_argument("--base-path", type=str, default=None, help="Prefijo explícito de ruta base.")
    parser.add_argument("--origin", type=str, default=None, help="Origen explícito HTTPS.")
    args = parser.parse_args()

    if (ROOT / "project.json").exists():
        print("Error: directorio ambiguo (contiene project.json de iniciativa).", file=sys.stderr)
        return 1

    registry = json.loads((ROOT / "data" / "projects.registry.json").read_text(encoding="utf-8"))

    # Si aún no existen los snapshots derivados locales, resolverlos en modo offline automáticamente
    if not (ROOT / "data" / "projects.snapshot.json").exists() or not (ROOT / "data" / "atlas.snapshot.json").exists():
        from sync_catalog import run_sync
        run_sync(online=False)

    catalog_snap = json.loads((ROOT / "data" / "projects.snapshot.json").read_text(encoding="utf-8"))
    atlas_snap = json.loads((ROOT / "data" / "atlas.snapshot.json").read_text(encoding="utf-8"))
    agenda_doc = json.loads((ROOT / "data" / "events.agenda.json").read_text(encoding="utf-8"))

    seg_path = ROOT / "data" / "seguimiento.json"
    if not seg_path.exists():
        seg_path = ROOT / "data" / "seguimiento.initial.json"
    progress_snap = json.loads(seg_path.read_text(encoding="utf-8"))

    board_cfg_path = ROOT / "data" / "project_board.config.json"
    board_cfg = json.loads(board_cfg_path.read_text(encoding="utf-8")) if board_cfg_path.exists() else {"project_url": None}

    explicit_bp = args.base_path if args.base_path is not None else os.environ.get("SITE_BASE_PATH")
    ctx = compute_site_context(
        canonical_repo_url_or_slug=registry.get("hub", {}).get("repository"),
        explicit_base_path=explicit_bp,
        explicit_origin=args.origin,
    )

    out_dir = (ROOT / args.output).resolve()
    if out_dir == ROOT:
        print("Error: --output no puede ser la raíz del repositorio.", file=sys.stderr)
        return 1
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Recursos estáticos
    shutil.copytree(ROOT / "web" / "assets", out_dir / "assets")
    boot_logos_dir = ROOT / "bootstrap" / "branding" / "logos"
    if boot_logos_dir.exists():
        shutil.copytree(boot_logos_dir, out_dir / "assets" / "img" / "projects", dirs_exist_ok=True)

    # Publicar snapshots derivados en site/data/
    write_deterministic(
        out_dir / "data" / "projects.snapshot.json",
        json.dumps(catalog_snap, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    write_deterministic(
        out_dir / "data" / "atlas.snapshot.json",
        json.dumps(atlas_snap, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    write_deterministic(
        out_dir / "data" / "seguimiento.json",
        json.dumps(progress_snap, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    build_meta = {
        "hub_id": "comunidad-urbana",
        "schema_version": "1.0.0",
        "template_version": TEMPLATE_VERSION,
        "theme_version": THEME_VERSION,
        "base_path": ctx.base_path,
        "origin": ctx.origin,
        "effective_mode": ctx.effective_mode,
        "canonical_repository": ctx.canonical_repository,
    }
    write_deterministic(
        out_dir / "data" / "build-meta.json",
        json.dumps(build_meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )

    # Copiar archivo .ics de agenda
    (out_dir / "agenda").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "data" / "jornada-copernicus-2026.ics", out_dir / "agenda" / "jornada-copernicus-2026.ics")

    # Índices rápidos
    reg_by_id = {e["id"]: e for e in registry["projects"]}
    atlas_by_proj: dict[str, list[dict[str, Any]]] = {}
    for ap in atlas_snap.get("products", []):
        atlas_by_proj.setdefault(ap["project_id"], []).append(ap)
    proj_by_id = {it["project"]["id"]: it["project"] for it in catalog_snap.get("projects", [])}

    # Generar páginas del portal
    write_deterministic(out_dir / "index.html", build_home_page(ctx, registry, catalog_snap, atlas_snap, agenda_doc))
    write_deterministic(out_dir / "proyectos" / "index.html", build_proyectos_catalog_page(ctx, registry, catalog_snap))
    for it in catalog_snap.get("projects", []):
        pid = it["project"]["id"]
        write_deterministic(
            out_dir / "proyectos" / pid / "index.html",
            build_hub_project_detail_page(
                ctx,
                registry,
                reg_by_id[pid],
                it,
                atlas_by_proj.get(pid, []),
                catalog_snap.get("generated_at"),
            ),
        )

    write_deterministic(out_dir / "ejercicio" / "index.html", build_ejercicio_page(ctx, registry, catalog_snap))
    write_deterministic(out_dir / "atlas" / "index.html", build_atlas_index_page(ctx, registry, atlas_snap, catalog_snap))
    for ap in atlas_snap.get("products", []):
        write_deterministic(
            out_dir / "atlas" / ap["id"] / "index.html",
            build_atlas_detail_page(ctx, registry, ap, proj_by_id.get(ap["project_id"]), atlas_snap.get("generated_at")),
        )

    write_deterministic(out_dir / "seguimiento" / "index.html", build_seguimiento_page(ctx, registry, progress_snap, catalog_snap, board_cfg))
    write_deterministic(out_dir / "comunidad" / "index.html", build_comunidad_page(ctx, registry, catalog_snap))
    write_deterministic(out_dir / "recursos" / "index.html", build_recursos_page(ctx, registry, catalog_snap))
    write_deterministic(out_dir / "agenda" / "index.html", build_agenda_page(ctx, registry, agenda_doc, catalog_snap))
    write_deterministic(out_dir / "404.html", build_404_page(ctx, registry, catalog_snap.get("generated_at")))

    print(
        f"[OK] Portal comunitario 'clusterurbano' construido en {out_dir} "
        f"(base_path='{ctx.base_path}', modo='{ctx.effective_mode}')."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
