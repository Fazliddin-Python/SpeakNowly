from fastapi import APIRouter, HTTPException
from models.tests.grammar import Grammar, GrammarPart1, GrammarPart2, GrammarPart3
from api.client_site.v1.serializers.tests.grammar import (
    GrammarSerializer,
    GrammarPart1Serializer,
    GrammarPart2Serializer,
    GrammarPart3Serializer,
)

router = APIRouter()

# Grammar endpoints
@router.get("/", response_model=list[GrammarSerializer])
async def get_grammars():
    grammars = await Grammar.all()
    return grammars


@router.get("/{grammar_id}/", response_model=GrammarSerializer)
async def get_grammar(grammar_id: int):
    grammar = await Grammar.get_or_none(id=grammar_id)
    if not grammar:
        raise HTTPException(status_code=404, detail="Grammar test not found")
    return grammar


@router.post("/", response_model=GrammarSerializer)
async def create_grammar(data: GrammarSerializer):
    grammar = await Grammar.create(**data.dict())
    return grammar


@router.delete("/{grammar_id}/")
async def delete_grammar(grammar_id: int):
    grammar = await Grammar.get_or_none(id=grammar_id)
    if not grammar:
        raise HTTPException(status_code=404, detail="Grammar test not found")
    await grammar.delete()
    return {"message": "Grammar test deleted successfully"}


# GrammarPart1 endpoints
@router.get("/part1/", response_model=list[GrammarPart1Serializer])
async def get_grammar_part1():
    parts = await GrammarPart1.all()
    return parts


@router.post("/part1/", response_model=GrammarPart1Serializer)
async def create_grammar_part1(data: GrammarPart1Serializer):
    part = await GrammarPart1.create(**data.dict())
    return part


# GrammarPart2 endpoints
@router.get("/part2/", response_model=list[GrammarPart2Serializer])
async def get_grammar_part2():
    parts = await GrammarPart2.all()
    return parts


@router.post("/part2/", response_model=GrammarPart2Serializer)
async def create_grammar_part2(data: GrammarPart2Serializer):
    part = await GrammarPart2.create(**data.dict())
    return part


# GrammarPart3 endpoints
@router.get("/part3/", response_model=list[GrammarPart3Serializer])
async def get_grammar_part3():
    parts = await GrammarPart3.all()
    return parts


@router.post("/part3/", response_model=GrammarPart3Serializer)
async def create_grammar_part3(data: GrammarPart3Serializer):
    part = await GrammarPart3.create(**data.dict())
    return part