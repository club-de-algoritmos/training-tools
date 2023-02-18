import math
from dataclasses import dataclass
from typing import List

import omegaup

import libomegaup.omegaup.api as api


@dataclass(frozen=True)
class Problem:
    name: str
    is_solved: bool
    submissions: int
    penalty: int


@dataclass(frozen=True)
class Contestant:
    username: str
    total_solved: int
    total_submissions: int
    total_penalty: int
    problems: List[Problem]


@dataclass(frozen=True)
class Contest:
    name: str
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
            if is_solved:
                last_submit_time = last_submit_time_per_problem[problem.alias]
                minutes = math.floor((last_submit_time - user_start).total_seconds() / 60)
                penalty = minutes + 20 * (submissions - 1)

            problems.append(Problem(name=problem.alias, is_solved=is_solved, submissions=submissions, penalty=penalty))

            total_solved += 1 if is_solved else 0
            total_submissions += submissions
            total_penalty += penalty

        contestants.append(Contestant(username=ranking.username,
                                      total_solved=total_solved,
                                      total_submissions=total_submissions,
                                      total_penalty=total_penalty,
                                      problems=problems,
                                      ))

    contestants.sort(key=lambda c: (-c.total_solved, c.total_penalty, c.username))

    return Contest(name=scoreboard.title, contestants=contestants)


def _generate_speed_contest_scoreboard(contest_alias: str) -> None:
    contest = _get_speed_contest(contest_alias)
    print('username,solved,runs')
    for contestant in contest.contestants:
        print(f'{contestant.username},{contestant.total_solved},{contestant.total_penalty}')


if __name__ == '__main__':
    _generate_speed_contest_scoreboard('velocidad-cas-2023-01')
