from fastapi import APIRouter, HTTPException, Query, status
from typing import List
from tortoise.exceptions import DoesNotExist
from models.tariffs import Tariff, TariffCategory, Feature, TariffFeature
from ..serializers.tariffs import (
    TariffSerializer,
    TariffDetailSerializer,
    TariffCategorySerializer,
    FeatureSerializer,
    SaleSerializer,
)

router = APIRouter()


@router.get("/", response_model=List[TariffSerializer])
async def list_tariffs(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1)):
    """
    List all tariffs with pagination.
    """
    offset = (page - 1) * page_size
    tariffs = await Tariff.all().offset(offset).limit(page_size)
    return tariffs


@router.get("/{tariff_id}/", response_model=TariffDetailSerializer)
async def get_tariff_detail(tariff_id: int):
    """
    Retrieve detailed information about a specific tariff.
    """
    try:
        tariff = await Tariff.get(id=tariff_id).prefetch_related("features", "category")
        return tariff
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Tariff not found")


@router.get("/categories/", response_model=List[TariffCategorySerializer])
async def list_tariff_categories():
    """
    List all tariff categories.
    """
    categories = await Tariff.category.all()
    return categories


@router.get("/features/", response_model=List[FeatureSerializer])
async def list_features():
    """
    List all features.
    """
    features = await Feature.all()
    return features


@router.get("/{tariff_id}/features/", response_model=List[FeatureSerializer])
async def list_tariff_features(tariff_id: int):
    """
    List all features for a specific tariff.
    """
    try:
        tariff = await Tariff.get(id=tariff_id).prefetch_related("features")
        return tariff.features
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Tariff not found")


@router.get("/sales/", response_model=List[SaleSerializer])
async def list_sales():
    """
    List all active sales.
    """
    sales = await Sale.filter(is_active=True)
    return sales


@router.get("/{tariff_id}/sales/", response_model=List[SaleSerializer])
async def list_tariff_sales(tariff_id: int):
    """
    List all sales for a specific tariff.
    """
    try:
        sales = await Sale.filter(tariff_id=tariff_id, is_active=True)
        return sales
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="No sales found for this tariff")