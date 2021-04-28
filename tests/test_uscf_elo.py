import pytest
from datetime import date
from uscf_elo import Player

test_player_rating = 1200


@pytest.fixture
def test_player():
    '''returns a test player with a rating of 1200 and 10 games played  - 8 wins, 1 loss (and thus 1 draw)'''
    test_player = Player(rating=1200, nr_games_played=10,
                         nr_wins=8, nr_losses=1)
    return test_player


@pytest.fixture
def new_player():
    '''returns a test player with no existing track record'''
    new_player = Player(rating=None, nr_games_played=0, nr_wins=0, nr_losses=0)
    return new_player


@pytest.fixture
def test_tournament():
    '''returns a test tournament with 6 games against 3 players'''
    test_player = Player(rating=1200, nr_games_played=10,
                         nr_wins=8, nr_losses=1)
    tournament_results = [('opponent_1', 1300, 1), ('opponent_2', 1250, 0.5), ('opponent_3',
                                                                               1200, 0), ('opponent_3', 1200, 0.5), ('opponent_2', 1250, 0), ('opponent_1', 1300, 1)]
    tournament = test_player.Tournament(test_player, tournament_results)
    return tournament


# test the function that returns a rating based on age, covering all three possibilities
@pytest.mark.parametrize("birth_year, tournament_year, expected", [
    (1990, 2021, 1300),
    (2001, 2021, 1000),
    (2020, 2021, 100)
])
def test_age_based_rating(test_player, birth_year, tournament_year, expected):
    test_player.birth_date = date(birth_year, 1, 1)
    test_player.tournament_end_date = date(tournament_year, 1, 1)
    age_based_rating = test_player.compute_age_based_rating()
    assert age_based_rating == expected


# test the rating initialization function for a new player (for whom rating will be initialized based on age)
def test_initialize_rating(new_player):
    initialized_rating = new_player.initialize_rating()
    assert initialized_rating == 1300


# test the effective number of games calculation for a range of different scenarios
@pytest.mark.parametrize("rating, games_played, expected", [
    (900, 0, 0),
    (1300, 10, 10),
    (1300, 20, 14),
    (2400, 40, 40),
    (2400, 60, 50)
])
def test_compute_effective_nr_games(test_player, rating, games_played, expected):
    test_player.rating = rating
    test_player.nr_games_played = games_played
    test_player.initial_rating = test_player.initialize_rating()
    effective_nr_games = test_player.compute_effective_nr_games()
    effective_nr_games_truncated = int(effective_nr_games)
    assert effective_nr_games_truncated == expected
