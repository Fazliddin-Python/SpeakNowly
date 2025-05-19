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


@router.get("/", response_model=List[TariffSerializer])
async def list_tariffs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    lang: str = Query("en", description="Language code: en, ru, uz")
):
    """
    List all tariffs with pagination.
    """

    cache_key = f"tariffs:{lang}:page={page}:size={page_size}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    offset = (page - 1) * page_size
    tariffs = await Tariff.filter(is_active=True).offset(offset).limit(page_size)
    # Map only the requested language fields
    result = []
    for tariff in tariffs:
        result.append({
            "id": tariff.id,
            "name": getattr(tariff, f"name_{lang}", tariff.name_en),
            "description": getattr(tariff, f"description_{lang}", tariff.description_en),
            # ...other fields...
        })
    await cache.set(cache_key, result, expire=3600)
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