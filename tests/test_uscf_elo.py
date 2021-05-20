import pytest
import numpy as np
from datetime import date
from chessratings import uscf_elo


'''
FIXTURES 
Player, Tournament and PlayerTournament instances used for testing purposes
'''


# returns an unrated test player
@pytest.fixture
def test_player_1():
    test_player = uscf_elo.Player(
        id='player_1', rating=None, nr_games_played=0, nr_wins=0, nr_losses=0)
    return test_player


# returns a test player with a rating of 1200 and 10 games played - all wins
@pytest.fixture
def test_player_2():
    test_player = uscf_elo.Player(
        id='player_2', rating=1200, nr_games_played=10, nr_wins=10, nr_losses=0)
    return test_player


# returns a test player with a rating of 1500 and 8 games played - 6 wins and 2 losses
@pytest.fixture
def test_player_3():
    test_player = uscf_elo.Player(
        id='player_3', rating=1500, nr_games_played=8, nr_wins=6, nr_losses=2)
    return test_player


# test experienced test player with rating of 2400 and 150 games played
@pytest.fixture
def test_player_4():
    test_player = uscf_elo.Player(
        id='player_4', rating=2400, nr_games_played=150, nr_wins=130, nr_losses=12)
    return test_player


# returns experienced test player with a rating of 2200 and 100 games played
@pytest.fixture
def test_player_5():
    test_player = uscf_elo.Player(
        id='player_5', rating=2200, nr_games_played=100, nr_wins=70, nr_losses=23)
    return test_player


# test tournament with 4 players of different levels, 6 total games
@pytest.fixture
def test_tournament_1(test_player_1, test_player_2, test_player_3, test_player_4):
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


# test tournament with 2 players (individual match) that is invalid
@pytest.fixture
def test_tournament_2(test_player_1, test_player_2):
    players = [test_player_1, test_player_2]
    tournament_results = [[('player_1', 'player_2'), 'player_1'],
                          [('player_1', 'player_2'), np.nan]
                          ]

    tournament = uscf_elo.Tournament(players, tournament_results)
    return tournament


# test tournament with 2 players (valid individual match)
@ pytest.fixture
def test_tournament_3(test_player_4, test_player_5):
    '''returns a test tournament that is an valid individual match'''

    players = [test_player_4, test_player_5]
    tournament_results = [[('player_4', 'player_5'), 'player_5'],
                          [('player_4', 'player_5'), 'player_4'],
                          ]

    tournament = uscf_elo.Tournament(players, tournament_results)
    return tournament


# test playertournament (player 1 participating in test tournament 1)
@ pytest.fixture
def test_player_tournament_1(test_player_1, test_tournament_1):
    '''returns a test tournament that is an valid individual match'''
    player_tournament = uscf_elo._PlayerTournament(
        test_player_1, test_tournament_1)
    return player_tournament


# test playertournament (player 4 participating in test tournament 1)
@ pytest.fixture
def test_player_tournament_2(test_player_4, test_tournament_1):
    '''returns a test tournament that is an valid individual match'''
    player_tournament = uscf_elo._PlayerTournament(
        test_player_4, test_tournament_1)
    return player_tournament


# test playertournament (player 2 participating in test tournament 1)
@ pytest.fixture
def test_player_tournament_3(test_player_2, test_tournament_1):
    '''returns a test tournament that is an valid individual match'''
    player_tournament = uscf_elo._PlayerTournament(
        test_player_2, test_tournament_1)
    return player_tournament


# test playertournament (player 4 participating in test tournament 3)
@ pytest.fixture
def test_player_tournament_4(test_player_4, test_tournament_3):
    '''returns a test tournament that is an valid individual match'''
    player_tournament = uscf_elo._PlayerTournament(
        test_player_4, test_tournament_3)
    return player_tournament


'''
TESTS
__________________________________________________________________________________________________

PLAYER TESTS - testing the functions of the Player class
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
TOURNAMENT TESTS - testing functions of the tournament class
'''


# test the function that determines whether a tournament is an individual match
def test_individual_match(test_tournament_1, test_tournament_3):
    tournament_1_match = test_tournament_1._verify_individual_match()
    tournament_3_match = test_tournament_3._verify_individual_match()
    assert tournament_1_match is False
    assert tournament_3_match is True


# test the function that determines whether a tournament is valid
def test_tournament_validity(test_tournament_1, test_tournament_2, test_tournament_3):
    tournament_1_validity = test_tournament_1._valid_tournament()
    tournament_2_validity = test_tournament_2._valid_tournament()
    tournament_3_validity = test_tournament_3._valid_tournament()

    assert tournament_1_validity is True
    assert tournament_2_validity is False
    assert tournament_3_validity is True


# test the function that computes estimated ratings for select players
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
PLAYERTOURNAMENT TESTS - testing functions of the PlayerTournament class
'''


# test whether player opponents are being retrieved correctly
def test_player_tournament_opponents(test_player_tournament_1, test_player_tournament_2):
    player_1_opponents = test_player_tournament_1._opponents
    player_4_opponents = test_player_tournament_2._opponents

    player_1_opponent_ids = [o.id for o in player_1_opponents]
    player_4_opponent_ids = [o.id for o in player_4_opponents]

    assert set(player_1_opponent_ids) == set(
        ['player_2', 'player_3', 'player_4'])
    assert set(player_4_opponent_ids) == set(
        ['player_1', 'player_2', 'player_3'])


# test whether the tournament score (sum of all match scores) is being calculated correctly
def test_compute_tournament_score(test_player_tournament_1, test_player_tournament_2):
    score_1 = test_player_tournament_1._tournament_score()
    score_2 = test_player_tournament_2._tournament_score()
    assert score_1 == 1.5
    assert score_2 == 2.5


# test whether aggregate tournament stats (games, wins, draws, losses) are being calculated correctly
def test_tournament_stats(test_player_tournament_1, test_player_tournament_2):
    nr_games_1, nr_wins_1, nr_draws_1, nr_losses_1 = test_player_tournament_1._tournament_stats()
    nr_games_2, nr_wins_2, nr_draws_2, nr_losses_2 = test_player_tournament_2._tournament_stats()
    assert (nr_games_1, nr_wins_1, nr_draws_1, nr_losses_1) == (3, 1, 1, 1)
    assert (nr_games_2, nr_wins_2, nr_draws_2, nr_losses_2) == (3, 2, 1, 0)


# test whether the adjusted initialized rating and adjusted score are being computed correctly
def test_compute_adjusted_initialized_rating_and_score(test_player_tournament_1, test_player_tournament_3):
    adjusted_initialized_rating_1, adjusted_score_1 = test_player_tournament_1._compute_adjusted_initialized_rating_and_score()
    adjusted_initialized_rating_2, adjusted_score_2 = test_player_tournament_3._compute_adjusted_initialized_rating_and_score()

    assert (adjusted_initialized_rating_1, adjusted_score_1) == (1600, 1.5)
    assert (adjusted_initialized_rating_2, adjusted_score_2) == (800, 10.5)


# test the provisional winning expectancy function for special ratings is worked as intended
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


# test the special rating objective function
@ pytest.mark.parametrize("special_rating_estimate, expected", [
    (1200, -0.875),
    (1550, 0),
    (1800, 0.375)
])
def test_special_rating_objective(test_player_tournament_1, special_rating_estimate, expected):
    objective_fn = test_player_tournament_1._special_rating_objective(
        special_rating_estimate)
    assert objective_fn == expected


# test function used to compute Sz
def test_compute_sz(test_player_tournament_1):
    Sz_1 = test_player_tournament_1._compute_Sz()
    assert set(Sz_1) == set([800, 1100, 1200, 1600, 1900, 2000, 2800])


# test the first step of the special rating computation function, in which the special rating is approximated
def test_special_rating_step_1(test_player_tournament_1, test_player_tournament_3):
    M_1 = test_player_tournament_1._special_rating_step_1_compute_M()
    M_2 = test_player_tournament_3._special_rating_step_1_compute_M()

    assert abs(M_1 - 1700) < 1
    assert abs(M_2 - 977) < 1


# test the second step of the function to calculate the special rating. these test values have been calibrated to go through all the iterative steps of the function.
@ pytest.mark.parametrize("M, f_M, expected_M, expected_f_M", [
    (1200, 0, 1200, 0),
    (1200, 0.5, 1169, -0.95),
    (1300, 0.5, 1264, -0.72)
])
def test_special_rating_step_2(test_player_tournament_1, M, f_M, expected_M, expected_f_M):
    Sz = test_player_tournament_1._compute_Sz()
    M, f_M = test_player_tournament_1._special_rating_step_2(M, f_M, Sz)
    assert abs(M - expected_M) < 1
    assert abs(f_M - expected_f_M) < 0.1


# test the third step of the function to calculate the special rating
@ pytest.mark.parametrize("M, f_M, expected_M, expected_f_M", [
    (1200, 0, 1200, 0),
    (1200, -0.5, 1550, 0),
    (1300, -1, 1567, 0.04)
])
def test_special_rating_step_3(test_player_tournament_1, M, f_M, expected_M, expected_f_M):
    Sz = test_player_tournament_1._compute_Sz()
    M, f_M = test_player_tournament_1._special_rating_step_3(M, f_M, Sz)
    assert abs(M - expected_M) < 1
    assert abs(f_M - expected_f_M) < 0.1


# test the fourth and final step of the function to calculate the special rating
@ pytest.mark.parametrize("M, f_M, expected_M", [
    (1200, 1, 1200),
    (1600, 0, 1600)
])
def test_special_rating_step_4(test_player_tournament_1, M, f_M, expected_M):
    Sz = test_player_tournament_1._compute_Sz()
    M = test_player_tournament_1._special_rating_step_4(f_M, M, Sz)
    assert abs(M - expected_M) < 1


# test the overall special rating computation function
def test_compute_special_rating(test_player_tournament_1, test_player_tournament_3):
    M_1 = test_player_tournament_1._compute_special_rating()
    M_2 = test_player_tournament_3._compute_special_rating()
    assert abs(M_1 - 1550) < 1
    assert abs(M_2 - 1350) < 1


# test the winning expectancy formula for standard ratings
@ pytest.mark.parametrize("player_rating, opponent_rating, expected", [
    (1200, 1200, 0.5),
    (1600, 1200, 0.91),
    (1200, 1600, 0.09)
])
def test_compute_standard_winning_expectancy(test_player_tournament_2, player_rating, opponent_rating, expected):
    swe = test_player_tournament_2._compute_standard_winning_expectancy(
        player_rating, opponent_rating)
    assert abs(swe - expected) < 0.01


# test the calculation of K for standard ratings
@ pytest.mark.parametrize("rating, effective_nr_games, nr_tournament_matches, expected", [
    (1000, 0, 6, 133.3),
    (1200, 50, 6, 13.8),
    (2300, 40, 6, 13.0),
    (2700, 40, 6, 4.34)
])
def test_compute_standard_rating_K(test_player_tournament_3, rating, effective_nr_games, nr_tournament_matches, expected):
    K = test_player_tournament_3._compute_standard_rating_K(
        rating, effective_nr_games, nr_tournament_matches)
    assert abs(K - expected) < 1


# test whether the overall calculation of the standard rating is working as intended
def test_compute_standard_rating(test_player_tournament_3, test_player_tournament_4):
    rating_1 = test_player_tournament_3._compute_standard_rating()
    rating_2 = test_player_tournament_4._compute_standard_rating()
    assert abs(rating_1 - 1200) < 1
    assert abs(rating_2 - 2396) < 1


# test whether the rating floor function is working as intended
def test_compute_rating_floor(test_player_tournament_1, test_player_tournament_2, test_player_tournament_3, test_player_tournament_4):
    floor_1 = test_player_tournament_1._compute_rating_floor()
    floor_2 = test_player_tournament_2._compute_rating_floor()
    floor_3 = test_player_tournament_3._compute_rating_floor()
    floor_4 = test_player_tournament_4._compute_rating_floor()

    assert abs(floor_1 - 107) < 1
    assert abs(floor_2 - 2200) < 1
    assert abs(floor_3 - 143) < 1
    assert abs(floor_4 - 2200) < 1


# test whether ratings are being updated as intended (special and standard)
def test_update_rating(test_player_tournament_1, test_player_tournament_2, test_player_tournament_3, test_player_tournament_4):
    rating_1 = test_player_tournament_1.update_player_rating()
    rating_2 = test_player_tournament_2.update_player_rating()
    rating_3 = test_player_tournament_3.update_player_rating()
    rating_4 = test_player_tournament_4.update_player_rating()

    assert abs(rating_1 - 1550) < 1
    assert abs(rating_2 - 2396) < 1
    assert abs(rating_3 - 1350) < 1
    assert abs(rating_4 - 2396) < 1
