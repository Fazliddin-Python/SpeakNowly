from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List
from tortoise.exceptions import DoesNotExist

from models.tariffs import TariffCategory
from ..serializers.tariffs import PlanInfo, TariffInfo, FeatureItemInfo, FeatureInfo
from services.cache_service import cache
from utils.i18n import get_translation

router = APIRouter()


def _translate(obj, field: str, lang: str) -> str:
    return getattr(obj, f"{field}_{lang}", None) or getattr(obj, field, "") or ""


@router.get("/", response_model=List[PlanInfo])
async def list_plans(
    request: Request,
    t: dict = Depends(get_translation),
):
    """
    Return all plans with nested tariffs and features.
    Uses Accept-Language header to pick one of: en, ru, uz.
    """
    raw_lang = request.headers.get("Accept-Language", "en").split(",")[0]
    lang = raw_lang.split("-")[0].lower()
    if lang not in {"en", "ru", "uz"}:
        raise HTTPException(status_code=400, detail=t.get("invalid_language", "Unsupported language"))

    cache_key = f"plans_{lang}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    categories = await TariffCategory.filter(is_active=True).prefetch_related(
        "tariffs__features__feature"
    )

    result: List[PlanInfo] = []
    for category in categories:
        category_name = _translate(category, "name", lang)
        active_tariffs = [t_obj for t_obj in category.tariffs if t_obj.is_active]
        tariffs_list: List[TariffInfo] = []

        for tariff in active_tariffs:
            t_name = _translate(tariff, "name", lang)
            t_desc = _translate(tariff, "description", lang)
            redirect_url = getattr(tariff, "redirect_url", "") or ""
            features_list: List[FeatureItemInfo] = []

            for tf in tariff.features:
                feat = tf.feature
                if not feat:
                    continue

                f_name = _translate(feat, "name", lang)
                f_desc = _translate(feat, "description", lang)

                feature_info = FeatureInfo(
                    id=feat.id,
                    name=f_name,
                    description=f_desc
                )
                feat_item = FeatureItemInfo(
                    id=tf.id,
                    tariff=tf.tariff_id,
                    feature=feature_info,
                    is_included=tf.is_included
                )
                features_list.append(feat_item)

            tariff_info = TariffInfo(
                id=tariff.id,
                name=t_name,
                price=float(tariff.price),
                old_price=float(tariff.old_price) if tariff.old_price is not None else None,
                description=t_desc,
                tokens=int(tariff.tokens),
                duration=int(tariff.duration),
                redirect_url=redirect_url,
                is_default=bool(tariff.is_default),
                price_in_stars=int(tariff.price_in_stars),
                features=features_list
            )
            tariffs_list.append(tariff_info)

        plan_info = PlanInfo(
            id=category.id,
            name=category_name,
            sale=float(category.sale),
            tariffs=tariffs_list
        )
        result.append(plan_info)

    await cache.set(cache_key, result, expire=3600)
    return result
