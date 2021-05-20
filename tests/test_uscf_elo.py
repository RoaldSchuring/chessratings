import pytest
import numpy as np
from datetime import date
from chessratings import uscf_elo


@pytest.fixture
def test_player_1():
    '''returns an unrated test player'''
    test_player = uscf_elo.Player(
        id='player_1', rating=None, nr_games_played=0, nr_wins=0, nr_losses=0)
    return test_player


@pytest.fixture
def test_player_2():
    '''returns a test player with a rating of 1200 and 10 games played  - all wins'''
    test_player = uscf_elo.Player(
        id='player_2', rating=1200, nr_games_played=10, nr_wins=10, nr_losses=0)
    return test_player


@pytest.fixture
def test_player_3():
    '''returns a test player with a rating of 1500 and 8 games played - 6 wins and 2 losses '''
    test_player = uscf_elo.Player(
        id='player_3', rating=1500, nr_games_played=8, nr_wins=6, nr_losses=2)
    return test_player


@pytest.fixture
def test_player_4():
    '''returns a test player with a rating of 2400 and 150 games played'''
    test_player = uscf_elo.Player(
        id='player_4', rating=2400, nr_games_played=150, nr_wins=130, nr_losses=12)
    return test_player


@pytest.fixture
def test_player_5():
    '''returns a test player with a rating of 2200 and 100 games played'''
    test_player = uscf_elo.Player(
        id='player_5', rating=2200, nr_games_played=100, nr_wins=70, nr_losses=23)
    return test_player


@pytest.fixture
def test_tournament_1(test_player_1, test_player_2, test_player_3, test_player_4):
    '''returns a test tournament with 6 games between 4 players'''

    players = [test_player_1, test_player_2, test_player_3, test_player_4]
    tournament_results = [[('player_1', 'player_2'), 'player_1'],
                          [('player_1', 'player_3'), np.nan],
                          [('player_2', 'player_3'), 'player_3'],
                          [('player_4', 'player_2'), np.nan],
                          [('player_4', 'player_3'), 'player_4'],
                          [('player_4', 'player_1'), 'player_4']
                          ]

    tournament = uscf_elo.Tournament(players, tournament_results)
    return tournament


@pytest.fixture
def test_tournament_2(test_player_1, test_player_2):
    '''returns a test tournament that is an invalid individual match'''

    players = [test_player_1, test_player_2]
    tournament_results = [[('player_1', 'player_2'), 'player_1'],
                          [('player_1', 'player_2'), np.nan]
                          ]

    tournament = uscf_elo.Tournament(players, tournament_results)
    return tournament


@ pytest.fixture
def test_tournament_3(test_player_4, test_player_5):
    '''returns a test tournament that is an valid individual match'''

    players = [test_player_4, test_player_5]
    tournament_results = [[('player_4', 'player_5'), 'player_5'],
                          [('player_4', 'player_5'), 'player_4'],
                          ]

    tournament = uscf_elo.Tournament(players, tournament_results)
    return tournament


@ pytest.fixture
def test_player_tournament_1(test_player_1, test_tournament_1):
    '''returns a test tournament that is an valid individual match'''
    player_tournament = uscf_elo._PlayerTournament(
        test_player_1, test_tournament_1)
    return player_tournament


@ pytest.fixture
def test_player_tournament_2(test_player_4, test_tournament_1):
    '''returns a test tournament that is an valid individual match'''
    player_tournament = uscf_elo._PlayerTournament(
        test_player_4, test_tournament_1)
    return player_tournament


@ pytest.fixture
def test_player_tournament_3(test_player_2, test_tournament_1):
    '''returns a test tournament that is an valid individual match'''
    player_tournament = uscf_elo._PlayerTournament(
        test_player_2, test_tournament_1)
    return player_tournament


'''
__________________________________________________________________________________________________

'''


# test whether the tag for an established player is being assigned correctly
def test_determine_established_rating(test_player_1, test_player_5):
    established_rating_test_player_1 = test_player_1.determine_established_rating()
    established_rating_test_player_5 = test_player_5.determine_established_rating()
    assert established_rating_test_player_1 is False
    assert established_rating_test_player_5 is True


# test the function that returns a rating based on age, covering all three possibilities
@ pytest.mark.parametrize("birth_year, current_year, expected", [
    (1990, 2021, 1300),
    (2001, 2021, 1000),
    (2020, 2021, 100)
])
def test_age_based_rating(test_player_1, birth_year, current_year, expected):
    test_player_1.birth_date = date(birth_year, 1, 1)
    test_player_1.current_date = date(current_year, 1, 1)
    age_based_rating = test_player_1._compute_age_based_rating()
    assert age_based_rating == expected


# test the rating initialization function for a new player (for whom rating will be initialized based on age)
def test_initialize_rating(test_player_1, test_player_2, test_player_3, test_player_4):
    initialized_rating_test_player_1 = test_player_1.initialize_rating()
    initialized_rating_test_player_2 = test_player_2.initialize_rating()
    initialized_rating_test_player_3 = test_player_3.initialize_rating()
    initialized_rating_test_player_4 = test_player_4.initialize_rating()
    assert initialized_rating_test_player_1 == 1300
    assert initialized_rating_test_player_2 == 1200
    assert initialized_rating_test_player_3 == 1500
    assert initialized_rating_test_player_4 == 2400


# test the effective number of games calculation for a range of different scenarios
def test_compute_effective_nr_games(test_player_1, test_player_2, test_player_4):
    effective_nr_games_test_player_1 = int(
        test_player_1.compute_effective_nr_games())
    effective_nr_games_test_player_2 = int(
        test_player_2.compute_effective_nr_games())
    effective_nr_games_test_player_4 = int(
        test_player_4.compute_effective_nr_games())

    assert effective_nr_games_test_player_1 == 0
    assert effective_nr_games_test_player_2 == 10
    assert effective_nr_games_test_player_4 == 50


# test the categorization function tht assigns a rating type to each player
def test_rating_type(test_player_1, test_player_2, test_player_4):

    rating_type_test_player_1 = test_player_1.compute_rating_type()
    rating_type_test_player_2 = test_player_2.compute_rating_type()
    rating_type_test_player_4 = test_player_4.compute_rating_type()

    assert rating_type_test_player_1 == 'special-new'
    assert rating_type_test_player_2 == 'special-only-wins'
    assert rating_type_test_player_4 == 'standard'


'''
TOURNAMENT TESTS
'''


def test_individual_match(test_tournament_1, test_tournament_3):
    tournament_1_match = test_tournament_1._verify_individual_match()
    tournament_3_match = test_tournament_3._verify_individual_match()
    assert tournament_1_match is False
    assert tournament_3_match is True


def test_tournament_validity(test_tournament_1, test_tournament_2, test_tournament_3):
    tournament_1_validity = test_tournament_1._valid_tournament()
    tournament_2_validity = test_tournament_2._valid_tournament()
    tournament_3_validity = test_tournament_3._valid_tournament()

    assert tournament_1_validity is True
    assert tournament_2_validity is False
    assert tournament_3_validity is True


def test_tournament_estimated_ratings(test_tournament_1, test_player_2, test_player_3, test_player_4):

    for p in test_tournament_1.players:
        if p.id == 'player_1':
            assert p.estimated_rating == 1600
        elif p.id == 'player_2':
            assert p.estimated_rating == test_player_2.estimated_rating
        elif p.id == 'player_3':
            assert p.estimated_rating == test_player_3.estimated_rating
        elif p.id == 'player_4':
            assert p.estimated_rating == test_player_4.estimated_rating
        else:
            continue


'''
PLAYER TOURNAMENT TESTS
'''


def test_player_tournament_opponents(test_player_tournament_1, test_player_tournament_2):
    player_1_opponents = test_player_tournament_1._opponents
    player_4_opponents = test_player_tournament_2._opponents

    player_1_opponent_ids = [o.id for o in player_1_opponents]
    player_4_opponent_ids = [o.id for o in player_4_opponents]

    assert set(player_1_opponent_ids) == set(
        ['player_2', 'player_3', 'player_4'])
    assert set(player_4_opponent_ids) == set(
        ['player_1', 'player_2', 'player_3'])


def test_compute_tournament_score(test_player_tournament_1, test_player_tournament_2):
    score_1 = test_player_tournament_1._tournament_score()
    score_2 = test_player_tournament_2._tournament_score()
    assert score_1 == 1.5
    assert score_2 == 2.5


def test_tournament_stats(test_player_tournament_1, test_player_tournament_2):
    nr_games_1, nr_wins_1, nr_draws_1, nr_losses_1 = test_player_tournament_1._tournament_stats()
    nr_games_2, nr_wins_2, nr_draws_2, nr_losses_2 = test_player_tournament_2._tournament_stats()
    assert (nr_games_1, nr_wins_1, nr_draws_1, nr_losses_1) == (3, 1, 1, 1)
    assert (nr_games_2, nr_wins_2, nr_draws_2, nr_losses_2) == (3, 2, 1, 0)


def test_compute_adjusted_initialized_rating_and_score(test_player_tournament_1, test_player_tournament_3):
    adjusted_initialized_rating_1, adjusted_score_1 = test_player_tournament_1._compute_adjusted_initialized_rating_and_score()
    adjusted_initialized_rating_2, adjusted_score_2 = test_player_tournament_3._compute_adjusted_initialized_rating_and_score()

    assert (adjusted_initialized_rating_1, adjusted_score_1) == (1600, 1.5)
    assert (adjusted_initialized_rating_2, adjusted_score_2) == (800, 10.5)


# test the function that returns a rating based on age, covering all three possibilities
@ pytest.mark.parametrize("player_rating, opponent_rating, expected", [
    (1000, 1500, 0),
    (1200, 1200, 0.5),
    (1200, 1300, 0.375),
    (1500, 1000, 1)
])
def test_compute_provisional_winning_expectancy(test_player_tournament_1, player_rating, opponent_rating, expected):
    pwe = test_player_tournament_1._compute_provisional_winning_expectancy(
        player_rating, opponent_rating)
    assert pwe == expected


'''




# test the PWE calculation that is part of the special rating procedure
@pytest.mark.parametrize("rating, opponent_rating, expected", [
    (1200, 1800, 0),
    (1200, 1200, 0.5),
    (1800, 1200, 1)
])
def test_compute_pwe(tournament_test_player, rating, opponent_rating, expected):
    pwe = tournament_test_player._compute_pwe(rating, opponent_rating)
    assert pwe == expected



# test the special rating objective function. for a special rating estimate of 1200 we should see an output of -0.375 for the objective fn
def test_special_rating_objective(tournament_test_player):
    special_rating_estimate = 1200
    objective_fn = tournament_test_player._special_rating_objective(
        special_rating_estimate)
    assert objective_fn == -0.375


# test function used to compute Sz
def test_compute_Sz(tournament_test_player):
    opponent_ratings = [r[1]
                        for r in tournament_test_player.tournament_results]
    Sz = tournament_test_player._compute_Sz(opponent_ratings)
    assert Sz == [1700, 1650, 1600, 1600, 1650,
                  1700, 900, 850, 800, 800, 850, 900]


# test the first step of the special rating computation function, in which the special rating is approximated
def test_special_rating_step_1_compute_M(test_player, tournament_test_player):
    tournament_games = len(tournament_test_player.tournament_results)
    opponent_ratings = [r[1]
                        for r in tournament_test_player.tournament_results]
    M = tournament_test_player._special_rating_step_1_compute_M(test_player.effective_nr_games, test_player.initialized_rating,
                                                                opponent_ratings, tournament_test_player.tournament_score, tournament_games)
    assert M == 1218.75


# test the second step of the function to calculate the special rating. these test values have been calibrated to go through all the iterative steps of the function.
@pytest.mark.parametrize("M, f_M, Sz, expected_M, expected_f_M", [
    (1230, -0.394999999999, [1199, 1201,
     1203, 1250, 1150, 1104], 1203, -0.3149999)
])
def test_special_rating_step_2(tournament_test_player, M, f_M, Sz, expected_M, expected_f_M):
    M, f_M = tournament_test_player._special_rating_step_2(M, f_M, Sz)
    assert abs(M - expected_M) < 0.1
    assert abs(f_M - expected_f_M) < 0.001


# test the third step of the function to calculate the special rating. these test values have been calibrated to go through all the iterative steps of the function.
@pytest.mark.parametrize("M, f_M, Sz, expected_M, expected_f_M", [
    (1218.75, -0.375, [1700, 1650, 1600, 1600, 1650,
     1700, 900, 850, 800, 800, 850, 900], 1236.6, 0.357),
    (1200, -0.355, [1199, 1201, 1203, 1250], 1218.75, 0)
])
def test_special_rating_step_3(tournament_test_player, M, f_M, Sz, expected_M, expected_f_M):
    M, f_M = tournament_test_player._special_rating_step_3(M, f_M, Sz)
    assert abs(M - expected_M) < 0.1
    assert abs(f_M - expected_f_M) < 0.001


# test the fourth step of the function to calculate the special rating. these test values have been calibrated to go through all the iterative steps of the function.
@pytest.mark.parametrize("f_M, M, opponent_ratings, expected_M", [
    (0, 1300, [1000, 1200, 1400], 1300),
    (1, 1800, [1800, 1750, 900, 1100], 1500)
])
def test_special_rating_step_4(tournament_test_player, f_M, M, opponent_ratings, expected_M):
    Sz = tournament_test_player._compute_Sz(opponent_ratings)
    M = tournament_test_player._special_rating_step_4(
        f_M, opponent_ratings, M, Sz)
    assert abs(M - expected_M) < 0.1


# test the overall computation of the special rating for the test tournament
def test_compute_special_rating(tournament_test_player):
    M = tournament_test_player._compute_special_rating()
    assert abs(M - 1218.75) < 0.1


# test the function used to compute K, a key component of the standard rating formula
@pytest.mark.parametrize("rating, time_control_minutes, time_control_increment_seconds, effective_nr_games, nr_games_tournament, expected", [
    (1200, 60, 0, 40, 10, 16),
    (2300, 60, 0, 40, 10, 12),
    (2600, 60, 0, 40, 10, 4)
])
def test_compute_standard_rating_K(tournament_test_player, rating, time_control_minutes, time_control_increment_seconds, effective_nr_games, nr_games_tournament, expected):
    K = tournament_test_player.compute_standard_rating_K(
        rating, time_control_minutes, time_control_increment_seconds, effective_nr_games, nr_games_tournament)
    assert K == expected


# test the winning expectancy formula used in the standard rating
def test_compute_standard_winning_expectancy(tournament_test_player):
    winning_expectancy = tournament_test_player.compute_standard_winning_expectancy(
        1500, 1400)
    assert abs(winning_expectancy - 0.64) < 0.01


# test the overall standard rating computation function for our test player
def test_compute_standard_rating(tournament_test_player):
    rating_new = tournament_test_player._compute_standard_rating()
    assert abs(rating_new - 1221) < 1


# test whether the rating floor is being calculated correctly for our test player
def test_compute_rating_floor(tournament_test_player):
    rating_floor = tournament_test_player.compute_rating_floor()
    assert rating_floor == 135


# test whether the rating is being updated correctly for our test and new players
def test_update_rating(tournament_test_player, tournament_new_player):
    updated_rating_test_player = tournament_test_player.update_rating()
    updated_rating_new_player = tournament_new_player.update_rating()
    assert abs(updated_rating_test_player - 1221) < 1
    assert abs(updated_rating_new_player - 841) < 1
'''
