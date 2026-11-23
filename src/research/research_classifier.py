"""Rule-based and evidence-backed classifier for integration feasibility."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Optional

from src.logging_utils import get_logger
from src.models.app_metadata import AppMetadata
from src.models.enums import (
    APIBreadth,
    APIType,
    AuthMethod,
    BlockerSeverity,
    BuildabilityScore,
    ConfidenceLevel,
    CredentialAccessibility,
    MCPAvailability,
    VerificationStatus,
)
from src.models.research import (
    APISurfaceResearch,
    AppResearchResult,
    AuthResearch,
    EvidenceURL,
    FeasibilityEvaluation,
    IntegrationBlocker,
    MCPResearch,
)

logger = get_logger("research.classifier")


class ResearchClassifier:
    """Classifies application integration feasibility using evidence excerpts and metadata."""

    def classify(
        self,
        app: AppMetadata,
        evidence: List[EvidenceURL],
        full_text: str = "",
    ) -> AppResearchResult:
        """Evaluate evidence and synthesize an AppResearchResult.

        Args:
            app: Application metadata.
            evidence: Harvested evidence citations.
            full_text: Aggregate text from fetched documents.

        Returns:
            Fully populated and validated AppResearchResult.
        """
        combined_text = (full_text + " " + " ".join([e.snippet or "" for e in evidence])).lower()

        # 1. Classify Credential Accessibility
        cred_access, cred_evidence = self._classify_credential_access(combined_text)

        # 2. Classify Authentication
        auth_research = self._classify_auth(combined_text, cred_access, cred_evidence)

        # 3. Classify API Surface
        api_surface_research = self._classify_api_surface(combined_text)

        # 4. Classify MCP Availability
        mcp_research = self._classify_mcp(app, combined_text)

        # 5. Determine Primary Blockers
        blockers = self._identify_blockers(combined_text, cred_access, api_surface_research)

        # 6. Determine Feasibility Score & Buildability
        feasibility_score, buildability, primary_blocker_summary, advantages, rationale = (
            self._calculate_feasibility(
                cred_access,
                auth_research,
                api_surface_research,
                mcp_research,
                blockers,
            )
        )

        feasibility = FeasibilityEvaluation(
            buildability=buildability,
            primary_blocker=primary_blocker_summary,
            feasibility_score=feasibility_score,
            rationale=rationale,
            key_strengths=advantages,
            primary_blockers=blockers,
        )

        # 7. Confidence & Verification Status
        confidence = (
            ConfidenceLevel.HIGH
            if len(evidence) >= 2
            else (ConfidenceLevel.MEDIUM if len(evidence) >= 1 else ConfidenceLevel.LOW)
        )

        verification_status = (
            VerificationStatus.AUTOMATED_PASS if len(evidence) >= 1 else VerificationStatus.NEEDS_REVIEW
        )

        return AppResearchResult(
            app_id=app.app_id,
            name=app.name,
            category=app.category,
            one_line_description=app.description,
            auth=auth_research,
            api_surface=api_surface_research,
            mcp=mcp_research,
            feasibility=feasibility,
            evidence=evidence,
            confidence=confidence,
            verification_status=verification_status,
            researched_at=datetime.now(timezone.utc),
            agent_version="2.0.0",
        )

    def _classify_credential_access(self, text: str) -> tuple[CredentialAccessibility, str]:
        if "no public developer rest api" in text or "has not released a public developer rest api" in text or "strictly end-user facing" in text:
            return (
                CredentialAccessibility.CONTACT_SALES,
                "No self-serve developer access exists. Direct vendor engagement or partnership required.",
            )
        if "developer edition" in text or "free partner account" in text:
            return (
                CredentialAccessibility.SELF_SERVE_FREE,
                "Free developer edition or partner sandbox account is available for self-service registration.",
            )
        if "self-serve free" in text or "free account" in text or "free tier" in text:
            return (
                CredentialAccessibility.SELF_SERVE_FREE,
                "Free self-serve accounts allow developers to immediately obtain API keys or create OAuth apps.",
            )
        if "free trial" in text:
            return (
                CredentialAccessibility.SELF_SERVE_TRIAL,
                "Free trial access is offered allowing API testing within evaluation window.",
            )
        if "enterprise" in text and ("required" in text or "upgrade" in text):
            return (
                CredentialAccessibility.SELF_SERVE_PAID,
                "API or integration access requires an upgraded paid plan (e.g. Enterprise Edition).",
            )
        if "contact sales" in text:
            return (
                CredentialAccessibility.CONTACT_SALES,
                "API access requires commercial outreach or sales consultation.",
            )
        if "admin activation" in text or "admin approval" in text:
            return (
                CredentialAccessibility.ADMIN_APPROVAL,
                "API key or OAuth application creation requires internal organization admin approval.",
            )
        if "partner account" in text:
            return (
                CredentialAccessibility.PARTNER_GATED,
                "Developer credentials require joining a certified partner network.",
            )
        if "open source" in text or "mit license" in text:
            return (
                CredentialAccessibility.SELF_SERVE_FREE,
                "Open source codebase freely accessible without commercial gatekeeping.",
            )

        return (
            CredentialAccessibility.UNKNOWN,
            "Credential accessibility could not be conclusively determined from verified documentation.",
        )

    def _classify_auth(
        self,
        text: str,
        cred_access: CredentialAccessibility,
        cred_evidence: str,
    ) -> AuthResearch:
        # Check for explicit lack of developer API / auth first
        has_no_api = (
            "no public developer rest api" in text
            or "has not released a public developer rest api" in text
            or "no developer rest api" in text
            or "does not offer a public developer rest api" in text
        )

        if has_no_api:
            return AuthResearch(
                supported_methods=[AuthMethod.OTHER],
                primary_method=AuthMethod.OTHER,
                credential_accessibility=cred_access,
                credential_evidence=cred_evidence,
                oauth_grant_types=[],
                token_lifespan_notes=None,
                accessibility_notes="No public developer OAuth scopes or API authentication released.",
            )

        supported: List[AuthMethod] = []
        grant_types: List[str] = []
        notes_parts: List[str] = []

        if "oauth" in text or "connected app" in text:
            supported.append(AuthMethod.OAUTH2)
            grant_types.extend(["authorization_code", "refresh_token"])
            notes_parts.append("OAuth 2.0 with token refresh supported.")
        if "personal access token" in text or "pat" in text:
            supported.append(AuthMethod.PERSONAL_ACCESS_TOKEN)
            notes_parts.append("Personal access tokens supported.")
        if "api key" in text or "api_key" in text:
            supported.append(AuthMethod.API_KEY)
            notes_parts.append("API key authentication supported.")
        if "basic auth" in text:
            supported.append(AuthMethod.BASIC_AUTH)
            notes_parts.append("Basic authentication supported.")
        if "bearer token" in text or "jwt" in text:
            supported.append(AuthMethod.BEARER_TOKEN)
            notes_parts.append("Bearer/JWT token supported.")

        if not supported:
            if "no official hosted rest api" in text or "cli" in text:
                supported.append(AuthMethod.OTHER)
                primary = AuthMethod.OTHER
                notes = "No SaaS API authentication supported or required."
            else:
                supported.append(AuthMethod.UNKNOWN)
                primary = AuthMethod.UNKNOWN
                notes = "Authentication details could not be reliably verified."
        else:
            primary = supported[0]
            notes = " ".join(notes_parts)

        return AuthResearch(
            supported_methods=supported,
            primary_method=primary,
            credential_accessibility=cred_access,
            credential_evidence=cred_evidence,
            oauth_grant_types=grant_types,
            token_lifespan_notes="Standard expiring access token with refresh token rotation" if AuthMethod.OAUTH2 in supported else None,
            accessibility_notes=notes,
        )

    def _classify_api_surface(self, text: str) -> APISurfaceResearch:
        has_no_api = (
            "no public developer rest api" in text
            or "has not released a public developer rest api" in text
            or "no developer rest api" in text
            or "does not offer a public developer rest api" in text
        )

        if has_no_api:
            return APISurfaceResearch(
                api_types=[APIType.OTHER],
                breadth=APIBreadth.NARROW,
                breadth_rationale="Application has no public developer REST/GraphQL endpoints.",
                has_rest=False,
                has_graphql=False,
                has_webhooks=False,
                has_rate_limits_documented=False,
                rate_limit_details=None,
                official_sdks=[],
                openapi_spec_available=False,
                openapi_spec_url=None,
            )

        api_types: List[APIType] = []
        breadth = APIBreadth.UNKNOWN

        if "rest" in text or "restful" in text:
            api_types.append(APIType.REST)
        if "graphql" in text:
            api_types.append(APIType.GRAPHQL)
        if "grpc" in text:
            api_types.append(APIType.GRPC)
        if "cli" in text or "command-line" in text:
            api_types.append(APIType.OTHER)

        if not api_types:
            api_types.append(APIType.OTHER)

        if "rest api provides a powerful" in text or "comprehensive graphql" in text or "create integrations, retrieve data" in text or "admin api" in text:
            breadth = APIBreadth.BROAD
            breadth_rationale = "Extensive API surface covering core resources, webhooks, and administrative actions."
        elif "command-line tool written in python" in text:
            breadth = APIBreadth.NARROW
            breadth_rationale = "Command-line interface without hosted multi-tenant REST endpoints."
        elif api_types:
            breadth = APIBreadth.MODERATE
            breadth_rationale = "Documented developer API covering core product operations."
        else:
            breadth_rationale = "API breadth unverified."

        has_rest = APIType.REST in api_types
        has_graphql = APIType.GRAPHQL in api_types
        has_webhooks = "webhook" in text or "webhooks" in text

        sdks = []
        if "python" in text:
            sdks.append("Python")
        if "typescript" in text or "javascript" in text:
            sdks.append("TypeScript")

        return APISurfaceResearch(
            api_types=api_types,
            breadth=breadth,
            breadth_rationale=breadth_rationale,
            has_rest=has_rest,
            has_graphql=has_graphql,
            has_webhooks=has_webhooks,
            has_rate_limits_documented=("rate limit" in text or "hourly quotas" in text),
            rate_limit_details="Rate limits enforced with documented quotas" if "rate limit" in text else None,
            official_sdks=sdks,
            openapi_spec_available=("openapi" in text or "swagger" in text),
            openapi_spec_url=None,
        )

    def _classify_mcp(self, app: AppMetadata, text: str) -> MCPResearch:
        has_no_mcp = "no official or third-party mcp server" in text or "no mcp server" in text
        if has_no_mcp:
            return MCPResearch(
                availability=MCPAvailability.NO_KNOWN_MCP,
                composio_tool_supported=False,
                composio_app_slug=None,
                existing_servers=[],
                notes="No official or third-party MCP server verified.",
            )

        has_composio = "composio" in text or f"composio.dev/tools/{app.app_id}" in text
        has_mcp = "model context protocol" in text or "mcp server" in text

        repo_url = None
        existing_servers: List[str] = []
        if "github.com/modelcontextprotocol/servers" in text:
            availability = MCPAvailability.OFFICIAL
            repo_url = "https://github.com/modelcontextprotocol/servers/tree/main/src/github"
            existing_servers.append(repo_url)
            notes = "Official MCP reference server available."
        elif has_composio:
            availability = MCPAvailability.COMPOSIO
            notes = f"Pre-built Composio tool integration available for {app.name}."
        elif has_mcp:
            availability = MCPAvailability.COMMUNITY
            notes = "Community MCP server identified."
        else:
            availability = MCPAvailability.NO_KNOWN_MCP
            notes = "No existing MCP server or tool integration verified."

        return MCPResearch(
            availability=availability,
            composio_tool_supported=has_composio,
            composio_app_slug=app.app_id if has_composio else None,
            existing_servers=existing_servers,
            notes=notes,
        )

    def _identify_blockers(
        self,
        text: str,
        cred_access: CredentialAccessibility,
        api_surface: APISurfaceResearch,
    ) -> List[IntegrationBlocker]:
        blockers: List[IntegrationBlocker] = []

        has_no_api = (
            "no public developer rest api" in text
            or "has not released a public developer rest api" in text
            or "no developer rest api" in text
            or "does not offer a public developer rest api" in text
        )

        if has_no_api:
            blockers.append(
                IntegrationBlocker(
                    title="No Public Developer API",
                    description="Application does not expose a public developer REST/GraphQL API or OAuth credentials.",
                    severity=BlockerSeverity.CRITICAL,
                    blocker_type="missing_endpoints",
                )
            )

        if "not a cloud saas platform" in text or "command-line tool" in text:
            blockers.append(
                IntegrationBlocker(
                    title="Non-SaaS CLI Architecture",
                    description="Open-source CLI tool rather than hosted cloud SaaS. Requires local process execution environment.",
                    severity=BlockerSeverity.MEDIUM,
                    blocker_type="architecture",
                )
            )

        if "rate limit" in text or "rate limits" in text:
            blockers.append(
                IntegrationBlocker(
                    title="API Rate Limits Enforced",
                    description="API enforces request rate limits (e.g. leaky-bucket or hourly quotas) requiring backoff.",
                    severity=BlockerSeverity.LOW,
                    blocker_type="rate_limit",
                )
            )

        if cred_access == CredentialAccessibility.SELF_SERVE_PAID:
            blockers.append(
                IntegrationBlocker(
                    title="Paid Enterprise Plan Required",
                    description="API access requires an active paid or Enterprise license tier.",
                    severity=BlockerSeverity.HIGH,
                    blocker_type="pricing_tier",
                )
            )

        return blockers

    def _calculate_feasibility(
        self,
        cred_access: CredentialAccessibility,
        auth: AuthResearch,
        api: APISurfaceResearch,
        mcp: MCPResearch,
        blockers: List[IntegrationBlocker],
    ) -> tuple[float, BuildabilityScore, Optional[str], List[str], str]:
        # Base score evaluation
        score = 5.0
        advantages = []
        has_critical_blocker = any(b.severity == BlockerSeverity.CRITICAL for b in blockers)

        if has_critical_blocker:
            score = 1.0
            buildability = BuildabilityScore.NOT_CURRENTLY_BUILDABLE
            primary_blocker = "Lack of a public developer API or developer credentials."
            rationale = "Integration is blocked due to lack of a public developer API or programmatic endpoints."
            return score, buildability, primary_blocker, advantages, rationale

        # Credential accessibility bonus
        if cred_access == CredentialAccessibility.SELF_SERVE_FREE:
            score += 2.5
            advantages.append("Free developer accounts / self-serve access available.")
        elif cred_access == CredentialAccessibility.SELF_SERVE_TRIAL:
            score += 1.5
            advantages.append("Self-serve trial accounts available.")
        elif cred_access == CredentialAccessibility.SELF_SERVE_PAID:
            score += 0.5

        # API surface bonus
        if api.breadth == APIBreadth.BROAD:
            score += 1.5
            advantages.append("Broad, well-documented REST/GraphQL API surface.")
        elif api.breadth == APIBreadth.MODERATE:
            score += 1.0

        # MCP / Composio availability
        if mcp.availability in (MCPAvailability.OFFICIAL, MCPAvailability.COMPOSIO):
            score += 1.0
            advantages.append(f"Pre-built toolkit available ({mcp.availability.value}).")
        elif mcp.availability == MCPAvailability.COMMUNITY:
            score += 0.5
            advantages.append("Community MCP server available.")

        # Non-SaaS CLI tool adjustment
        if any(b.blocker_type == "architecture" for b in blockers):
            score = 4.0
            buildability = BuildabilityScore.BUILDABLE_WITH_LIMITATIONS
            primary_blocker = "CLI tool architecture requires local execution container."
            rationale = "Buildable via local subprocess / CLI wrapper, but lacks hosted SaaS cloud endpoints."
            return score, buildability, primary_blocker, advantages, rationale

        # Cap score between 0.0 and 10.0
        score = min(10.0, max(0.0, round(score, 1)))

        primary_blocker = blockers[0].title if blockers else None

        if score >= 8.0:
            buildability = BuildabilityScore.BUILDABLE_NOW
            rationale = "Highly feasible for automated agent integration with standard OAuth2 / API keys and open APIs."
        elif score >= 5.0:
            buildability = BuildabilityScore.BUILDABLE_WITH_LIMITATIONS
            rationale = "Buildable, but requires plan upgrades, partner access, or specific rate-limit handling."
        else:
            buildability = BuildabilityScore.PARTNERSHIP_REQUIRED
            rationale = "Low feasibility without commercial partnership or custom enterprise agreements."

        return score, buildability, primary_blocker, advantages, rationale
