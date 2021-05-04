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

    def __init__(self, id, rating, nr_games_played, nr_wins, nr_losses, nr_tournaments=0, birth_date=date(1990, 1, 1), current_date=date(2021, 1, 1), Nr=0):
        self.id = id
        self.nr_games_played = nr_games_played
        self.nr_wins = nr_wins
        self.nr_draws = nr_games_played - nr_wins - nr_losses
        self.nr_losses = nr_losses
        self.rating = rating
        self._nr_tournaments = nr_tournaments
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
        self.players = players
        self.individual_match = self._verify_individual_match()
        self.valid_tournament = self._valid_tournament()
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
            if player_1.established_rating is False or player_2.established_rating is False or abs(player_1.initialized_rating - player_2.initialized_rating) > 400:
                return False
            else:
                return True
        else:
            return True

    def _verify_individual_match(self):
        if len(self.players) == 2:
            return True
        else:
            return False

    def run_tournament(self):
        if self.valid_tournament:
            updated_info = []
            for p in self.players:

                playertournament = PlayerTournament(p, self)
                new_rating = playertournament.update_player_rating()
                player_tournament_info = [p.id, self.tournament_date, playertournament._tournament_nr, playertournament.nr_matches,
                                          playertournament.nr_wins, playertournament.nr_draws, playertournament.nr_losses, new_rating]

                updated_info.append(player_tournament_info)

            return updated_info
        else:
            return None


class PlayerTournament:

    def __init__(self, player, tournament):
        self.player = player
        self.tournament = tournament
        self._matches = self._player_matches()
        self.score = self._tournament_score()
        self.nr_matches, self.nr_wins, self.nr_draws, self.nr_losses = self._tournament_stats()
        self._tournament_nr = self.player._nr_tournaments + 1
        self._opponents = self._retrieve_opponents()
        self._opponent_ratings = [
            o.initialized_rating for o in self._opponents]
        self._adjusted_initialized_rating, self._adjusted_score = self._compute_adjusted_initialized_rating_and_score()

    def __iter___(self):
        return iter(self._opponents)

    def _player_matches(self):
        player_matches = []
        for m in self.tournament.tournament_results:
            if self.player.id in m[0]:
                player_matches.append(m)
        return player_matches

    def _retrieve_opponents(self):
        opponents = []
        # an opponent is any player that a player faces in a match during a tournament
        for m in self._matches:
            pairing = m[0]
            if self.player.id in pairing:
                opponent_id = [o for o in pairing if o != self.player.id][0]
                opponent = [
                    p for p in self.tournament.players if p.id == opponent_id][0]
                opponents.append(opponent)

        return opponents

    def _compute_match_performance(self, player_id, match):
        if player_id == match[1]:
            score = 1
        elif match[1] in [p.id for p in self.tournament.players]:
            score = 0
        else:
            score = 0.5

        return score

    def _tournament_score(self):
        tournament_score = 0
        for m in self._matches:
            match_score = self._compute_match_performance(self.player.id, m)
            tournament_score += match_score

        return tournament_score

    def _tournament_stats(self):
        nr_games = len(self._matches)
        nr_wins = 0
        nr_draws = 0
        nr_losses = 0
        for t in self._matches:
            score = self._compute_match_performance(self.player.id, t)
            if score == 0:
                nr_losses += 1
            elif score == 0.5:
                nr_draws += 1
            else:
                nr_wins += 1

        return nr_games, nr_wins, nr_draws, nr_losses

   # an adjusted initialized rating and adjusted score are used as variables to calculate the special rating

    def _compute_adjusted_initialized_rating_and_score(self):

        # players with <= 8 games, or players that have had only wins/losses in all previous rated games, get a special rating
        if self.player.rating_type == 'special-only-wins':
            adjusted_initialized_rating = self.player.initialized_rating - 400
            adjusted_score = self.score + self.player.effective_nr_games
        elif self.player.rating_type == 'special-only-losses':
            adjusted_initialized_rating = self.player.initialized_rating + 400
            adjusted_score = self.score
        else:
            adjusted_initialized_rating = self.player.initialized_rating
            adjusted_score = self.score + self.player.effective_nr_games/2

        return adjusted_initialized_rating, adjusted_score

    # an objective function for the special rating. The goal is to determine the value of the special rating estimate (R) such that the value of this objecive is equal to 0 within reasonable tolerance

    def _special_rating_objective(self, special_rating_estimate):

        sum_pwe = sum([_compute_provisional_winning_expectancy(
            special_rating_estimate, o.initialized_rating) for o in self._opponents])

        objective_fn = self.player.effective_nr_games*_compute_provisional_winning_expectancy(special_rating_estimate, self._adjusted_initialized_rating) + \
            sum_pwe - self._adjusted_score

        return objective_fn

    # Sz is used in the iterative procedure to find the solution for the special rating objective function
    def _compute_Sz(self):
        Sz = [o + 400 for o in self._opponent_ratings] + \
            [o - 400 for o in self._opponent_ratings] + \
            [self.player.initialized_rating - 400] + \
            [self.player.initialized_rating + 400]
        return Sz

    # the first step of the iterative algorithm - provides the first estimate of the special rating

    def _special_rating_step_1_compute_M(self):
        # print('effective games', self.player.effective_nr_games)
        # print('initialized rating', self.player.initialized_rating)
        # print('sum opponent ratings', sum(self._opponent_ratings))
        # print('score', self.score)
        # print('nr_matches', self.nr_matches)

        # M = 2000

        M = (self.player.effective_nr_games*self.player.initialized_rating + sum(self._opponent_ratings) +
             400 * (2*self.score - self.nr_matches))/(self.player.effective_nr_games + self.nr_matches)
        return M

    # the second step of the iterative process to find the special rating

    def _special_rating_step_2(self, M, f_M, Sz):
        step_2_satisfied = False
        while step_2_satisfied is False:
            if f_M > epsilon_special_rating:
                # Let za be the largest value in Sz for which M > za.

                za = max([z for z in Sz if z < M])
                f_za = self._special_rating_objective(za)

                if abs(f_M - f_za) < epsilon_special_rating:
                    M = za
                    f_M = f_za
                    continue
                else:
                    M_star = M - f_M * ((M - za) / (f_M - f_za))
                    if M_star < za:
                        M = za
                        f_M = f_za
                        continue
                    elif za <= M_star < M:
                        M = M_star
                        f_M = self._special_rating_objective(M_star)
                        continue
                    else:
                        step_2_satisfied = True
                        break
            else:
                step_2_satisfied = True
                break

        return M, f_M

    # the third step of the iterative process to find the special rating

    def _special_rating_step_3(self, M, f_M, Sz):
        step_3_satisfied = False
        while step_3_satisfied is False:
            if f_M < -epsilon_special_rating:

                zb = min([z for z in Sz if z > M])
                f_zb = self._special_rating_objective(zb)
                if abs(f_zb - f_M) < epsilon_special_rating:
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
            else:
                step_3_satisfied = True
                return M, f_M

    # the fourth step of the iterative process to find the special rating

    def _special_rating_step_4(self, f_M, M, Sz):
        if abs(f_M) < -epsilon_special_rating:
            p = 0
            if abs(f_M) < epsilon_special_rating:
                p = len([o for o in self._opponent_ratings if abs(M - o) <= 400])
            if abs(M - self._adjusted_initialized_rating) <= 400:
                p += 1
            if p > 0:
                return M

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

        return M

    def _compute_special_rating(self):

        M = self._special_rating_step_1_compute_M()
        f_M = self._special_rating_objective(M)
        Sz = self._compute_Sz()

        M, f_M = self._special_rating_step_2(M, f_M, Sz)
        M, f_M = self._special_rating_step_3(M, f_M, Sz)
        M = self._special_rating_step_4(f_M, M, Sz)

        M = min(2700, M)
        return M

    # the value of K is an important component in calculating changes in the standard rating

    def compute_standard_rating_K(self, rating, effective_nr_games, nr_tournament_matches):

        K = 800/(effective_nr_games + nr_tournament_matches)

        if 30 <= (self.tournament.time_control_minutes + self.tournament.time_control_increment_seconds) <= 65 and rating > 2200:
            if rating < 2500:
                K = (800 * (6.5 - 0.0025*rating))/(effective_nr_games +
                                                   nr_tournament_matches)
            else:
                K = 200/(effective_nr_games +
                         nr_tournament_matches)
        return K

    # the standard rating function is used for players with N > 8 who have not had either all wins or all losses in every previous rated game

    def _compute_standard_rating(self, bonus=True):
        sum_swe = sum([_compute_standard_winning_expectancy(
            self.player.initialized_rating, o.initialized_rating) for o in self._opponents])

        K = self.compute_standard_rating_K(
            self.player.initialized_rating, self.player.effective_nr_games, self.nr_matches)

        opponent_ids = list(set([o.id for o in self._opponents]))
        max_nr_games_one_opponent = max(
            Counter(opponent_ids).values())

        if self.nr_matches < 3 or max_nr_games_one_opponent > 2:

            rating_new = self.player.initialized_rating + \
                K*(self.score - sum_swe)
        else:
            if bonus:
                rating_new = self.player.initialized_rating + K*(self.score - sum_swe) + max(
                    0, K*(self.score - sum_swe) - B*np.sqrt(max(self.nr_matches, 4)))
            else:
                rating_new = self.player.initialized_rating + \
                    K*(self.score - sum_swe)

        return rating_new

    # all ratings are subject to a floor of 100, and this may be higher depending on the conditions outlined below

    def compute_rating_floor(self):

        # number of total wins after the tournament
        Nw = self.player.nr_wins + self.nr_wins

        # number of total draws after the tournament
        Nd = self.player.nr_draws + self.nr_draws

        # number of events in which a player has completed three rating games. defaults to 0 when class initialized, but other value can be specified
        # NOTE: can be updated
        if self.nr_matches >= 3:
            self.player.Nr += 1

        otb_absolute_rating_floor = min(
            absolute_rating_floor + 4*Nw + 2*Nd + self.player.Nr, 150)

        # a player with an established rating has a rating floor possibly higher than the absolute floor. Higher rating floors exists at 1200 - 2100
        if self.player.initialized_rating >= 1200 and self.player.established_rating is True:
            otb_absolute_rating_floor = int(
                (self.player.initialized_rating - 200) / 100)*100

        return otb_absolute_rating_floor

    # function to update the rating of a player after a tournament

    def update_player_rating(self):

        # Valid individual matches are rated differently. The bonus formula does not apply, and the maximum rating change in a match is 50 points. Rating floors do not apply.

        rating_floor = self.compute_rating_floor()
        if self.tournament.individual_match:
            updated_rating = self._compute_standard_rating(bonus=False)
            updated_rating_bounded = min(max(
                self.player.initialized_rating - 50, updated_rating), self.player.initialized_rating + 50, updated_rating)
            return updated_rating_bounded
        else:
            if self.player.rating_type == 'standard':
                updated_rating = self._compute_standard_rating()
            else:
                updated_rating = self._compute_special_rating()

            updated_rating_bounded = max(updated_rating, rating_floor)
            return updated_rating_bounded


def _compute_provisional_winning_expectancy(player_rating, opponent_rating):
    if player_rating <= opponent_rating - 400:
        pwe = 0
    elif opponent_rating - 400 < player_rating < opponent_rating + 400:
        pwe = 0.5 + (player_rating - opponent_rating)/800
    else:
        pwe = 1

    return pwe

# the winning expectancy of a player in a given matchup, under the standard rating logic


def _compute_standard_winning_expectancy(player_rating, opponent_rating):
    winning_expectancy = 1 / \
        (1+10**-((player_rating - opponent_rating)/400))
    return winning_expectancy


player_1 = Player('roald', rating=1600, nr_games_played=260,
                  nr_wins=100, nr_losses=29)
player_2 = Player('mickelton', rating=None,
                  nr_games_played=0, nr_wins=0, nr_losses=0)
player_3 = Player('jana', rating=1400, nr_games_played=300,
                  nr_wins=20, nr_losses=6)
player_4 = Player('holland beer', rating=800,
                  nr_games_played=300, nr_wins=0, nr_losses=250)


# results = [(('mickelton', 'jana'), 'mickelton'),
#            (('holland beer', 'jana'), 'holland beer'),
#            (('mickelton', 'holland beer'), 'holland beer'),
#            (('roald', 'holland beer'), 'holland beer'),
#            (('mickelton', 'jana'), 'jana')]

# tournament = Tournament(
#     players=[player_1, player_2, player_4, player_3], tournament_results=results)


# updated_scores = tournament.run_tournament()
# [print(u) for u in updated_scores]
