"""
Incident service orchestrating core incident lifecycle, matching, timelines, and claims.
Zero direct infrastructure, notification, or raw database dependencies.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from app.domain.claims import Claim, Contradiction
from app.domain.entities import NamedEntity
from app.domain.events import (
    BreakingIncidentDetected,
    ContradictionDetected,
    EventDispatcher,
    IncidentCreated,
    IncidentUpdated,
)
from app.domain.incidents import Incident, IncidentStatus, TimelineEntry
from app.domain.messages import Message
from app.incidents.contradictions import ContradictionDetector
from app.incidents.detector import IncidentDetector
from app.incidents.matcher import IncidentMatcher
from app.incidents.timeline import TimelineService
from app.incidents.updater import IncidentUpdater
from app.intelligence.confidence import ConfidenceCalculator
from app.intelligence.entities import EntityExtractor
from app.intelligence.summarizer import IntelligenceSummarizer
from app.storage.repositories.incidents import IncidentRepository
from app.storage.repositories.messages import MessageRepository


@dataclass
class IncidentResult:
    """Outcome of processing a message through the incident service."""
    incident: Incident
    created: bool
    is_material_change: bool
    change_summary: str
    contradictions_detected: List[Contradiction]


class IncidentService:
    """Orchestrates incident discovery, updates, and domain event publishing."""

    def __init__(
        self,
        incident_repo: IncidentRepository,
        message_repo: MessageRepository,
        event_dispatcher: Optional[EventDispatcher] = None,
        summarizer: Optional[IntelligenceSummarizer] = None,
        detector: Optional[IncidentDetector] = None,
        matcher: Optional[IncidentMatcher] = None,
        updater: Optional[IncidentUpdater] = None,
        contradiction_detector: Optional[ContradictionDetector] = None,
        confidence_calculator: Optional[ConfidenceCalculator] = None,
    ):
        self.incident_repo = incident_repo
        self.message_repo = message_repo
        self.event_dispatcher = event_dispatcher or EventDispatcher()
        self.summarizer = summarizer or IntelligenceSummarizer()
        self.detector = detector or IncidentDetector()
        self.matcher = matcher or IncidentMatcher()
        self.updater = updater or IncidentUpdater()
        self.contradiction_detector = contradiction_detector or ContradictionDetector()
        self.confidence_calc = confidence_calculator or ConfidenceCalculator()

    async def get_details(self, incident_id: int) -> Optional[Incident]:
        """Fetch complete incident domain model by ID."""
        return await self.incident_repo.get(incident_id)

    async def get_hourly_updates(self, limit: int = 20) -> List[Incident]:
        """Retrieve active incidents updated during the current cycle."""
        return await self.incident_repo.list_active()

    async def process_message(self, message: Message) -> Optional[IncidentResult]:
        """
        Process a processed message through incident domain lifecycle.

        Steps:
        1. Find candidate incidents
        2. Match against candidates
        3. Create new or update matched incident
        4. Update timeline
        5. Process claims
        6. Detect contradictions
        7. Recalculate confidence
        8. Check material change & emit domain events
        """
        now = datetime.now(timezone.utc)
        candidates = await self.incident_repo.find_candidates(message)
        matched_incident, match_score = self.matcher.find_best_match(message, candidates)

        # If it doesn't match an existing incident, check if it qualifies to initiate a new one
        if matched_incident is None and not self.detector.should_track_as_incident(message):
            return None

        created = False
        is_material = False
        change_summary = ""

        if matched_incident is not None:
            # Update existing candidate
            incident, is_material, change_summary = self.updater.update_incident(
                matched_incident, message
            )
        else:
            # Create new incident
            created = True
            is_material = True
            change_summary = "Initial incident creation"

            # Generate initial title and summary if missing
            title = message.headline or (message.cleaned_text[:80] + ("..." if len(message.cleaned_text) > 80 else ""))
            summary = message.summary or message.cleaned_text[:250]
            why_it_matters = message.why_it_matters or "Initial intelligence report."

            entities = EntityExtractor.extract_entities(message.cleaned_text)

            incident = Incident(
                id=None,
                title=title,
                category=message.category or "other",
                status=IncidentStatus.NEW,
                importance_score=message.importance_score,
                confidence_score=0.5,
                summary=summary,
                why_it_matters=why_it_matters,
                sources=[message.source_channel] if message.source_channel else [],
                entities=entities,
                created_at=now,
                updated_at=now,
            )
            incident.recompute_severity()
            incident = await self.incident_repo.create(incident)

        # 4. Add timeline entry
        timeline_entry = TimelineService.create_timeline_entry(
            incident_id=incident.id,  # type: ignore
            message=message,
        )
        saved_timeline = await self.incident_repo.add_timeline_entry(timeline_entry)
        incident.add_timeline_entry(saved_timeline)

        # 5. Extract & attach simple claim
        claim = Claim(
            id=None,
            incident_id=incident.id,
            message_id=message.id,
            statement=message.headline or message.cleaned_text[:120],
            source_name=message.source_channel,
            confidence=0.7,
            extracted_at=now,
        )
        saved_claim = await self.incident_repo.add_claim(claim)
        incident.claims.append(saved_claim)

        # 6. Detect contradictions
        contradictions = self.contradiction_detector.find_all_contradictions(incident.claims)
        if len(contradictions) > incident.contradictions_count:
            incident.contradictions_count = len(contradictions)
            is_material = True
            change_summary += "; New contradiction detected"
            for c in contradictions:
                await self.event_dispatcher.publish(
                    ContradictionDetected(incident=incident, contradiction=c)
                )

        # 7. Recalculate confidence
        has_official = any("gov" in s or "official" in s for s in incident.sources)
        incident.confidence_score = self.confidence_calc.calculate_incident_confidence(
            sources=incident.sources,
            claims_count=len(incident.claims),
            contradictions_count=incident.contradictions_count,
            has_official_source=has_official,
        )

        # 8. Persist updated incident
        incident = await self.incident_repo.update(incident)

        # 9. Link message to incident
        message.incident_id = incident.id
        if message.id:
            await self.message_repo.update(message)

        # 10. Publish Domain Events
        if created:
            await self.event_dispatcher.publish(IncidentCreated(incident=incident))
        elif is_material:
            await self.event_dispatcher.publish(
                IncidentUpdated(
                    incident=incident,
                    is_material_change=True,
                    change_summary=change_summary,
                )
            )

        if incident.is_breaking:
            await self.event_dispatcher.publish(
                BreakingIncidentDetected(
                    incident=incident,
                    trigger_message_text=message.cleaned_text,
                )
            )

        return IncidentResult(
            incident=incident,
            created=created,
            is_material_change=is_material,
            change_summary=change_summary,
            contradictions_detected=contradictions,
        )
