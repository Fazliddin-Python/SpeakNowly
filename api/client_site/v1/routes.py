from fastapi import APIRouter
from app.api.client_site.v1.views import SomeView  # Импортируйте ваши представления

router = APIRouter()

@router.get("/some-endpoint")
async def some_endpoint():
    return await SomeView.some_method()  # Пример вызова метода из представления

# Добавьте другие маршруты по мере необходимости
