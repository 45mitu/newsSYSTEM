import pytest
from datetime import datetime
from src.models import RawArticle, ProcessedArticle

@pytest.fixture
def sample_raw_articles():
    now = datetime.utcnow()
    return [
        RawArticle(url="https://ai.com/1", title="Claude 3.7 released", summary="Anthropic releases Claude 3.7 with improved capabilities", source_name="Test AI", published_at=now, category="ai"),
        RawArticle(url="https://ai.com/2", title="GPT-5 announced by OpenAI", summary="OpenAI announces GPT-5 with reasoning improvements", source_name="Test AI", published_at=now, category="ai"),
        RawArticle(url="https://ai.com/3", title="Google DeepMind LLM paper", summary="New LLM research from Google DeepMind shows RAG improvements", source_name="Test AI", published_at=now, category="ai"),
        RawArticle(url="https://pc.com/1", title="AMD Ryzen 9950X benchmark", summary="Ryzen 9950X benchmark results show significant performance gains", source_name="Test PC", published_at=now, category="pc"),
        RawArticle(url="https://pc.com/2", title="RTX 5080 Ti specs leaked", summary="Leaked RTX 5080 Ti specs show 24GB GDDR7 with PCIe 5.0", source_name="Test PC", published_at=now, category="pc"),
        RawArticle(url="https://pc.com/3", title="DDR5-8000 price drop", summary="DDR5-8000 prices drop significantly, NVMe SSD prices also declining", source_name="Test PC", published_at=now, category="pc"),
    ]

@pytest.fixture
def sample_processed_articles():
    now = datetime.utcnow()
    return [
        ProcessedArticle(url="https://ai.com/1", title="Claude 3.7 released", ai_summary="Anthropicが最新モデルClaude 3.7をリリースしました。", source_name="Test AI", published_at=now, category="ai"),
        ProcessedArticle(url="https://pc.com/1", title="AMD Ryzen 9950X benchmark", ai_summary="Ryzen 9950Xのベンチマーク結果が公開されました。", source_name="Test PC", published_at=now, category="pc"),
    ]
