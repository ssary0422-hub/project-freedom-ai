"""Search discovery for an explicit list of public landing pages."""

from xml.etree.ElementTree import Element, SubElement, tostring

from flask import Blueprint, Response


discovery_bp = Blueprint("discovery", __name__)
PUBLIC_ORIGIN = "https://projectfreedom-ai.com"
PUBLIC_PATHS = (
    "/",
    "/services",
    "/static/tools/subtitle-check/index.html",
)


@discovery_bp.get("/robots.txt")
def robots():
    return Response(
        "User-agent: *\nAllow: /\n"
        f"Sitemap: {PUBLIC_ORIGIN}/sitemap.xml\n",
        mimetype="text/plain",
    )


@discovery_bp.get("/sitemap.xml")
def sitemap():
    root = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for path in PUBLIC_PATHS:
        url = SubElement(root, "url")
        SubElement(url, "loc").text = PUBLIC_ORIGIN + path
    return Response(
        tostring(root, encoding="utf-8", xml_declaration=True),
        mimetype="application/xml",
    )
