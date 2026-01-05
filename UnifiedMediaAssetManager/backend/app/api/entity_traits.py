"""
Entity Traits API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..models.database import EntityTraitDB, ElementDB
from ..schemas.world_building import (
    EntityTraitCreate,
    EntityTraitUpdate,
    EntityTraitResponse,
    TraitTemplatesResponse,
    TRAIT_TEMPLATES,
    ENTITY_SUBTYPES
)
from ..database import get_db


router = APIRouter(prefix="/api", tags=["entity-traits"])


@router.get("/entity-types/{entity_type}/traits", response_model=TraitTemplatesResponse)
async def get_trait_templates(entity_type: str):
    """
    Get suggested trait templates for an entity type.

    Returns predefined trait templates that guide users in adding
    type-specific information to their entities.
    """
    if entity_type not in ENTITY_SUBTYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid entity type. Must be one of: {', '.join(ENTITY_SUBTYPES)}"
        )

    if entity_type not in TRAIT_TEMPLATES:
        return TraitTemplatesResponse(
            entity_type=entity_type,
            templates=[]
        )

    return TraitTemplatesResponse(
        entity_type=entity_type,
        templates=TRAIT_TEMPLATES[entity_type]
    )


@router.post("/elements/{element_id}/traits", response_model=EntityTraitResponse, status_code=status.HTTP_201_CREATED)
async def add_trait(
    element_id: UUID,
    trait: EntityTraitCreate,
    db: Session = Depends(get_db)
):
    """
    Add a trait to an element.

    Traits are type-specific attributes that provide rich context for AI agents.
    Examples: character backstory, location geography, item powers.
    """
    # Check if element exists
    element = db.query(ElementDB).filter(ElementDB.id == str(element_id)).first()
    if not element:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Element with id {element_id} not found"
        )

    # Check if trait with same key already exists
    existing_trait = db.query(EntityTraitDB).filter(
        EntityTraitDB.element_id == str(element_id),
        EntityTraitDB.trait_key == trait.trait_key
    ).first()
    if existing_trait:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Trait with key '{trait.trait_key}' already exists for this element"
        )

    # Create trait
    db_trait = EntityTraitDB(
        element_id=str(element_id),
        **trait.model_dump()
    )
    db.add(db_trait)
    db.commit()
    db.refresh(db_trait)

    return db_trait


@router.get("/elements/{element_id}/traits", response_model=List[EntityTraitResponse])
async def list_traits(
    element_id: UUID,
    category: str = None,
    db: Session = Depends(get_db)
):
    """
    List all traits for an element.

    Optionally filter by category (core, physical, behavioral, historical).
    """
    query = db.query(EntityTraitDB).filter(EntityTraitDB.element_id == str(element_id))

    if category:
        query = query.filter(EntityTraitDB.trait_category == category)

    traits = query.order_by(EntityTraitDB.display_order, EntityTraitDB.trait_key).all()

    return traits


@router.get("/elements/{element_id}/traits/{trait_id}", response_model=EntityTraitResponse)
async def get_trait(
    element_id: UUID,
    trait_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific trait by ID.
    """
    trait = db.query(EntityTraitDB).filter(
        EntityTraitDB.id == str(trait_id),
        EntityTraitDB.element_id == str(element_id)
    ).first()

    if not trait:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trait with id {trait_id} not found for element {element_id}"
        )

    return trait


@router.put("/elements/{element_id}/traits/{trait_id}", response_model=EntityTraitResponse)
async def update_trait(
    element_id: UUID,
    trait_id: UUID,
    trait_update: EntityTraitUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a trait.

    Only provided fields will be updated.
    """
    trait = db.query(EntityTraitDB).filter(
        EntityTraitDB.id == str(trait_id),
        EntityTraitDB.element_id == str(element_id)
    ).first()

    if not trait:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trait with id {trait_id} not found for element {element_id}"
        )

    # Update only provided fields
    update_data = trait_update.model_dump(exclude_unset=True)

    # If trait_key is being changed, check for conflicts
    if "trait_key" in update_data and update_data["trait_key"] != trait.trait_key:
        existing_trait = db.query(EntityTraitDB).filter(
            EntityTraitDB.element_id == str(element_id),
            EntityTraitDB.trait_key == update_data["trait_key"],
            EntityTraitDB.id != str(trait_id)
        ).first()
        if existing_trait:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Trait with key '{update_data['trait_key']}' already exists for this element"
            )

    for field, value in update_data.items():
        setattr(trait, field, value)

    db.commit()
    db.refresh(trait)

    return trait


@router.delete("/elements/{element_id}/traits/{trait_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trait(
    element_id: UUID,
    trait_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a trait.
    """
    trait = db.query(EntityTraitDB).filter(
        EntityTraitDB.id == str(trait_id),
        EntityTraitDB.element_id == str(element_id)
    ).first()

    if not trait:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trait with id {trait_id} not found for element {element_id}"
        )

    db.delete(trait)
    db.commit()

    return None
