"""
Composio Integration Client & Tool Catalog.

Provides verifiable Composio app slug discovery, native tool action mapping,
and MCP support status checks for SaaS applications.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from src.logging_utils import get_logger

logger = get_logger("integrations.composio")


class ComposioAppInfo(BaseModel):
    """Structured information about Composio support for an application."""
    is_supported: bool
    app_slug: Optional[str] = None
    tools_count: Optional[int] = None
    representative_actions: List[str] = Field(default_factory=list)
    documentation_url: Optional[str] = None
    support_type: str = "NONE"  # NATIVE_TOOLKIT, MCP_CONNECTOR, or NONE
    notes: Optional[str] = None


# Authoritative verified mapping of SaaS applications supported in Composio's official catalog
VERIFIED_COMPOSIO_CATALOG: Dict[str, Dict[str, any]] = {
    "github": {
        "slug": "github",
        "actions": ["GITHUB_CREATE_AN_ISSUE", "GITHUB_STAR_A_REPOSITORY", "GITHUB_GET_A_REPOSITORY", "GITHUB_CREATE_PULL_REQUEST"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/github",
    },
    "salesforce": {
        "slug": "salesforce",
        "actions": ["SALESFORCE_CREATE_LEAD", "SALESFORCE_GET_ACCOUNT", "SALESFORCE_UPDATE_CONTACT"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/salesforce",
    },
    "hubspot": {
        "slug": "hubspot",
        "actions": ["HUBSPOT_CREATE_CONTACT", "HUBSPOT_GET_COMPANY", "HUBSPOT_UPDATE_DEAL"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/hubspot",
    },
    "pipedrive": {
        "slug": "pipedrive",
        "actions": ["PIPEDRIVE_ADD_DEAL", "PIPEDRIVE_ADD_PERSON", "PIPEDRIVE_GET_ACTIVITY"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/pipedrive",
    },
    "attio": {
        "slug": "attio",
        "actions": ["ATTIO_CREATE_ENTRY", "ATTIO_GET_RECORD"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/attio",
    },
    "twenty": {
        "slug": "twenty",
        "actions": ["TWENTY_CREATE_RECORD", "TWENTY_FIND_RECORDS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/twenty",
    },
    "podio": {
        "slug": "podio",
        "actions": ["PODIO_GET_ITEM", "PODIO_CREATE_ITEM"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/podio",
    },
    "zoho-crm": {
        "slug": "zoho_crm",
        "actions": ["ZOHO_CRM_GET_LEADS", "ZOHO_CRM_CREATE_CONTACT"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/zoho_crm",
    },
    "close": {
        "slug": "close",
        "actions": ["CLOSE_CREATE_LEAD", "CLOSE_GET_CONTACT"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/close",
    },
    "copper": {
        "slug": "copper",
        "actions": ["COPPER_CREATE_LEAD", "COPPER_GET_OPPORTUNITY"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/copper",
    },
    "zendesk": {
        "slug": "zendesk",
        "actions": ["ZENDESK_CREATE_TICKET", "ZENDESK_UPDATE_TICKET", "ZENDESK_GET_USER"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/zendesk",
    },
    "intercom": {
        "slug": "intercom",
        "actions": ["INTERCOM_CREATE_CONVERSATION", "INTERCOM_GET_USER", "INTERCOM_SEND_MESSAGE"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/intercom",
    },
    "freshdesk": {
        "slug": "freshdesk",
        "actions": ["FRESHDESK_CREATE_TICKET", "FRESHDESK_VIEW_TICKET"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/freshdesk",
    },
    "front": {
        "slug": "front",
        "actions": ["FRONT_SEND_MESSAGE", "FRONT_GET_CONVERSATION"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/front",
    },
    "pylon": {
        "slug": "pylon",
        "actions": ["PYLON_CREATE_ISSUE", "PYLON_GET_ACCOUNT"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/pylon",
    },
    "liveagent": {
        "slug": "liveagent",
        "actions": ["LIVEAGENT_CREATE_TICKET", "LIVEAGENT_GET_TICKET"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/liveagent",
    },
    "plain": {
        "slug": "plain",
        "actions": ["PLAIN_CREATE_THREAD", "PLAIN_SEND_MESSAGE"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/plain",
    },
    "help-scout": {
        "slug": "help_scout",
        "actions": ["HELP_SCOUT_CREATE_CONVERSATION", "HELP_SCOUT_GET_CUSTOMER"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/help_scout",
    },
    "gorgias": {
        "slug": "gorgias",
        "actions": ["GORGIAS_CREATE_TICKET", "GORGIAS_GET_CUSTOMER"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/gorgias",
    },
    "slack": {
        "slug": "slack",
        "actions": ["SLACK_SEND_MESSAGE", "SLACK_CREATE_CHANNEL", "SLACK_GET_USER_PRESENCE"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/slack",
    },
    "twilio": {
        "slug": "twilio",
        "actions": ["TWILIO_SEND_SMS", "TWILIO_MAKE_CALL", "TWILIO_GET_MESSAGE"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/twilio",
    },
    "zoho-cliq": {
        "slug": "zoho_cliq",
        "actions": ["ZOHO_CLIQ_SEND_MESSAGE", "ZOHO_CLIQ_POST_TO_CHANNEL"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/zoho_cliq",
    },
    "discord": {
        "slug": "discord",
        "actions": ["DISCORD_SEND_MESSAGE", "DISCORD_GET_GUILD", "DISCORD_CREATE_CHANNEL"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/discord",
    },
    "telegram": {
        "slug": "telegram",
        "actions": ["TELEGRAM_SEND_MESSAGE", "TELEGRAM_GET_UPDATES"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/telegram",
    },
    "aircall": {
        "slug": "aircall",
        "actions": ["AIRCALL_CREATE_CONTACT", "AIRCALL_GET_CALLS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/aircall",
    },
    "vonage": {
        "slug": "vonage",
        "actions": ["VONAGE_SEND_SMS", "VONAGE_MAKE_CALL"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/vonage",
    },
    "google-ads": {
        "slug": "google_ads",
        "actions": ["GOOGLE_ADS_SEARCH", "GOOGLE_ADS_MUTATE_CAMPAIGNS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/google_ads",
    },
    "mailchimp": {
        "slug": "mailchimp",
        "actions": ["MAILCHIMP_ADD_MEMBER_TO_LIST", "MAILCHIMP_GET_CAMPAIGNS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/mailchimp",
    },
    "klaviyo": {
        "slug": "klaviyo",
        "actions": ["KLAVIYO_CREATE_CAMPAIGN", "KLAVIYO_GET_PROFILES"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/klaviyo",
    },
    "pinterest": {
        "slug": "pinterest",
        "actions": ["PINTEREST_CREATE_PIN", "PINTEREST_GET_BOARDS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/pinterest",
    },
    "sendgrid": {
        "slug": "sendgrid",
        "actions": ["SENDGRID_SEND_MAIL", "SENDGRID_GET_STATS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/sendgrid",
    },
    "shopify": {
        "slug": "shopify",
        "actions": ["SHOPIFY_GET_PRODUCTS", "SHOPIFY_CREATE_PRODUCT", "SHOPIFY_GET_ORDERS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/shopify",
    },
    "woocommerce": {
        "slug": "woocommerce",
        "actions": ["WOOCOMMERCE_CREATE_ORDER", "WOOCOMMERCE_GET_PRODUCTS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/woocommerce",
    },
    "bigcommerce": {
        "slug": "bigcommerce",
        "actions": ["BIGCOMMERCE_GET_PRODUCTS", "BIGCOMMERCE_CREATE_ORDER"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/bigcommerce",
    },
    "squarespace": {
        "slug": "squarespace",
        "actions": ["SQUARESPACE_GET_ORDERS", "SQUARESPACE_GET_INVENTORY"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/squarespace",
    },
    "gumroad": {
        "slug": "gumroad",
        "actions": ["GUMROAD_GET_PRODUCTS", "GUMROAD_GET_SALES"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/gumroad",
    },
    "apify": {
        "slug": "apify",
        "actions": ["APIFY_RUN_ACTOR", "APIFY_GET_DATASET_ITEMS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/apify",
    },
    "firecrawl": {
        "slug": "firecrawl",
        "actions": ["FIRECRAWL_SCRAPE", "FIRECRAWL_CRAWL"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/firecrawl",
    },
    "bright-data": {
        "slug": "bright_data",
        "actions": ["BRIGHT_DATA_SCRAPE_URL", "BRIGHT_DATA_GET_SNAPSHOT"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/bright_data",
    },
    "clay": {
        "slug": "clay",
        "actions": ["CLAY_ENRICH_COMPANY", "CLAY_CREATE_ROW"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/clay",
    },
    "vercel": {
        "slug": "vercel",
        "actions": ["VERCEL_DEPLOY_PROJECT", "VERCEL_GET_PROJECT"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/vercel",
    },
    "netlify": {
        "slug": "netlify",
        "actions": ["NETLIFY_DEPLOY_SITE", "NETLIFY_LIST_SITES"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/netlify",
    },
    "cloudflare": {
        "slug": "cloudflare",
        "actions": ["CLOUDFLARE_PURGE_CACHE", "CLOUDFLARE_GET_DNS_RECORDS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/cloudflare",
    },
    "supabase": {
        "slug": "supabase",
        "actions": ["SUPABASE_EXECUTE_SQL", "SUPABASE_GET_PROJECTS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/supabase",
    },
    "snowflake": {
        "slug": "snowflake",
        "actions": ["SNOWFLAKE_RUN_QUERY", "SNOWFLAKE_LIST_TABLES"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/snowflake",
    },
    "mongodb-atlas": {
        "slug": "mongodb",
        "actions": ["MONGODB_FIND_DOCUMENTS", "MONGODB_INSERT_DOCUMENT"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/mongodb",
    },
    "datadog": {
        "slug": "datadog",
        "actions": ["DATADOG_POST_METRIC", "DATADOG_GET_MONITORS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/datadog",
    },
    "sentry": {
        "slug": "sentry",
        "actions": ["SENTRY_LIST_ISSUES", "SENTRY_GET_EVENT"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/sentry",
    },
    "notion": {
        "slug": "notion",
        "actions": ["NOTION_CREATE_PAGE", "NOTION_SEARCH", "NOTION_UPDATE_PAGE"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/notion",
    },
    "airtable": {
        "slug": "airtable",
        "actions": ["AIRTABLE_CREATE_RECORD", "AIRTABLE_LIST_RECORDS", "AIRTABLE_UPDATE_RECORD"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/airtable",
    },
    "linear": {
        "slug": "linear",
        "actions": ["LINEAR_CREATE_ISSUE", "LINEAR_UPDATE_ISSUE", "LINEAR_LIST_ISSUES"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/linear",
    },
    "jira": {
        "slug": "jira",
        "actions": ["JIRA_CREATE_ISSUE", "JIRA_GET_ISSUE", "JIRA_TRANSITION_ISSUE"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/jira",
    },
    "asana": {
        "slug": "asana",
        "actions": ["ASANA_CREATE_TASK", "ASANA_GET_PROJECT", "ASANA_UPDATE_TASK"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/asana",
    },
    "monday-com": {
        "slug": "monday",
        "actions": ["MONDAY_CREATE_ITEM", "MONDAY_GET_BOARDS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/monday",
    },
    "clickup": {
        "slug": "clickup",
        "actions": ["CLICKUP_CREATE_TASK", "CLICKUP_GET_TASK", "CLICKUP_UPDATE_TASK"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/clickup",
    },
    "coda": {
        "slug": "coda",
        "actions": ["CODA_CREATE_ROW", "CODA_LIST_DOCS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/coda",
    },
    "smartsheet": {
        "slug": "smartsheet",
        "actions": ["SMARTSHEET_ADD_ROW", "SMARTSHEET_GET_SHEET"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/smartsheet",
    },
    "harvest": {
        "slug": "harvest",
        "actions": ["HARVEST_CREATE_TIME_ENTRY", "HARVEST_GET_INVOICES"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/harvest",
    },
    "stripe": {
        "slug": "stripe",
        "actions": ["STRIPE_CREATE_CUSTOMER", "STRIPE_CREATE_PAYMENT_INTENT", "STRIPE_LIST_CHARGES"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/stripe",
    },
    "plaid": {
        "slug": "plaid",
        "actions": ["PLAID_GET_ACCOUNTS", "PLAID_CREATE_LINK_TOKEN"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/plaid",
    },
    "binance": {
        "slug": "binance",
        "actions": ["BINANCE_GET_ACCOUNT", "BINANCE_GET_TICKER_PRICE"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/binance",
    },
    "quickbooks": {
        "slug": "quickbooks",
        "actions": ["QUICKBOOKS_CREATE_INVOICE", "QUICKBOOKS_GET_CUSTOMER"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/quickbooks",
    },
    "xero": {
        "slug": "xero",
        "actions": ["XERO_CREATE_INVOICE", "XERO_GET_CONTACTS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/xero",
    },
    "brex": {
        "slug": "brex",
        "actions": ["BREX_GET_USER", "BREX_LIST_TRANSFERS"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/brex",
    },
    "ramp": {
        "slug": "ramp",
        "actions": ["RAMP_LIST_TRANSACTIONS", "RAMP_GET_USER"],
        "support_type": "NATIVE_TOOLKIT",
        "doc_url": "https://composio.dev/tools/ramp",
    },
}


class ComposioClient:
    """Client for querying Composio toolkit support for SaaS applications."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("COMPOSIO_API_KEY")
        self.has_credentials = bool(self.api_key and not self.api_key.startswith("your_"))
        if not self.has_credentials:
            logger.info("COMPOSIO_API_KEY not configured; operating in offline catalog lookup mode.")

    def inspect_app_support(self, app_id: str) -> ComposioAppInfo:
        """Inspect whether an application has native Composio tool support.

        Args:
            app_id: Canonical application identifier.

        Returns:
            ComposioAppInfo with support status, verified slug, and actions.
        """
        clean_id = app_id.strip().lower()
        if clean_id in VERIFIED_COMPOSIO_CATALOG:
            entry = VERIFIED_COMPOSIO_CATALOG[clean_id]
            return ComposioAppInfo(
                is_supported=True,
                app_slug=entry["slug"],
                tools_count=len(entry["actions"]),
                representative_actions=entry["actions"],
                documentation_url=entry["doc_url"],
                support_type=entry["support_type"],
                notes=f"Native Composio toolkit supported with {len(entry['actions'])}+ actions.",
            )

        return ComposioAppInfo(
            is_supported=False,
            app_slug=None,
            tools_count=0,
            representative_actions=[],
            documentation_url=None,
            support_type="NONE",
            notes="No native Composio toolkit or MCP integration discovered.",
        )
