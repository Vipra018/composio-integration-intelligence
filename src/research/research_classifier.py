"""Rule-based and evidence-backed classifier with strict polarity enforcement and provenance tracking."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from pydantic import HttpUrl

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
    EvidencePolarity,
    MCPAvailability,
    Provenance,
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
    ResearchClaim,
)

logger = get_logger("research.classifier")


class ResearchClassifier:
    """Classifies integration feasibility strictly separating documented facts, inferences, and unknowns."""

    def classify(
        self,
        app: AppMetadata,
        evidence: List[EvidenceURL],
        full_text: str = "",
        search_status: Optional[str] = None,
    ) -> AppResearchResult:
        """Evaluate evidence citations to produce validated research profile with claim provenance.

        Args:
            app: Application metadata.
            evidence: Harvested evidence citations (with polarity & provenance).
            full_text: Aggregate text from fetched documents.
            search_status: Search engine execution status identifier.

        Returns:
            Fully populated and validated AppResearchResult.
        """
        # Separate evidence citations by polarity
        positive_evidence = [e for e in evidence if e.polarity == EvidencePolarity.POSITIVE]
        negative_evidence = [e for e in evidence if e.polarity == EvidencePolarity.NEGATIVE]
        ambiguous_evidence = [e for e in evidence if e.polarity == EvidencePolarity.AMBIGUOUS]

        pos_text = " ".join([e.snippet or "" for e in positive_evidence]).lower()
        neg_text = " ".join([e.snippet or "" for e in negative_evidence]).lower()
        combined_text = (full_text + " " + pos_text).lower()

        claims: List[ResearchClaim] = []

        # 1. Classify Credential Accessibility
        cred_access, cred_evidence_url, cred_excerpt, cred_prov, cred_polarity = (
            self._classify_credential_access(pos_text, neg_text, combined_text, positive_evidence, negative_evidence)
        )
        claims.append(
            ResearchClaim(
                field_name="auth.credential_accessibility",
                extracted_value=cred_access.value,
                provenance=cred_prov,
                source_url=cred_evidence_url,
                supporting_excerpt=cred_excerpt,
                confidence=ConfidenceLevel.HIGH if cred_excerpt else ConfidenceLevel.LOW,
                polarity=cred_polarity,
            )
        )

        # 2. Classify Authentication
        auth_research, auth_claims = self._classify_auth(
            pos_text, neg_text, combined_text, cred_access, cred_excerpt or "", positive_evidence, negative_evidence
        )
        claims.extend(auth_claims)

        # 3. Classify API Surface
        api_surface_research, api_claims = self._classify_api_surface(
            pos_text, neg_text, combined_text, positive_evidence, negative_evidence
        )
        claims.extend(api_claims)

        # 4. Classify MCP Availability
        mcp_research, mcp_claim = self._classify_mcp(app, pos_text, neg_text, positive_evidence)
        claims.append(mcp_claim)

        # 5. Determine Primary Blockers
        blockers = self._identify_blockers(neg_text, combined_text, cred_access, api_surface_research, negative_evidence)

        # 6. Determine Feasibility Score & Buildability
        feasibility_score, buildability, primary_blocker_summary, advantages, rationale = (
            self._calculate_feasibility(cred_access, auth_research, api_surface_research, mcp_research, blockers)
        )

        claims.append(
            ResearchClaim(
                field_name="feasibility.buildability",
                extracted_value=buildability.value,
                provenance=Provenance.INFERRED,
                source_url=None,
                supporting_excerpt=None,
                confidence=ConfidenceLevel.HIGH if len(positive_evidence) >= 2 else ConfidenceLevel.MEDIUM,
                polarity=EvidencePolarity.POSITIVE,
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
        live_evidence_count = sum(1 for e in evidence if e.provenance == Provenance.LIVE_FETCHED)
        confidence = (
            ConfidenceLevel.HIGH
            if live_evidence_count >= 2
            else (ConfidenceLevel.MEDIUM if live_evidence_count >= 1 else ConfidenceLevel.LOW)
        )

        verification_status = (
            VerificationStatus.AUTOMATED_PASS
            if live_evidence_count >= 1
            else VerificationStatus.REQUIRES_HUMAN_REVIEW
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
            claims=claims,
            search_provider_used=search_status,
            confidence=confidence,
            verification_status=verification_status,
            researched_at=datetime.now(timezone.utc),
            agent_version="3.0.0",
        )

    def _classify_credential_access(
        self,
        pos_text: str,
        neg_text: str,
        combined_text: str,
        pos_ev: List[EvidenceURL],
        neg_ev: List[EvidenceURL],
    ) -> Tuple[CredentialAccessibility, Optional[HttpUrl], Optional[str], Provenance, EvidencePolarity]:
        # 1. Check positive developer access indicators
        for ev in pos_ev:
            snip = (ev.snippet or "").lower()
            if "developer edition" in snip:
                return (
                    CredentialAccessibility.SELF_SERVE_FREE,
                    ev.url,
                    ev.snippet,
                    ev.provenance,
                    EvidencePolarity.POSITIVE,
                )
            if "partner account" in snip or "partner development" in snip:
                return (
                    CredentialAccessibility.PARTNER_GATED,
                    ev.url,
                    ev.snippet,
                    ev.provenance,
                    EvidencePolarity.POSITIVE,
                )
            if "self-serve free" in snip or "free account" in snip or "free tier" in snip:
                return (
                    CredentialAccessibility.SELF_SERVE_FREE,
                    ev.url,
                    ev.snippet,
                    ev.provenance,
                    EvidencePolarity.POSITIVE,
                )
            if "free trial" in snip:
                return (
                    CredentialAccessibility.SELF_SERVE_TRIAL,
                    ev.url,
                    ev.snippet,
                    ev.provenance,
                    EvidencePolarity.POSITIVE,
                )
            if "enterprise" in snip and ("required" in snip or "upgrade" in snip):
                return (
                    CredentialAccessibility.SELF_SERVE_PAID,
                    ev.url,
                    ev.snippet,
                    ev.provenance,
                    EvidencePolarity.POSITIVE,
                )
            if "admin approval" in snip or "admin activation" in snip:
                return (
                    CredentialAccessibility.ADMIN_APPROVAL,
                    ev.url,
                    ev.snippet,
                    ev.provenance,
                    EvidencePolarity.POSITIVE,
                )
            if "contact sales" in snip:
                return (
                    CredentialAccessibility.CONTACT_SALES,
                    ev.url,
                    ev.snippet,
                    ev.provenance,
                    EvidencePolarity.POSITIVE,
                )

        # 2. Check for open-source repository
        if "open source" in combined_text or "mit license" in combined_text:
            matching = next((e for e in pos_ev if "open source" in (e.snippet or "").lower() or "mit" in (e.snippet or "").lower()), None)
            return (
                CredentialAccessibility.SELF_SERVE_FREE,
                matching.url if matching else None,
                matching.snippet if matching else "Open source codebase available without credential gating.",
                matching.provenance if matching else Provenance.INFERRED,
                EvidencePolarity.POSITIVE,
            )

        # 3. SAFETY RULE: Absence of a public developer API does NOT imply CONTACT_SALES.
        # If API is absent or only consumer UI exists, credentials are UNKNOWN / NOT_AVAILABLE.
        if "no public developer rest api" in neg_text or "strictly end-user facing" in neg_text or "has not released" in neg_text:
            matching = next((e for e in neg_ev if "strictly" in (e.snippet or "").lower() or "not released" in (e.snippet or "").lower()), None)
            return (
                CredentialAccessibility.UNKNOWN,
                matching.url if matching else None,
                matching.snippet if matching else "No developer API exists; credential accessibility is not applicable.",
                matching.provenance if matching else Provenance.INFERRED,
                EvidencePolarity.NEGATIVE,
            )

        return (
            CredentialAccessibility.UNKNOWN,
            None,
            None,
            Provenance.UNKNOWN,
            EvidencePolarity.ABSENT,
        )

    def _classify_auth(
        self,
        pos_text: str,
        neg_text: str,
        combined_text: str,
        cred_access: CredentialAccessibility,
        cred_evidence: str,
        pos_ev: List[EvidenceURL],
        neg_ev: List[EvidenceURL],
    ) -> Tuple[AuthResearch, List[ResearchClaim]]:
        supported: List[AuthMethod] = []
        grant_types: List[str] = []
        claims: List[ResearchClaim] = []

        # SAFETY RULE: Explicitly negative statements must NEVER produce a positive auth capability.
        is_oauth_negated = "does not require oauth" in neg_text or "no oauth" in neg_text or "without oauth" in neg_text
        is_apikey_negated = "does not require.*api key" in neg_text or "does not require oauth or api keys" in neg_text or "no api key" in neg_text

        # 1. Evaluate OAuth2
        if not is_oauth_negated:
            matching_oauth = next((e for e in pos_ev if "oauth" in (e.snippet or "").lower() or "connected app" in (e.snippet or "").lower()), None)
            if matching_oauth:
                supported.append(AuthMethod.OAUTH2)
                grant_types.extend(["authorization_code", "refresh_token"])
                claims.append(
                    ResearchClaim(
                        field_name="auth.supported_methods.oauth2",
                        extracted_value="OAUTH2",
                        provenance=matching_oauth.provenance,
                        source_url=matching_oauth.url,
                        supporting_excerpt=matching_oauth.snippet,
                        confidence=ConfidenceLevel.HIGH,
                        polarity=EvidencePolarity.POSITIVE,
                    )
                )

        # 2. Evaluate Personal Access Tokens
        matching_pat = next((e for e in pos_ev if "personal access token" in (e.snippet or "").lower() or "pat" in (e.snippet or "").lower()), None)
        if matching_pat:
            supported.append(AuthMethod.PERSONAL_ACCESS_TOKEN)
            claims.append(
                ResearchClaim(
                    field_name="auth.supported_methods.personal_access_token",
                    extracted_value="PERSONAL_ACCESS_TOKEN",
                    provenance=matching_pat.provenance,
                    source_url=matching_pat.url,
                    supporting_excerpt=matching_pat.snippet,
                    confidence=ConfidenceLevel.HIGH,
                    polarity=EvidencePolarity.POSITIVE,
                )
            )

        # 3. Evaluate API Key
        if not is_apikey_negated:
            matching_key = next((e for e in pos_ev if "api key" in (e.snippet or "").lower()), None)
            if matching_key:
                supported.append(AuthMethod.API_KEY)
                claims.append(
                    ResearchClaim(
                        field_name="auth.supported_methods.api_key",
                        extracted_value="API_KEY",
                        provenance=matching_key.provenance,
                        source_url=matching_key.url,
                        supporting_excerpt=matching_key.snippet,
                        confidence=ConfidenceLevel.HIGH,
                        polarity=EvidencePolarity.POSITIVE,
                    )
                )

        # 4. Evaluate Basic Auth & Bearer Tokens
        matching_basic = next((e for e in pos_ev if "basic auth" in (e.snippet or "").lower()), None)
        if matching_basic:
            supported.append(AuthMethod.BASIC_AUTH)

        matching_bearer = next((e for e in pos_ev if "jwt" in (e.snippet or "").lower() or "bearer token" in (e.snippet or "").lower()), None)
        if matching_bearer:
            supported.append(AuthMethod.BEARER_TOKEN)

        # 5. Handle tools with NO API or NO Auth required
        if not supported:
            if is_oauth_negated or is_apikey_negated or "cli" in combined_text or "command-line" in combined_text:
                supported.append(AuthMethod.OTHER)
                primary = AuthMethod.OTHER
                notes = "No SaaS API authentication supported or required."
                claims.append(
                    ResearchClaim(
                        field_name="auth.primary_method",
                        extracted_value="OTHER",
                        provenance=neg_ev[0].provenance if neg_ev else Provenance.INFERRED,
                        source_url=neg_ev[0].url if neg_ev else None,
                        supporting_excerpt=neg_ev[0].snippet if neg_ev else "Application does not expose API authentication.",
                        confidence=ConfidenceLevel.HIGH,
                        polarity=EvidencePolarity.NEGATIVE,
                    )
                )
            else:
                supported.append(AuthMethod.UNKNOWN)
                primary = AuthMethod.UNKNOWN
                notes = "Authentication details could not be verified from available documentation."
                claims.append(
                    ResearchClaim(
                        field_name="auth.primary_method",
                        extracted_value="UNKNOWN",
                        provenance=Provenance.UNKNOWN,
                        source_url=None,
                        supporting_excerpt=None,
                        confidence=ConfidenceLevel.LOW,
                        polarity=EvidencePolarity.ABSENT,
                    )
                )
        else:
            primary = supported[0]
            notes = f"Primary authentication: {primary.value}."

        auth_obj = AuthResearch(
            supported_methods=supported,
            primary_method=primary,
            credential_accessibility=cred_access,
            credential_evidence=cred_evidence or None,
            oauth_grant_types=grant_types,
            token_lifespan_notes="Standard expiring access token with refresh token rotation" if AuthMethod.OAUTH2 in supported else None,
            accessibility_notes=notes,
        )
        return auth_obj, claims

    def _classify_api_surface(
        self,
        pos_text: str,
        neg_text: str,
        combined_text: str,
        pos_ev: List[EvidenceURL],
        neg_ev: List[EvidenceURL],
    ) -> Tuple[APISurfaceResearch, List[ResearchClaim]]:
        api_types: List[APIType] = []
        claims: List[ResearchClaim] = []

        is_rest_negated = "does not provide a hosted rest api" in neg_text or "no hosted rest api" in neg_text or "no public developer rest api" in neg_text

        # 1. REST
        if not is_rest_negated and ("rest" in pos_text or "restful" in pos_text):
            matching_rest = next((e for e in pos_ev if "rest" in (e.snippet or "").lower()), None)
            if matching_rest:
                api_types.append(APIType.REST)
                claims.append(
                    ResearchClaim(
                        field_name="api_surface.has_rest",
                        extracted_value="True",
                        provenance=matching_rest.provenance,
                        source_url=matching_rest.url,
                        supporting_excerpt=matching_rest.snippet,
                        confidence=ConfidenceLevel.HIGH,
                        polarity=EvidencePolarity.POSITIVE,
                    )
                )

        # 2. GraphQL
        if "graphql" in pos_text:
            matching_gql = next((e for e in pos_ev if "graphql" in (e.snippet or "").lower()), None)
            if matching_gql:
                api_types.append(APIType.GRAPHQL)
                claims.append(
                    ResearchClaim(
                        field_name="api_surface.has_graphql",
                        extracted_value="True",
                        provenance=matching_gql.provenance,
                        source_url=matching_gql.url,
                        supporting_excerpt=matching_gql.snippet,
                        confidence=ConfidenceLevel.HIGH,
                        polarity=EvidencePolarity.POSITIVE,
                    )
                )

        # 3. CLI / Local tools
        if "command-line" in combined_text or "cli" in combined_text:
            api_types.append(APIType.OTHER)

        if not api_types:
            api_types.append(APIType.OTHER)

        # Determine Breadth
        has_rest = APIType.REST in api_types
        has_graphql = APIType.GRAPHQL in api_types

        if is_rest_negated or ("no public" in neg_text and not has_rest):
            breadth = APIBreadth.NARROW
            breadth_rationale = "Application exposes no public developer REST/GraphQL endpoints."
        elif has_rest and has_graphql:
            breadth = APIBreadth.BROAD
            breadth_rationale = "Comprehensive multi-engine surface providing both REST and GraphQL APIs."
        elif has_rest:
            breadth = APIBreadth.BROAD if "comprehensive" in pos_text or "powerful" in pos_text else APIBreadth.MODERATE
            breadth_rationale = "Documented REST API surface for platform integrations."
        elif "command-line" in combined_text:
            breadth = APIBreadth.NARROW
            breadth_rationale = "Command-line interface without hosted multi-tenant REST endpoints."
        else:
            breadth = APIBreadth.UNKNOWN
            breadth_rationale = "API breadth unverified."

        claims.append(
            ResearchClaim(
                field_name="api_surface.breadth",
                extracted_value=breadth.value,
                provenance=Provenance.INFERRED,
                source_url=None,
                supporting_excerpt=None,
                confidence=ConfidenceLevel.MEDIUM,
                polarity=EvidencePolarity.POSITIVE,
            )
        )

        has_webhooks = "webhook" in pos_text or "webhooks" in pos_text

        # Rate limits
        has_rate_limits = "rate limit" in pos_text
        rate_limit_details = None
        if has_rate_limits:
            matching_rl = next((e for e in pos_ev if "rate limit" in (e.snippet or "").lower()), None)
            rate_limit_details = matching_rl.snippet if matching_rl else "Documented rate limits enforced."

        sdks = []
        if "python" in pos_text:
            sdks.append("Python")

        api_obj = APISurfaceResearch(
            api_types=api_types,
            breadth=breadth,
            breadth_rationale=breadth_rationale,
            has_rest=has_rest,
            has_graphql=has_graphql,
            has_webhooks=has_webhooks,
            has_rate_limits_documented=has_rate_limits,
            rate_limit_details=rate_limit_details,
            official_sdks=sdks,
            openapi_spec_available=("openapi" in pos_text or "swagger" in pos_text),
            openapi_spec_url=None,
        )
        return api_obj, claims

    def _classify_mcp(
        self,
        app: AppMetadata,
        pos_text: str,
        neg_text: str,
        pos_ev: List[EvidenceURL],
    ) -> Tuple[MCPResearch, ResearchClaim]:
        # SAFETY RULE: Community reference server (e.g. modelcontextprotocol/servers) must NOT be labeled OFFICIAL
        has_mcp_negated = "no mcp server" in neg_text or "no official or third-party mcp" in neg_text
        if has_mcp_negated:
            res = MCPResearch(
                availability=MCPAvailability.NO_KNOWN_MCP,
                composio_tool_supported=False,
                composio_app_slug=None,
                existing_servers=[],
                notes="Explicitly confirmed: no MCP server or public API exists.",
            )
            claim = ResearchClaim(
                field_name="mcp.availability",
                extracted_value="NO_KNOWN_MCP",
                provenance=Provenance.LIVE_FETCHED,
                source_url=None,
                supporting_excerpt="No MCP server exists.",
                confidence=ConfidenceLevel.HIGH,
                polarity=EvidencePolarity.NEGATIVE,
            )
            return res, claim

        has_composio = "composio" in pos_text or f"composio.dev/tools/{app.app_id}" in pos_text

        # Check repository link
        matching_mcp = next((e for e in pos_ev if "model context protocol" in (e.snippet or "").lower() or "mcp" in (e.snippet or "").lower()), None)

        if matching_mcp and "modelcontextprotocol/servers" in str(matching_mcp.url).lower():
            # Anthropic/community reference server -> COMMUNITY
            availability = MCPAvailability.COMMUNITY
            existing = [str(matching_mcp.url)]
            notes = "Community / Reference Model Context Protocol server authored by MCP open-source team."
        elif has_composio:
            availability = MCPAvailability.COMPOSIO
            existing = []
            notes = f"Pre-built Composio action and trigger toolkit available for {app.name}."
        elif matching_mcp:
            availability = MCPAvailability.COMMUNITY
            existing = [str(matching_mcp.url)]
            notes = "Community MCP server identified."
        else:
            availability = MCPAvailability.NO_KNOWN_MCP
            existing = []
            notes = "No verified MCP server discovered."

        res = MCPResearch(
            availability=availability,
            composio_tool_supported=has_composio,
            composio_app_slug=app.app_id if has_composio else None,
            existing_servers=existing,
            notes=notes,
        )
        claim = ResearchClaim(
            field_name="mcp.availability",
            extracted_value=availability.value,
            provenance=matching_mcp.provenance if matching_mcp else Provenance.INFERRED,
            source_url=matching_mcp.url if matching_mcp else None,
            supporting_excerpt=matching_mcp.snippet if matching_mcp else None,
            confidence=ConfidenceLevel.HIGH if matching_mcp else ConfidenceLevel.MEDIUM,
            polarity=EvidencePolarity.POSITIVE,
        )
        return res, claim

    def _identify_blockers(
        self,
        neg_text: str,
        combined_text: str,
        cred_access: CredentialAccessibility,
        api_surface: APISurfaceResearch,
        neg_ev: List[EvidenceURL],
    ) -> List[IntegrationBlocker]:
        blockers: List[IntegrationBlocker] = []

        # 1. No Public Developer API
        if "no public developer rest api" in neg_text or "has not released" in neg_text or "strictly end-user facing" in neg_text:
            blockers.append(
                IntegrationBlocker(
                    title="No Public Developer API",
                    description="Application does not expose a public developer REST/GraphQL API or OAuth credentials.",
                    severity=BlockerSeverity.CRITICAL,
                    blocker_type="missing_endpoints",
                )
            )

        # 2. Open source CLI / Non-SaaS
        if "command-line tool" in combined_text or "cli tool" in combined_text:
            blockers.append(
                IntegrationBlocker(
                    title="Non-SaaS CLI Architecture",
                    description="Open-source CLI tool rather than hosted cloud SaaS. Requires local process execution environment.",
                    severity=BlockerSeverity.MEDIUM,
                    blocker_type="architecture",
                )
            )

        # 3. Rate limits
        if api_surface.has_rate_limits_documented:
            blockers.append(
                IntegrationBlocker(
                    title="API Rate Limits Enforced",
                    description="API enforces request rate limits requiring backoff and request throttling in agents.",
                    severity=BlockerSeverity.LOW,
                    blocker_type="rate_limit",
                )
            )

        # 4. Paid tier
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
    ) -> Tuple[float, BuildabilityScore, Optional[str], List[str], str]:
        has_critical_blocker = any(b.severity == BlockerSeverity.CRITICAL for b in blockers)
        advantages: List[str] = []

        if has_critical_blocker:
            score = 1.0
            buildability = BuildabilityScore.NOT_CURRENTLY_BUILDABLE
            primary_blocker = "Lack of a public developer API or developer credentials."
            rationale = "Integration is blocked due to lack of a public developer API or programmatic endpoints."
            return score, buildability, primary_blocker, advantages, rationale

        score = 5.0

        # Credential accessibility bonus
        if cred_access == CredentialAccessibility.SELF_SERVE_FREE:
            score += 2.5
            advantages.append("Free developer accounts / self-serve access available.")
        elif cred_access == CredentialAccessibility.SELF_SERVE_TRIAL:
            score += 1.5
            advantages.append("Self-serve trial accounts available.")
        elif cred_access == CredentialAccessibility.PARTNER_GATED:
            score += 1.0
            advantages.append("Developer partner program provides test stores/sandboxes.")
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
            advantages.append("Community / Reference Model Context Protocol server available.")

        # Non-SaaS CLI adjustment
        if any(b.blocker_type == "architecture" for b in blockers):
            score = 4.0
            buildability = BuildabilityScore.BUILDABLE_WITH_LIMITATIONS
            primary_blocker = "CLI tool architecture requires local execution container."
            rationale = "Buildable via local subprocess / CLI wrapper, but lacks hosted SaaS cloud endpoints."
            return score, buildability, primary_blocker, advantages, rationale

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
