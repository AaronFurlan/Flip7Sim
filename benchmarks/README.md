# MCTS benchmarks

The tournament compares `MCTSAgent` with `SimpleThresholdAgent`. Seat
positions alternate, and each game uses a reproducible seed.

Run the default tournament:

```powershell
python -m benchmarks.mcts_tournament --games 20
```

Example with explicit search settings:

```powershell
python -m benchmarks.mcts_tournament `
    --games 20 `
    --simulations 200 `
    --exploration-weight 0.9 `
    --max-depth 20 `
    --seed 1000
```

## Recorded comparison

These results used 20 games, seeds 1000 through 1019, a winning score of
100, 200 simulations, and a maximum depth of 20.

| Rollout policy | Exploration | MCTS wins | Threshold wins | Average score difference | Time |
|---|---:|---:|---:|---:|---:|
| Random actions | 0.9 | 11 | 9 | -8.8 | 139.0 s |
| Threshold agent | 0.9 | 12 | 8 | -15.3 | 103.8 s |

The agent rollout won one additional game and reduced runtime by about 25%.
An exploration weight of `0.6` performed worse in an additional ten-game
check, so `0.9` remains the default. Results can vary between seed ranges;
larger tournaments are recommended before further tuning. Runtime depends on
the computer.
