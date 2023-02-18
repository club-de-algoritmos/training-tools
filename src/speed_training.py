import argparse
import dataclasses
import math
from dataclasses import dataclass
from typing import List

import omegaup

import libomegaup.omegaup.api as api


@dataclass(frozen=True)
class Problem:
    name: str
    is_solved: bool
    solved_at: int
    submissions: int
    penalty: int


@dataclass(frozen=True)
class Contestant:
    username: str
    name: str
    rank: int
    total_solved: int
    total_submissions: int
    total_penalty: int
    problems: List[Problem]


@dataclass(frozen=True)
class Contest:
    name: str
    problem_count: int
    contestants: List[Contestant]


def _get_speed_contest(contest_alias: str) -> Contest:
    client = omegaup.get_omegaup_client()
    contests = api.Contest(client)

    scoreboard = contests.scoreboard(contest_alias=contest_alias)
    activity = contests.activityReport(contest_alias=contest_alias, length=100_000)

    contestants: List[Contestant] = []
    for ranking in scoreboard.ranking:
        user_events = [event for event in activity.events if event.username == ranking.username]
        user_start = min((event.time for event in user_events if event.event.name == 'open'))

        last_submit_time_per_problem = {}
        for event in user_events:
            if event.event.name != 'submit':
                continue
            problem = event.event.problem
            last_time = last_submit_time_per_problem.get(problem)
            if last_time is None or last_time < event.time:
                last_submit_time_per_problem[problem] = event.time

        problems: List[Problem] = []
        total_solved = 0
        total_submissions = 0
        total_penalty = 0
        for problem in ranking.problems:
            is_solved = problem.points == 1
            submissions = problem.runs
            penalty = 0
            solved_at = 0
            if is_solved:
                last_submit_time = last_submit_time_per_problem[problem.alias]
                solved_at = math.floor((last_submit_time - user_start).total_seconds() / 60)
                penalty = solved_at + 20 * (submissions - 1)

            problems.append(Problem(name=problem.alias,
                                    is_solved=is_solved,
                                    solved_at=solved_at,
                                    submissions=submissions,
                                    penalty=penalty,
                                    ))

            total_solved += 1 if is_solved else 0
            total_submissions += submissions
            total_penalty += penalty

        contestants.append(Contestant(username=ranking.username,
                                      name=ranking.name,
                                      rank=0,
                                      total_solved=total_solved,
                                      total_submissions=total_submissions,
                                      total_penalty=total_penalty,
                                      problems=problems,
                                      ))

    # Sort and set actual ranks
    contestants.sort(key=lambda c: (-c.total_solved, c.total_penalty, c.username))
    for i in range(len(contestants)):
        rank = i + 1
        contestant = contestants[i]
        if i > 0:
            prev_contestant = contestants[i - 1]
            if (contestant.total_solved == prev_contestant.total_solved
                    and contestant.total_penalty == prev_contestant.total_penalty):
                rank = prev_contestant.rank

        contestants[i] = dataclasses.replace(contestant, rank=rank)

    return Contest(name=scoreboard.title, problem_count=len(scoreboard.problems), contestants=contestants)


def _generate_speed_contest_scoreboard(contest_alias: str) -> None:
    contest = _get_speed_contest(contest_alias)

    problem_ids = [chr(ord('A') + i) for i in range(0, contest.problem_count)]
    print(f'#,Username,Name,{",".join(problem_ids)},Total')
    for contestant in contest.contestants:
        row1: List[str] = [str(contestant.rank), contestant.username, contestant.name]
        row2: List[str] = ['', '', '']
        for problem in contestant.problems:
            if problem.submissions:
                row1.append(str(1 if problem.is_solved else 0))
                row2.append(f'{problem.solved_at} ({problem.submissions})')
            else:
                row1.append('')
                row2.append('')

        row1.append(str(contestant.total_solved))
        row2.append(f'{contestant.total_penalty} ({contestant.total_submissions})')

        print(','.join(row1))
        print(','.join(row2))


def _main() -> None:
    parser = argparse.ArgumentParser(
        prog='speed_training',
        description='Generate the scoreboard for contests that had different starts',
    )
    parser.add_argument('-c',
                        '--contest',
                        required=True,
                        help='Alias of the contest to work with (can be obtained from the URL)')
    args = parser.parse_args()

    contest_alias = args.contest
    _generate_speed_contest_scoreboard(contest_alias)


if __name__ == '__main__':
    _main()
