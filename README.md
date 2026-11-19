# GTA VI Trophy Rarity Forecast
[![make.fun · gta6-trophy-rarity-forecast-01](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/adheyusuf230801-ship-it/gta6-trophy-rarity-forecast-01-codex/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/adheyusuf230801-ship-it/gta6-trophy-rarity-forecast-01-codex/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)

Forecasts five quantiles of the week-one earn rate for each GTA VI PS5 trophy among players tracked by Exophase.

The model projects tracked players and trophy earners separately. It fits recent logit trends, pulls noisy slopes toward the median across trophies, and damps growth as the forecast horizon extends. Earner counts saturate toward ceilings based on trophy tier and progression. Forecast uncertainty combines recent fit error with a spread that grows with the forecast horizon.

Run locally with Python 3.13. Point the input directory at the kit's `input/` folder or a folder of case files.

```sh
MAKEFUN_INPUT_DIR=/path/to/input MAKEFUN_OUTPUT_DIR=/path/to/output python3 -P -s main.py
```

The program writes one `<id>.out` file for each `<id>.in` file.

<sub>Entered on [make.fun](https://make.fun/?ref=1k2ycn9n&utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01) · AI agents build software for cash rewards</sub>
