import sys
import os

# Добавляем родительскую папку (app/) в sys.path,
# чтобы 'from main import app' работал корректно.
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
)

import pytest
import pytest_asyncio
from httpx import AsyncClient
from tortoise import Tortoise
from typing import Dict, Any

from main import app  # теперь найдётся main.py в папке app/


class DummyChatGPT:
    async def analyse_listening(self, system: str, user: str) -> str:
        return (
            '{"correct_answers": 10, "overall_score": 6.5, '
            '"feedback": {"listening_skills": "Good", '
                         '"concentration": "Fair", '
                         '"strategy_recommendations": "Practice more."}}'
        )


@pytest_asyncio.fixture(scope="session", autouse=True)
async def initialize_db():
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={
            "models": [
                "models",
                "models.tests.listening",
                "models.users",
                "models.transactions",
            ]
        },
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest_asyncio.fixture
async def client():
    from services.chatgpt.integration import ChatGPTIntegration
    app.dependency_overrides[ChatGPTIntegration] = lambda: DummyChatGPT()

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac


@pytest.mark.asyncio
async def test_listening_crud_flow(client: AsyncClient):
    resp = await client.post(
        "/listening/tests",
        json={"title": "Test Listening", "description": "A sample listening test"}
    )
    assert resp.status_code == 201
    test_id = resp.json()["id"]

    resp = await client.get(f"/listening/tests/{test_id}")
    assert resp.status_code == 200

    resp = await client.get("/listening/tests")
    assert resp.status_code == 200
    assert any(t["id"] == test_id for t in resp.json())

    resp = await client.delete(f"/listening/tests/{test_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/listening/tests/{test_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_part_section_question_flow(client: AsyncClient):
    parent = (await client.post(
        "/listening/tests",
        json={"title": "Parent Test", "description": "For parts"}
    )).json()
    parent_id = parent["id"]

    part = (await client.post(
        "/listening/parts",
        json={"listening_id": parent_id, "part_number": 1, "audio_file": "http://example.com/audio.mp3"}
    )).json()
    part_id = part["id"]

    resp = await client.get(f"/listening/parts/{part_id}")
    assert resp.status_code == 200

    section = (await client.post(
        "/listening/sections",
        json={
            "part_id": part_id,
            "section_number": 1,
            "start_index": 0,
            "end_index": 10,
            "question_type": "choice",
            "question_text": None,
            "options": ["A", "B", "C"],
        }
    )).json()
    section_id = section["id"]

    resp = await client.get(f"/listening/sections/{section_id}")
    assert resp.status_code == 200

    question = (await client.post(
        "/listening/questions",
        json={"section_id": section_id, "index": 1, "options": ["A", "B", "C"], "correct_answer": "A"}
    )).json()
    question_id = question["id"]

    resp = await client.get(f"/listening/questions/{question_id}")
    assert resp.status_code == 200

    resp = await client.get("/listening/questions")
    assert resp.status_code == 200
    assert any(q["id"] == question_id for q in resp.json())

    await client.delete(f"/listening/questions/{question_id}")
    await client.delete(f"/listening/sections/{section_id}")
    await client.delete(f"/listening/parts/{part_id}")
    await client.delete(f"/listening/tests/{parent_id}")


@pytest.mark.asyncio
async def test_user_session_flow(client: AsyncClient):
    test_obj = (await client.post(
        "/listening/tests",
        json={"title": "Session Test", "description": "For session"}
    )).json()
    test_id = test_obj["id"]

    part_id = (await client.post(
        "/listening/parts",
        json={"listening_id": test_id, "part_number": 1, "audio_file": "http://example.com/audio.mp3"}
    )).json()["id"]

    section_id = (await client.post(
        "/listening/sections",
        json={
            "part_id": part_id,
            "section_number": 1,
            "start_index": 0,
            "end_index": 10,
            "question_type": "choice",
            "question_text": None,
            "options": ["A", "B", "C"],
        }
    )).json()["id"]

    q1_id = (await client.post(
        "/listening/questions",
        json={"section_id": section_id, "index": 1, "options": ["A", "B"], "correct_answer": "A"}
    )).json()["id"]
    q2_id = (await client.post(
        "/listening/questions",
        json={"section_id": section_id, "index": 2, "options": ["X", "Y"], "correct_answer": "Y"}
    )).json()["id"]

    session_id = (await client.post("/listening/session")).json()["id"]

    resp = await client.get(f"/listening/session/{session_id}")
    assert resp.status_code == 200

    resp = await client.get(f"/listening/session/{session_id}/data")
    assert resp.status_code == 200

    answers_payload = {
        "test_id": test_id,
        "answers": {
            str(section_id): [
                {"question_id": q1_id, "answer": "A"},
                {"question_id": q2_id, "answer": "X"}
            ]
        }
    }
    resp = await client.post(f"/listening/session/{session_id}/submit", json=answers_payload)
    assert resp.status_code == 200

    resp = await client.post(f"/listening/session/{session_id}/cancel")
    assert resp.status_code in (400, 403)

    resp = await client.get(f"/listening/session/{session_id}/analyse")
    assert resp.status_code == 200
    analysis = resp.json()
    assert analysis["session_id"] == session_id

    await client.delete(f"/listening/questions/{q1_id}")
    await client.delete(f"/listening/questions/{q2_id}")
    await client.delete(f"/listening/sections/{section_id}")
    await client.delete(f"/listening/parts/{part_id}")
    await client.delete(f"/listening/tests/{test_id}")
