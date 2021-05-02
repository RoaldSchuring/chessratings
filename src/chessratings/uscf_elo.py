import numpy as np
from datetime import date
from collections import Counter

'''
This package is an implementation of the US Chess Federation (USCF) rating system for Regular, Over-The-Board (OTB) events. Details can be found here: http://www.glicko.net/ratings/rating.system.pdf

When initializing ratings for unrated players, we use the recommended age-based initialization logic. If no age is provided, we assume that a player is an adult above the age of 26.

This package only implements partial logic for rating floors, disregarding rating floor logic for players with an original Life Master (OLM) title or the effect of large cash prizes.

At this time, this package does not allow for updating USCF ratings based on results from foreign FIDE events.
'''

epsilon_special_rating = 10**-7
absolute_rating_floor = 100
B = 14


class Player:

    def __init__(self, id, rating, nr_games_played, nr_wins, nr_losses, birth_date=date(1990, 1, 1), current_date=date(2021, 1, 1), Nr=0):
        self.id = id
        self.nr_games_played = nr_games_played
        self.nr_wins = nr_wins
        self.nr_draws = nr_games_played - nr_wins - nr_losses
        self.nr_losses = nr_losses
        self.rating = rating
        self.birth_date = birth_date
        self.current_date = current_date
        # Nr is the number of events (tournaments) in which a player completed three rated games
        self.Nr = Nr
        self.initialized_rating = self.initialize_rating()
        self.established_rating = self.determine_established_rating()
        self.effective_nr_games = self.compute_effective_nr_games()
        self.rating_type = self.compute_rating_type()

    # players with > 25 games are deemed to have an 'established' rating

    def determine_established_rating(self):
        if self.nr_games_played > 25:
            established_rating = True
        else:
            established_rating = False
        return established_rating

    # age-based rating initialization for players that are unrated
    def _compute_age_based_rating(self):
        age = (self.current_date - self.birth_date).days/365.25
        if age < 2:
            rating = 100
        elif 2 <= age <= 26:
            rating = 50*age
        else:
            rating = 1300
        return rating

    # initialize the rating - based on age for unrated players, and based on the actual rating for rated players
    def initialize_rating(self):
        if self.rating is None:
            initialized_rating = self._compute_age_based_rating()
        else:
            initialized_rating = self.rating
        return initialized_rating

    # computation of a quantity called the effective number of games, used to convey the approximate reliability of a rating on the scale of a game count
    def compute_effective_nr_games(self):
        if self.initialized_rating <= 2355:
            n = 50/np.sqrt(0.662 + 0.00000739*(2569 -
                           self.initialized_rating)**2)
        else:
            n = 50

        effective_nr_games = min(n, self.nr_games_played)
        return effective_nr_games

    # categorization of players to determine whether the special or standard rating algorithm should be used
    def compute_rating_type(self):
        if self.nr_games_played <= 8:
            rating_type = 'special-new'
        elif self.nr_wins == self.nr_games_played:
            rating_type = 'special-only-wins'
        elif self.nr_losses == self.nr_games_played:
            rating_type = 'special-only-losses'
        else:
            rating_type = 'standard'
        return rating_type


class Tournament:

    # Note: tournament_results needs to be in a specific format:
    # [ [ ( player A ID, player B ID ), winner ID ], [ ( player B ID , player C ID ), winner ID ], ... ]
    # winner is the ID of the player who won. If a draw, the value is null.

    def __init__(self, players, tournament_results, tournament_date=date.today(), time_control_minutes=60, time_control_increment_seconds=0):

        self.nr_games_tournament = len(tournament_results)
        self.tournament_results = tournament_results
        self.tournament_date = tournament_date
        self.time_control_minutes = time_control_minutes
        self.time_control_increment_seconds = time_control_increment_seconds
        self.valid_tournament = self._valid_tournament()
        self.individual_match = _individual_match(self.players)
        if players is not None:
            self.players = list(players)
        else:
            self.players = []
        self.nr_players = len(self.players)

    def __iter___(self):
        return iter(self.players)

    # only tournaments that satisfy certain criteria are valid
    def _valid_tournament(self):
        if len(self.players) <= 1:
            return False
        elif self.individual_match:
            player_1 = self.players[0]
            player_2 = self.players[1]
            if player_1.established is False or player_2.established is False or abs(player_1.initialized_rating - player_2.initialized_rating) <= 400:
                return False
            else:
                return True
        else:
            return True

    def _compute_pwe(self, player_rating, opponent_rating):
        if player_rating <= opponent_rating - 400:
            pwe = 0
        elif opponent_rating - 400 < player_rating < opponent_rating + 400:
            pwe = 0.5 + (player_rating - opponent_rating)/800
        else:
            pwe = 1

        return pwe

    # an adjusted initialized rating and adjusted score are used as variables to calculate the special rating

    def _compute_adjusted_initialized_rating_and_score(self, player, tournament_score):

        # players with <= 8 games, or players that have had only wins/losses in all previous rated games, get a special rating
        if player.rating_type == 'special-only-wins':
            adjusted_initialized_rating = player.initialized_rating - 400
            adjusted_score = tournament_score + player.effective_nr_games
        elif player.rating_type == 'special-only-losses':
            adjusted_initialized_rating = player.initialized_rating + 400
            adjusted_score = tournament_score
        else:
            adjusted_initialized_rating = player.initialized_rating
            adjusted_score = tournament_score + player.effective_nr_games/2

        return adjusted_initialized_rating, adjusted_score

    # an objective function for the special rating. The goal is to determine the value of the special rating estimate (R) such that the value of this objecive is equal to 0 within reasonable tolerance

    def _special_rating_objective(self, special_rating_estimate, tournament_results, effective_nr_games, adjusted_initialized_rating, adjusted_score):

        sum_pwe = sum([self._compute_pwe(special_rating_estimate, t[1])
                       for t in tournament_results])

        objective_fn = effective_nr_games * \
            self._compute_pwe(special_rating_estimate, adjusted_initialized_rating) + \
            sum_pwe - adjusted_score

        return objective_fn

    # Sz is used in the iterative procedure to find the solution for the special rating objective function

    def _compute_Sz(self, opponent_ratings):
        Sz = [o + 400 for o in opponent_ratings] + \
            [o - 400 for o in opponent_ratings]
        return Sz

    # the first step of the iterative algorithm - provides the first estimate of the special rating

    def _special_rating_step_1_compute_M(self, effective_nr_games, initialized_rating, opponent_ratings, tournament_score, tournament_games):
        M = (effective_nr_games*initialized_rating + sum(opponent_ratings) + 400 *
             (2*tournament_score - tournament_games))/(effective_nr_games + tournament_games)
        return M

    # the second step of the iterative process to find the special rating

    def _special_rating_step_2(self, M, f_M, Sz):
        step_2_satisfied = False
        while step_2_satisfied is False:

            # Let za be the largest value in Sz for which M > za.
            za = max([z for z in Sz if z < M])
            f_za = self._special_rating_objective(za)

            if abs(f_M - f_za) < self.epsilon_special_rating:
                M = za
                f_M = f_za
                print('if 1,', M, f_M)
                continue
            else:
                M_star = M - f_M * ((M - za) / (f_M - f_za))
                print('M_star', M_star)
                if M_star < za:
                    M = za
                    f_M = f_za
                    print('step 2', M, f_M)
                    continue
                elif za <= M_star < M:
                    M = M_star
                    f_M = self._special_rating_objective(M_star)
                    print('step 3', M, f_M)
                    continue
                else:
                    step_2_satisfied = True
                    print('final', M, f_M)
                    break
        return M, f_M

    # the third step of the iterative process to find the special rating

    def _special_rating_step_3(M, f_M, Sz):
        step_3_satisfied = False
        while step_3_satisfied is False:

            zb = min([z for z in Sz if z > M])
            f_zb = _special_rating_objective(zb)
            if abs(f_zb - f_M) < epsilon_special_rating:
                M = zb
                f_M = f_zb
            else:
                M_star = M - f_M * ((zb - M) / (f_zb - f_M))
                if M_star > zb:
                    M = zb
                    f_M = _special_rating_objective(M)
                    continue
                elif M < M_star <= zb:
                    M = M_star
                    f_M = _special_rating_objective(M)
                    continue
                else:
                    step_3_satisfied = True
                    return M, f_M

    # the fourth step of the iterative process to find the special rating

    def _special_rating_step_4(f_M, opponent_ratings, M, Sz, adjusted_initialized_rating, initialized_rating):
        p = 0
        if abs(f_M) < epsilon_special_rating:
            p = len([o for o in opponent_ratings if abs(M - o) <= 400])
        if abs(M - adjusted_initialized_rating) <= 400:
            p += 1
        if p > 0:
            pass
        elif p == 0:
            za = max([s for s in Sz if s < M])
            zb = min([s for s in Sz if s > M])
            if za <= initialized_rating <= zb:
                M = initialized_rating
            elif initialized_rating < za:
                M = za
            elif initialized_rating > zb:
                M = zb
            else:
                raise Exception(
                    'M is outside the range of expected values.')

        M = min(2700, M)
        return M

    # the overall process to compute the special rating

    def _compute_special_rating(player, tournament_score, opponent_ratings, tournament_games):

        # tournament_games = len(tournament_results)
        # tournament_score = sum([t[2] for t in tournament_results])
        # opponent_ratings = [r[1] for r in tournament_results]

        adjusted_initialized_rating, adjusted_score = self._compute_adjusted_initialized_rating_and_score(
            player, tournament_score)

        M = _special_rating_step_1_compute_M(
            effective_nr_games, initialized_rating, opponent_ratings, tournament_score, tournament_games)

        f_M = _special_rating_objective(M)
        Sz = _compute_Sz(opponent_ratings)

        if f_M > epsilon_special_rating:
            M, f_M = _special_rating_step_2(M, f_M, Sz)

        if f_M < -epsilon_special_rating:
            M, f_M = _special_rating_step_3(M, f_M, Sz)

        if abs(f_M) < epsilon_special_rating:
            M = _special_rating_step_4(f_M, opponent_ratings, M, Sz)
            M = min(2700, M)
            return M

    # the value of K is an important component in calculating changes in the standard rating

    def compute_standard_rating_K(rating, time_control_minutes, time_control_increment_seconds, effective_nr_games, nr_games_tournament):

        K = 800/(effective_nr_games + nr_games_tournament)

        if 30 <= (time_control_minutes + time_control_increment_seconds) <= 65 and rating > 2200:
            if rating < 2500:
                K = (800 * (6.5 - 0.0025*rating))/(effective_nr_games +
                                                   nr_games_tournament)
            else:
                K = 200/(effective_nr_games +
                         nr_games_tournament)
        return K

    # the winning expectancy of a player in a given matchup, under the standard rating logic

    def compute_standard_winning_expectancy(self, rating, opponent_rating):
        winning_expectancy = 1/(1+10**-((rating - opponent_rating)/400))
        return winning_expectancy

    # the standard rating function is used for players with N > 8 who have not had either all wins or all losses in every previous rated game

    def _compute_standard_rating(self, player, player_tournament_matches, bonus=True):

        opponent_ratings = _player_opponent_ratings(
            player, self.players, player_tournament_matches)
        nr_tournament_matches = len(player_tournament_matches)

        sum_swe = sum([self.compute_standard_winning_expectancy(
            player.initialized_rating, o) for o in opponent_ratings])

        K = self.compute_standard_rating_K(player.initialized_rating, self.time_control_minutes,
                                           self.time_control_increment_seconds, player.effective_nr_games, nr_tournament_matches)

        opponent_ids = [i[0] for i in player_tournament_matches]

        max_nr_games_one_opponent = max(Counter(opponent_ids).values())

        if nr_games_tournament < 3 or max_nr_games_one_opponent > 2:

            rating_new = initialized_rating + \
                K*(tournament_score - sum_swe)
        else:
            if bonus:
                rating_new = initialized_rating + K*(tournament_score - sum_swe) + max(
                    0, K*(tournament_score - sum_swe) - B*np.sqrt(max(nr_games_tournament, 4)))
            else:
                rating_new = initialized_rating + \
                    K*(tournament_score - sum_swe)

        return rating_new

    # all ratings are subject to a floor of 100, and this may be higher depending on the conditions outlined below

    def compute_rating_floor(self, player, tournament_games, tournament_wins, tournament_draws, tournament_losses):

        # number of total wins after the tournament
        Nw = player.nr_wins + tournament_wins

        # number of total draws after the tournament
        Nd = player.nr_draws + tournament_draws

        # number of events in which a player has completed three rating games. defaults to 0 when class initialized, but other value can be specified
        if tournament_games >= 3:
            player.Nr += 1

        rating_floor = min(absolute_rating_floor + 4 *
                           Nw + 2*Nd + player.Nr, 150)

        # a player with an established rating has a rating floor possibly higher than the absolute floor. Higher rating floors exists at 1200 - 2100
        if player.initialized_rating >= 1200 and player.established is True:
            rating_floor = int((player.initialized_rating - 200) / 100)*100

        return rating_floor

    # function to update the rating of a player after a tournament

    def update_player_rating(self, player, player_tournament_matches, nr_tournament_matches, rating_floor):

        # opponent_ratings = _player_opponent_ratings(
        #     player, self.players, player_tournament_matches)
        # tournament_score = _player_tournament_score(
        #     player, player_tournament_matches)

        # Valid individual matches are rated differently. The bonus formula does not apply, and the maximum rating change in a match is 50 points. Rating floors do not apply.
        if self.individual_match:
            updated_rating = self._compute_standard_rating(
                player, player_tournament_matches, bonus=False)
            updated_rating_bounded = min(max(
                player.initialized_rating - 50, updated_rating), player.initialized_rating + 50, updated_rating)
            return updated_rating_bounded
        else:
            if player.rating_type == 'standard':
                updated_rating = self._compute_standard_rating()
            else:
                updated_rating = self._compute_special_rating()

            updated_rating_bounded = max(updated_rating, rating_floor)
            return updated_rating_bounded

    def run_tournament(self):
        if self.valid_tournament:
            updated_info = []
            for p in self.players:

                player_tournament_matches = _player_tournament_matches(
                    p, self.tournament_results)
                nr_tournament_matches, nr_tournament_wins, nr_tournament_draws, nr_tournament_losses = _tournament_stats(
                    p, player_tournament_matches)
                rating_floor = self.compute_rating_floor(
                    p, nr_tournament_matches, nr_tournament_wins, nr_tournament_draws, nr_tournament_losses)

                new_rating = self.update_player_rating(
                    p, player_tournament_matches, nr_tournament_matches, rating_floor)

                player_tournament_info = (
                    p.id, self.tournament_date, nr_tournament_matches, nr_tournament_wins, nr_tournament_draws, nr_tournament_losses, new_rating)

                updated_info.append(player_tournament_info)

            return updated_info
        else:
            return None


# General-purpose functions for computing tournament statistics

def _player_opponent_ratings(player, players, player_tournament_matches):
    opponent_ratings = []
    for m in player_tournament_matches:
        pairing = m[0]
        if player.id in pairing:
            opponent_id = [o for o in pairing if o != player.id][0]
            opponent_rating = [
                p.initialized_rating for p in players if p.id == opponent_id][0]
            opponent_ratings.append(opponent_rating)

    return opponent_ratings


def _player_tournament_matches(player, tournament_results):
    player_matches = []
    for m in tournament_results:
        if player.id in m[0]:
            player_matches.append(m)
    return player_matches


def _compute_match_performance(player_id, match):
    if match[1] is None:
        score = 0.5
    elif player_id == match[1]:
        score = 1
    else:
        score = 0
    return score


def _player_tournament_score(player, player_tournament_matches):
    tournament_score = 0
    for m in player_tournament_matches:
        match_score = _compute_match_performance(player.id, m)
        tournament_score += match_score

    return tournament_score


def _tournament_stats(player, player_tournament_matches):
    nr_games = len(player_tournament_matches)
    nr_wins = 0
    nr_draws = 0
    nr_losses = 0
    for t in player_tournament_matches:
        if t[1] is None:
            nr_draws += 1
        elif t[1] == player.id:
            nr_wins += 1
        else:
            nr_losses += 1

    return nr_games, nr_wins, nr_draws, nr_losses


def _individual_match(players):
    if len(players) == 2:
        return True
    else:
        return False
