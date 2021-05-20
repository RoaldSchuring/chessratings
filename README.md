

## Chessratings

A python implementation of official chess rating systems, specified as used by organizations such a FIDE and the US Chess Federation (USCF) to estimate player strength.

Currently available modules are:

- US Chess Federation (ELO): http://www.glicko.net/ratings/rating.system.pdf


## Installation

Available in PyPi.

```
pip install chessratings
```


## Usage

To use the chessratings package, import your module of choice into your python script:

```
from chessratings import uscf_elo
```

There are a few important concepts to know when using this package: Players and Tournaments. 

A Player is a rated entity that can participate in a game/match against other Players. Players are initiated with, at minimum, the following information:
- **id**: an identifier such as a name
- **rating**: their most recent rating, if known

Additional optional arguments may vary by module and can be found in the source code.

```
example_player_1 = uscf_elo.Player(id='player_1', rating=1600)
example_player_2 = uscf_elo.Player(id='player_2', rating=1500)
```

A Tournament is a match or series of matches between two or more players. As per the official specifications, player ratings are updated after a Tournament is concluded. 

A Tournament requires two arguments:
- **players**: a list of participating Player entities
- **tournament_results**: a summary of tournament results

The tournament_results must be provided in the following format:

```
[ 
    [ ( player_1_id, player_2_id ), winner_id ],
    [ ( ... )],
]
``` 
If the match was a draw, winner_id can be set to null (or any value other than one of the two player IDs). Here's an example:


```
players = [example_player_1, example_player_2]
tournament_results =    [
                            [ ( 'player_1', 'player_2' ), 'player_2'],
                            [ ( 'player_1' ,'player_2' ), 'player_1'],
                            [ ( 'player_1', 'player_2' ), np.nan ]
                        ]
tournament = uscf_elo.Tournament(players, tournament_results)
```

Running the tournaments will update player ratings, and optionally output summarized information about the tournament results. 

```
tournament_results = tournament.run()
print(tournament_results)
```

```

```







## Contributing

If you would like to help develop this package, along with the tools you need to develop and run tests, run the following in your virtualenv:

```bash
$ pip install -e .[dev]
```
