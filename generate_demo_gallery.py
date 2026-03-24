#!/usr/bin/env python3
"""
Generate a demo gallery with realistic sample ad data and SVG placeholder images.
This demonstrates the gallery layout when Apify data is not available.
Run: python3 generate_demo_gallery.py
"""

import json
import hashlib
from datetime import date
from pathlib import Path

TODAY = date(2026, 3, 24)
OUTPUT_DIR = Path("ad-gallery")
IMAGES_DIR = OUTPUT_DIR / "images"

# Realistic sample ads for the 4 search terms across IN, US, UAE
SAMPLE_ADS = [
    {"brand": "Databricks", "text": "Unify your data, analytics and AI on one platform. Databricks helps data engineering teams build reliable data pipelines at scale. Start your free trial today.", "start": "2025-11-15", "color": "#FF3621"},
    {"brand": "Snowflake", "text": "Streamline your data engineering workflows with Snowflake. Build, deploy, and manage data pipelines faster than ever. Join 9,000+ organizations.", "start": "2025-12-01", "color": "#29B5E8"},
    {"brand": "Fivetran", "text": "Automated data integration for modern data teams. 500+ connectors. Zero maintenance pipelines. Focus on insights, not infrastructure.", "start": "2025-10-20", "color": "#0073FF"},
    {"brand": "dbt Labs", "text": "Transform your data with dbt. The standard for data transformation. Trusted by 30,000+ companies for analytics engineering.", "start": "2025-09-10", "color": "#FF694A"},
    {"brand": "Talend", "text": "Enterprise data integration and data integrity. Clean, complete, and compliant data for your entire organization. Request a demo.", "start": "2025-08-05", "color": "#1BB0CE"},
    {"brand": "Informatica", "text": "AI-powered data management platform. From data engineering to governance, power your digital transformation with intelligent automation.", "start": "2025-11-01", "color": "#FF4D00"},
    {"brand": "Matillion", "text": "Data productivity for the cloud era. Build data pipelines 5x faster. Native integrations with Snowflake, Databricks, and Redshift.", "start": "2025-07-20", "color": "#5FCC6D"},
    {"brand": "Stitch Data", "text": "Simple, extensible ETL built for data teams. Move data from 130+ sources to your warehouse in minutes. Open source & cloud-hosted.", "start": "2026-01-05", "color": "#47B881"},
    {"brand": "Prefect", "text": "Workflow orchestration for data engineers. Monitor, schedule, and orchestrate your data pipelines with confidence. Open source.", "start": "2025-10-12", "color": "#3B82F6"},
    {"brand": "Airbyte", "text": "Open-source data integration platform. 350+ pre-built connectors. Move data from any source to any destination. Self-hosted or cloud.", "start": "2025-12-18", "color": "#615EFF"},
    {"brand": "Tableau (Salesforce)", "text": "See and understand your data with Tableau. Self-service analytics for everyone. Interactive dashboards that drive decisions.", "start": "2025-06-15", "color": "#E8762D"},
    {"brand": "Power BI (Microsoft)", "text": "Turn data into opportunity with Power BI. Enterprise analytics for your organization. AI-powered insights at your fingertips.", "start": "2025-09-22", "color": "#F2C811"},
    {"brand": "Looker (Google Cloud)", "text": "Modern business intelligence that delivers actionable insights. Explore, share, and operationalize trusted data analytics across your org.", "start": "2025-08-30", "color": "#4285F4"},
    {"brand": "ThoughtSpot", "text": "AI-powered analytics and search-driven insights. Ask questions in natural language and get instant answers from your data.", "start": "2025-11-08", "color": "#2770EE"},
    {"brand": "Qlik", "text": "Active Intelligence Platform. From raw data to remarkable outcomes. Real-time analytics and data integration in one platform.", "start": "2025-10-01", "color": "#009845"},
    {"brand": "Sisense", "text": "Embed analytics everywhere. Infuse AI-powered analytics into your products and workflows. White-label BI for SaaS companies.", "start": "2025-07-10", "color": "#FFCB05"},
    {"brand": "Zapier", "text": "Automate your work across 6,000+ apps. No code required. Build powerful workflow automations in minutes. Free to start.", "start": "2025-05-20", "color": "#FF4F00"},
    {"brand": "Make (Integromat)", "text": "Visual workflow automation for teams. Connect apps, design workflows, and automate processes without writing code. 1,500+ integrations.", "start": "2025-09-15", "color": "#6D00CC"},
    {"brand": "n8n", "text": "Fair-code workflow automation. Self-hostable, extendable, and privacy-first. Build complex automations with a visual editor.", "start": "2025-11-25", "color": "#EA4B71"},
    {"brand": "Monday.com", "text": "Work OS that powers workflow automation. Automate repetitive tasks, streamline approvals, and keep your team aligned. Try free.", "start": "2025-08-18", "color": "#FF3D57"},
    {"brand": "Workato", "text": "Enterprise workflow automation and integration platform. Connect your apps and automate business processes at scale. SOC 2 compliant.", "start": "2025-10-05", "color": "#108043"},
    {"brand": "Celonis", "text": "Process mining meets workflow automation. Discover inefficiencies, automate fixes, and continuously improve your business processes.", "start": "2025-12-10", "color": "#00C16E"},
    {"brand": "UiPath", "text": "AI-powered automation platform. From robotic process automation to intelligent document processing. Automate anything.", "start": "2025-07-01", "color": "#FA4616"},
    {"brand": "Automation Anywhere", "text": "Intelligent automation for the enterprise. Cloud-native RPA + AI. Automate complex business processes end to end.", "start": "2025-06-25", "color": "#FFB511"},
    {"brand": "Tray.io", "text": "The universal automation cloud. Connect any stack, automate any process, innovate at any scale. Built for business & IT.", "start": "2025-09-28", "color": "#7B61FF"},
    {"brand": "Alteryx", "text": "Analytics automation platform. Democratize data science. Empower every analyst to prepare, blend, and analyze data faster.", "start": "2025-08-12", "color": "#0078C0"},
    {"brand": "Atlan", "text": "The active metadata platform for modern data teams. Data cataloging, governance, and collaboration in one place.", "start": "2025-11-20", "color": "#3B82F6"},
    {"brand": "Monte Carlo", "text": "Data observability for the modern data stack. End-to-end visibility into your data pipelines. Detect and resolve data issues fast.", "start": "2025-10-28", "color": "#00D4AA"},
    {"brand": "Great Expectations", "text": "Data quality you can trust. Open-source framework for validating, documenting, and profiling your data. Stop bad data.", "start": "2025-09-05", "color": "#FF6310"},
    {"brand": "Hevo Data", "text": "No-code data pipeline platform. Automated ETL/ELT from 150+ sources. Built for data engineers in India and worldwide.", "start": "2025-12-22", "color": "#4B87FF"},
    {"brand": "Rivery", "text": "SaaS ELT platform for data teams. Ingest, transform, and orchestrate data pipelines. Pre-built workflows for instant value.", "start": "2025-10-15", "color": "#00D1B2"},
    {"brand": "Hightouch", "text": "Reverse ETL for growth teams. Sync your data warehouse to 120+ business tools. Activate your data where it matters.", "start": "2025-11-02", "color": "#6C5CE7"},
    {"brand": "Census", "text": "Operational analytics. Sync data from your warehouse to every business tool. No engineering required. The reverse ETL platform.", "start": "2026-01-10", "color": "#2563EB"},
    {"brand": "Rudderstack", "text": "Customer data infrastructure for developers. Open-source CDP alternative. Collect, unify, and activate customer data.", "start": "2025-08-22", "color": "#7B2FBF"},
    {"brand": "Apache Kafka (Confluent)", "text": "Data streaming for data engineers. Real-time data pipelines and streaming analytics. Fully managed Apache Kafka.", "start": "2025-07-15", "color": "#171A21"},
    {"brand": "Dagster", "text": "The data orchestration platform. Build, test, and maintain data pipelines with software engineering best practices.", "start": "2025-12-05", "color": "#4F43DD"},
    {"brand": "Palantir", "text": "Build data-driven operations. From data integration to AI-powered decision making. Trusted by governments and Fortune 500.", "start": "2025-06-01", "color": "#101010"},
    {"brand": "DataRobot", "text": "AI platform for data analytics teams. Automate machine learning from data prep to deployment. Get value from AI faster.", "start": "2025-09-18", "color": "#0D47A1"},
    {"brand": "Sigma Computing", "text": "Cloud analytics built for the modern data stack. Spreadsheet-like interface on your cloud data warehouse. No SQL required.", "start": "2025-10-30", "color": "#00BFA5"},
    {"brand": "Hex", "text": "The modern analytics workspace. Notebooks, dashboards, and data apps — all connected to your data warehouse.", "start": "2025-11-12", "color": "#F8C200"},
    {"brand": "Lightdash", "text": "Open source BI for dbt users. Build dashboards directly from your dbt project. Self-hosted or cloud.", "start": "2026-02-01", "color": "#7C3AED"},
    {"brand": "Metabase", "text": "Fast, simple analytics for everyone. Open source BI tool. Ask questions about your data and get beautiful charts. No SQL needed.", "start": "2025-07-28", "color": "#509EE3"},
]


def generate_svg_placeholder(brand: str, color: str, ad_text: str) -> str:
    """Generate an SVG placeholder image for an ad."""
    initials = "".join(w[0].upper() for w in brand.split()[:2])
    short_text = ad_text[:60] + "..." if len(ad_text) > 60 else ad_text
    # Escape for SVG
    short_text = short_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;").replace('"', "&quot;")
    brand_escaped = brand.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;").replace('"', "&quot;")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{color};stop-opacity:0.9"/>
      <stop offset="100%" style="stop-color:#0a0a0a;stop-opacity:1"/>
    </linearGradient>
  </defs>
  <rect width="800" height="600" fill="url(#bg)"/>
  <rect x="40" y="40" width="720" height="520" rx="20" fill="rgba(0,0,0,0.3)"/>
  <circle cx="400" cy="200" r="60" fill="{color}" opacity="0.8"/>
  <text x="400" y="215" text-anchor="middle" fill="white" font-size="36" font-weight="bold" font-family="Arial">{initials}</text>
  <text x="400" y="310" text-anchor="middle" fill="white" font-size="28" font-weight="bold" font-family="Arial">{brand_escaped}</text>
  <text x="400" y="370" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="16" font-family="Arial">
    <tspan x="400" dy="0">{short_text[:40]}</tspan>
    <tspan x="400" dy="24">{short_text[40:]}</tspan>
  </text>
  <rect x="300" y="440" width="200" height="50" rx="25" fill="{color}"/>
  <text x="400" y="472" text-anchor="middle" fill="white" font-size="16" font-weight="bold" font-family="Arial">Learn More</text>
  <text x="400" y="540" text-anchor="middle" fill="rgba(255,255,255,0.3)" font-size="12" font-family="Arial">Sponsored · Meta Ad Library</text>
</svg>'''
    return svg


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(exist_ok=True)

    # Filter for 30+ days
    processed = []
    for ad in SAMPLE_ADS:
        start = date.fromisoformat(ad["start"])
        days = (TODAY - start).days
        if days < 30:
            continue

        img_hash = hashlib.md5(ad["brand"].encode()).hexdigest()[:12]
        img_filename = f"ad_{img_hash}.svg"

        # Generate SVG placeholder
        svg = generate_svg_placeholder(ad["brand"], ad["color"], ad["text"])
        (IMAGES_DIR / img_filename).write_text(svg)

        processed.append({
            "brand": ad["brand"],
            "text": ad["text"],
            "image_url": "",
            "image_file": img_filename,
            "start_date": ad["start"],
            "days_running": days,
        })

    print(f"Generated {len(processed)} ads (30+ days filter applied)")

    # Save processed data
    with open(OUTPUT_DIR / "processed_ads.json", "w") as f:
        json.dump(processed, f, indent=2)

    # Build gallery HTML (import from main script)
    from scrape_meta_ads import build_gallery_html
    build_gallery_html(processed)
    print(f"Gallery saved to {OUTPUT_DIR / 'index.html'}")
    print(f"SVG images saved to {IMAGES_DIR}/")


if __name__ == "__main__":
    main()
