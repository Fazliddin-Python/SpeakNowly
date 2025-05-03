from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Optional
from tortoise.exceptions import DoesNotExist
from models.tariffs import Tariff, TariffCategory, Feature, TariffFeature
from ..serializers.tariffs import (
    TariffSerializer,
    TariffDetailSerializer,
    TariffCategorySerializer,
    FeatureSerializer,
    TariffFeatureSerializer,
)

router = APIRouter()


@router.get("/", response_model=List[TariffSerializer])
async def get_tariffs(
    is_active: Optional[bool] = Query(None),
    category: Optional[int] = Query(None),
):
    """
    Get a list of tariffs with optional filters.
    """
    query = Tariff.all()
    if is_active is not None:
        query = query.filter(is_active=is_active)
    if category:
        query = query.filter(category_id=category)

    tariffs = await query.all()
    if not tariffs:
        raise HTTPException(status_code=404, detail="No tariffs found")
    return tariffs


@router.get("/{id}/", response_model=TariffDetailSerializer)
async def get_tariff_detail(id: int):
    """
    Get detailed information about a specific tariff.
    """
    try:
        tariff = await Tariff.get(id=id).prefetch_related("category", "features__feature")
        return {
            "id": tariff.id,
            "category": {
                "id": tariff.category.id,
                "name": tariff.category.name,
                "name_uz": tariff.category.name_uz,
                "name_ru": tariff.category.name_ru,
                "name_en": tariff.category.name_en,
                "sale": tariff.category.sale,
                "is_active": tariff.category.is_active,
            } if tariff.category else None,
            "name": tariff.name,
            "old_price": tariff.old_price,
            "price": tariff.price,
            "price_in_stars": tariff.price_in_stars,
            "description": tariff.description,
            "description_uz": tariff.description_uz,
            "description_ru": tariff.description_ru,
            "description_en": tariff.description_en,
            "tokens": tariff.tokens,
            "duration": tariff.duration,
            "is_active": tariff.is_active,
            "is_default": tariff.is_default,
            "features": [
                {
                    "id": feature.feature.id,
                    "name": feature.feature.name,
                    "description": feature.feature.description,
                }
                for feature in tariff.features
            ],
        }
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Tariff not found")


@router.get("/categories/", response_model=List[TariffCategorySerializer])
async def get_tariff_categories():
    """
    Get a list of tariff categories.
    """
    categories = await TariffCategory.filter(is_active=True).all()
    if not categories:
        raise HTTPException(status_code=404, detail="No tariff categories found")
    return categories


@router.get("/features/", response_model=List[FeatureSerializer])
async def get_features():
    """
    Get a list of all features.
    """
    features = await Feature.all()
    if not features:
        raise HTTPException(status_code=404, detail="No features found")
    return features


@router.get("/{tariff_id}/features/", response_model=List[TariffFeatureSerializer])
async def get_tariff_features(tariff_id: int):
    """
    Get a list of features for a specific tariff.
    """
    try:
        tariff = await Tariff.get(id=tariff_id).prefetch_related("features__feature")
        return [
            {
                "id": feature.id,
                "tariff_id": tariff.id,
                "feature_id": feature.feature.id,
                "is_included": feature.is_included,
            }
            for feature in tariff.features
        ]
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Tariff not found")