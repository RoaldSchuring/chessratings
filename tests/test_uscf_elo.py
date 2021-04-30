import pytest
from datetime import date
from uscf_elo import Player


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
def tournament_test_player(test_player):
    '''returns a test tournament with 6 games against 3 players'''
    tournament_results = [('opponent_1', 1300, 1), ('opponent_2', 1250, 0.5), ('opponent_3',
                                                                               1200, 0), ('opponent_3', 1200, 0.5), ('opponent_2', 1250, 0), ('opponent_1', 1300, 1)]
    tournament = test_player.Tournament(test_player, tournament_results)
    return tournament


@pytest.fixture
def tournament_new_player(new_player):
    '''returns a test tournament with 6 games against 3 players'''
    tournament_results = [('opponent_1', 900, 0), ('opponent_2', 800, 0.5), ('opponent_3',
                                                                             1200, 0), ('opponent_3', 1200, 0.5), ('opponent_2', 600, 1), ('opponent_1', 750, 0.5)]
    tournament = new_player.Tournament(new_player, tournament_results)
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
    age_based_rating = test_player._compute_age_based_rating()
    assert age_based_rating == expected


# test the rating initialization function for a new player (for whom rating will be initialized based on age)
def test_initialize_rating(new_player, test_player):
    initialized_rating_new_player = new_player.initialize_rating()
    initialized_rating_test_player = test_player.initialize_rating()
    assert initialized_rating_new_player == 1300
    assert initialized_rating_test_player == 1200

# test whether the tag for an established player is being assigned correctly


def test_determine_established_rating(new_player, test_player):
    established_rating_new_player = new_player.determine_established_rating()
    established_rating_test_player = test_player.determine_established_rating()
    assert established_rating_new_player is False
    assert established_rating_test_player is False


# test the effective number of games calculation for a range of different scenarios
@pytest.mark.parametrize("rating, games_played, expected", [
    (900, 0, 0),
    (1200, 10, 10),
    (1300, 20, 14),
    (2400, 40, 40),
    (2400, 60, 50)
])
def test_compute_effective_nr_games(test_player, rating, games_played, expected):
    test_player.rating = rating
    test_player.nr_games_played = games_played
    test_player.initialized_rating = test_player.initialize_rating()
    effective_nr_games = test_player.compute_effective_nr_games()
    effective_nr_games_truncated = int(effective_nr_games)
    assert effective_nr_games_truncated == expected


# test the categorization function tht assigns a rating type to each player
@pytest.mark.parametrize("games_played, wins, losses, expected", [
    (6, 0, 5, 'special-new'),
    (9, 9, 0, 'special-only-wins'),
    (9, 0, 9, 'special-only-losses'),
    (10, 7, 1, 'standard')
])
def test_rating_type(test_player, games_played, wins, losses, expected):
    test_player.nr_games_played = games_played
    test_player.nr_wins = wins
    test_player.nr_losses = losses
    rating_type = test_player.compute_rating_type()
    assert rating_type == expected


# test whether the total tournament score is being calculated correctly in the test tournament we created
def tournament_test_player_score(tournament_test_player, tournament_new_player):
    assert tournament_test_player.tournament_score == 3
    assert tournament_new_player.tournament_score == 2.5


# test the PWE calculation that is part of the special rating procedure
@pytest.mark.parametrize("rating, opponent_rating, expected", [
    (1200, 1800, 0),
    (1200, 1200, 0.5),
    (1800, 1200, 1)
])
def test_compute_pwe(tournament_test_player, rating, opponent_rating, expected):
    pwe = tournament_test_player._compute_pwe(rating, opponent_rating)
    assert pwe == expected


# test the initial rating and score calculation for the tournament
@pytest.mark.parametrize("rating_type, expected_initialized_rating, expected_score", [
    ('special-new', 1200, 8),
    ('special-only-wins', 800, 13),
    ('special-only-losses', 1600, 3),
    ('standard', 1200, 8)
])
def test_adjusted_initialized_rating_and_score(test_player, tournament_test_player, rating_type, expected_initialized_rating, expected_score):
    test_player.rating_type = rating_type
    tournament_test_player.player = test_player
    adjusted_initialized_rating, adjusted_score = tournament_test_player._compute_adjusted_initialized_rating_and_score()
    assert adjusted_initialized_rating == expected_initialized_rating
    assert adjusted_score == expected_score


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
