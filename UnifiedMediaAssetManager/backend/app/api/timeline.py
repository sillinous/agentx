"""
Timeline Events API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..models.database import TimelineEventDB, UniverseDB, ElementDB
from ..schemas.world_building import (
    TimelineEventCreate,
    TimelineEventUpdate,
    TimelineEventResponse
)
from ..database import get_db


router = APIRouter(prefix="/api", tags=["timeline"])


@router.post("/universes/{universe_id}/timeline", response_model=TimelineEventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    universe_id: UUID,
    event: TimelineEventCreate,
    db: Session = Depends(get_db)
):
    """
    Create a timeline event for a universe.

    Timeline events track chronological narrative progression with:
    - Title, description, timestamp
    - Event type (battle, discovery, meeting, etc.)
    - Participants (element IDs)
    - Location (element ID)
    - Significance and consequences
    """
    # Check if universe exists
    universe = db.query(UniverseDB).filter(UniverseDB.id == str(universe_id)).first()
    if not universe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Universe with id {universe_id} not found"
        )

    # Validate location if provided
    if event.location_id:
        location = db.query(ElementDB).filter(
            ElementDB.id == str(event.location_id),
            ElementDB.universe_id == str(universe_id)
        ).first()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location element {event.location_id} not found in universe"
            )

    # Create event
    db_event = TimelineEventDB(
        universe_id=str(universe_id),
        **event.model_dump()
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event


@router.get("/universes/{universe_id}/timeline", response_model=List[TimelineEventResponse])
async def list_events(
    universe_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Filter events after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events before this date"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    significance: Optional[str] = Query(None, description="Filter by significance (minor/major/pivotal)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    db: Session = Depends(get_db)
):
    """
    List timeline events for a universe, sorted chronologically.

    Supports filtering by:
    - Date range (start_date, end_date)
    - Event type
    - Significance level
    """
    query = db.query(TimelineEventDB).filter(
        TimelineEventDB.universe_id == str(universe_id)
    )

    # Apply filters
    if start_date:
        query = query.filter(TimelineEventDB.event_timestamp >= start_date)
    if end_date:
        query = query.filter(TimelineEventDB.event_timestamp <= end_date)
    if event_type:
        query = query.filter(TimelineEventDB.event_type == event_type)
    if significance:
        query = query.filter(TimelineEventDB.significance == significance)

    # Sort chronologically and limit
    events = query.order_by(TimelineEventDB.event_timestamp.asc()).limit(limit).all()

    return events


@router.get("/timeline/{event_id}", response_model=TimelineEventResponse)
async def get_event(
    event_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific timeline event by ID.
    """
    event = db.query(TimelineEventDB).filter(TimelineEventDB.id == str(event_id)).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timeline event with id {event_id} not found"
        )

    return event


@router.put("/timeline/{event_id}", response_model=TimelineEventResponse)
async def update_event(
    event_id: UUID,
    event_update: TimelineEventUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a timeline event.

    Only provided fields will be updated.
    """
    event = db.query(TimelineEventDB).filter(TimelineEventDB.id == str(event_id)).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timeline event with id {event_id} not found"
        )

    # Update only provided fields
    update_data = event_update.model_dump(exclude_unset=True)

    # Validate location if being updated
    if "location_id" in update_data and update_data["location_id"]:
        location = db.query(ElementDB).filter(
            ElementDB.id == str(update_data["location_id"]),
            ElementDB.universe_id == event.universe_id
        ).first()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location element {update_data['location_id']} not found in universe"
            )

    for field, value in update_data.items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)

    return event


@router.delete("/timeline/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a timeline event.
    """
    event = db.query(TimelineEventDB).filter(TimelineEventDB.id == str(event_id)).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timeline event with id {event_id} not found"
        )

    db.delete(event)
    db.commit()

    return None


@router.get("/timeline/{event_id}/participants", response_model=dict)
async def get_event_participants(
    event_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about event participants.

    Returns element details for all participant IDs.
    """
    event = db.query(TimelineEventDB).filter(TimelineEventDB.id == str(event_id)).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timeline event with id {event_id} not found"
        )

    if not event.participants:
        return {"participants": []}

    # Fetch participant elements
    participants = db.query(ElementDB).filter(
        ElementDB.id.in_(event.participants)
    ).all()

    return {
        "event_id": event_id,
        "participants": [
            {
                "id": str(p.id),
                "name": p.name,
                "element_type": p.element_type,
                "entity_subtype": p.entity_subtype
            }
            for p in participants
        ]
    }
