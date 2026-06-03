from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ContractContext:
    objeto: str
    tipo_contratacao: str
    area_demandante: str
    valor_estimado: float
    criticidade: str
    prazo: str
    modalidade: str
    contexto: str


@dataclass(frozen=True)
class RiskItem:
    id: str
    titulo: str
    tipo_contratacao: list[str]
    palavras_chave: list[str]
    causa: str
    consequencia: str
    probabilidade_padrao: str
    impacto_padrao: str
    acao_preventiva: str
    acao_contingencia: str
    responsavel_sugerido: str


@dataclass
class MatrixRow:
    id: str
    risco: str
    causa: str
    consequencia: str
    probabilidade: str
    impacto: str
    nivel: str
    acao_preventiva: str
    acao_contingencia: str
    responsavel: str
    justificativa: str = ""
    selecionado: bool = True
    tags: list[str] = field(default_factory=list)
