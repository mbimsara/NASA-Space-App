
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from sqlalchemy import update

from app.schemas.farm import (
    FarmProfile,
    FarmResponse,
    FarmUpdateRequest
)

from app.database.connection import get_db
from app.models.farm import Farm
from app.schemas.farm import FarmProfile, FarmResponse


router = APIRouter(
    prefix="/farms",
    tags=["Farms"]
)


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED
)
def create_farm(
    profile: FarmProfile,
    db: Session = Depends(get_db)
):
    # Create a new farm database record
    new_farm = Farm(
        profile=profile.model_dump(mode="json")
    )

    # Save to database
    db.add(new_farm)
    db.commit()
    db.refresh(new_farm)

    # Return saved farm information
    return {
        "id": new_farm.id,
        "input_version": new_farm.input_version,
        "profile": new_farm.profile
    }


@router.get(
    "/{farm_id}",
    response_model=FarmResponse
)
def get_farm(
    farm_id: str,
    db: Session = Depends(get_db)
):
    # Find the farm using its ID
    farm = db.get(Farm, farm_id)

    # Return 404 if the farm does not exist
    if farm is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Farm not found."
                }
            }
        )

    # Return the saved farm
    return {
        "id": farm.id,
        "input_version": farm.input_version,
        "profile": farm.profile
    }


@router.patch(
    "/{farm_id}",
    response_model=FarmResponse
)
def update_farm(
    farm_id: str,
    request: FarmUpdateRequest,
    db: Session = Depends(get_db)
):
    # Update only if the expected version matches
    result = db.execute(
        update(Farm)
        .where(
            Farm.id == farm_id,
            Farm.input_version == request.expected_input_version
        )
        .values(
            profile=request.profile.model_dump(mode="json"),
            input_version=Farm.input_version + 1
        )
    )

    if result.rowcount == 0:
        db.rollback()

        # Check whether this farm exists
        farm = db.get(Farm, farm_id)

        if farm is None:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Farm not found."
                    }
                }
            )

        # The farm exists but its version has changed
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "VERSION_CONFLICT",
                    "message": "Farm version is outdated. Retrieve the latest version and try again."
                }
            }
        )

    db.commit()

    updated_farm = db.get(Farm, farm_id)

    return {
        "id": updated_farm.id,
        "input_version": updated_farm.input_version,
        "profile": updated_farm.profile
    }
