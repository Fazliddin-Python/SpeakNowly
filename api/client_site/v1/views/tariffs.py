from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List
from tortoise.exceptions import DoesNotExist
from models.tariffs import Sale, Tariff, TariffCategory, Feature, TariffFeature
from ..serializers.tariffs import (
    TariffSerializer,
    TariffDetailSerializer,
    TariffCategorySerializer,
    FeatureSerializer,
    SaleSerializer,
)
from services.cache_service import cache

router = APIRouter()


@router.get("/categories/", response_model=List[TariffCategorySerializer])
async def list_tariff_categories():
    """
    List all tariff categories.
    """
    cache_key = "tariff_categories"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    categories = await TariffCategory.filter(is_active=True)
    await cache.set(cache_key, categories, expire=86400)  # one day
    return categories

@router.get("/categories/{category_id}/", response_model=TariffCategorySerializer)
async def get_category_details(category_id: int):
    """
    Retrieve details of a specific tariff category.
    """
    try:
        category = await TariffCategory.get(id=category_id, is_active=True)
        return category
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Category not found")


@router.get("/features/", response_model=List[FeatureSerializer])
async def list_features():
    """
    List all features.
    """
    cache_key = "tariff_features"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    features = await Feature.all()
    await cache.set(cache_key, features, expire=86400)  # one day
    return features


@router.get("/features/{feature_id}/", response_model=List[FeatureSerializer])
async def list_tariff_features(tariff_id: int):
    """
    List all features for a specific tariff.
    """
    try:
        tariff_features = await TariffFeature.filter(tariff_id=tariff_id).select_related("feature")
        features = [tf.feature for tf in tariff_features]
        return features
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Tariff not found")


@router.get("/sales/", response_model=List[SaleSerializer])
async def list_sales():
    """
    List all active sales.
    """
    sales = await Sale.filter(is_active=True)
    return sales


@router.get("/sales/{sale_id}/", response_model=List[SaleSerializer])
async def list_tariff_sales(tariff_id: int):
    """
    List all sales for a specific tariff.
    """
    try:
        sales = await Sale.filter(tariff_id=tariff_id, is_active=True)
        return sales
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="No sales found for this tariff")


@router.get("/", response_model=List[TariffDetailSerializer])
async def list_tariffs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    lang: str = Query("en", description="Language code: en, ru, uz")
):
    """
    List all active tariffs with pagination and language support.
    - `page`: Page number for pagination (default is 1).
    - `page_size`: Number of tariffs per page (default is 10).
    - `lang`: Language code for tariff names and descriptions (default is "en").
    """
    if page < 1 or page_size < 1:
        raise HTTPException(status_code=400, detail="Page and page_size must be greater than 0")
    offset = (page - 1) * page_size
    tariffs = await Tariff.filter(is_active=True)\
        .offset(offset).limit(page_size)\
        .prefetch_related("features__feature", "category")
    result = []
    for tariff in tariffs:
        result.append({
            "id": tariff.id,
            "created_at": tariff.created_at,
            "updated_at": tariff.updated_at,
            "category": {
                "name": getattr(tariff.category, f"name_{lang}", getattr(tariff.category, "name", "")) if tariff.category else "",
                "name_uz": getattr(tariff.category, "name_uz", ""),
                "name_ru": getattr(tariff.category, "name_ru", ""),
                "name_en": getattr(tariff.category, "name_en", ""),
                "sale": float(getattr(tariff.category, "sale", 0)),
                "is_active": getattr(tariff.category, "is_active", False),
            } if tariff.category else None,
            "name": getattr(tariff, f"name_{lang}", getattr(tariff, "name", "")) or "",
            "old_price": int(getattr(tariff, "old_price", 0) or 0),
            "price": int(getattr(tariff, "price", 0) or 0),
            "price_in_stars": int(getattr(tariff, "price_in_stars", 0) or 0),
            "description": getattr(tariff, "description", "") or "",
            "description_uz": getattr(tariff, "description_uz", "") or "",
            "description_ru": getattr(tariff, "description_ru", "") or "",
            "description_en": getattr(tariff, "description_en", "") or "",
            "tokens": int(getattr(tariff, "tokens", 0) or 0),
            "duration": int(getattr(tariff, "duration", 0) or 0),
            "is_active": bool(getattr(tariff, "is_active", False)),
            "is_default": bool(getattr(tariff, "is_default", False)),
            "features": [
                {
                    "name": f.feature.name,
                    "description": f.feature.description
                } for f in getattr(tariff, "features", []) if f.feature
            ]
        })
    return result


@router.get("/{tariff_id}/", response_model=TariffDetailSerializer)
async def get_tariff_detail(tariff_id: int):
    """
    Retrieve detailed information about a specific tariff.
    """
    try:
        tariff = await Tariff.get(id=tariff_id, is_active=True).prefetch_related("features", "category")
        return tariff
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Tariff not found")