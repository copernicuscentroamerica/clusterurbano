#!/usr/bin/env python3
"""
Generador estático determinista del Portal Comunitario (clusterurbano).
Construye Inicio, Proyectos, fichas proyectos/{id}/, Atlas, fichas atlas/{product_id}/,
Seguimiento, Comunidad, Recursos, Agenda (+ .ics) y 404.html.
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
    SiteContext,
    badge_html,
    compute_site_context,
    esc,
)

ROOT = Path(__file__).resolve().parent.parent


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
            f'  <script src="{html.escape(ctx.site_url("assets/js/geovisor.js"), quote=True)}"></script>'
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

    sync_label = snapshot_generated_at or "Semillas iniciales del paquete"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(page_title)} · Comunidad Urbana Copernicus Centroamérica</title>
  <meta name="description" content="Comunidad de Práctica del Clúster de Asentamientos Humanos Copernicus Centroamérica · Fase II. Proyectos, geovisores GeoLibre, seguimiento y Atlas Urbano Regional.">
  {robots_meta}
  <link rel="stylesheet" href="{html.escape(ctx.site_url('assets/css/styles.css'), quote=True)}">
  {maplibre_head}
</head>
<body>
  <a class="skip-link" href="#contenido-principal">Saltar al contenido principal</a>
  {work_banner_html}
  <div class="topbar">
    <div class="container">
      <div><strong>Comunidad Urbana Copernicus Centroamérica</strong> · Clúster de Asentamientos Humanos · Fase II</div>
      <div>Último catálogo generado: <code>{esc(sync_label)}</code> · {hub_repo_html}</div>
    </div>
  </div>
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

  <footer class="site-footer">
    <div class="container footer-grid">
      <div>
        <p class="footer-title">Comunidad Urbana Copernicus Centroamérica</p>
        <p>Clúster de Asentamientos Humanos · Fase II. Espacio regional que articula iniciativas institucionales, métodos reproducibles, geovisores basados en GeoLibre y el Atlas Urbano Regional.</p>
      </div>
      <div>
        <p class="footer-title">Secciones del portal</p>
        <p>
          <a href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">Proyectos</a> ·
          <a href="{html.escape(ctx.site_url('atlas/'), quote=True)}">Atlas Urbano Regional</a> ·
          <a href="{html.escape(ctx.site_url('seguimiento/'), quote=True)}">Seguimiento</a> ·
          <a href="{html.escape(ctx.site_url('comunidad/'), quote=True)}">Comunidad</a> ·
          <a href="{html.escape(ctx.site_url('recursos/'), quote=True)}">Recursos</a> ·
          <a href="{html.escape(ctx.site_url('agenda/'), quote=True)}">Agenda San Salvador</a>
        </p>
      </div>
      <div>
        <p class="footer-title">Fuentes de verdad y trazabilidad</p>
        <p>Cada iniciativa mantiene su manifiesto canónico <code>project.json</code> y su propio geovisor en su repositorio independiente. Este portal consulta registros autorizados y distingue datos declarados, propuestas y asuntos por confirmar.</p>
      </div>
    </div>
  </footer>

  <script src="{html.escape(ctx.site_url('assets/js/ui.js'), quote=True)}"></script>
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
    inst_str = ", ".join(p["institutional_use"].get("institutions", []))
    search_blob = f"{pid} {p['title']} {country_name} {p['territory']['label']} {inst_str} {' '.join(tags)}"

    detail_href = html.escape(ctx.site_url(f"proyectos/{pid}/"), quote=True)
    site_link = p["links"].get("website")
    ext_site_btn = (
        f'<a class="btn btn-outline btn-xs" href="{html.escape(site_link, quote=True)}" target="_blank" rel="noopener noreferrer">Sitio / Geovisor ↗</a>'
        if site_link and site_link.startswith("https://")
        else '<span class="badge badge-pendiente">Sitio propio en preparación</span>'
    )
    tags_html = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags)

    return f"""
    <article class="card" data-filter-item
             data-country="{esc(country_code)}"
             data-tag="{esc(tags_attr)}"
             data-pmv="{esc(p['pmv']['scope_status'])}"
             data-search-text="{esc(search_blob)}">
      <div style="display:flex;flex-wrap:wrap;justify-content:space-between;gap:0.4rem;">
        <span class="badge badge-country">{esc(country_name)} ({esc(country_code)})</span>
        {badge_html(p['pmv']['scope_status'], 'PMV')}
      </div>
      <h3><a href="{detail_href}" style="color:var(--c-navy);text-decoration:none;">{esc(p['title'])}</a></h3>
      <p style="font-size:0.86rem;color:var(--c-text-muted);"><strong>Territorio:</strong> {esc(p['territory']['label'])}</p>
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
                "short_name": gv.get("short_name") or p["title"],
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
        <p class="hero-lead">La comunidad reúne iniciativas de Centroamérica y República Dominicana que emplean información geoespacial y observación de la Tierra para abordar retos de los asentamientos humanos. Este espacio conecta proyectos, métodos, avances y contribuciones al Atlas Urbano Regional.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{html.escape(ctx.site_url('proyectos/'), quote=True)}">Explorar proyectos</a>
          <a class="btn btn-teal" href="{html.escape(ctx.site_url('atlas/'), quote=True)}">Consultar el Atlas</a>
          <a class="btn btn-outline-light" href="{html.escape(ctx.site_url('comunidad/'), quote=True)}">Participar</a>
          <a class="btn btn-outline-light" href="{html.escape(ctx.site_url('agenda/'), quote=True)}">Ver Agenda 10–12 nov</a>
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
      <div class="section-header">
        <h2>Distribución territorial referencial de las iniciativas</h2>
        <span class="badge badge-declarado">Ubicaciones referenciales según cada perfil</span>
      </div>
      <div class="hub-map-card">
        <div id="hub-regional-map" class="hub-map-canvas" role="region" aria-label="Mapa regional orientativo de las ocho iniciativas"></div>
        <div style="padding:0.65rem 1rem;background:var(--c-surface-alt);font-size:0.82rem;color:var(--c-text-muted);">
          <strong>Nota cartográfica:</strong> Los marcadores señalan únicamente el centroide o ámbito referencial declarado en cada ficha de proyecto para facilitar la navegación; no representan resultados analíticos ni límites oficiales validados. Cada iniciativa cuenta con su propio geovisor basado en GeoLibre.
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
          <p>Las tareas técnicas viven en el repositorio de cada iniciativa y los compromisos transversales en el hub, distinguiendo el avance operativo de la validación del PMV.</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="{html.escape(ctx.site_url('seguimiento/'), quote=True)}">Ir a Seguimiento</a>
          </div>
        </article>
        <article class="card">
          <span class="badge badge-propuesta">Colaboración abierta</span>
          <h3>Plantilla común, Fork y Geovisor GeoLibre</h3>
          <p>Cada participante trabaja desde un fork del repositorio canónico de su iniciativa, valida localmente y despliega sus capas en el Geovisor basado en GeoLibre.</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="{html.escape(ctx.site_url('recursos/'), quote=True)}">Guías y plantilla</a>
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

    has_decl_demo = any(
        st.get("pointer") == "/links/demo" and st.get("status") == "declarado"
        for st in p.get("provenance", {}).get("statements", [])
    )

    site_btn = render_link_or_pending(
        p["links"].get("website"),
        "Abrir sitio y Geovisor GeoLibre de la iniciativa",
        "Sitio independiente en preparación",
        "btn btn-primary",
    )
    repo_btn = render_link_or_pending(
        p["links"].get("repository"),
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

    sync_badge = badge_html("validado" if item["sync_state"] == "ok" else ("en_revision" if item["sync_state"] == "stale" else "propuesta"), f" Catálogo: {item['sync_state']}")

    fork_snippet = f"""gh repo fork {effective_slug} --clone=false
git clone https://github.com/TU_USUARIO_GITHUB/{reg_entry['proposed_repository']}.git
cd {reg_entry['proposed_repository']}
git remote add upstream https://github.com/{effective_slug}.git"""

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
        <p class="hero-lead">{esc(p['summary'])}</p>
        <div class="hero-actions">
          {site_btn}
          {repo_btn}
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
      <div class="grid-2">
        <div class="prose">
          {render_markdown(content_md)}
        </div>
        <div style="display:flex;flex-direction:column;gap:1.2rem;">
          <article class="card">
            <h3>Metadatos de origen y sincronización</h3>
            <p><strong>Autoridad configurada:</strong> <code>{esc(item.get('source_mode'))}</code></p>
            <p><strong>Repositorio registrado:</strong> <code>{esc(item.get('source_repository'), 'Semilla local bootstrap')}</code></p>
            <p><strong>Revisión SHA:</strong> <code>{esc(item.get('source_commit'), 'N/A (bootstrap)')}</code></p>
            <p><strong>Fecha de lectura:</strong> <code>{esc(item.get('fetched_at'))}</code></p>
            <p><strong>Actualización declarada del contenido:</strong> {esc(item.get('content_updated_at'), 'Fecha de actualización no informada')}</p>
          </article>

          <article class="card">
            <h3>Contribución prevista al Atlas</h3>
            <ul>{"".join(atlas_links) if atlas_links else "<li>En definición</li>"}</ul>
          </article>

          <article class="card">
            <h3>Colaborar en esta iniciativa (Fork / Clone)</h3>
            <p style="font-size:0.86rem;">Para aportar cambios o desplegar capas en el Geovisor GeoLibre de este equipo, haz fork del repositorio específico de esta iniciativa:</p>
            <pre id="fork-{esc(pid)}" class="code-block"><code>{html.escape(fork_snippet)}</code></pre>
            <div class="card-footer">
              <button type="button" class="btn btn-outline btn-xs" data-copy-target="fork-{esc(pid)}">Copiar comandos</button>
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
    gen_at = progress_snap.get("generated_at") or "Seguimiento pendiente de primera sincronización"
    proj_titles = {it["project"]["id"]: it["project"]["title"] for it in catalog_snap.get("projects", [])}

    board_url = board_cfg.get("project_url")
    board_btn = render_link_or_pending(
        board_url,
        "Abrir tablero GitHub Project regional",
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
        proj_rows.append(
            f"<tr>"
            f'<td><a href="{proj_href}"><code>{esc(pid)}</code></a><br><span style="font-size:0.8rem;color:var(--c-text-muted);">{esc(proj_titles.get(pid, ""))}</span></td>'
            f"<td><code>{esc(p_entry['sync_state'])}</code></td>"
            f"<td>{fmt(m['open_tasks'])}</td>"
            f"<td>{fmt(m['in_review_tasks'])}</td>"
            f"<td>{fmt(m['completed_tasks'])}</td>"
            f"<td>{fmt(m['blocked_tasks'])}</td>"
            f"<td>{esc(p_entry.get('last_success_at'), '—')}</td>"
            f"</tr>"
        )
        for t in p_entry.get("tasks", []):
            all_tasks.append(t)

    tasks_section = ""
    if all_tasks:
        t_cards = []
        for t in all_tasks:
            blk_badge = '<span class="badge badge-danger">Bloqueado</span>' if t.get("blocked") else ""
            t_cards.append(
                f"""
                <article class="card" data-filter-item
                         data-tproj="{esc(t['project_id'])}"
                         data-tblocked="{'si' if t.get('blocked') else 'no'}"
                         data-search-text="{esc(t['task_id'] + ' ' + t['title'] + ' ' + t['project_id'])}">
                  <div style="display:flex;justify-content:space-between;gap:0.4rem;flex-wrap:wrap;">
                    <code>{esc(t['task_id'])}</code>
                    <span>{badge_html('ok' if t['workflow_status'] == 'Terminado' else 'pendiente', t['workflow_status'])} {blk_badge}</span>
                  </div>
                  <h3><a href="{html.escape(t['issue_url'], quote=True)}" target="_blank" rel="noopener noreferrer">{esc(t['title'])} ↗</a></h3>
                  <p style="font-size:0.83rem;color:var(--c-text-muted);">Iniciativa: <code>{esc(t['project_id'])}</code> · Estado Issue: <code>{esc(t['issue_state'])}</code> · Actualizada: {esc(t['source_updated_at'])}</p>
                </article>
                """
            )
        p_opts = '<option value="all">Todas las iniciativas</option>' + "".join(
            f'<option value="{esc(p["project_id"])}">{esc(p["project_id"])}</option>' for p in progress_snap.get("projects", [])
        )
        tasks_section = f"""
        <section class="section" data-catalog-progress>
          <h2>Tarjetas operativas exportadas ({len(all_tasks)})</h2>
          <div class="filter-bar">
            <div class="filter-field" style="flex:2;">
              <label for="f-tsk-q">Buscar tarea</label>
              <input id="f-tsk-q" type="search" placeholder="Título o repo#número..." data-filter-search>
            </div>
            <div class="filter-field">
              <label for="f-tsk-p">Iniciativa</label>
              <select id="f-tsk-p" data-filter-select="tproj">{p_opts}</select>
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
          <div class="grid-2">{"".join(t_cards)}</div>
        </section>
        """

    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <span class="badge badge-lime">Operación comunitaria</span>
          <span class="badge badge-country">Estado del snapshot: {esc(overall)}</span>
        </div>
        <h1>Seguimiento de compromisos, tareas y bloqueos</h1>
        <p class="hero-lead">Vista pública de consulta alimentada por GitHub Issues y GitHub Projects. El cierre de una tarea técnica nunca se interpreta automáticamente como aceptación del PMV ni validación institucional.</p>
        <div class="hero-actions">
          {board_btn}
        </div>
      </div>
    </section>
    """

    body = f"""
    <div class="callout">
      <strong>Estado de sincronización de seguimiento: <code>{esc(overall)}</code></strong>
      <span>Última generación registrada: <code>{esc(gen_at)}</code>. Cuando una iniciativa aún no ha sincronizado Issues, las métricas se muestran como <code>—</code> (nunca como cero tareas ni 100 % completado). Los cierres marcados como <code>not_planned</code> se excluyen del conteo de tareas terminadas.</span>
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
      <h2>¿Dónde registrar cada tarea o solicitud de apoyo?</h2>
      <div class="grid-3">
        <article class="card">
          <h3>1. Tareas técnicas del PMV</h3>
          <p>Se crean como Issues dentro del repositorio canónico de la iniciativa (<code>urbano-{{id}}</code>) usando el formulario <strong>Tarea del PMV</strong>.</p>
        </article>
        <article class="card">
          <h3>2. Bloqueos y mentoría</h3>
          <p>Se registran con el formulario <strong>Bloqueo o solicitud de apoyo</strong> (etiqueta <code>bloqueado</code>), conservando la columna actual en el tablero para visibilizar la ayuda requerida.</p>
        </article>
        <article class="card">
          <h3>3. Compromisos regionales</h3>
          <p>Acuerdos transversales, calendario comunitario y coordinación del Atlas se registran en las Issues del repositorio central <code>clusterurbano</code>.</p>
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

    hub_repo = registry.get("hub", {}).get("repository")
    discussions_url = f"https://github.com/{hub_repo}/discussions" if hub_repo else None
    disc_btn = render_link_or_pending(
        discussions_url,
        "Abrir GitHub Discussions de la comunidad",
        "GitHub Discussions se enlaza al activar la función en el repositorio central",
        "btn btn-primary",
    )

    hero = f"""
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <span class="badge badge-lime">Comunidad de Práctica</span>
        </div>
        <h1>Gobernanza colaborativa, roles e intercambio regional</h1>
        <p class="hero-lead">Red interinstitucional y académica de Centroamérica y República Dominicana enfocada en desarrollar métodos abiertos, sostener productos territoriales útiles y nutrir el Atlas Urbano Regional.</p>
        <div class="hero-actions">
          {disc_btn}
          <a class="btn btn-outline-light" href="{html.escape(ctx.site_url('agenda/'), quote=True)}">Ver sesión de acuerdos (12 nov)</a>
        </div>
      </div>
    </section>
    """

    body = f"""
    <section class="section">
      <h2>Instituciones participantes documentadas en los perfiles</h2>
      <p>Los nombres personales y canales de contacto se publican únicamente tras autorización expresa de cada equipo; aquí se listan las instituciones declaradas en las ocho fichas:</p>
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
            <li><strong>Coordinación de comunidad:</strong> facilita acuerdos, calendario, apoyos y seguimiento del Project regional (responsable nominal por confirmar en la jornada).</li>
            <li><strong>Administración técnica:</strong> gestiona permisos de repositorios, flujos de GitHub Pages y sincronización de catálogos.</li>
            <li><strong>Curaduría del Atlas:</strong> revisa consistencia de metadatos, unidades y advertencias de comparabilidad antes de publicar productos.</li>
          </ul>
        </article>
        <article class="card">
          <h3>Equipos de iniciativa y revisión</h3>
          <ul>
            <li><strong>Punto focal de iniciativa:</strong> cuida la coherencia de <code>project.json</code>, <code>content/project.md</code> y tareas del equipo.</li>
            <li><strong>Revisor técnico:</strong> comprueba reproducibilidad metodológica, código, CRS y limitaciones.</li>
            <li><strong>Referente institucional:</strong> examina pertinencia para la decisión pública y condiciones reales de adopción.</li>
          </ul>
        </article>
      </div>
    </section>

    <section class="section">
      <h2>Espacios de conversación (GitHub Discussions)</h2>
      <div class="grid-3">
        <div class="card"><span class="badge badge-country">Categoría 1</span><h3>Anuncios y acuerdos</h3><p>Decisiones colectivas registradas, hitos y convocatorias regionales.</p></div>
        <div class="card"><span class="badge badge-country">Categoría 2</span><h3>Preguntas y respuestas</h3><p>Consultas técnicas sobre GEE, Sentinel-1/2, openEO, QGIS o GeoLibre con soluciones reutilizables.</p></div>
        <div class="card"><span class="badge badge-country">Categoría 3</span><h3>Métodos y recursos</h3><p>Scripts, plantillas de validación muestral, diccionarios de datos y flujos reproducibles.</p></div>
        <div class="card"><span class="badge badge-country">Categoría 4</span><h3>Experiencias de aplicación</h3><p>Relatos de uso en instrumentos de planificación, diferenciando expectativas de adopción documentada.</p></div>
        <div class="card"><span class="badge badge-country">Categoría 5</span><h3>Propuestas comunitarias</h3><p>Nuevas colaboraciones entre países, mejoras a la plantilla común y al Atlas Urbano Regional.</p></div>
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
    faqs = [
        (
            "¿Cómo encuentro mi iniciativa y su repositorio?",
            "Entra a la sección Proyectos, filtra por tu país o busca tu institución. Dentro de la ficha verás el identificador estable (ej. pa-panama-oeste), el estado del repositorio canónico y los comandos exactos para clonar o hacer fork.",
        ),
        (
            "¿Cómo creo mi fork personal y configuro upstream sin confundir el portal?",
            "Haz fork únicamente del repositorio canónico de tu iniciativa (urbano-{id}), nunca del repositorio general clusterurbano si vas a editar tu proyecto. En tu clon local, 'origin' apunta a tu cuenta personal y 'upstream' apunta a copernicuscentroamerica/urbano-{id}.",
        ),
        (
            "¿Cómo despliego las capas que genere mi equipo en el Geovisor basado en GeoLibre?",
            "Coloca tu archivo vectorial validado (EPSG:4326, sin datos personales) en geovisor/data/ o usa una URL HTTPS de servicio COG/XYZ/WMS, actualiza source_path y status en geovisor/layers.json y ejecuta python3 scripts/build_site.py --output site. También puedes probar cualquier .geojson arrastrándolo directamente en la pestaña 'Probar GeoJSON' del visor.",
        ),
        (
            "¿Cómo registro una tarea del PMV o un bloqueo?",
            "Abre la pestaña Issues del repositorio de tu iniciativa y elige el formulario 'Tarea del PMV' o 'Bloqueo o solicitud de apoyo'. Toda tarea debe describir un resultado verificable y su criterio de aceptación.",
        ),
        (
            "¿Cómo solicito una revisión técnica o validación institucional?",
            "Usa el formulario 'Solicitud de revisión' adjuntando el enlace HTTPS al producto, PR o vista previa. Para que project.json cambie el estado a 'validado', el contrato exige URL de evidencia, fecha ISO y nombre del revisor.",
        ),
        (
            "¿Cómo propongo e incorporo un producto al Atlas Urbano Regional?",
            "Actualiza o añade un archivo JSON en atlas/products/ siguiendo schemas/atlas-product.schema.json (indicando cobertura, resolución, indicador, unidad, método y limitaciones) y abre el formulario 'Contribución al Atlas' para curaduría.",
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

    hero = """
    <section class="hero">
      <div class="container">
        <div class="hero-eyebrow">
          <span class="badge badge-lime">Guías técnicas y referencias</span>
        </div>
        <h1>Recursos para desarrollo, GeoLibre y colaboración</h1>
        <p class="hero-lead">Documentación práctica para trabajar durante los laboratorios de la jornada y dar continuidad técnica a los repositorios y al Atlas Urbano Regional.</p>
      </div>
    </section>
    """

    body = f"""
    <section class="section">
      <h2>Plataformas y herramientas técnicas verificadas</h2>
      <div class="grid-3">
        <article class="card">
          <span class="badge badge-ok">Geovisualización</span>
          <h3>GeoLibre Web &amp; MapLibre GL JS</h3>
          <p>Plataforma SIG ligera en navegador compatible con archivos de proyecto <code>.geolibre.json</code>, GeoJSON, COG, PMTiles, GeoParquet y STAC.</p>
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
          <span class="badge badge-declarado">Procesamiento y referencia</span>
          <h3>Google Earth Engine &amp; GHSL</h3>
          <p>Catálogo armonizado Sentinel-2 SR (desde marzo de 2017), Sentinel-1 GRD y capas globales de asentamientos humanos (JRC GHSL).</p>
          <div class="card-footer">
            <a class="btn btn-outline btn-xs" href="https://code.earthengine.google.com/" target="_blank" rel="noopener noreferrer">GEE Code Editor ↗</a>
            <a class="btn btn-outline btn-xs" href="https://ghsl.jrc.ec.europa.eu/" target="_blank" rel="noopener noreferrer">GHSL JRC ↗</a>
          </div>
        </article>

        <article class="card">
          <span class="badge badge-propuesta">Plantilla oficial del clúster</span>
          <h3>Plantilla de iniciativa (<code>clusterurbano-proyecto-template</code>)</h3>
          <p>Estructura base independiente con contratos JSON Schema Draft 2020-12, generador Python, validaciones automáticas y geovisor GeoLibre preconfigurado.</p>
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
          <input id="f-faq-q" type="search" placeholder="Ej. fork, geovisor, geojson, revisión, atlas..." data-filter-search>
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
        body_html="<section class='section'><p>Utiliza la barra superior para acceder al catálogo de proyectos, el Atlas Urbano Regional, el seguimiento o la agenda.</p></section>",
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
    shutil.copy2(ROOT / "data" / "jornada-copernicus-2026.ics", out_dir / "agenda" / "jornada-copernicus-2026.ics") if (out_dir / "agenda").exists() else None
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
