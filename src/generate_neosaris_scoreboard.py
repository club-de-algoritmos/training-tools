import argparse
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict

from dataclasses_json import dataclass_json

import omegaup
from libomegaup.omegaup import api


@dataclass_json
@dataclass(frozen=True)
class NeoSarisContestMetadata:
    duration: int
    frozenTimeDuration: int
    name: str
    type: str


@dataclass_json
@dataclass(frozen=True)
class NeoSarisProblem:
    index: str


@dataclass_json
@dataclass(frozen=True)
class NeoSarisContestant:
    id: int
    name: str


@dataclass_json
@dataclass(frozen=True)
class NeoSarisVerdicts:
    accepted: List[str]
    wrongAnswerWithPenalty: List[str]
    wrongAnswerWithoutPenalty: List[str]


@dataclass_json
@dataclass(frozen=True)
class NeoSarisSubmission:
    timeSubmitted: int
    contestantName: str
    problemIndex: str
    verdict: str


@dataclass_json
@dataclass(frozen=True)
class NeoSarisContest:
    contestMetadata: NeoSarisContestMetadata
    problems: List[NeoSarisProblem]
    contestants: List[NeoSarisContestant]
    verdicts: NeoSarisVerdicts
    submissions: List[NeoSarisSubmission]


def _get_neosaris_scoreboard(contest_alias: str) -> NeoSarisContest:
    client = omegaup.get_omegaup_client()
    contests = api.Contest(client)
    details = contests.adminDetails(contest_alias=contest_alias)

    has_different_starts = details.window_length is not None
    if has_different_starts:
        contest_duration_min = details.window_length
    else:
        contest_duration_min = round((details.finish_time - details.start_time).total_seconds() / 60)

    scoreboard_freeze_perc = details.scoreboard
    scoreboard_freeze_min = round(contest_duration_min * scoreboard_freeze_perc / 100)

    contest_metadata = NeoSarisContestMetadata(
        name=details.title,
        duration=contest_duration_min,
        frozenTimeDuration=scoreboard_freeze_min,
        type='ICPC',
    )

    problems = [NeoSarisProblem(index=problem.letter) for problem in details.problems]

    users = contests.users(contest_alias=contest_alias)
    contestants = [
        NeoSarisContestant(id=index+1, name=user.username)
        for index, user in enumerate(users.users)
        if user.is_owner is None
    ]

    user_access_time: Dict[str, datetime] = {
        user.username: user.access_time
        for user in users.users
    }

    submissions = []
    all_verdicts = set()
    for problem in details.problems:
        for run in contests.runs(contest_alias=contest_alias, problem_alias=problem.alias, rowcount=100_000).runs:
            all_verdicts.add(run.verdict)
            if has_different_starts:
                contest_start = user_access_time[run.username]
            else:
                contest_start = details.start_time
            submission_time_min = int((run.time - contest_start).total_seconds() / 60)

            submissions.append(NeoSarisSubmission(
                timeSubmitted=submission_time_min,
                contestantName=run.username,
                problemIndex=problem.letter,
                verdict=run.verdict,
            ))

    wa_verdicts = all_verdicts.copy()
    wa_verdicts.discard('AC')
    wa_verdicts.discard('CE')
    verdicts = NeoSarisVerdicts(
        accepted=['AC'],
        wrongAnswerWithPenalty=list(sorted(wa_verdicts)),
        wrongAnswerWithoutPenalty=['CE'],
    )

    return NeoSarisContest(
        contestMetadata=contest_metadata,
        problems=problems,
        contestants=contestants,
        verdicts=verdicts,
        submissions=submissions,
    )


def _generate_neosaris_scoreboard(contest_alias: str, filename: str) -> None:
    contest = _get_neosaris_scoreboard(contest_alias)
    with open(filename, 'w') as f:
        f.write(contest.to_json(indent=2))


def _main() -> None:
    parser = argparse.ArgumentParser(
        prog='generate_neosaris_scoreboard',
        description='Generate the NeoSaris scoreboard to reveal frozen contests',
    )
    parser.add_argument('-c',
                        '--contest',
                        required=True,
                        help='Alias of the contest to work with (can be obtained from the URL)')
    parser.add_argument('-f',
                        '--filename',
                        required=True,
                        help='File location where the NeoSaris scoreboard will be written to')
    args = parser.parse_args()

    contest_alias = args.contest
    filename = args.filename
    _generate_neosaris_scoreboard(contest_alias, filename)


if __name__ == '__main__':
    _main()
