import numpy as np
from datetime import date
from collections import Counter

'''
This package is an implementation of the US Chess Federation (USCF) rating system for Regular, Over-The-Board (OTB) events. Details can be found here: http://www.glicko.net/ratings/rating.system.pdf

When initializing ratings for unrated players, we use the recommended age-based initialization logic. If no age is provided, we assume that a player is an adult above the age of 26.

This package only implements partial logic for rating floors, disregarding rating floor logic for players with an original Life Master (OLM) title or the effect of large cash prizes.

At this time, this package does not allow for updating USCF ratings based on results from foreign FIDE events.
'''


class Player:

    def __init__(self, rating, nr_games_played, nr_wins, nr_losses, birth_date=date(1990, 1, 1), tournament_end_date=date(2021, 1, 1), Nr=0):
        self.nr_games_played = nr_games_played
        self.nr_wins = nr_wins
        self.nr_draws = nr_games_played - nr_wins - nr_losses
        self.nr_losses = nr_losses
        self.rating = rating
        self.birth_date = birth_date
        self.tournament_end_date = tournament_end_date
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
        age = (self.tournament_end_date - self.birth_date).days/365.25
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

    def _create_tournament(self, tournament_results):
        return self.Tournament(self, tournament_results)

    class Tournament:

        epsilon_special_rating = 10**-7
        absolute_rating_floor = 100
        B = 14

        # Note: tournament_results needs to be in a specific format: a list of tuples/lists, each representing one match and containing (opponent_id, opponent_rating, score), where score is 1 for a win, 0.5 for a draw and 0 for a loss

        def __init__(self, player, tournament_results, time_control_minutes=60, time_control_increment_seconds=0):
            self.player = player
            self.nr_games_tournament = len(tournament_results)
            self.tournament_score = sum([i[2] for i in tournament_results])
            self.tournament_results = tournament_results
            self.time_control_minutes = time_control_minutes
            self.time_control_increment_seconds = time_control_increment_seconds
            self._adjusted_initialized_rating, self._adjusted_score = self._compute_adjusted_initialized_rating_and_score()

        # the provisional winning expectancy for special ratings
        def _compute_pwe(self, player_rating, opponent_rating):
            if player_rating <= opponent_rating - 400:
                pwe = 0
            elif opponent_rating - 400 < player_rating < opponent_rating + 400:
                pwe = 0.5 + (player_rating - opponent_rating)/800
            else:
                pwe = 1

            return pwe

        # an adjusted initialized rating and adjusted score are used as variables to calculate the special rating

        def _compute_adjusted_initialized_rating_and_score(self):

            # players with <= 8 games, or players that have had only wins/losses in all previous rated games, get a special rating
            if self.player.rating_type == 'special-only-wins':
                adjusted_initialized_rating = self.player.initialized_rating - 400
                adjusted_score = self.tournament_score + self.player.effective_nr_games
            elif self.player.rating_type == 'special-only-losses':
                adjusted_initialized_rating = self.player.initialized_rating + 400
                adjusted_score = self.tournament_score
            else:
                adjusted_initialized_rating = self.player.initialized_rating
                adjusted_score = self.tournament_score + self.player.effective_nr_games/2

            return adjusted_initialized_rating, adjusted_score

        # an objective function for the special rating. The goal is to determine the value of the special rating estimate (R) such that the value of this objecive is equal to 0 within reasonable tolerance

        def _special_rating_objective(self, special_rating_estimate):

            sum_pwe = sum([self._compute_pwe(special_rating_estimate, t[1])
                          for t in self.tournament_results])

            objective_fn = self.player.effective_nr_games * \
                self._compute_pwe(special_rating_estimate, self._adjusted_initialized_rating) + \
                sum_pwe - self._adjusted_score

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

                print(za, f_za)

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

        def _special_rating_step_3(self, M, f_M, Sz):
            step_3_satisfied = False
            while step_3_satisfied is False:

                zb = min([z for z in Sz if z > M])
                f_zb = self._special_rating_objective(zb)
                if abs(f_zb - f_M) < self.epsilon_special_rating:
                    M = zb
                    f_M = f_zb
                else:
                    M_star = M - f_M * ((zb - M) / (f_zb - f_M))
                    if M_star > zb:
                        M = zb
                        f_M = self._special_rating_objective(M)
                        continue
                    elif M < M_star <= zb:
                        M = M_star
                        f_M = self._special_rating_objective(M)
                        continue
                    else:
                        step_3_satisfied = True
                        return M, f_M

        # the fourth step of the iterative process to find the special rating

        def _special_rating_step_4(self, f_M, opponent_ratings, M, Sz):
            p = 0
            if abs(f_M) < self.epsilon_special_rating:
                p = len([o for o in opponent_ratings if abs(M - o) <= 400])
            if abs(M - self._adjusted_initialized_rating) <= 400:
                p += 1
            if p > 0:
                pass
            elif p == 0:
                za = max([s for s in Sz if s < M])
                zb = min([s for s in Sz if s > M])
                if za <= self.player.initialized_rating <= zb:
                    M = self.player.initialized_rating
                elif self.player.initialized_rating < za:
                    M = za
                elif self.player.initialized_rating > zb:
                    M = zb
                else:
                    raise Exception(
                        'M is outside the range of expected values.')

            M = min(2700, M)
            return M

        # the overall process to compute the special rating

        def _compute_special_rating(self):

            tournament_games = len(self.tournament_results)
            tournament_score = sum([t[2] for t in self.tournament_results])
            opponent_ratings = [r[1] for r in self.tournament_results]

            M = self._special_rating_step_1_compute_M(self.player.effective_nr_games, self.player.initialized_rating,
                                                      opponent_ratings, tournament_score, tournament_games)

            f_M = self._special_rating_objective(M)
            Sz = self._compute_Sz(opponent_ratings)

            if f_M > self.epsilon_special_rating:
                M, f_M = self._special_rating_step_2(M, f_M, Sz)

            if f_M < -self.epsilon_special_rating:
                M, f_M = self._special_rating_step_3(M, f_M, Sz)

            if abs(f_M) < self.epsilon_special_rating:
                M = self._special_rating_step_4(f_M, opponent_ratings, M, Sz)
                M = min(2700, M)
                return M

        # the value of K is an important component in calculating changes in the standard rating

        def compute_standard_rating_K(self, rating, time_control_minutes, time_control_increment_seconds, effective_nr_games, nr_games_tournament):

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

        def _compute_standard_rating(self, bonus=True):
            sum_swe = sum([self.compute_standard_winning_expectancy(
                self.player.initialized_rating, r[1]) for r in self.tournament_results])

            K = self.compute_standard_rating_K(
                self.player.initialized_rating, self.time_control_minutes, self.time_control_increment_seconds, self.player.effective_nr_games, self.nr_games_tournament)

            opponent_ids = [i[0] for i in self.tournament_results]
            max_nr_games_one_opponent = max(Counter(opponent_ids).values())

            if self.nr_games_tournament < 3 or max_nr_games_one_opponent > 2:

                rating_new = self.player.initialized_rating + \
                    K*(self.tournament_score - sum_swe)
            else:
                if bonus:
                    rating_new = self.player.initialized_rating + K*(self.tournament_score - sum_swe) + max(
                        0, K*(self.tournament_score - sum_swe) - self.B*np.sqrt(max(self.nr_games_tournament, 4)))
                else:
                    rating_new = self.player.initialized_rating + \
                        K*(self.tournament_score - sum_swe)

            return rating_new

        # all ratings are subject to a floor of 100, and this may be higher depending on the conditions outlined below

        def compute_rating_floor(self):

            # number of total wins after the tournament
            Nw = self.player.nr_wins + \
                len([i for i in self.tournament_results[2] if i == 1])

            # number of total draws after the tournament
            Nd = self.player.nr_games_played - self.player.nr_wins - self.player.nr_losses + \
                len([i for i in self.tournament_results[2] if i == 0.5])

            # number of events in which a player has completed three rating games. defaults to 0 when class initialized, but other value can be specified
            if len(self.tournament_results) >= 3:
                self.player.Nr += 1

            otb_absolute_rating_floor = min(
                self.absolute_rating_floor + 4*Nw + 2*Nd + self.player.Nr, 150)

            # a player with an established rating has a rating floor possibly higher than the absolute floor. Higher rating floors exists at 1200 - 2100
            if self.player.initialized_rating >= 1200 and self.player.established_rating is True:
                otb_absolute_rating_floor = int(
                    (self.player.initialized_rating - 200) / 100)*100

            return otb_absolute_rating_floor

        # function to update the rating of a player after a tournament

        def update_rating(self):

            if self.player.rating_type == 'standard':
                updated_rating = self._compute_standard_rating()
            else:
                updated_rating = self._compute_special_rating()

            opponent_ids = [i[0] for i in self.tournament_results]
            # an individual match will only be rated if both players involved have an etablished published rating with a maximum difference of 400 points. The bonus formula does not apply, and the maximum rating change in a match is 50 points. Rating floors do not apply.
            if len(set(opponent_ids)) == 1:
                if self.player.established_rating is True and abs(self.player.initialized_rating - self.tournament_results[0][1]) <= 400:
                    updated_rating = self._compute_standard_rating(bonus=False)
                    updated_rating_bounded = min(max(
                        self.player.initialized_rating - 50, updated_rating), self.player.initialized_rating + 50, updated_rating)
                else:
                    return self.player.initialized_rating
            else:
                updated_rating_bounded = max(
                    updated_rating, self.compute_rating_floor())

            # now update the player's overall number of games played, wins, losses
            self.player.nr_games_played += len(self.tournament_results)
            self.player.nr_wins += len(
                [t for t in self.tournament_results if t[2] == 1])
            self.player.nr_losses += len(
                [t for t in self.tournament_results if t[2] == 0])

            return updated_rating_bounded
