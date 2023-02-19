from dataclasses import dataclass
from typing import List

import dataclasses_json


@dataclass(frozen=True)
@dataclasses_json
class NeoSarisContestMetadata:
    duration: int
    frozenTimeDuration: int
    name: str
    type: str


@dataclass(frozen=True)
@dataclasses_json
class NeoSarisProblem:
    index: str


@dataclass(frozen=True)
@dataclasses_json
class NeoSarisContestant:
    id: int
    name: str


@dataclass(frozen=True)
@dataclasses_json
class NeoSarisVerdicts:
    accepted: List[str]
    wrongAnswerWithPenalty: List[str]
    wrongAnswerWithoutPenalty: List[str]


@dataclass(frozen=True)
@dataclasses_json
class NeoSarisSubmission:
    timeSubmitted: int
    contestantName: str
    problemIndex: str
    verdict: str


@dataclass(frozen=True)
@dataclasses_json
class NeoSarisContest:
    contestMetadata: NeoSarisContestMetadata
    problems: List[NeoSarisProblem]
    contestants: List[NeoSarisContestant]
    verdicts: NeoSarisVerdicts
    submissions: List[NeoSarisSubmission]
