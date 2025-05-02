from fastapi import APIRouter, HTTPException
from models.tariffs import Tariff, TariffCategory, Feature, TariffFeature, Sale, Payment
from api.client_site.v1.serializers.tariffs import (
    TariffSerializer,
    TariffCategorySerializer,
    FeatureSerializer,
    TariffFeatureSerializer,
    SaleSerializer,
    PaymentSerializer,
)

router = APIRouter()

# TariffCategory endpoints
@router.get("/categories/", response_model=list[TariffCategorySerializer])
async def get_tariff_categories():
    categories = await TariffCategory.all()
    return categories

# Tariff endpoints
@router.get("/", response_model=list[TariffSerializer])
async def get_tariffs():
    tariffs = await Tariff.all()
    return tariffs

@router.get("/{tariff_id}/", response_model=TariffSerializer)
async def get_tariff(tariff_id: int):
    tariff = await Tariff.get_or_none(id=tariff_id)
    if not tariff:
        raise HTTPException(status_code=404, detail="Tariff not found")
    return tariff

# Feature endpoints
@router.get("/features/", response_model=list[FeatureSerializer])
async def get_features():
    features = await Feature.all()
    return features

# TariffFeature endpoints
@router.get("/tariff-features/", response_model=list[TariffFeatureSerializer])
async def get_tariff_features():
    tariff_features = await TariffFeature.all()
    return tariff_features

# Sale endpoints
@router.get("/sales/", response_model=list[SaleSerializer])
async def get_sales():
    sales = await Sale.all()
    return sales

# Payment endpoints
@router.get("/payments/", response_model=list[PaymentSerializer])
async def get_payments():
    payments = await Payment.all()
    return payments