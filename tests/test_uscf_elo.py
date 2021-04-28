import pytest
from uscf_elo import Player

roald = Player(rating=1200, nr_games_played=10, nr_wins=8, nr_losses=1)
print(roald.effective_nr_games)
