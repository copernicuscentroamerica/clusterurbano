#!/usr/bin/env python3
"""
Generador estático determinista del Portal Comunitario (clusterurbano).
Construye Inicio, Proyectos y Geovisores, fichas proyectos/{id}/ (+ redirección gt-salud-metropolitana),
Atlas Urbano Regional, fichas atlas/{product_id}/, Metodologías y Código (/recursos/), Comunidad,
rutas de respaldo (/ejercicio/, /seguimiento/, /agenda/ + .ics) y 404.html.
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
    "sv-amss": "San Salvador (AMSS) · Valor del suelo GEE y expansión urbana",
    "cr-la-carpio": "La Carpio (San José) · Exposición multiamenaza y Plan Maestro",
    "sv-la-union": "Conchagua y La Unión · Dinámica de asentamientos costeros",
    "gt-bethania": "Bethania (Guatemala) · Evaluación de riesgo a nivel de lote",
    "do-santiago": "Santiago · Expansión urbana 2018–2036 e inundación HAND",
    "pa-colon": "Colón (Panamá) · Comparador multianual y corredor portuario",
    "hn-distrito-central": "Distrito Central · Brecha catastral y huella en laderas",
}

PROJECT_ENRICHMENT: dict[str, dict[str, Any]] = {
    "pa-panama-oeste": {
        "subpage_slug": "modelo-ocupacion",
        "subpage_label": "Modelo de Ocupación",
        "layers_summary": "11 capas activas · RF + NDBI/NDVI + focos prioritarios MIVIOT",
        "atlas_pages": 27,
        "docx_file": "Metodologia_pa-panama-oeste.docx",
        "badge_label": "PA · Panamá Oeste",
        "label_dir": "bottom",
        "center": [-79.75532, 8.94515],
        "bbox": [-79.99104, 8.77428, -79.54905, 9.18479],
        "zoom": 11.2,
    },
    "sv-amss": {
        "subpage_slug": "modelo-suelo",
        "subpage_label": "Modelo Valor Suelo GEE",
        "layers_summary": "9 capas activas · AlphaEarth 64D + RF (R² = 83.27 %) + malla 100 m",
        "atlas_pages": 27,
        "docx_file": "Metodologia_sv-amss.docx",
        "badge_label": "SV · San Salvador (AMSS)",
        "label_dir": "left",
        "center": [-89.2182, 13.6989],
        "bbox": [-89.62858, 13.41821, -89.0253, 13.92034],
        "zoom": 10.8,
    },
    "cr-la-carpio": {
        "subpage_slug": "indice-multiamenaza",
        "subpage_label": "Índice Multiamenaza",
        "layers_summary": "7 capas curadas + Tablero · Malla 20 m (2,470 hex) + Multiamenaza + INEC",
        "atlas_pages": 27,
        "docx_file": "Metodologia_cr-la-carpio.docx",
        "badge_label": "CR · La Carpio (San José)",
        "label_dir": "left",
        "center": [-84.1502, 9.96309],
        "bbox": [-84.15566, 9.95785, -84.14461, 9.96671],
        "zoom": 14.8,
    },
    "sv-la-union": {
        "subpage_slug": "dinamica-asentamientos",
        "subpage_label": "Dinámica 2019–2025",
        "layers_summary": "9 capas activas · Huella costera 2019–2025 + susceptibilidad DEM",
        "atlas_pages": 27,
        "docx_file": "Metodologia_sv-la-union.docx",
        "badge_label": "SV · Conchagua / La Unión",
        "label_dir": "bottom",
        "center": [-87.865, 13.315],
        "bbox": [-87.99621, 13.14399, -87.7293, 13.39793],
        "zoom": 10.6,
    },
    "gt-bethania": {
        "subpage_slug": "evaluacion-riesgo",
        "subpage_label": "Evaluación de Riesgo",
        "layers_summary": "9 capas activas · 199 lotes catastrales + ortofoto UAV + taludes",
        "atlas_pages": 27,
        "docx_file": "Metodologia_gt-bethania.docx",
        "badge_label": "GT · Bethania",
        "label_dir": "top",
        "center": [-90.52035, 14.66843],
        "bbox": [-90.52139, 14.66695, -90.51931, 14.6699],
        "zoom": 17.4,
    },
    "do-santiago": {
        "subpage_slug": "expansion-urbana",
        "subpage_label": "Expansión 2018–2036",
        "layers_summary": "8 capas activas · Serie Sentinel-2 2018–2024 + escenario 2036 + HAND",
        "atlas_pages": 27,
        "docx_file": "Metodologia_do-santiago.docx",
        "badge_label": "DO · Santiago",
        "label_dir": "left",
        "center": [-70.697, 19.4517],
        "bbox": [-70.90852, 19.38343, -70.61675, 19.65088],
        "zoom": 11.3,
    },
    "pa-colon": {
        "subpage_slug": "comparador",
        "subpage_label": "Comparador 2018–2024",
        "layers_summary": "9 capas activas · Comparador Sentinel-2 + LULC 10 m + huella portuaria",
        "atlas_pages": 15,
        "docx_file": "Metodologia_pa-colon.docx",
        "badge_label": "PA · Colón",
        "label_dir": "top",
        "center": [-79.858, 9.332],
        "bbox": [-79.935, 9.255, -79.775, 9.405],
        "zoom": 12.1,
    },
    "hn-distrito-central": {
        "subpage_slug": "brecha-catastral",
        "subpage_label": "Brecha Catastral",
        "layers_summary": "9 capas activas · Malla 250 m + contraste catastral AMDC + multiamenaza",
        "atlas_pages": 37,
        "docx_file": "Metodologia_hn-distrito-central.docx",
        "badge_label": "HN · Distrito Central",
        "label_dir": "right",
        "center": [-87.20542, 14.085],
        "bbox": [-87.48832, 13.89506, -87.00542, 14.37191],
        "zoom": 11.8,
    },
}


def get_project_urls(ctx: SiteContext, pid: str, website: str | None) -> dict[str, str]:
    base = (website or f"https://copernicuscentroamerica.github.io/urbano-{pid}/").rstrip("/")
    enr = PROJECT_ENRICHMENT.get(pid, {})
    sub_slug = enr.get("subpage_slug", "resultados")
    docx_file = enr.get("docx_file", f"Metodologia_{pid}.docx")
    return {
        "home": f"{base}/",
        "geovisor": f"{base}/aplicacion/",
        "atlas_web": f"{base}/resultados/",
        "subpage": f"{base}/{sub_slug}/",
        "atlas_pdf": ctx.site_url(f"assets/descargas/atlas_copernicus_{pid}.pdf"),
        "docx": ctx.site_url(f"assets/descargas/{docx_file}"),
        "detail": ctx.site_url(f"proyectos/{pid}/"),
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
        ("proyectos", "Proyectos y Geovisores", ctx.site_url("proyectos/")),
        ("atlas", "Atlas Regional", ctx.site_url("atlas/")),
        ("recursos", "Metodologías y Código", ctx.site_url("recursos/")),
        ("comunidad", "Comunidad", ctx.site_url("comunidad/")),
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
            f'  <script src="{html.escape(ctx.site_url("assets/js/geovisor.js"), quote=True)}?v=2.3.0"></script>'
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

    sync_label = format_spanish_date(snapshot_generated_at, "Catálogo regional sincronizado")
    upper_bar_html = render_upper_institutional_bar(
        ctx,
        "<strong>Clúster Copernicus Urbano</strong> · Comunidad Urbana Copernicus Centroamérica y República Dominicana",
        f"Última sincronización: <strong>{esc(sync_label)}</strong> · {hub_repo_html}",
    )
    regional_band_html = render_regional_institutional_band(ctx, extra_class="is-footer-band")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(page_title)} · Clúster Copernicus Urbano Centroamérica</title>
  <meta name="description" content="Portal regional del Clúster Copernicus Urbano (Asentamientos Humanos). Acceso directo a los 8 geovisores interactivos, Atlas temáticos (Parte I + Parte II Copernicus) y metodologías reproducibles en Centroamérica y República Dominicana.">
  {robots_meta}
  <link rel="stylesheet" href="{html.escape(ctx.site_url('assets/css/styles.css'), quote=True)}?v=2.4.0">
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
          <span class="brand-subtitle">Clúster de Asentamientos Humanos · Geovisores y Atlas Urbano</span>
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
        <p class="footer-title">Clúster Copernicus Urbano · Centroamérica y República Dominicana</p>
        <p>Articulación de datos satelitales abiertos del Programa Copernicus con información local e institucional generada por los equipos técnicos para apoyar decisiones urbanas en 8 zonas de estudio (Tema común: <code>{esc(THEME_VERSION)}</code>).</p>
      </div>
      <div>
        <p class="footer-title">Accesos directos del portal</p>
        <p>
          <a href="{html.escape(ctx.site_url(''), quote=True)}">Inicio</a> ·
          <a href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">Proyectos y Geovisores</a> ·
          <a href="{html.escape(ctx.site_url('atlas/'), quote=True)}">Atlas Urbano Regional</a> ·
          <a href="{html.escape(ctx.site_url('recursos/'), quote=True)}">Metodologías y Código</a> ·
          <a href="{html.escape(ctx.site_url('comunidad/'), quote=True)}">Comunidad</a>
        </p>
      </div>
      <div>
        <p class="footer-title">Trazabilidad y reproducibilidad</p>
        <p>Cada proyecto publica su propio Geovisor interactivo, su subpágina analítica de resultados, su Atlas temático estructurado (Parte I de resultados locales + Parte II Copernicus) y su documento metodológico descargable.</p>
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
    primary_inst = inst_list[0] if inst_list else "Institución contraparte"
    inst_str = ", ".join(inst_list)
    short_title = SHORT_CARD_TITLES.get(pid, p["title"])
    enr = PROJECT_ENRICHMENT.get(pid, {})
    urls = get_project_urls(ctx, pid, p["links"].get("website"))
    layers_summary = enr.get("layers_summary", "Capas temáticas publicadas en Geovisor")
    sub_label = enr.get("subpage_label", "Resultados")
    atlas_pages = enr.get("atlas_pages", 27)

    search_blob = f"{pid} {short_title} {p['title']} {country_name} {p['territory']['label']} {inst_str} {layers_summary} {' '.join(tags)}"
    detail_href = html.escape(urls["detail"], quote=True)
    geovisor_href = html.escape(urls["geovisor"], quote=True)
    atlas_web_href = html.escape(urls["atlas_web"], quote=True)
    atlas_pdf_href = html.escape(urls["atlas_pdf"], quote=True)
    subpage_href = html.escape(urls["subpage"], quote=True)

    tags_html = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags[:5])

    branding = item.get("branding")
    logo_imgs: list[str] = []
    if isinstance(branding, dict):
        pl = branding.get("project_logo")
        if isinstance(pl, dict) and pl.get("logo_path"):
            lsrc = ctx.site_url(f"assets/img/projects/{pid}/{pl['logo_path']}")
            lalt = esc(pl.get("alt_text") or pl.get("name") or f"Logo {pid}")
            logo_imgs.append(f'<img src="{html.escape(lsrc, quote=True)}" alt="{lalt}" height="24" style="height:24px;width:auto;max-width:74px;object-fit:contain;display:block;background:#FFFFFF;padding:2px 5px;border:1px solid #E2E8F4;border-radius:4px;" loading="lazy">')
        for b_inst in sorted(branding.get("institutions", []), key=lambda x: (int(x.get("order", 99)), str(x.get("id", "")))):
            if len(logo_imgs) >= 3:
                break
            if isinstance(b_inst, dict) and b_inst.get("logo_path"):
                lsrc = ctx.site_url(f"assets/img/projects/{pid}/{b_inst['logo_path']}")
                lalt = esc(b_inst.get("alt_text") or b_inst.get("name") or primary_inst)
                logo_imgs.append(f'<img src="{html.escape(lsrc, quote=True)}" alt="{lalt}" height="24" style="height:24px;width:auto;max-width:74px;object-fit:contain;display:block;background:#FFFFFF;padding:2px 5px;border:1px solid #E2E8F4;border-radius:4px;" loading="lazy">')

    logos_strip_right = f'<div class="card-inst-strip-logos" style="display:flex;align-items:center;gap:0.35rem;flex-wrap:wrap;">{"".join(logo_imgs)}</div>' if logo_imgs else ""
    team_names = [esc(m.get("name", "")) for m in (p.get("team") or []) if isinstance(m, dict) and m.get("name")]
    team_card_html = (
        f'<p style="font-size:0.82rem;color:var(--c-brand-blue);margin:0 0 0.25rem;">'
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
          <span class="badge badge-ok">Atlas {atlas_pages} págs.</span>
        </div>
      </div>
      <h3><a href="{detail_href}" style="color:var(--c-brand-blue);text-decoration:none;">{esc(short_title)}</a></h3>
      <div class="card-inst-strip">
        <div class="card-inst-strip-text">
          <strong>Institución contraparte</strong>
          <span>{esc(primary_inst)}</span>
        </div>
        {logos_strip_right}
      </div>
      {team_card_html}
      <p style="font-size:0.84rem;color:var(--c-text-muted);margin-bottom:0.3rem;"><strong>Territorio:</strong> {esc(p['territory']['label'])}</p>
      <p style="font-size:0.8rem;background:#F3F6FD;border-left:3px solid var(--c-teal);padding:0.35rem 0.55rem;border-radius:4px;margin:0 0 0.5rem;color:var(--c-brand-blue);"><strong>Capas en Geovisor:</strong> {esc(layers_summary)}</p>
      <p style="font-size:0.88rem;">{esc(p['summary'])}</p>
      <div class="tag-list">{tags_html}</div>
      <div class="card-footer" style="display:flex;flex-wrap:wrap;gap:0.4rem;padding-top:0.65rem;">
        <a class="btn btn-primary btn-xs" href="{geovisor_href}" target="_blank" rel="noopener noreferrer">🗺️ Abrir Geovisor ↗</a>
        <a class="btn btn-teal btn-xs" href="{atlas_web_href}" target="_blank" rel="noopener noreferrer">📘 Abrir Atlas ↗</a>
        <a class="btn btn-outline btn-xs" href="{atlas_pdf_href}" download="Atlas_Copernicus_{esc(pid)}.pdf">📥 Atlas PDF</a>
        <a class="btn btn-outline btn-xs" href="{subpage_href}" target="_blank" rel="noopener noreferrer">📊 {esc(sub_label)} ↗</a>
        <a class="btn btn-outline btn-xs" href="{detail_href}">Ficha →</a>
      </div>
    </article>
    """


def build_home_page(
    ctx: SiteContext,
    registry: dict[str, Any],
    catalog_snap: dict[str, Any],
    atlas_snap: dict[str, Any],
) -> str:
    projects_items = catalog_snap.get("projects", [])
    n_initiatives = len(projects_items)
    countries = sorted({it["project"]["country"]["code"] for it in projects_items})
    n_countries = len(countries)

    map_points = []
    matrix_rows = []
    sidebar_rows_by_id: dict[str, str] = {}
    for it in projects_items:
        p = it["project"]
        pid = p["id"]
        gv = it.get("geovisor_summary") or {}
        enr = PROJECT_ENRICHMENT.get(pid, {})
        raw_center = gv.get("center")
        if (
            not isinstance(raw_center, list)
            or len(raw_center) != 2
            or (abs(raw_center[0] - (-84.0)) < 1e-4 and abs(raw_center[1] - 13.5) < 1e-4)
        ):
            center = enr.get("center")
        else:
            center = raw_center
        bbox = gv.get("bbox") or enr.get("bbox")
        zoom = gv.get("zoom") or enr.get("zoom", 12.0)
        badge_lbl = gv.get("badge_label") or enr.get("badge_label") or f"{p['country']['code']} · {pid}"
        label_dir = enr.get("label_dir", "right")
        insts = p["institutional_use"].get("institutions", [])
        primary_inst = insts[0] if insts else "Institución contraparte"
        urls = get_project_urls(ctx, pid, p["links"].get("website"))
        short_lbl = SHORT_CARD_TITLES.get(pid) or gv.get("short_name") or p["title"]

        if center:
            map_points.append(
                {
                    "id": pid,
                    "country_code": p["country"]["code"],
                    "country_name": p["country"]["name"],
                    "badge_label": badge_lbl,
                    "label_dir": label_dir,
                    "short_name": short_lbl,
                    "territory_label": p["territory"]["label"],
                    "institution": primary_inst,
                    "layers_summary": enr.get("layers_summary", ""),
                    "center": center,
                    "bbox": bbox,
                    "zoom": zoom,
                    "geovisor_url": urls["geovisor"],
                    "atlas_url": urls["atlas_web"],
                    "atlas_pdf_url": urls["atlas_pdf"],
                    "subpage_url": urls["subpage"],
                    "detail_url": urls["detail"],
                }
            )
            sidebar_rows_by_id[pid] = (
                f'<div class="hub-zone-row" role="button" tabindex="0" aria-pressed="false" data-hub-focus-zone="{esc(pid)}">'
                f'<div class="hub-zone-row-top">'
                f'<span class="hub-zone-row-name"><span class="hub-zone-row-country">{esc(p["country"]["code"])}</span>{esc(short_lbl)}</span>'
                f'</div>'
                f'<div class="hub-zone-row-bottom">'
                f'<span class="hub-zone-row-meta">{esc(primary_inst)}</span>'
                f'<span class="hub-zone-row-links">'
                f'<a class="hub-mini-link is-gv" href="{html.escape(urls["geovisor"], quote=True)}" target="_blank" rel="noopener noreferrer" data-zone-direct-link="true" title="Abrir Geovisor Interactivo">🗺️ Geovisor</a>'
                f'<a class="hub-mini-link is-atlas" href="{html.escape(urls["atlas_web"], quote=True)}" target="_blank" rel="noopener noreferrer" data-zone-direct-link="true" title="Abrir Atlas Temático Web">📘 Atlas</a>'
                f'<a class="hub-mini-link is-pdf" href="{html.escape(urls["atlas_pdf"], quote=True)}" download="Atlas_Copernicus_{esc(pid)}.pdf" data-zone-direct-link="true" title="Descargar Atlas en PDF">📥 PDF</a>'
                f'</span>'
                f'</div>'
                f'</div>'
            )

        matrix_rows.append(
            f"<tr>"
            f"<td><span class=\"badge badge-country\">{esc(p['country']['code'])}</span> <strong>{esc(p['country']['name'])}</strong></td>"
            f"<td><a href=\"{html.escape(urls['detail'], quote=True)}\"><strong>{esc(short_lbl)}</strong></a><br>"
            f"<span style=\"font-size:0.78rem;color:var(--c-text-muted);\">{esc(enr.get('layers_summary', ''))}</span></td>"
            f"<td style=\"white-space:nowrap;\"><a class=\"btn btn-primary btn-xs\" href=\"{html.escape(urls['geovisor'], quote=True)}\" target=\"_blank\" rel=\"noopener noreferrer\">🗺️ Geovisor ↗</a></td>"
            f"<td style=\"white-space:nowrap;\">"
            f"<a class=\"btn btn-teal btn-xs\" href=\"{html.escape(urls['atlas_web'], quote=True)}\" target=\"_blank\" rel=\"noopener noreferrer\">📘 Atlas Web ↗</a> "
            f"<a class=\"btn btn-outline btn-xs\" href=\"{html.escape(urls['atlas_pdf'], quote=True)}\" download=\"Atlas_Copernicus_{esc(pid)}.pdf\">📥 PDF ({enr.get('atlas_pages', 27)}p)</a>"
            f"</td>"
            f"<td style=\"white-space:nowrap;\">"
            f"<a class=\"btn btn-outline btn-xs\" href=\"{html.escape(urls['subpage'], quote=True)}\" target=\"_blank\" rel=\"noopener noreferrer\">📊 {esc(enr.get('subpage_label', 'Análisis'))} ↗</a> "
            f"<a class=\"btn btn-outline btn-xs\" href=\"{html.escape(urls['docx'], quote=True)}\" download>📄 .docx</a>"
            f"</td>"
            f"</tr>"
        )

    geo_order = [
        "gt-bethania",
        "sv-amss",
        "hn-distrito-central",
        "sv-la-union",
        "cr-la-carpio",
        "pa-colon",
        "pa-panama-oeste",
        "do-santiago",
    ]
    ordered_sidebar_rows = [sidebar_rows_by_id[k] for k in geo_order if k in sidebar_rows_by_id]
    for k, v in sidebar_rows_by_id.items():
        if k not in geo_order:
            ordered_sidebar_rows.append(v)

    safe_points_json = json.dumps(map_points, ensure_ascii=False).replace("</", "<\\/")
    cards_html = "".join(build_project_card_html(ctx, it) for it in projects_items)

    hero = f"""
    <section class="hero hero-home-compact">
      <div class="container hero-home-grid">
        <div>
          <div class="hero-eyebrow">
            <span class="badge badge-lime">Clúster Copernicus Urbano · Centroamérica y República Dominicana</span>
          </div>
          <h1>Observación de la Tierra Copernicus y datos locales para decisiones urbanas</h1>
          <p class="hero-lead">Explora en el mapa regional las <strong>8 zonas de estudio</strong> en 6 países y accede con un clic al <strong>Geovisor interactivo</strong>, <strong>Atlas temático (Parte I + Parte II Copernicus)</strong> y metodología reproducible de cada proyecto.</p>
        </div>
        <div class="hero-kpi-panel" aria-label="Indicadores consolidados y accesos regionales">
          <div class="hero-kpi-grid">
            <div class="hero-kpi-pill"><span class="hero-kpi-val">{n_initiatives}</span><span class="hero-kpi-lbl">Geovisores</span></div>
            <div class="hero-kpi-pill"><span class="hero-kpi-val">{n_countries}</span><span class="hero-kpi-lbl">Países</span></div>
            <div class="hero-kpi-pill"><span class="hero-kpi-val">83</span><span class="hero-kpi-lbl">Capas activas</span></div>
            <div class="hero-kpi-pill"><span class="hero-kpi-val">8 + 1</span><span class="hero-kpi-lbl">Atlas Web/PDF</span></div>
          </div>
          <div class="hero-quick-links">
            <a class="btn btn-primary btn-xs" href="{html.escape(ctx.site_url('atlas/'), quote=True)}">📘 Atlas Urbano Regional</a>
            <a class="btn btn-outline-light btn-xs" href="#acceso-directo-geovisores-atlas">📋 Matriz de los 8 proyectos ↓</a>
            <a class="btn btn-outline-light btn-xs" href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">📂 Catálogo</a>
            <a class="btn btn-outline-light btn-xs" href="{html.escape(ctx.site_url('recursos/'), quote=True)}">📄 Metodologías y Código</a>
          </div>
        </div>
      </div>
    </section>
    """

    body = f"""
    <section class="section hub-map-first-section" id="mapa-regional" aria-label="Mapa regional interactivo de zonas de estudio">
      <div class="hub-map-card">
        <div class="geovisor-toolbar" style="border-radius:0;padding:0.38rem 0.8rem;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:0.35rem;">
          <div style="display:flex;flex-wrap:wrap;align-items:center;gap:0.35rem;">
            <strong style="font-size:0.78rem;white-space:nowrap;">🛰️ Capas Copernicus (23):</strong>
            <select id="hub-basemap-select" aria-label="Seleccionar mapa base o producto Copernicus" style="padding:0.2rem 0.42rem;border-radius:4px;border:1px solid rgba(255,255,255,0.4);font-size:0.75rem;background:#FFFFFF;color:var(--c-brand-blue);font-weight:600;max-width:250px;">
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
            <button type="button" class="btn btn-outline-light btn-xs" data-hub-basemap-quick="copernicus-dem-glo30">⛰️ DEM</button>
            <button type="button" class="btn btn-outline-light btn-xs" data-hub-basemap-quick="esa-worldcover-2021">🏙️ WorldCover</button>
            <button type="button" class="btn btn-outline-light btn-xs" data-hub-basemap-quick="sentinel2-2024">🛰️ S2 2024</button>
            <button type="button" class="btn btn-teal btn-xs" data-hub-basemap-quick="carto-positron">🗺️ Vectorial</button>
          </div>
          <div class="geovisor-toolbar-actions" style="display:flex;flex-wrap:wrap;gap:0.35rem;">
            <button type="button" id="hub-fit-all-zones" class="btn btn-teal btn-xs" style="white-space:nowrap;">🌎 Encuadrar las 8 zonas</button>
            <button type="button" id="hub-toggle-fullscreen" class="btn btn-primary btn-xs" style="white-space:nowrap;">⛶ Pantalla completa</button>
          </div>
        </div>
        <div id="hub-basemap-legend" style="padding:0.24rem 0.85rem;background:#1A2766;color:#E8ECF8;font-size:0.73rem;border-bottom:1px solid rgba(255,255,255,0.12);">
          🗺️ Mapa base vectorial con los perímetros oficiales de las 8 zonas de estudio · Haz clic en un marcador, polígono o fila lateral para explorar cada territorio
        </div>
        <div class="hub-map-workspace">
          <div class="hub-map-stage">
            <div id="hub-regional-map" class="hub-map-canvas" role="region" aria-label="Mapa regional interactivo de las ocho zonas de estudio"></div>
          </div>
          <aside class="hub-zone-sidebar" aria-label="Selector rápido de las ocho zonas de estudio y accesos directos">
            <div class="hub-zone-sidebar-head">
              <div>
                <div class="hub-zone-sidebar-title">🎯 8 Zonas de Estudio</div>
                <div class="hub-zone-sidebar-sub">Clic para acercar mapa · Acceso a Geovisor y Atlas</div>
              </div>
              <button type="button" class="btn btn-primary btn-xs" data-hub-focus-all="true" style="white-space:nowrap;flex-shrink:0;">🌎 Ver las 8</button>
            </div>
            <div class="hub-zone-sidebar-list" id="hub-zone-sidebar-list">
              {"".join(ordered_sidebar_rows)}
            </div>
          </aside>
        </div>
      </div>
      <script id="hub-map-points" type="application/json">{safe_points_json}</script>
    </section>

    <section class="section" id="acceso-directo-geovisores-atlas" aria-labelledby="titulo-acceso-directo">
      <div class="hub-matrix-card">
        <div class="section-header" style="margin-bottom:0.75rem;">
          <div>
            <span class="badge badge-ok">Matriz regional consolidada · {n_initiatives} proyectos en {n_countries} países</span>
            <h2 id="titulo-acceso-directo" style="margin:0.3rem 0 0.2rem;">Acceso directo a Geovisores Interactivos, Atlas Temáticos y Metodologías</h2>
            <p style="margin:0;font-size:0.88rem;color:var(--c-text-muted);">Consulta de un vistazo las capas integradas en cada proyecto y abre directamente su <strong>Geovisor</strong>, su <strong>Atlas Temático (versión interactiva web y PDF institucional)</strong>, su subpágina de resultados y su documento metodológico (<code>.docx</code>).</p>
          </div>
          <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
            <a class="btn btn-teal btn-xs" href="{html.escape(ctx.site_url('atlas/'), quote=True)}">📘 Visor del Atlas Regional →</a>
            <a class="btn btn-outline btn-xs" href="{html.escape(ctx.site_url('assets/descargas/atlas_copernicus_regional.pdf'), quote=True)}" download="Atlas_Urbano_Regional_Copernicus.pdf">📥 Atlas Regional Consolidado (PDF)</a>
          </div>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>País</th>
                <th>Proyecto y capas integradas</th>
                <th>Geovisor Interactivo</th>
                <th>Atlas (Web Parte I+II y PDF)</th>
                <th>Resultados y Metodología</th>
              </tr>
            </thead>
            <tbody>
              {"".join(matrix_rows)}
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="section" id="portafolio-proyectos">
      <div class="section-header">
        <h2>Fichas institucionales del portafolio ({n_initiatives})</h2>
        <a class="btn btn-outline btn-xs" href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">Filtrar y buscar en catálogo →</a>
      </div>
      <div class="grid-3">
        {cards_html}
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

    country_opts = f'<option value="all">Todos los países ({len(countries)})</option>' + "".join(
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
          <span class="badge badge-lime">Catálogo regional · Geovisores y Atlas</span>
        </div>
        <h1>Proyectos del Clúster Copernicus Urbano</h1>
        <p class="hero-lead">Ocho proyectos consolidados en seis países con acceso directo a su Geovisor interactivo, su Atlas temático (Parte I de resultados específicos + Parte II de capas Copernicus), su subpágina analítica y su documento metodológico.</p>
      </div>
    </section>
    """

    body = f"""
    <section class="section" data-catalog-projects>
      <div class="filter-bar" role="search" aria-label="Filtrar proyectos">
        <div class="filter-field" style="flex:2;">
          <label for="f-proj-q">Buscar por título, territorio, institución o capa</label>
          <input id="f-proj-q" type="search" placeholder="Ej. Colón, AMSS, OPAMSS, La Carpio, catastro, riesgo, suelo..." data-filter-search>
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
        page_title="Proyectos y Geovisores",
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
    enr = PROJECT_ENRICHMENT.get(pid, {})
    urls = get_project_urls(ctx, pid, p["links"].get("website"))
    sub_label = enr.get("subpage_label", "Análisis y Resultados")
    atlas_pages = enr.get("atlas_pages", 27)
    layers_summary = enr.get("layers_summary", "Capas publicadas en el Geovisor")

    ac_rows = "".join(
        f"<tr><td><code>{esc(ac['id'])}</code></td><td>{esc(ac['description'])}</td><td>{badge_html(ac['status'])}</td></tr>"
        for ac in p["pmv"].get("acceptance_criteria", [])
    )
    lim_li = "".join(f"<li>{esc(l)}</li>" for l in p.get("limitations", []))

    atlas_links = []
    for ap in atlas_products:
        ahref = html.escape(ctx.site_url(f"atlas/{ap['id']}/"), quote=True)
        atlas_links.append(f'<li><a href="{ahref}"><strong>{esc(ap["title"])}</strong></a> ({esc(ap["publication_status"])})</li>')

    sync_badge = '<span class="badge badge-ok">Productos publicados y sincronizados</span>'

    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <a href="{html.escape(ctx.site_url('proyectos/'), quote=True)}" style="color:#FFFFFF;font-weight:600;">← Catálogo de proyectos</a>
          <span class="badge badge-lime">{esc(p['country']['name'])} ({esc(p['country']['code'])})</span>
          <span class="badge badge-country">ID: {esc(pid)}</span>
          {sync_badge}
        </div>
        <h1>{esc(p['title'])}</h1>
        {render_hero_team(p)}
        <p class="hero-lead">{esc(p['summary'])}</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{html.escape(urls['geovisor'], quote=True)}" target="_blank" rel="noopener noreferrer">🗺️ Abrir Geovisor Interactivo ↗</a>
          <a class="btn btn-teal" href="{html.escape(urls['atlas_web'], quote=True)}" target="_blank" rel="noopener noreferrer">📘 Abrir Atlas Interactivo (Parte I + II) ↗</a>
          <a class="btn btn-outline-light" href="{html.escape(urls['atlas_pdf'], quote=True)}" download="Atlas_Copernicus_{esc(pid)}.pdf">📥 Descargar Atlas PDF ({atlas_pages} págs.)</a>
          <a class="btn btn-outline-light" href="{html.escape(urls['subpage'], quote=True)}" target="_blank" rel="noopener noreferrer">📊 {esc(sub_label)} ↗</a>
          <a class="btn btn-outline-light" href="{html.escape(urls['docx'], quote=True)}" download>📄 Metodología (.docx)</a>
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
      <div class="direct-access-strip">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.75rem;">
          <div>
            <span class="badge badge-ok">Ecosistema completo del proyecto</span>
            <h2 style="margin:0.25rem 0;">Accesos directos a aplicaciones, Atlas y documentación técnica</h2>
            <p style="margin:0;font-size:0.88rem;color:var(--c-text-muted);"><strong>Capas activas en el Geovisor:</strong> {esc(layers_summary)}</p>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:0.45rem;">
            <a class="btn btn-primary btn-xs" href="{html.escape(urls['home'], quote=True)}" target="_blank" rel="noopener noreferrer">🏠 Sitio principal del proyecto ↗</a>
            <a class="btn btn-teal btn-xs" href="{html.escape(urls['geovisor'], quote=True)}" target="_blank" rel="noopener noreferrer">🗺️ Geovisor Interactivo ↗</a>
            <a class="btn btn-teal btn-xs" href="{html.escape(urls['atlas_web'], quote=True)}" target="_blank" rel="noopener noreferrer">📘 Atlas Web (Parte I + II) ↗</a>
            <a class="btn btn-outline btn-xs" href="{html.escape(urls['subpage'], quote=True)}" target="_blank" rel="noopener noreferrer">📊 {esc(sub_label)} ↗</a>
            <a class="btn btn-outline btn-xs" href="{html.escape(urls['atlas_pdf'], quote=True)}" download="Atlas_Copernicus_{esc(pid)}.pdf">📥 Atlas PDF ({atlas_pages} págs.)</a>
            <a class="btn btn-outline btn-xs" href="{html.escape(urls['docx'], quote=True)}" download>📄 Documento Metodológico (.docx)</a>
            <a class="btn btn-outline btn-xs" href="{html.escape(canon_repo_url, quote=True)}" target="_blank" rel="noopener noreferrer">💻 Repositorio GitHub ↗</a>
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
            <h3>Productos integrados en el Atlas Urbano</h3>
            <p style="font-size:0.86rem;color:var(--c-text-muted);">El Atlas de esta iniciativa presenta en sus primeras páginas (<strong>Parte I</strong>) los mapas específicos generados por el equipo combinando datos Copernicus y registros locales, seguidos por las 10 láminas satelitales estandarizadas (<strong>Parte II</strong>).</p>
            <ul>{"".join(atlas_links) if atlas_links else "<li>Publicado en el visor del proyecto</li>"}</ul>
            <div class="card-footer" style="display:flex;gap:0.45rem;flex-wrap:wrap;">
              <a class="btn btn-teal btn-xs" href="{html.escape(urls['atlas_web'], quote=True)}" target="_blank" rel="noopener noreferrer">📘 Abrir Atlas Web ↗</a>
              <a class="btn btn-outline btn-xs" href="{html.escape(urls['atlas_pdf'], quote=True)}" download="Atlas_Copernicus_{esc(pid)}.pdf">📥 Descargar PDF ({atlas_pages} págs.)</a>
            </div>
          </article>

          <article class="card">
            <h3>Trazabilidad y repositorio canónico</h3>
            <p><strong>Repositorio oficial:</strong> <code>{esc(effective_slug)}</code></p>
            <p><strong>Revisión SHA verificada:</strong> <code>{esc((item.get('source_commit') or '')[:12] or None, 'Sincronizado')}</code></p>
            <p><strong>Última sincronización en portal:</strong> {esc(format_spanish_date(item.get('fetched_at')))}</p>
            <p><strong>Actualización de contenido (<code>governance.content_updated_at</code>):</strong> {esc(format_spanish_date(item.get('content_updated_at'), '12 nov 2026'))}</p>
            <div class="card-footer">
              <a class="btn btn-outline btn-xs" href="{html.escape(canon_repo_url, quote=True)}" target="_blank" rel="noopener noreferrer">Ver código y capas en GitHub ↗</a>
            </div>
          </article>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>Criterios de aceptación y verificación técnica del PMV</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>Descripción</th><th>Estado</th></tr></thead>
          <tbody>{ac_rows}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <div class="callout callout-warn">
        <strong>Limitaciones y alcances metodológicos documentados</strong>
        <ul>{lim_li}</ul>
      </div>
    </section>

    {render_project_institutions_band(
        ctx,
        item.get("branding"),
        p,
        colaborar_href=None,
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


def build_legacy_gt_salud_redirect_page(ctx: SiteContext, registry: dict[str, Any], snapshot_generated_at: str | None) -> str:
    colon_detail = html.escape(ctx.site_url("proyectos/pa-colon/"), quote=True)
    colon_pdf = html.escape(ctx.site_url("assets/descargas/atlas_copernicus_pa-colon.pdf"), quote=True)
    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <a href="{html.escape(ctx.site_url('proyectos/'), quote=True)}" style="color:#FFFFFF;font-weight:600;">← Catálogo de proyectos</a>
          <span class="badge badge-lime">Actualización de Cartera · Clúster Copernicus Urbano</span>
        </div>
        <h1>Iniciativa sustituida en la cartera activa por Colón, Panamá (<code>pa-colon</code>)</h1>
        <p class="hero-lead">En el marco de la consolidación empírica del <strong>Clúster de Asentamientos Humanos (Comunidad Urbana Copernicus Centroamérica)</strong>, este espacio fue reemplazado por el proyecto desarrollado en la zona de <strong>Colón, Panamá</strong>: <em>Comparador Multianual de Cobertura Urbana, Logística Portuaria y Expansión Territorial 2018–2024</em>.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{colon_detail}">Ir a la ficha de Colón, Panamá (pa-colon) →</a>
          <a class="btn btn-teal" href="https://copernicuscentroamerica.github.io/urbano-pa-colon/aplicacion/" target="_blank" rel="noopener noreferrer">🗺️ Abrir Geovisor de Colón ↗</a>
          <a class="btn btn-outline-light" href="https://copernicuscentroamerica.github.io/urbano-pa-colon/comparador/" target="_blank" rel="noopener noreferrer">🔀 Abrir Comparador 2018–2024 ↗</a>
          <a class="btn btn-outline-light" href="https://copernicuscentroamerica.github.io/urbano-pa-colon/resultados/" target="_blank" rel="noopener noreferrer">📘 Abrir Atlas de Colón ↗</a>
        </div>
      </div>
    </section>
    """
    body = f"""
    <section class="section">
      <div class="card" style="border-left:5px solid var(--c-brand-blue);">
        <h2>Acceso directo a los productos publicados de Colón, Panamá (<code>pa-colon</code>)</h2>
        <p>El proyecto activo integra series ópticas y clasificaciones supervisadas anuales de 10 m derivadas de <strong>Copernicus Sentinel-2 L2A (2018–2024)</strong> sobre las 24,696.2 ha del corredor urbano-portuario de Colón (Isla Manzanillo, Zona Libre, Cristóbal, Cativá, Sabanitas y Puerto Pilón), combinadas con límites de corregimientos, recintos logísticos y áreas protegidas de manglar.</p>
        <div style="display:flex;flex-wrap:wrap;gap:0.6rem;margin-top:0.75rem;">
          <a class="btn btn-primary btn-xs" href="https://copernicuscentroamerica.github.io/urbano-pa-colon/" target="_blank" rel="noopener noreferrer">🏠 Sitio principal Colón ↗</a>
          <a class="btn btn-teal btn-xs" href="https://copernicuscentroamerica.github.io/urbano-pa-colon/aplicacion/" target="_blank" rel="noopener noreferrer">🗺️ Geovisor Interactivo ↗</a>
          <a class="btn btn-teal btn-xs" href="https://copernicuscentroamerica.github.io/urbano-pa-colon/resultados/" target="_blank" rel="noopener noreferrer">📘 Atlas Interactivo (Parte I + II) ↗</a>
          <a class="btn btn-outline btn-xs" href="{colon_pdf}" download="Atlas_Copernicus_pa-colon.pdf">📥 Descargar Atlas PDF (15 págs.)</a>
          <a class="btn btn-outline btn-xs" href="{colon_detail}">Ver ficha en el Portal Regional →</a>
        </div>
      </div>
    </section>
    """
    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Actualización de cartera: Colón, Panamá (pa-colon)",
        active_nav="proyectos",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=snapshot_generated_at,
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
        urls = get_project_urls(ctx, pid, p_info.get("links", {}).get("website"))
        enr = PROJECT_ENRICHMENT.get(pid, {})
        detail_href = html.escape(ctx.site_url(f"atlas/{ap['id']}/"), quote=True)
        proj_pdf_href = html.escape(urls["atlas_pdf"], quote=True)
        search_txt = f"{ap['title']} {ap['summary']} {c_name} {ap['coverage']['label']} {ap.get('governance', {}).get('institution', '')}"
        cards.append(
            f"""
            <article class="card" data-filter-item
                     data-pproj="{esc(pid)}"
                     data-ptype="{esc(ap['product_type'])}"
                     data-pstatus="{esc(ap['publication_status'])}"
                     data-search-text="{esc(search_txt)}">
              <div style="display:flex;flex-wrap:wrap;gap:0.4rem;justify-content:space-between;">
                <span class="badge badge-country">{esc(c_name)} ({esc(c_code)}) · {esc(pid)}</span>
                {badge_html(ap['publication_status'], 'Catálogo')}
              </div>
              <h3><a href="{detail_href}" style="color:var(--c-navy);text-decoration:none;">{esc(ap['title'])}</a></h3>
              <p>{esc(ap['summary'])}</p>
              <p style="font-size:0.84rem;color:var(--c-text-muted);">
                <strong>Tipo:</strong> <code>{esc(ap['product_type'])}</code> ·
                <strong>Resolución:</strong> {esc(ap['coverage'].get('spatial_resolution'), '10 m / 30 m')}
              </p>
              <div class="card-footer" style="display:flex;flex-wrap:wrap;gap:0.4rem;">
                <a class="btn btn-primary btn-xs" href="{html.escape(urls['atlas_web'], quote=True)}" target="_blank" rel="noopener noreferrer">📘 Atlas Parte I+II ↗</a>
                <a class="btn btn-teal btn-xs" href="{html.escape(urls['geovisor'], quote=True)}" target="_blank" rel="noopener noreferrer">🗺️ Geovisor ↗</a>
                <a class="btn btn-outline btn-xs" href="{proj_pdf_href}" download="Atlas_Copernicus_{esc(pid)}.pdf">📥 PDF ({enr.get('atlas_pages', 27)}p)</a>
                <a class="btn btn-outline btn-xs" href="{detail_href}">Metadatos →</a>
              </div>
            </article>
            """
        )

    perim_path = ROOT / "data" / "perimetros_proyectos.json"
    perims_raw = perim_path.read_text(encoding="utf-8") if perim_path.exists() else "{}"
    safe_perims_json = perims_raw.replace("</", "<\\/")

    proj_options = []
    catalog_proj_opts = ['<option value="all">Todas las zonas de estudio (8)</option>']
    pdf_pills = []
    intro_zone_rows = []
    for idx_p, it in enumerate(catalog_snap.get("projects", [])):
        p = it["project"]
        pid = p["id"]
        c_name = p["country"]["name"]
        c_code = p["country"]["code"]
        t_lbl = p["territory"]["label"]
        urls = get_project_urls(ctx, pid, p["links"].get("website"))
        enr = PROJECT_ENRICHMENT.get(pid, {})
        opt_html = f'<option value="{esc(pid)}">{esc(c_name)} · {esc(t_lbl)} ({esc(pid)})</option>'
        proj_options.append(opt_html)
        catalog_proj_opts.append(opt_html)
        pdf_href = html.escape(urls["atlas_pdf"], quote=True)
        active_cls = " is-active" if idx_p == 0 else " is-filtered-out"
        pdf_pills.append(
            f'<a class="atlas-pdf-pill{active_cls}" data-pdf-project-id="{esc(pid)}" href="{pdf_href}" download="Atlas_Copernicus_{esc(pid)}.pdf">'
            f'📄 Descargar Atlas PDF · {esc(c_name)} ({esc(c_code)}) · {esc(t_lbl)} ({esc(pid)})</a>'
        )
        intro_zone_rows.append(
            f"<tr>"
            f"<td><strong>{esc(c_name)} ({esc(c_code)})</strong></td>"
            f"<td>{esc(SHORT_CARD_TITLES.get(pid, t_lbl))}</td>"
            f"<td><a class=\"btn btn-teal btn-xs\" href=\"{html.escape(urls['atlas_web'], quote=True)}\" target=\"_blank\" rel=\"noopener noreferrer\">📘 Atlas Parte I+II ↗</a></td>"
            f"<td><a class=\"btn btn-primary btn-xs\" href=\"{html.escape(urls['geovisor'], quote=True)}\" target=\"_blank\" rel=\"noopener noreferrer\">🗺️ Abrir Geovisor ↗</a></td>"
            f"<td><a class=\"btn btn-outline btn-xs\" href=\"{pdf_href}\" download=\"Atlas_Copernicus_{esc(pid)}.pdf\">📥 PDF ({enr.get('atlas_pages', 27)} págs.)</a></td>"
            f"</tr>"
        )

    pdf_pills_html = "".join(pdf_pills)
    catalog_proj_opts_html = "".join(catalog_proj_opts)
    reg_pdf_href = html.escape(ctx.site_url("assets/descargas/atlas_copernicus_regional.pdf"), quote=True)
    default_proj_pdf_href = html.escape(ctx.site_url("assets/descargas/atlas_copernicus_pa-panama-oeste.pdf"), quote=True)

    plates_meta = [
        ("sentinel2-cloudless", "🛰️ 1. Mosaicos Anuales Sentinel-2 (2018–2024)"),
        ("copernicus-dem-glo30", "⛰️ 2. Geomorfología y Pendientes (DEM 30 m)"),
        ("esa-worldcover-2021", "🏙️ 3. Cobertura y Mancha Urbana 10 m (WorldCover)"),
        ("s2-lulc-2023", "📈 4. Uso del Suelo Anual 10 m (LULC 2017–2023)"),
        ("s2-l2a-ndvi", "🌿 5. Vegetación Urbana e Islas Verdes (NDVI)"),
        ("s2-l2a-ndbi", "🏗️ 6. Densidad Edificada e Impermeabilización (NDBI)"),
        ("s2-l2a-ndwi", "💧 7. Humedad Superficial y Estrés Térmico (NDWI)"),
        ("s2-l2a-composites", "🔬 8. Falso Color Infrarrojo y SWIR Urbano (S2 L2A)"),
        ("s1-rtc-falsecolor", "📡 9. Morfología Urbana por Radar (Sentinel-1 SAR)"),
        ("jrc-gsw-occurrence", "🌊 10. Agua Superficial e Inundación (JRC)"),
    ]
    hub_plate_tabs = "".join(
        f'<button type="button" class="atlas-plate-tab{" is-active" if i == 0 else ""}" data-atlas-plate="{esc(pk)}">{esc(plbl)}</button>'
        for i, (pk, plbl) in enumerate(plates_meta)
    )

    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <span class="badge badge-lime">Clúster Copernicus Urbano · Atlas Urbano Regional y Ediciones por Proyecto</span>
        </div>
        <h1>Atlas Urbano Regional: Resultados Específicos y Capas Copernicus</h1>
        <p class="hero-lead">Desarrollado en el marco del <strong>Clúster Copernicus Urbano (Comunidad Urbana Copernicus Centroamérica y República Dominicana)</strong>. Cada Atlas integra en su portada y primeras páginas los trabajos analíticos propios de cada territorio (Parte I), seguidos por las series satelitales Copernicus (Parte II), con enlace directo a su Geovisor interactivo.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{reg_pdf_href}" download="Atlas_Urbano_Regional_Copernicus.pdf">📘 Descargar Atlas Regional Consolidado (48 págs. · PDF)</a>
          <a class="btn btn-teal" href="#atlas-copernicus-regional">🛰️ Explorar Visor Regional por Zona</a>
          <a class="btn btn-outline-light" href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">🗺️ Ver todos los Geovisores</a>
        </div>
      </div>
    </section>
    """

    body = f"""
    <section class="section">
      <div class="atlas-intro-institutional" role="region" aria-label="Introducción institucional del Atlas del Clúster Copernicus Urbano">
        <span class="badge badge-lime" style="margin-bottom:0.45rem;">Introducción Institucional · Clúster Copernicus Urbano</span>
        <h2 style="margin:0.2rem 0 0.55rem;color:var(--c-brand-blue);">Cómo la combinación de datos Copernicus y datos locales apoya la toma de decisiones urbanas</h2>
        <p style="margin:0 0 0.65rem;line-height:1.6;">Esta colección cartográfica ha sido desarrollada en el contexto del <strong>Clúster Copernicus Urbano (Clúster de Asentamientos Humanos · Comunidad Urbana Copernicus Centroamérica)</strong>. En cada una de las ocho zonas de estudio, las observaciones satelitales abiertas del Programa Copernicus (<em>Sentinel-2 MSI, Copernicus DEM GLO-30, ESA WorldCover, Sentinel-1 SAR y JRC Global Surface Water</em>) se integran con <strong>datos locales obtenidos y generados por las instituciones contrapartes</strong> —incluyendo catastros municipales, avalúos inmobiliarios, ortofotos de dron, inventarios de amenazas y planes de ordenamiento territorial— para respaldar decisiones concretas de inversión pública, actualización catastral, gestión de suelo y reducción del riesgo de desastres.</p>
        <p style="margin:0 0 0.85rem;line-height:1.6;">Siguiendo el estándar editorial del Clúster, <strong>la portada y las primeras páginas (Parte I)</strong> de cada Atlas presentan los productos analíticos específicos desarrollados en el proyecto, seguidos en la <strong>Parte II</strong> por las 10 láminas satelitales Copernicus estandarizadas. Además del documento estático e interactivo del Atlas, puedes acceder en cualquier momento al <strong>Geovisor Interactivo</strong> de cada zona de estudio mediante los enlaces directos a continuación:</p>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>País</th>
                <th>Zona de estudio / Proyecto</th>
                <th>Atlas Completo del Proyecto (Parte I + II)</th>
                <th>Geovisor Interactivo</th>
                <th>Edición Imprimible PDF</th>
              </tr>
            </thead>
            <tbody>
              {"".join(intro_zone_rows)}
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="section" id="atlas-copernicus-regional" aria-labelledby="titulo-atlas-copernicus-reg">
      <div class="section-header" style="margin-bottom:0.8rem;">
        <div>
          <span class="badge badge-lime">Visor Comparativo Regional · 10 Láminas Copernicus Enmascaradas</span>
          <h2 id="titulo-atlas-copernicus-reg" style="margin:0.3rem 0 0.2rem;">Explorador Satelital Copernicus sobre las 8 Zonas de Estudio</h2>
          <p style="margin:0;color:var(--c-text-muted);font-size:0.93rem;">Selecciona cualquiera de las 8 zonas de estudio activas (incluyendo Colón y Panamá Oeste en Panamá, AMSS y La Unión en El Salvador, Bethania en Guatemala, Distrito Central en Honduras, La Carpio en Costa Rica y Santiago en República Dominicana) para inspeccionar las series 2017–2024.</p>
        </div>
        <div class="filter-field" style="min-width:290px;max-width:420px;">
          <label for="atlas-project-select">Zona de estudio / Iniciativa:</label>
          <select id="atlas-project-select">
            {"".join(proj_options)}
          </select>
        </div>
      </div>

      <div class="atlas-pdf-banner" role="region" aria-label="Descarga del Atlas Regional y por Proyecto en PDF con identidad institucional">
        <div class="atlas-pdf-banner-inner">
          <div class="atlas-pdf-banner-text">
            <span id="atlas-banner-active-zone" class="atlas-pdf-banner-eyebrow">ZONA SELECCIONADA: PANAMÁ · DISTRITOS DE ARRAIJÁN Y LA CHORRERA (PA-PANAMA-OESTE)</span>
            <h3 class="atlas-pdf-banner-title">Descarga del Atlas PDF Correspondiente a la Zona Seleccionada (Parte I + Parte II) y Edición Regional</h3>
            <p class="atlas-pdf-banner-desc">Cada archivo PDF comienza con la portada institucional, la introducción del Clúster Copernicus Urbano con enlace al Geovisor y las láminas de resultados propios del proyecto (Parte I), seguidas del anexo Copernicus (Parte II).</p>
          </div>
          <div class="atlas-pdf-banner-actions">
            <a id="atlas-download-project-pdf" class="btn btn-primary" href="{default_proj_pdf_href}" download="Atlas_Copernicus_pa-panama-oeste.pdf">📥 Descargar Atlas PDF: Panamá Oeste (pa-panama-oeste)</a>
            <button type="button" class="btn btn-teal" data-atlas-export-pdf>🖨️ Exportar lámina / año actual a PDF</button>
            <a class="btn btn-outline-light" href="{reg_pdf_href}" download="Atlas_Urbano_Regional_Copernicus.pdf">📘 Atlas Regional Consolidado (8 Zonas · PDF)</a>
          </div>
        </div>
        <div class="atlas-pdf-project-pills" aria-label="Archivo PDF disponible para la zona de estudio filtrada">
          <span style="font-size:0.75rem;color:var(--c-accent-yellow);font-weight:700;margin-right:0.25rem;">Archivo PDF de la zona filtrada:</span>
          {pdf_pills_html}
          <button type="button" id="atlas-toggle-all-pdfs" class="btn btn-outline-light btn-xs" style="margin-left:auto;">Ver descargas de las 8 zonas</button>
        </div>
      </div>

      <div class="atlas-plate-tabs" role="tablist" aria-label="Láminas temáticas del Atlas Copernicus">
        {hub_plate_tabs}
      </div>

      <div class="atlas-copernicus-shell">
        <div class="atlas-copernicus-map-col">
          <div class="geovisor-toolbar" style="border-radius:0;">
            <div style="display:flex;flex-wrap:wrap;align-items:center;gap:0.5rem;">
              <strong id="atlas-toolbar-plate-label" style="font-size:0.82rem;color:var(--c-accent-yellow);">🛰️ 1. Mosaicos Anuales Sentinel-2 (2018–2024)</strong>
              <label style="display:inline-flex;align-items:center;gap:0.3rem;font-size:0.76rem;color:#FFFFFF;">
                <span>Año / Capa:</span>
                <select id="atlas-toolbar-variant-select" class="atlas-toolbar-select" aria-label="Seleccionar año o variante de la lámina en la barra del mapa"></select>
              </label>
              <button type="button" id="atlas-toolbar-play-btn" class="atlas-play-btn" title="Reproducir o pausar secuencia multitemporal animada">▶ Reproducir serie</button>
              <label style="display:inline-flex;align-items:center;gap:0.35rem;font-size:0.76rem;background:rgba(255,255,255,0.12);padding:0.2rem 0.48rem;border-radius:4px;cursor:pointer;">
                <input type="checkbox" id="atlas-toggle-mask" checked>
                <span>Enmascarar límite</span>
              </label>
              <label style="display:inline-flex;align-items:center;gap:0.3rem;font-size:0.74rem;">
                <span>Opacidad:</span>
                <input type="range" id="atlas-mask-opacity" min="0" max="1" step="0.05" value="0.88" style="width:68px;" aria-label="Opacidad de la máscara del límite">
              </label>
            </div>
            <div class="geovisor-toolbar-actions">
              <button type="button" id="atlas-fit-bounds" class="btn btn-outline-light btn-xs">Encuadrar límite</button>
              <button type="button" class="btn btn-outline-light btn-xs" data-atlas-export-pdf title="Exportar la lámina y año actual a formato PDF institucional">🖨️ Lámina a PDF</button>
              <button type="button" id="atlas-toggle-fullscreen" class="btn btn-primary btn-xs">⛶ Pantalla completa</button>
            </div>
          </div>
          <div class="atlas-map-stage">
            <div id="atlas-map-year-badge" class="atlas-map-year-badge" aria-live="polite">
              <span id="atlas-map-year-top" class="atlas-map-year-badge-top">SERIE MULTITEMPORAL (7/7)</span>
              <span id="atlas-map-year-main" class="atlas-map-year-badge-main">2024</span>
            </div>
            <div id="atlas-copernicus-map" class="atlas-copernicus-canvas" data-center="[-79.78, 8.95]" data-zoom="10.8" role="region" aria-label="Mapa del Atlas Temático Copernicus enmascarado con la zona de estudio"></div>
          </div>
        </div>

        <div class="atlas-copernicus-info-col" id="atlas-plate-detail">
          <div>
            <span id="atlas-plate-badge" class="badge badge-lime">Lámina 1 · 2024</span>
            <h3 id="atlas-plate-title" style="margin:0.35rem 0 0.25rem;font-size:1.1rem;color:var(--c-brand-blue);">Mosaico Anual sin Nubes Copernicus Sentinel-2 Cloudless · Año 2024 (10 m)</h3>
            <p style="margin:0;font-size:0.8rem;color:var(--c-text-muted);"><strong>Sensor / Fuente:</strong> <span id="atlas-plate-sensor">Copernicus Sentinel-2 MSI · Mosaicos anuales sin nubes (10 m)</span></p>
            <p style="margin:0.15rem 0 0;font-size:0.78rem;color:var(--c-text-muted);"><strong>Parámetro / Expresión:</strong> <code id="atlas-plate-formula">Compuesto anual óptico en Color Verdadero RGB (B04-B03-B02)</code></p>
          </div>

          <div class="atlas-variant-box">
            <label for="atlas-panel-variant-select" id="atlas-variant-selector-label" class="atlas-variant-box-label">📅 Seleccionar año o variante de la capa:</label>
            <select id="atlas-panel-variant-select" class="atlas-variant-select" aria-label="Selector desplegable de año o capa del tema"></select>
            <div id="atlas-variant-pills" class="atlas-variant-pills" role="group" aria-label="Botones rápidos de año o variante"></div>
            <div id="atlas-timeline-controls" class="atlas-timeline-controls" aria-label="Controles de animación multitemporal">
              <div class="atlas-timeline-row">
                <button type="button" id="atlas-panel-play-btn" class="atlas-play-btn">▶ Reproducir secuencia</button>
                <button type="button" id="atlas-step-prev" class="atlas-step-btn" title="Año anterior">⏮ Ant.</button>
                <button type="button" id="atlas-step-next" class="atlas-step-btn" title="Año siguiente">Sig. ⏭</button>
                <select id="atlas-play-speed" class="atlas-speed-select" aria-label="Velocidad de la animación">
                  <option value="2800">Lento (2.8 s)</option>
                  <option value="1800" selected>Normal (1.8 s)</option>
                  <option value="1000">Rápido (1.0 s)</option>
                </select>
              </div>
              <div class="atlas-timeline-row" style="gap:0.5rem;">
                <input type="range" id="atlas-timeline-slider" min="0" max="6" step="1" value="6" style="flex:1;" aria-label="Deslizador de línea de tiempo">
                <span id="atlas-timeline-counter" style="font-size:0.74rem;font-weight:700;color:var(--c-brand-blue);min-width:44px;text-align:right;">7 / 7</span>
              </div>
            </div>
          </div>

          <div style="background:#F3F6FD;border-left:3px solid var(--c-brand-blue);padding:0.65rem 0.8rem;border-radius:4px;font-size:0.85rem;line-height:1.45;">
            <strong style="color:var(--c-brand-blue);display:block;margin-bottom:0.2rem;">Lectura e interpretación territorial de la lámina:</strong>
            <span id="atlas-plate-reading">Permite inspeccionar visualmente la evolución física del territorio año por año entre 2018 y 2024.</span>
          </div>

          <div>
            <h4 style="margin:0 0 0.45rem;font-size:0.86rem;text-transform:uppercase;letter-spacing:0.03em;color:var(--c-brand-blue);">Guía de interpretación de los colores de la leyenda</h4>
            <ul id="atlas-plate-swatches" class="atlas-swatch-list"></ul>
          </div>

          <div style="margin-top:auto;padding-top:0.55rem;border-top:1px solid var(--c-border);display:flex;flex-wrap:wrap;gap:0.45rem;">
            <a id="atlas-panel-download-pdf" class="btn btn-primary btn-xs" href="{default_proj_pdf_href}" download="Atlas_Copernicus_pa-panama-oeste.pdf">📥 Descargar Atlas PDF (pa-panama-oeste)</a>
            <button type="button" class="btn btn-teal btn-xs" data-atlas-export-pdf>🖨️ Exportar lámina / año actual a PDF</button>
          </div>
        </div>
      </div>
      <script id="atlas-perimeters-json" type="application/json">{safe_perims_json}</script>
    </section>

    <section class="section" data-catalog-atlas>
      <div class="section-header">
        <h2>Fichas catalográficas de productos del Atlas por proyecto ({len(products)})</h2>
      </div>
      <div class="filter-bar" role="search" aria-label="Filtrar catálogo del Atlas">
        <div class="filter-field" style="flex:1.5;">
          <label for="f-atlas-q">Buscar por territorio, institución o indicador</label>
          <input id="f-atlas-q" type="search" placeholder="Ej. valor del suelo, Colón, brecha catastral, exposición, Santiago..." data-filter-search>
        </div>
        <div class="filter-field">
          <label for="f-atlas-project">Zona de estudio / Iniciativa</label>
          <select id="f-atlas-project" data-filter-select="pproj">{catalog_proj_opts_html}</select>
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
        <span>Restablece los filtros para explorar todos los productos publicados.</span>
      </div>

      <div class="grid-2">
        {"".join(cards)}
      </div>
    </section>
    """

    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Atlas Urbano Regional y Láminas Copernicus",
        active_nav="atlas",
        hero_html=hero,
        body_html=body,
        include_maplibre=True,
        snapshot_generated_at=atlas_snap.get("generated_at"),
    )


def build_atlas_detail_page(ctx: SiteContext, registry: dict[str, Any], ap: dict[str, Any], parent_proj: dict[str, Any] | None, snapshot_generated_at: str | None) -> str:
    pid = ap["project_id"]
    urls = get_project_urls(ctx, pid, parent_proj["links"].get("website") if parent_proj else None)
    proj_href = html.escape(urls["detail"], quote=True)

    outs = ap["outputs"]
    viewer_btn = render_link_or_pending(outs.get("viewer_url") or urls["atlas_web"], "Abrir Atlas Interactivo del proyecto", "Visor directo aún no publicado", "btn btn-teal")
    dl_btn = (
        f'<a class="btn btn-outline" href="{html.escape(urls["atlas_pdf"], quote=True)}" download="Atlas_Copernicus_{esc(pid)}.pdf">📥 Descargar Atlas PDF ({esc(pid)})</a>'
    )

    lim_li = "".join(f"<li>{esc(l)}</li>" for l in ap.get("limitations", [])) or "<li>Documentado en la nota metodológica de la iniciativa.</li>"

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
          <a class="btn btn-primary" href="{html.escape(urls['geovisor'], quote=True)}" target="_blank" rel="noopener noreferrer">🗺️ Abrir Geovisor del proyecto ↗</a>
          <a class="btn btn-teal" href="{html.escape(urls['atlas_web'], quote=True)}" target="_blank" rel="noopener noreferrer">📘 Abrir Atlas Interactivo (Parte I+II) ↗</a>
          <a class="btn btn-outline-light" href="{proj_href}">Ficha de la iniciativa ({esc(pid)})</a>
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
            <tr><th>Resolución espacial / escala</th><td>{esc(cov.get('spatial_resolution'), '10 m / 30 m')} (denominador de escala: {esc(cov.get('scale_denominator'), 'escala metropolitana / local')})</td></tr>
            <tr><th>Periodo temporal</th><td>Inicio: {esc(temp.get('start'), '2018')} · Fin: {esc(temp.get('end'), '2025')} · Fecha referencia: {esc(temp.get('reference_date'), '2025')}</td></tr>
            <tr><th>Indicador y unidad</th><td><strong>{esc(ind.get('name'), 'Indicador territorial')}</strong> · Unidad: <code>{esc(ind.get('unit'), 'ha / índice')}</code></td></tr>
            <tr><th>Definición y regla de agregación</th><td>{esc(ind.get('definition'), '—')}<br><strong>Agregación:</strong> {esc(ind.get('aggregation'), '—')}</td></tr>
            <tr><th>Método y versión</th><td>{esc(ap['method'].get('description'), 'Documentado en metodología')} (versión: <code>{esc(ap['method'].get('version'), '1.0.0')}</code>)</td></tr>
            <tr><th>Institución y mantenimiento</th><td>{esc(gov.get('institution'), 'Institución contraparte')} · Responsable: {esc(gov.get('maintainer'), 'Equipo técnico')} · Frecuencia: {esc(gov.get('update_frequency'), 'Anual')}</td></tr>
            <tr><th>Licencia y reutilización</th><td>{esc(lic.get('name'), 'CC BY 4.0')} — {esc(lic.get('reuse_note'), 'Atribución institucional requerida')}</td></tr>
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


def build_recursos_page(ctx: SiteContext, registry: dict[str, Any], catalog_snap: dict[str, Any]) -> str:
    colab_url = "https://colab.research.google.com/github/copernicuscentroamerica/clusterurbano/blob/main/web/assets/descargas/mancha_urbana_sentinel2_vmod01.ipynb"
    nb_dl = html.escape(ctx.site_url("assets/descargas/mancha_urbana_sentinel2_vmod01.ipynb"), quote=True)
    pptx_dl = html.escape(ctx.site_url("assets/descargas/scrum_aplicacion_geoespacial_Sesion_7_Previa_Encuentro.pptx"), quote=True)
    docx_dl = html.escape(ctx.site_url("assets/descargas/Manual_Guia_Antigravity_Proyectos_Copernicus.docx"), quote=True)
    reg_pdf_dl = html.escape(ctx.site_url("assets/descargas/atlas_copernicus_regional.pdf"), quote=True)

    doc_rows = []
    for it in catalog_snap.get("projects", []):
        p = it["project"]
        pid = p["id"]
        enr = PROJECT_ENRICHMENT.get(pid, {})
        urls = get_project_urls(ctx, pid, p["links"].get("website"))
        repo_url = p["links"].get("repository") or f"https://github.com/copernicuscentroamerica/urbano-{pid}"
        doc_rows.append(
            f"<tr>"
            f"<td><strong>{esc(p['country']['name'])} ({esc(p['country']['code'])})</strong></td>"
            f"<td><a href=\"{html.escape(urls['detail'], quote=True)}\"><strong>{esc(SHORT_CARD_TITLES.get(pid, p['title']))}</strong></a></td>"
            f"<td><a class=\"btn btn-primary btn-xs\" href=\"{html.escape(urls['docx'], quote=True)}\" download>📄 Metodología (.docx)</a></td>"
            f"<td><a class=\"btn btn-teal btn-xs\" href=\"{html.escape(urls['atlas_pdf'], quote=True)}\" download=\"Atlas_Copernicus_{esc(pid)}.pdf\">📥 Atlas PDF ({enr.get('atlas_pages', 27)}p)</a></td>"
            f"<td>"
            f"<a class=\"btn btn-outline btn-xs\" href=\"{html.escape(urls['subpage'], quote=True)}\" target=\"_blank\" rel=\"noopener noreferrer\">📊 {esc(enr.get('subpage_label', 'Resultados'))} ↗</a> "
            f"<a class=\"btn btn-outline btn-xs\" href=\"{html.escape(repo_url, quote=True)}\" target=\"_blank\" rel=\"noopener noreferrer\">💻 GitHub ↗</a>"
            f"</td>"
            f"</tr>"
        )

    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <span class="badge badge-lime">Biblioteca Metodológica, Atlas PDF y Scripts Reproducibles</span>
        </div>
        <h1>Metodologías documentadas, Atlas descargables y código abierto</h1>
        <p class="hero-lead">Repositorio consolidado de los documentos metodológicos en Word (<code>.docx</code>), ediciones imprimibles de los Atlas (Parte I + Parte II Copernicus), scripts en Google Earth Engine / Python y estándares técnicos GeoLibre de las 8 iniciativas.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{reg_pdf_dl}" download="Atlas_Urbano_Regional_Copernicus.pdf">📘 Descargar Atlas Regional Consolidado (PDF)</a>
          <a class="btn btn-teal" href="{html.escape(ctx.site_url('atlas/'), quote=True)}">🛰️ Abrir Atlas Urbano Regional</a>
        </div>
      </div>
    </section>
    """

    body = f"""
    <section class="section">
      <div class="section-header">
        <div>
          <h2>Documentos metodológicos (.docx), Atlas PDF y repositorios de los 8 proyectos</h2>
          <p style="margin:0.15rem 0 0;font-size:0.9rem;color:var(--c-text-muted);">Descarga directa de la documentación técnica de cada estudio de caso, junto con su Atlas estructurado y acceso a sus scripts de procesamiento satelital.</p>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>País</th>
              <th>Iniciativa</th>
              <th>Documento Metodológico</th>
              <th>Atlas Institucional PDF</th>
              <th>Análisis Web y Código</th>
            </tr>
          </thead>
          <tbody>
            {"".join(doc_rows)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Guías transversales y cuadernos base de procesamiento Copernicus</h2>
      <div class="grid-3">
        <article class="card" style="border-left:4px solid var(--c-navy);">
          <span class="badge badge-ok">Guía técnica (.docx)</span>
          <h3>Manual de Desarrollo Geoespacial Reproducible</h3>
          <p>Documentación de arquitectura de repositorios, validación de esquemas JSON Schema Draft 2020-12 y publicación de capas en Geovisores basados en MapLibre y GeoLibre Studio.</p>
          <div class="card-footer">
            <a class="btn btn-primary btn-xs" href="{docx_dl}" download="Manual_Guia_Antigravity_Proyectos_Copernicus.docx">Descargar Manual (.docx)</a>
          </div>
        </article>

        <article class="card" style="border-left:4px solid var(--c-teal);">
          <span class="badge badge-ok">Cuaderno Jupyter (.ipynb)</span>
          <h3> Flujo Base Sentinel-2 L2A y Random Forest</h3>
          <p>Cuaderno reproducible en Python con compuesto libre de nubes (<code>SCL</code>), 12 predictores espectrales/texturales y clasificación supervisada exportable a GeoTIFF/COG y GeoJSON.</p>
          <div class="card-footer">
            <a class="btn btn-teal btn-xs" href="{html.escape(colab_url, quote=True)}" target="_blank" rel="noopener noreferrer">Abrir en Google Colab ↗</a>
            <a class="btn btn-outline btn-xs" href="{nb_dl}" download="mancha_urbana_sentinel2_vmod01.ipynb">Descargar .ipynb</a>
          </div>
        </article>

        <article class="card" style="border-left:4px solid var(--c-lime);">
          <span class="badge badge-declarado">Marco metodológico (.pptx)</span>
          <h3>Gestión Iterativa de Aplicaciones Geoespaciales</h3>
          <p>Síntesis de estructuración de productos mínimos viables (PMV), criterios de aceptación espaciales y control de calidad cartográfico para equipos institucionales.</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="{pptx_dl}" download="scrum_aplicacion_geoespacial_Sesion_7_Previa_Encuentro.pptx">Descargar .pptx</a>
          </div>
        </article>
      </div>
    </section>

    <section class="section">
      <h2>Especificación de formatos espaciales en los Geovisores y GeoLibre Studio</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Formato</th>
              <th>Visualización</th>
              <th>Integración técnica</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>.geojson</code>, <code>.topojson</code>, <code>.kml</code> (<code>EPSG:4326</code>)</td>
              <td><strong>Visor integrado MapLibre GL JS</strong> y <strong>GeoLibre Studio</strong></td>
              <td>Renderizado vectorial directo con simbología temática categorizada o graduada, leyendas automáticas e inspección de atributos saneados al clic.</td>
            </tr>
            <tr>
              <td><code>.png</code> / <code>.webp</code> georreferenciado + <code>.tif</code> (COG)</td>
              <td><strong>Superposición ráster inmediata</strong> en el visor web + transferencia COG a <strong>GeoLibre Studio</strong></td>
              <td>Permite inspeccionar modelos continuos a nivel de píxel (valor del suelo, NDBI, NDVI, ortofotos UAV y series LULC 2018–2024) sin latencia de servidor externo.</td>
            </tr>
            <tr>
              <td><code>proyecto.geolibre.json</code> (v0.2.0)</td>
              <td><strong>GeoLibre Studio</strong> (<code>web.geolibre.app</code>)</td>
              <td>Empaquetado determinista generado por <code>scripts/build_site.py</code> con vista inicial, estilo base y capas activas listas para análisis SIG avanzado en navegador.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    """

    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Metodologías, Atlas PDF y Código",
        active_nav="recursos",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=catalog_snap.get("generated_at"),
    )


def build_comunidad_page(ctx: SiteContext, registry: dict[str, Any], catalog_snap: dict[str, Any]) -> str:
    proj_map = {it["project"]["id"]: it["project"] for it in catalog_snap.get("projects", [])}
    hub_repo = registry.get("hub", {}).get("repository") or "copernicuscentroamerica/clusterurbano"
    discussions_url = f"https://github.com/{hub_repo}/discussions"
    hub_repo_url = f"https://github.com/{hub_repo}"
    whatsapp_url = "https://chat.whatsapp.com/Kow0VLer8eg1XhfMtVHUoQ?s=hd&p=i&mlu=4&ilr=4&iam=2"
    portal_canonical_url = "https://copernicuscentroamerica.github.io/clusterurbano/"
    pres_pdf_url = ctx.site_url("assets/descargas/Presentacion_Lanzamiento_Comunidad_Copernicus_Urbano_2026-11-12.pdf")
    qr_wa_src = ctx.site_url("assets/img/comunidad/qr-whatsapp-comunidad.png")
    qr_portal_src = ctx.site_url("assets/img/comunidad/qr-portal-comunidad.png")

    country_network = [
        {
            "code": "SV · 2",
            "country": "El Salvador",
            "territories": "AMSS · Conchagua y La Unión",
            "institutions": [
                ("OPAMSS", "Oficina de Planificación del Área Metropolitana de San Salvador"),
                ("UCA", "Universidad Centroamericana José Simeón Cañas"),
                ("UNAB", "Universidad Dr. Andrés Bello"),
                ("MIVI", "Ministerio de Vivienda"),
            ],
            "projects": [
                ("sv-amss", "AMSS · San Salvador"),
                ("sv-la-union", "Conchagua y La Unión"),
            ],
        },
        {
            "code": "HN · 1",
            "country": "Honduras",
            "territories": "Distrito Central",
            "institutions": [
                ("AMDC", "Alcaldía Municipal del Distrito Central"),
                ("UNAH · MODUS", "Universidad Nacional Autónoma de Honduras; grupo Movilidad y Desarrollo Urbano Sostenible"),
                ("SEGOB", "Secretaría de Gobernación, Justicia y Descentralización"),
            ],
            "projects": [
                ("hn-distrito-central", "Distrito Central"),
            ],
        },
        {
            "code": "GT · 1",
            "country": "Guatemala",
            "territories": "Bethania · Nueva León de Judá",
            "institutions": [
                ("UDEVIPO", "Unidad para el Desarrollo de Vivienda Popular"),
            ],
            "projects": [
                ("gt-bethania", "Bethania · Ciudad de Guatemala"),
            ],
        },
        {
            "code": "CR · 1",
            "country": "Costa Rica",
            "territories": "La Carpio · San José",
            "institutions": [
                ("Municipalidad de San José", "Gobierno local del cantón central"),
                ("INVU", "Instituto Nacional de Vivienda y Urbanismo"),
                ("MIVAH", "Ministerio de Vivienda y Asentamientos Humanos"),
            ],
            "projects": [
                ("cr-la-carpio", "La Carpio · San José"),
            ],
        },
        {
            "code": "PA · 2",
            "country": "Panamá",
            "territories": "Panamá Oeste · Colón",
            "institutions": [
                ("MIVIOT", "Ministerio de Vivienda y Ordenamiento Territorial"),
                ("Municipio de Colón", "Alcaldía del Distrito de Colón"),
                ("MIVIOT", "Regional Colón"),
            ],
            "projects": [
                ("pa-panama-oeste", "Panamá Oeste"),
                ("pa-colon", "Colón · Corredor portuario"),
            ],
        },
        {
            "code": "DO · 1",
            "country": "República Dominicana",
            "territories": "Santiago de los Caballeros",
            "institutions": [
                ("MINPRE", "Ministerio de la Presidencia"),
                ("UEP-C2", "Unidad Ejecutora del Proyecto, Componente 2"),
                ("Usuario principal", "Ayuntamiento de Santiago"),
            ],
            "projects": [
                ("do-santiago", "Santiago de los Caballeros"),
            ],
        },
    ]

    country_cards_html = []
    for c_item in country_network:
        inst_lis = "".join(
            f"<li><strong>{esc(sigla)}</strong> · {esc(desc)}</li>"
            for sigla, desc in c_item["institutions"]
        )
        proj_rows_mini = []
        for pid, short_lbl in c_item["projects"]:
            p_obj = proj_map.get(pid, {})
            urls = get_project_urls(ctx, pid, p_obj.get("links", {}).get("website"))
            proj_rows_mini.append(
                f'<div class="comm-proj-mini-row">'
                f'<a class="comm-proj-mini-title" href="{html.escape(urls["detail"], quote=True)}">{esc(short_lbl)}</a>'
                f'<span class="comm-proj-mini-links">'
                f'<a class="btn btn-primary btn-xs" href="{html.escape(urls["geovisor"], quote=True)}" target="_blank" rel="noopener noreferrer">🗺️ Geovisor ↗</a>'
                f'<a class="btn btn-teal btn-xs" href="{html.escape(urls["atlas_web"], quote=True)}" target="_blank" rel="noopener noreferrer">📘 Atlas ↗</a>'
                f"</span>"
                f"</div>"
            )
        country_cards_html.append(
            f'<article class="comm-country-card">'
            f"<div>"
            f'<div class="comm-country-top">'
            f"<div>"
            f'<h3 class="comm-country-name">{esc(c_item["country"])}</h3>'
            f'<p class="comm-country-territories">{esc(c_item["territories"])}</p>'
            f"</div>"
            f'<span class="comm-country-badge">{esc(c_item["code"])}</span>'
            f"</div>"
            f'<ul class="comm-inst-ul" style="margin-top:0.75rem;">{inst_lis}</ul>'
            f"</div>"
            f'<div class="comm-country-projects">{"".join(proj_rows_mini)}</div>'
            f"</article>"
        )

    hn_urls = get_project_urls(
        ctx,
        "hn-distrito-central",
        proj_map.get("hn-distrito-central", {}).get("links", {}).get("website"),
    )

    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <span class="badge badge-lime">Comunidad de Práctica · Clúster Copernicus Urbano</span>
          <span class="badge badge-ok">Lanzamiento · San Salvador · 12 de noviembre de 2026</span>
        </div>
        <h1>Comunidad de Práctica Regional · Centroamérica y República Dominicana</h1>
        <p class="hero-lead"><strong>8 iniciativas activas · 6 países.</strong> Imágenes satelitales, inteligencia artificial y visualización territorial para la toma de decisiones en Costa Rica, El Salvador, Guatemala, Honduras, Panamá y República Dominicana.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{html.escape(whatsapp_url, quote=True)}" target="_blank" rel="noopener noreferrer">💬 Unirse al Espacio de WhatsApp ↗</a>
          <a class="btn btn-teal" href="{html.escape(pres_pdf_url, quote=True)}" download="Presentacion_Lanzamiento_Comunidad_Copernicus_Urbano_2026-11-12.pdf">📥 Presentación de lanzamiento (PDF)</a>
          <a class="btn btn-outline-light" href="{html.escape(discussions_url, quote=True)}" target="_blank" rel="noopener noreferrer">💻 Foro técnico en GitHub ↗</a>
          <a class="btn btn-outline-light" href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">🗺️ Explorar los 8 Proyectos →</a>
        </div>
      </div>
    </section>
    """

    body = f"""
    <section class="section" id="objetivo-y-proxima-actividad">
      <div class="comm-top-split">
        <article class="comm-objective-card">
          <div>
            <span class="comm-eyebrow">01 — Objetivo de la Comunidad</span>
            <p class="comm-objective-quote">«Mantener los lazos cercanos entre las personas de la región que utilizan herramientas tecnológicas, IA e imágenes satelitales para innovar en metodologías y visualización de información territorial para la toma de decisiones.»</p>
          </div>
          <div class="comm-launch-meta">
            <span>📍 <strong>Taller de uso de imágenes satelitales:</strong> San Salvador (<code>13.69° N · 89.19° W</code>)</span>
            <span>📅 <strong>Lanzamiento oficial:</strong> 12 de noviembre de 2026</span>
            <span>🌎 <strong>Base inicial:</strong> 08 iniciativas activas · 06 países</span>
          </div>
        </article>

        <aside class="comm-next-event-card" aria-label="Próxima actividad de la Comunidad">
          <div>
            <span class="comm-next-event-eyebrow">09 — Próxima actividad</span>
            <div class="comm-next-event-date-big">07.12</div>
            <h2 class="comm-next-event-title">Presentación de los servicios Copernicus</h2>
            <p class="comm-next-event-details">Copernicus Chile · San Salvador · Lunes 7 de diciembre de 2026</p>
          </div>
          <p class="comm-next-event-note">🕒 Hora y lugar: por confirmar · Convocatoria y detalles en el espacio de WhatsApp.</p>
        </aside>
      </div>
    </section>

    <section class="section" id="canales-y-puertas">
      <div class="comm-section-head">
        <span class="comm-eyebrow">06 &amp; 07 — Canales de comunicación y puertas de entrada</span>
        <h2>Cómo nos mantenemos conectados</h2>
        <p>Tres espacios complementarios articulan el intercambio cotidiano, la documentación técnica reproducible y los encuentros regionales de seguimiento.</p>
      </div>

      <div class="comm-channels-grid">
        <article class="comm-channel-card">
          <span class="comm-status-pill is-active">Activo</span>
          <h3>💬 Espacio de WhatsApp</h3>
          <p>Asuntos de mapeo y herramientas de análisis de imágenes satelitales; convocatorias a congresos, eventos, programas, podcasts y webinars.</p>
        </article>
        <article class="comm-channel-card">
          <span class="comm-status-pill is-active">Activo</span>
          <h3>🌐 Portal y GitHub</h3>
          <p>Proyectos, geovisores, Atlas, metodologías y código. Foro técnico en <a href="{html.escape(discussions_url, quote=True)}" target="_blank" rel="noopener noreferrer">GitHub Discussions ↗</a> para preguntas y <a href="{html.escape(hub_repo_url, quote=True)}" target="_blank" rel="noopener noreferrer">repositorios abiertos ↗</a> para contribuir.</p>
        </article>
        <article class="comm-channel-card">
          <span class="comm-status-pill is-quarterly">Trimestral</span>
          <h3>🤝 Encuentros de la comunidad</h3>
          <p>Sesiones presenciales o virtuales para presentar avances de las ciudades y equipos técnicos, resolver dudas metodológicas y planear actividades conjuntas.</p>
        </article>
      </div>

      <div class="comm-doors-grid">
        <article class="comm-qr-card">
          <div class="comm-qr-frame">
            <img src="{html.escape(qr_wa_src, quote=True)}" alt="Código QR oficial para unirse al espacio de WhatsApp de la Comunidad de Práctica del Clúster Copernicus Urbano" loading="lazy">
          </div>
          <div class="comm-qr-body">
            <span class="comm-qr-code-tag">QR-01 // WHATSAPP</span>
            <h3>WhatsApp para participar en el intercambio</h3>
            <p>Escanea el código QR con tu teléfono o utiliza el enlace directo para integrarte al canal regional de especialistas, instituciones y universidades.</p>
            <div class="comm-qr-actions">
              <a class="btn btn-primary" href="{html.escape(whatsapp_url, quote=True)}" target="_blank" rel="noopener noreferrer">Abrir WhatsApp ↗</a>
            </div>
          </div>
        </article>

        <article class="comm-qr-card">
          <div class="comm-qr-frame">
            <img src="{html.escape(qr_portal_src, quote=True)}" alt="Código QR oficial para acceder al Portal del Clúster Copernicus Urbano con proyectos, Atlas y recursos" loading="lazy">
          </div>
          <div class="comm-qr-body">
            <span class="comm-qr-code-tag">QR-02 // PORTAL</span>
            <h3>Portal para consultar proyectos, Atlas y recursos</h3>
            <p>Punto de acceso unificado a los 8 geovisores interactivos, láminas del Atlas Urbano Regional y documentos metodológicos (<code>clusterurbano</code>).</p>
            <div class="comm-qr-actions">
              <a class="btn btn-primary" href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">Explorar proyectos →</a>
              <a class="btn btn-outline-light" href="{html.escape(portal_canonical_url, quote=True)}" target="_blank" rel="noopener noreferrer">Portal oficial ↗</a>
            </div>
          </div>
        </article>
      </div>
    </section>

    <section class="section" id="plan-anual-actividades">
      <div class="comm-section-head">
        <span class="comm-eyebrow">08 — Plan de actividades</span>
        <h2>Cuatro actividades mínimas al año</h2>
        <p>Ciclo anual de intercambio continuo entre equipos institucionales, universidades y especialistas en observación de la Tierra de la región.</p>
      </div>

      <div class="comm-quarters-grid">
        <article class="comm-quarter-card">
          <div class="comm-quarter-head">
            <span class="comm-quarter-code">T1</span>
            <span class="comm-quarter-months">ENE — MAR</span>
          </div>
          <h3>Encuentro de la comunidad</h3>
          <p>Arranque del año: integración de miembros, presentación de avances territoriales y definición de la agenda común.</p>
        </article>

        <article class="comm-quarter-card">
          <div class="comm-quarter-head">
            <span class="comm-quarter-code">T2</span>
            <span class="comm-quarter-months">ABR — JUN</span>
          </div>
          <h3>Webinar técnico</h3>
          <p>Sesión abierta enfocada en una herramienta, dataset o método reproducible: Copernicus, Google Earth Engine e IA aplicada.</p>
        </article>

        <article class="comm-quarter-card">
          <div class="comm-quarter-head">
            <span class="comm-quarter-code">T3</span>
            <span class="comm-quarter-months">JUL — SEP</span>
          </div>
          <h3>Presentación en simposio o congreso</h3>
          <p>Ponencia o mesa conjunta para visibilizar los hallazgos y desarrollos aplicados generados por la comunidad regional.</p>
        </article>

        <article class="comm-quarter-card">
          <div class="comm-quarter-head">
            <span class="comm-quarter-code">T4</span>
            <span class="comm-quarter-months">OCT — DIC</span>
          </div>
          <h3>Taller práctico</h3>
          <p>Ejercicio aplicado sobre un caso territorial concreto de Centroamérica o República Dominicana y balance de cierre anual.</p>
        </article>
      </div>

      <div class="comm-quarters-note">
        <strong>Flexibilidad operativa:</strong> formatos intercambiables según la agenda regional del año — encuentros, simposios, talleres prácticos o webinars técnicos.
      </div>
    </section>

    <section class="section" id="red-instituciones">
      <div class="comm-section-head">
        <span class="comm-eyebrow">02 &amp; 03 — Cartera actual y red de instituciones</span>
        <h2>Una base inicial en seis países (8 iniciativas activas)</h2>
        <p>Ministerios de vivienda y ordenamiento territorial, oficinas metropolitanas de planificación, gobiernos locales y grupos académicos que impulsan las primeras ocho iniciativas del portal.</p>
      </div>

      <div class="comm-countries-grid">
        {"".join(country_cards_html)}
      </div>

      <div class="comm-open-network-banner">
        <div>
          <span class="comm-open-network-tag">+ RED ABIERTA</span>
          <strong>Ciudades, universidades y especialistas interesados pueden sumarse a la comunidad.</strong>
        </div>
        <a class="btn btn-teal btn-sm" href="{html.escape(whatsapp_url, quote=True)}" target="_blank" rel="noopener noreferrer">Sumarse en WhatsApp ↗</a>
      </div>
    </section>

    <section class="section" id="articulacion-y-metodos">
      <div class="grid-2">
        <article class="card">
          <span class="comm-eyebrow">04 — Articulación regional</span>
          <h2 style="margin-top:0.2rem;font-size:1.35rem;color:var(--c-brand-blue);">Un marco institucional común</h2>
          <p style="color:var(--c-text-muted);font-size:0.92rem;">La Comunidad de Práctica se articula dentro de la institucionalidad regional de integración social y asentamientos humanos, con acompañamiento técnico internacional especializado:</p>

          <h3 class="comm-articulation-subhead">Marco Regional</h3>
          <ul class="comm-pillar-list">
            <li><span class="comm-pillar-acronym">SICA</span> <span>Sistema de la Integración Centroamericana</span></li>
            <li><span class="comm-pillar-acronym">SISCA</span> <span>Secretaría de la Integración Social Centroamericana</span></li>
            <li><span class="comm-pillar-acronym">CCVAH</span> <span>Consejo Centroamericano de Vivienda y Asentamientos Humanos</span></li>
          </ul>

          <h3 class="comm-articulation-subhead">Apoyo Técnico</h3>
          <ul class="comm-pillar-list">
            <li><span class="comm-pillar-acronym">GIZ</span> <span>Cooperación Alemana</span></li>
            <li><span class="comm-pillar-acronym">Copernicus LAC</span> <span>Centro regional · Chile</span></li>
          </ul>
        </article>

        <article class="card">
          <span class="comm-eyebrow">05 — Lo que compartimos</span>
          <h2 style="margin-top:0.2rem;font-size:1.35rem;color:var(--c-brand-blue);">Métodos en construcción y código abierto</h2>
          <p style="color:var(--c-text-muted);font-size:0.92rem;">Compartimos flujos de trabajo transparentes y adaptables a otros municipios de la región, combinando datos satelitales Copernicus con cartografía local:</p>
          <ul>
            <li><strong>Caso compartido en el lanzamiento (<a href="{html.escape(hn_urls['detail'], quote=True)}">Distrito Central, Honduras</a>):</strong> detección multianual de aparición de nueva huella construida (<code>2016–2026</code>) en Google Earth Engine y tipología preliminar de brecha catastral sobre grilla de <code>250 m</code> consultable en su <a href="{html.escape(hn_urls['geovisor'], quote=True)}" target="_blank" rel="noopener noreferrer">Geovisor interactivo ↗</a>.</li>
            <li><strong>Modelos replicables en la cartera:</strong> estimación de valor de suelo con embeddings satelitales e IA (AMSS), expansión urbana y presión sobre áreas verdes (Panamá Oeste y Santiago), criticidad socioespacial e índices multiamenaza (La Carpio, Bethania, Colón y La Unión).</li>
            <li><strong>Documentación abierta:</strong> acceso libre a <a href="{html.escape(ctx.site_url('recursos/'), quote=True)}">memorias metodológicas y scripts</a>, <a href="{html.escape(ctx.site_url('atlas/'), quote=True)}">Atlas Regional en dos partes</a> y <a href="{html.escape(ctx.site_url('ejercicio/'), quote=True)}">cuaderno base con Sentinel-2</a>.</li>
          </ul>
        </article>
      </div>
    </section>

    <section class="section" id="requisitos-participacion">
      <div class="comm-section-head">
        <span class="comm-eyebrow">10 — Participa</span>
        <h2>Te invitamos a sumarte — Requisitos</h2>
        <p>La comunidad está abierta a profesionales del sector público, academia y equipos técnicos de la región que compartan cuatro compromisos básicos de convivencia y colaboración:</p>
      </div>

      <div class="comm-req-grid">
        <article class="comm-req-card">
          <span class="comm-req-num">01</span>
          <p>Interés en capacitarse o innovar en la temática.</p>
        </article>
        <article class="comm-req-card">
          <span class="comm-req-num">02</span>
          <p>Respeto y apertura a las ideas de los demás.</p>
        </article>
        <article class="comm-req-card">
          <span class="comm-req-num">03</span>
          <p>Compartir solo temas relacionados con la comunidad.</p>
        </article>
        <article class="comm-req-card">
          <span class="comm-req-num">04</span>
          <p>Intención de conectar y participar con otras personas que innovan en el tema.</p>
        </article>
      </div>

      <div class="comm-join-cta-strip">
        <p><strong>¿Listo para conectar con equipos de los seis países?</strong> Descarga la presentación del taller de lanzamiento en San Salvador o intégrate directamente al canal activo de la comunidad.</p>
        <div style="display:flex;flex-wrap:wrap;gap:0.6rem;">
          <a class="btn btn-primary" href="{html.escape(whatsapp_url, quote=True)}" target="_blank" rel="noopener noreferrer">💬 Unirse en WhatsApp ↗</a>
          <a class="btn btn-outline-light" href="{html.escape(pres_pdf_url, quote=True)}" download="Presentacion_Lanzamiento_Comunidad_Copernicus_Urbano_2026-11-12.pdf">📥 Descargar PDF del lanzamiento</a>
        </div>
      </div>
    </section>
    """

    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Comunidad de Práctica",
        active_nav="comunidad",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=catalog_snap.get("generated_at"),
    )


def build_ejercicio_page(ctx: SiteContext, registry: dict[str, Any], catalog_snap: dict[str, Any]) -> str:
    nb_dl = html.escape(ctx.site_url("assets/descargas/mancha_urbana_sentinel2_vmod01.ipynb"), quote=True)
    docx_dl = html.escape(ctx.site_url("assets/descargas/Manual_Guia_Antigravity_Proyectos_Copernicus.docx"), quote=True)
    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow"><span class="badge badge-lime">Referencia técnica reproducible</span></div>
        <h1>Flujo reproducible de detección de mancha urbana con Sentinel-2</h1>
        <p class="hero-lead">Material de referencia para procesamiento de compuestos Sentinel-2 L2A y clasificación supervisada en Google Colab y Google Earth Engine.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{nb_dl}" download="mancha_urbana_sentinel2_vmod01.ipynb">Descargar cuaderno (.ipynb)</a>
          <a class="btn btn-teal" href="{docx_dl}" download="Manual_Guia_Antigravity_Proyectos_Copernicus.docx">Descargar Manual (.docx)</a>
          <a class="btn btn-outline-light" href="{html.escape(ctx.site_url('recursos/'), quote=True)}">Ver Metodologías de los 8 Proyectos →</a>
        </div>
      </div>
    </section>
    """
    body = f"""
    <section class="section">
      <div class="card">
        <h2>Acceso a las metodologías específicas implementadas en cada proyecto</h2>
        <p>Los ocho proyectos del Clúster Copernicus Urbano cuentan ya con sus propios flujos productivos, scripts y documentos metodológicos publicados. Consulta la biblioteca consolidada en <a href="{html.escape(ctx.site_url('recursos/'), quote=True)}">Metodologías y Código</a> o explora directamente los <a href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">Proyectos y Geovisores</a>.</p>
      </div>
    </section>
    """
    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Flujo Reproducible Sentinel-2",
        active_nav="recursos",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=catalog_snap.get("generated_at"),
    )


def build_seguimiento_page(
    ctx: SiteContext,
    registry: dict[str, Any],
    progress_snap: dict[str, Any],
    catalog_snap: dict[str, Any],
    board_cfg: dict[str, Any],
) -> str:
    gen_at = format_spanish_date(progress_snap.get("generated_at"), "Sincronizado")
    proj_titles = {it["project"]["id"]: SHORT_CARD_TITLES.get(it["project"]["id"], it["project"]["title"]) for it in catalog_snap.get("projects", [])}
    board_url = board_cfg.get("project_url")
    board_btn = render_link_or_pending(board_url, "Abrir tablero público GitHub Project #1", "Tablero en preparación", "btn btn-primary")

    proj_rows = []
    for p_entry in progress_snap.get("projects", []):
        pid = p_entry["project_id"]
        m = p_entry["metrics"]
        fmt = lambda v: "—" if v is None else str(v)
        proj_href = html.escape(ctx.site_url(f"proyectos/{pid}/"), quote=True)
        proj_rows.append(
            f"<tr>"
            f'<td><a href="{proj_href}"><strong>{esc(proj_titles.get(pid, pid))}</strong></a> (<code>{esc(pid)}</code>)</td>'
            f'<td><span class="badge badge-ok">{esc(p_entry["sync_state"])}</span></td>'
            f"<td>{fmt(m['open_tasks'])}</td>"
            f"<td>{fmt(m['in_review_tasks'])}</td>"
            f"<td>{fmt(m['completed_tasks'])}</td>"
            f"</tr>"
        )

    hero = f"""
    <section class="hero">
      <div class="container">
        <h1>Registro histórico de seguimiento técnico ({esc(gen_at)})</h1>
        <p class="hero-lead">Estado sincronizado de repositorios de las ocho iniciativas del Clúster Copernicus Urbano.</p>
        <div class="hero-actions">{board_btn}</div>
      </div>
    </section>
    """
    body = f"""
    <section class="section">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Iniciativa</th><th>Estado</th><th>Abiertas</th><th>En revisión</th><th>Terminadas</th></tr></thead>
          <tbody>{"".join(proj_rows)}</tbody>
        </table>
      </div>
    </section>
    """
    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Seguimiento",
        active_nav="comunidad",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=catalog_snap.get("generated_at"),
    )


def build_agenda_page(ctx: SiteContext, registry: dict[str, Any], agenda_doc: dict[str, Any], catalog_snap: dict[str, Any]) -> str:
    ics_href = html.escape(ctx.site_url("agenda/jornada-copernicus-2026.ics"), quote=True)
    hero = f"""
    <section class="hero">
      <div class="container">
        <h1>Memoria de encuentro regional · {esc(agenda_doc.get('event_name'))}</h1>
        <p class="hero-lead">Registro de sesiones de trabajo del Clúster de Asentamientos Humanos Copernicus Centroamérica.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{ics_href}" download="jornada-copernicus-2026.ics">Descargar archivo de calendario (.ics)</a>
          <a class="btn btn-teal" href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">Ir a Geovisores y Atlas →</a>
        </div>
      </div>
    </section>
    """
    body = f"""
    <section class="section">
      <div class="card">
        <h2>Productos consolidados del Clúster</h2>
        <p>Consulta los resultados finales, geovisores interactivos y Atlas temáticos de las ocho zonas de estudio en el <a href="{html.escape(ctx.site_url(''), quote=True)}">Inicio del Portal</a> y en el <a href="{html.escape(ctx.site_url('atlas/'), quote=True)}">Atlas Urbano Regional</a>.</p>
      </div>
    </section>
    """
    return render_hub_shell(
        ctx=ctx,
        registry=registry,
        page_title="Memoria de Agenda",
        active_nav="comunidad",
        hero_html=hero,
        body_html=body,
        snapshot_generated_at=catalog_snap.get("generated_at"),
    )


def build_404_page(ctx: SiteContext, registry: dict[str, Any], snapshot_generated_at: str | None) -> str:
    hero = f"""
    <section class="hero">
      <div class="container">
        <h1>Página no encontrada (404)</h1>
        <p class="hero-lead">El enlace solicitado no corresponde a una ruta activa del Portal Regional del Clúster Copernicus Urbano.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{html.escape(ctx.site_url(''), quote=True)}">Ir a Inicio</a>
          <a class="btn btn-teal" href="{html.escape(ctx.site_url('atlas/'), quote=True)}">Abrir Atlas Urbano Regional</a>
          <a class="btn btn-outline-light" href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">Explorar los 8 Geovisores</a>
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
        body_html="<section class='section'><p>Utiliza la navegación principal para acceder directamente a los Geovisores interactivos, el Atlas Urbano Regional y las metodologías descargables de los ocho proyectos.</p></section>",
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
    write_deterministic(out_dir / "index.html", build_home_page(ctx, registry, catalog_snap, atlas_snap))
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

    # Ruta histórica de reemplazo gt-salud-metropolitana -> pa-colon
    write_deterministic(
        out_dir / "proyectos" / "gt-salud-metropolitana" / "index.html",
        build_legacy_gt_salud_redirect_page(ctx, registry, catalog_snap.get("generated_at")),
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
