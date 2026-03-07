"""
Modelos para o AI Search Engine
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base


class AgentSpecialty(str, Enum):
    """Especialidades dos agentes de busca"""
    CRAWLER = "crawler"          # Rastrea paginas
    INDEXER = "indexer"          # Indexa conteudo
    RANKER = "ranker"            # Rankeia resultados
    ANALYZER = "analyzer"        # Analisa qualidade
    SUMMARIZER = "summarizer"    # Resume conteudo
    MODERATOR = "moderator"      # Modera conteudo
    OPTIMIZER = "optimizer"      # Otimiza buscas


class TaskStatus(str, Enum):
    """Status de tarefas"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SearchAgent(Base):
    """Agentes de IA que gerenciam o mecanismo de busca"""
    __tablename__ = "search_agents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)  # llama, gemma, phi, etc
    specialty = Column(SQLEnum(AgentSpecialty), nullable=False)
    description = Column(Text, nullable=True)
    avatar = Column(String(10), default="")

    # Metricas de performance
    tasks_completed = Column(Integer, default=0)
    pages_processed = Column(Integer, default=0)
    accuracy_score = Column(Float, default=0.0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SearchAgent {self.name} ({self.specialty.value})>"


class WebPage(Base):
    """Paginas indexadas"""
    __tablename__ = "web_pages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String(2000), nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # Conteudo processado
    keywords = Column(Text, nullable=True)  # Keywords extraidas

    # Metricas de qualidade
    quality_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    freshness_score = Column(Float, default=0.0)

    # Quem processou
    indexed_by = Column(String(36), ForeignKey("search_agents.id"), nullable=True)
    analyzed_by = Column(String(36), ForeignKey("search_agents.id"), nullable=True)

    indexed_at = Column(DateTime, default=datetime.utcnow)
    last_crawled = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WebPage {self.url[:50]}>"


class SearchQuery(Base):
    """Queries de busca realizadas"""
    __tablename__ = "search_queries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query = Column(String(500), nullable=False, index=True)
    processed_query = Column(String(500), nullable=True)  # Query otimizada pela IA

    # Quem processou
    processed_by = Column(String(36), ForeignKey("search_agents.id"), nullable=True)

    results_count = Column(Integer, default=0)
    search_time_ms = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SearchQuery '{self.query[:30]}'>"


class SearchResult(Base):
    """Resultados de busca"""
    __tablename__ = "search_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String(36), ForeignKey("search_queries.id"), nullable=False)
    page_id = Column(String(36), ForeignKey("web_pages.id"), nullable=False)

    position = Column(Integer, nullable=False)  # Posicao no ranking
    score = Column(Float, default=0.0)  # Score de relevancia
    snippet = Column(Text, nullable=True)  # Trecho exibido

    # Feedback
    clicked = Column(Boolean, default=False)
    time_on_page = Column(Integer, default=0)  # Segundos

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SearchResult #{self.position} for query {self.query_id[:8]}>"


class IndexTask(Base):
    """Tarefas de indexacao"""
    __tablename__ = "index_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_type = Column(String(50), nullable=False)  # crawl, index, analyze, rank
    url = Column(String(2000), nullable=True)

    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(Integer, default=5)  # 1-10

    assigned_to = Column(String(36), ForeignKey("search_agents.id"), nullable=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<IndexTask {self.task_type} - {self.status.value}>"
