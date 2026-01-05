"""
World Configuration API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ..models.database import WorldConfigDB, UniverseDB
from ..schemas.world_building import (
    WorldConfigCreate,
    WorldConfigUpdate,
    WorldConfigResponse
)
from ..database import get_db


router = APIRouter(prefix="/api/universes", tags=["world-config"])


@router.post("/{universe_id}/world-config", response_model=WorldConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_world_config(
    universe_id: UUID,
    config: WorldConfigCreate,
    db: Session = Depends(get_db)
):
    """
    Create world configuration for a universe.

    This defines the core parameters that AI agents will use for context:
    - Genre, physics, magic system, tech level, tone
    - Color palette and art style notes
    - Reference images
    """
    # Check if universe exists
    universe = db.query(UniverseDB).filter(UniverseDB.id == str(universe_id)).first()
    if not universe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Universe with id {universe_id} not found"
        )

    # Check if config already exists
    existing_config = db.query(WorldConfigDB).filter(
        WorldConfigDB.universe_id == str(universe_id)
    ).first()
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"World configuration already exists for universe {universe_id}"
        )

    # Create config
    db_config = WorldConfigDB(
        universe_id=str(universe_id),
        **config.model_dump()
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)

    return db_config


@router.get("/{universe_id}/world-config", response_model=WorldConfigResponse)
async def get_world_config(
    universe_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get world configuration for a universe.
    """
    config = db.query(WorldConfigDB).filter(
        WorldConfigDB.universe_id == str(universe_id)
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World configuration not found for universe {universe_id}"
        )

    return config


@router.put("/{universe_id}/world-config", response_model=WorldConfigResponse)
async def update_world_config(
    universe_id: UUID,
    config_update: WorldConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    Update world configuration for a universe.

    Only provided fields will be updated.
    """
    config = db.query(WorldConfigDB).filter(
        WorldConfigDB.universe_id == str(universe_id)
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World configuration not found for universe {universe_id}"
        )

    # Update only provided fields
    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)

    return config


@router.delete("/{universe_id}/world-config", status_code=status.HTTP_204_NO_CONTENT)
async def delete_world_config(
    universe_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete world configuration for a universe.
    """
    config = db.query(WorldConfigDB).filter(
        WorldConfigDB.universe_id == str(universe_id)
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World configuration not found for universe {universe_id}"
        )

    db.delete(config)
    db.commit()

    return None
