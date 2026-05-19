from __future__ import annotations

from krheritage.models.base import KrHeritageModel


class ResearchRecord(KrHeritageModel):
    idx: int
    raw: dict[str, object]


class HyanggyoSurvey(ResearchRecord):
    pass


class StoneHeritage(ResearchRecord):
    pass


class DancheongPigment(ResearchRecord):
    pass


class ArchaeologyJournal(ResearchRecord):
    pass

