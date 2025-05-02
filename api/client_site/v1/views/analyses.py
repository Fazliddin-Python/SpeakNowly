from fastapi import APIRouter, HTTPException
from models.analyses import ListeningAnalyse, WritingAnalyse, SpeakingAnalyse, ReadingAnalyse, GrammarAnalyse
from api.client_site.v1.serializers.analyses import (
    ListeningAnalyseSerializer,
    WritingAnalyseSerializer,
    SpeakingAnalyseSerializer,
    ReadingAnalyseSerializer,
    GrammarAnalyseSerializer,
)

router = APIRouter()

@router.get("/listening/", response_model=list[ListeningAnalyseSerializer])
async def get_listening_analyses():
    analyses = await ListeningAnalyse.all()
    return analyses

@router.get("/writing/", response_model=list[WritingAnalyseSerializer])
async def get_writing_analyses():
    analyses = await WritingAnalyse.all()
    return analyses

@router.get("/speaking/", response_model=list[SpeakingAnalyseSerializer])
async def get_speaking_analyses():
    analyses = await SpeakingAnalyse.all()
    return analyses

@router.get("/reading/", response_model=list[ReadingAnalyseSerializer])
async def get_reading_analyses():
    analyses = await ReadingAnalyse.all()
    return analyses

@router.get("/grammar/", response_model=list[GrammarAnalyseSerializer])
async def get_grammar_analyses():
    analyses = await GrammarAnalyse.all()
    return analyses