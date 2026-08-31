# TODO – Flip 7 Simulation für Reinforcement Learning

## Ziel

Eine verständliche, objektorientierte Flip-7-Simulation entwickeln, die später als Grundlage für ein Reinforcement-Learning-Environment dient.

Grundprinzipien:

- OOP verwenden
- kleine, klar abgegrenzte Module
- selbsterklärende Variablen- und Funktionsnamen
- Lesbarkeit vor Cleverness
- Spiellogik strikt von Agenten und RL trennen
- jede wichtige Regel mit Unit Tests absichern
- Simulation muss ohne UI ausführbar sein

---

# 1. Projektstruktur

- [ ] Projektstruktur anlegen

```text
flip7/
│
├── game/
│   ├── __init__.py
│   ├── cards.py
│   ├── deck.py
│   ├── player.py
│   ├── round.py
│   ├── game.py
│   └── scoring.py
│
├── actions/
│   ├── __init__.py
│   ├── base_action.py
│   ├── freeze_action.py
│   ├── flip_three_action.py
│   └── second_chance_action.py
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── random_agent.py
│   ├── threshold_agent.py
│   └── rl_agent.py
│
├── simulation/
│   ├── __init__.py
│   ├── simulator.py
│   └── statistics.py
│
├── rl/
│   ├── __init__.py
│   ├── environment.py
│   ├── observation.py
│   ├── action_space.py
│   └── reward.py
│
├── tests/
│   ├── test_cards.py
│   ├── test_deck.py
│   ├── test_player.py
│   ├── test_scoring.py
│   ├── test_round.py
│   └── test_game.py
│
├── main.py
└── README.md
```

---

# 2. Kartenmodell

## `game/cards.py`

Ziel: Alle Karten als einfache Objekte darstellen.

- [ ] `Card` Basisklasse erstellen
- [ ] `NumberCard` erstellen
- [ ] `ModifierCard` erstellen
- [ ] `ActionCard` erstellen
- [ ] Kartentyp eindeutig speichern
- [ ] Kartenwert eindeutig speichern
- [ ] verständliche `__str__()`-Methode implementieren

Beispiel:

```python
class NumberCard(Card):
    def __init__(self, number: int):
        self.number = number
```

Regel:

> Kartenobjekte speichern primär Daten. Komplexe Spiellogik gehört nicht in die Kartenklasse.

---

# 3. Deck

## `game/deck.py`

Ziel: Das Flip-7-Deck verwalten.

- [ ] `Deck` Klasse erstellen
- [ ] vollständiges Standarddeck erzeugen
- [ ] korrekte Anzahl jeder Zahlenkarte erzeugen
- [ ] Modifierkarten hinzufügen
- [ ] Aktionskarten hinzufügen
- [ ] Deck mischen
- [ ] Karte ziehen
- [ ] verbleibende Karten zählen
- [ ] Ablagestapel verwalten
- [ ] leeres Deck erkennen
- [ ] Deck bei Bedarf neu mischen

Methoden:

```python
create_standard_deck()
shuffle()
draw_card()
remaining_card_count()
```

Tests:

- [ ] Gesamtzahl der Karten stimmt
- [ ] Anzahl jeder Zahlenkarte stimmt
- [ ] `draw_card()` entfernt genau eine Karte
- [ ] Seed erzeugt reproduzierbare Reihenfolge
- [ ] leeres Deck wird korrekt behandelt

---

# 4. Spieler

## `game/player.py`

Ziel: Den Zustand eines einzelnen Spielers verwalten.

Attribute:

```python
player_name
total_score
round_cards
is_active
has_stayed
has_busted
has_second_chance
```

- [ ] `Player` Klasse erstellen
- [ ] Gesamtpunktestand speichern
- [ ] aktuelle Rundekarten speichern
- [ ] aktiven Zustand speichern
- [ ] Bust-Zustand speichern
- [ ] Stay-Zustand speichern
- [ ] Second Chance speichern
- [ ] Spieler für neue Runde zurücksetzen
- [ ] Karte hinzufügen
- [ ] prüfen, ob Zahlenkarte bereits vorhanden ist
- [ ] Zahlenkarten zurückgeben
- [ ] Modifierkarten zurückgeben

Methoden:

```python
add_card(card)
has_number(number)
reset_for_new_round()
get_number_cards()
get_modifier_cards()
```

---

# 5. Punktelogik

## `game/scoring.py`

Ziel: Punkteberechnung von der restlichen Spiellogik trennen.

- [ ] Summe der Zahlenkarten berechnen
- [ ] additive Modifier berücksichtigen
- [ ] Multiplikatoren berücksichtigen
- [ ] Flip-7-Bonus berücksichtigen
- [ ] Bust mit 0 Rundepunkten behandeln

Hauptfunktion:

```python
def calculate_round_score(player: Player) -> int:
    ...
```

Tests:

- [ ] nur Zahlenkarten
- [ ] Zahlen + Bonus
- [ ] Multiplikator
- [ ] mehrere Modifier
- [ ] Flip 7
- [ ] Bust

---

# 6. Einzelne Spielrunde

## `game/round.py`

Ziel: Eine komplette Flip-7-Runde koordinieren.

Klasse:

```python
class GameRound:
    ...
```

- [ ] Spieler für neue Runde vorbereiten
- [ ] Startkarten verteilen
- [ ] Karte für Spieler ziehen
- [ ] Zahlenkarte verarbeiten
- [ ] Modifierkarte verarbeiten
- [ ] Aktionskarte verarbeiten
- [ ] doppelte Zahlen erkennen
- [ ] Bust auslösen
- [ ] Second Chance berücksichtigen
- [ ] Stay verarbeiten
- [ ] Flip 7 erkennen
- [ ] prüfen, ob noch aktive Spieler vorhanden sind
- [ ] Runde beenden
- [ ] Rundepunkte auf Gesamtpunktestand übertragen

Methoden:

```python
start_round()
draw_card_for_player(player)
player_stays(player)
check_for_bust(player)
check_for_flip_seven(player)
is_round_finished()
finish_round()
```

Wichtig:

> `GameRound` entscheidet nicht selbst, ob ein Spieler Hit oder Stay wählt.

Diese Entscheidung kommt von einem `Agent`.

---

# 7. Aktionskarten

## `actions/base_action.py`

Gemeinsames Interface:

```python
class BaseAction:
    def execute(
        self,
        game_round,
        source_player,
        target_player,
    ):
        raise NotImplementedError
```

---

## `actions/freeze_action.py`

- [ ] Zielspieler bestimmen
- [ ] Zielspieler stoppen
- [ ] aktueller Rundenscore bleibt erhalten
- [ ] Zielspieler aus weiteren Entscheidungen entfernen

---

## `actions/flip_three_action.py`

- [ ] Zielspieler bestimmen
- [ ] bis zu drei zusätzliche Karten ziehen
- [ ] Bust während Flip Three erkennen
- [ ] Second Chance berücksichtigen
- [ ] Flip 7 während Flip Three erkennen
- [ ] Aktionskarten innerhalb Flip Three korrekt behandeln

---

## `actions/second_chance_action.py`

- [ ] Second Chance dem Spieler zuweisen
- [ ] bei doppelter Zahl verwenden
- [ ] doppelte Karte entfernen
- [ ] Second Chance danach verbrauchen

Tests:

- [ ] jede Action separat
- [ ] Action + Bust
- [ ] Action + Second Chance
- [ ] Action + Flip 7

---

# 8. Gesamtes Spiel

## `game/game.py`

Ziel: Mehrere Runden zu einem vollständigen Spiel verbinden.

Klasse:

```python
class Flip7Game:
    ...
```

- [ ] Spieler speichern
- [ ] Deck verwalten
- [ ] neue Runde erzeugen
- [ ] Rundenergebnisse übernehmen
- [ ] Gesamtpunktestand aktualisieren
- [ ] Spielende erkennen
- [ ] Gewinner bestimmen
- [ ] mehrere Gewinner bei Gleichstand unterstützen

Methoden:

```python
start_game()
start_new_round()
play_round()
is_game_finished()
get_winners()
```

---

# 9. Agenteninterface

## `agents/base_agent.py`

Ziel: Spiellogik darf nicht wissen, wie Entscheidungen getroffen werden.

```python
class BaseAgent:

    def choose_hit_or_stay(self, observation):
        raise NotImplementedError

    def choose_target_player(
        self,
        observation,
        valid_targets,
    ):
        raise NotImplementedError
```

Damit können später dieselben Regeln verwendet werden für:

```text
Random Agent
Threshold Agent
Probability Agent
RL Agent
Menschlicher Spieler
```

---

# 10. Random Agent

## `agents/random_agent.py`

Erste Baseline.

- [ ] zufällig Hit oder Stay wählen
- [ ] zufälligen gültigen Zielspieler wählen
- [ ] Seed unterstützen

Beispiel:

```python
class RandomAgent(BaseAgent):

    def choose_hit_or_stay(self, observation):
        ...
```

Nutzen:

- Unit Tests
- Simulation testen
- RL-Baseline
- Fehler in der Game Engine finden

---

# 11. Threshold Agent

## `agents/threshold_agent.py`

Einfache regelbasierte Baseline.

Beispiel:

```python
if current_round_score >= stay_threshold:
    return STAY

return HIT
```

- [ ] `stay_threshold` konfigurierbar
- [ ] Zielauswahl für Aktionskarten implementieren

Danach verschiedene Varianten erstellen:

```text
ConservativeAgent   -> Stay ab 20
NormalAgent         -> Stay ab 30
AggressiveAgent     -> Stay ab 40
```

Optional später:

- [ ] Anzahl eigener Zahlen berücksichtigen
- [ ] Bust-Wahrscheinlichkeit berücksichtigen
- [ ] Gegnerpunktestand berücksichtigen

---

# 12. Simulation

## `simulation/simulator.py`

Ziel: Tausende Spiele ohne UI ausführen.

Klasse:

```python
class Flip7Simulator:
    ...
```

- [ ] Agenten entgegennehmen
- [ ] einzelnes Spiel simulieren
- [ ] mehrere Spiele simulieren
- [ ] Seeds unterstützen
- [ ] Sitzposition randomisieren
- [ ] Ergebnisse sammeln
- [ ] keine unnötigen `print()`-Aufrufe

Beispiel:

```python
simulator.run_games(
    agents=agents,
    number_of_games=10_000,
)
```

---

# 13. Statistiken

## `simulation/statistics.py`

Metriken sammeln:

- [ ] Anzahl Spiele
- [ ] Siege
- [ ] Win Rate
- [ ] durchschnittlicher Endscore
- [ ] durchschnittlicher Rundenscore
- [ ] Bust Rate
- [ ] durchschnittliche Anzahl Hits
- [ ] Stay Rate
- [ ] Flip-7-Häufigkeit
- [ ] Second-Chance-Nutzung
- [ ] Aktionskarten-Nutzung
- [ ] Siegquote nach Sitzposition

Optional:

- [ ] Ergebnisse als Dictionary
- [ ] Ergebnisse als pandas DataFrame
- [ ] CSV Export
- [ ] Konfidenzintervalle

---

# 14. Minimal Viable Simulation testen

Bevor RL begonnen wird:

- [ ] 2 Spieler funktionieren
- [ ] 3 Spieler funktionieren
- [ ] 4 Spieler funktionieren
- [ ] komplette Runde funktioniert
- [ ] komplettes Spiel funktioniert
- [ ] Bust funktioniert
- [ ] Stay funktioniert
- [ ] Flip 7 funktioniert
- [ ] Modifier funktionieren
- [ ] alle Aktionskarten funktionieren
- [ ] Random Agent funktioniert
- [ ] Threshold Agent funktioniert
- [ ] 10'000 Spiele laufen ohne Exception
- [ ] Simulation ist mit gleichem Seed reproduzierbar

**Erst danach RL implementieren.**

---

# 15. RL Observation

## `rl/observation.py`

Ziel: Den sichtbaren Spielzustand in Zahlen umwandeln.

Erste Observation:

```text
Eigener Zustand
---------------
total_score
round_score
number_of_unique_numbers
has_second_chance
has_stayed

Eigene Karten
-------------
has_number_0
has_number_1
...
has_number_12

Gegner
------
total_score
round_score
number_of_unique_numbers
is_active
has_second_chance

Spiel
-----
remaining_card_count
```

- [ ] Observation als `numpy.ndarray`
- [ ] feste Reihenfolge definieren
- [ ] Observation dokumentieren
- [ ] Werte normalisieren
- [ ] keine Informationen verwenden, die ein echter Spieler nicht kennt

---

# 16. RL Action Space

## `rl/action_space.py`

Normale Entscheidung:

```text
0 = HIT
1 = STAY
```

Zusätzliche Entscheidung bei Aktionskarten:

```text
TARGET_PLAYER_0
TARGET_PLAYER_1
TARGET_PLAYER_2
...
```

- [ ] Action Space definieren
- [ ] aktuelle Entscheidungsphase abbilden
- [ ] Action Masking implementieren
- [ ] ungültige Zielspieler maskieren
- [ ] ausgeschiedene Spieler maskieren

---

# 17. Gymnasium Environment

## `rl/environment.py`

Klasse:

```python
class Flip7Environment(gym.Env):
    ...
```

Implementieren:

- [ ] `reset()`
- [ ] `step(action)`
- [ ] `observation_space`
- [ ] `action_space`
- [ ] `terminated`
- [ ] `truncated`
- [ ] `info`

Gymnasium API:

```python
observation, reward, terminated, truncated, info = env.step(action)
```

Für Version 1:

```text
1 RL-Agent
+
regelbasierte Gegner
```

Noch kein Self-Play.

---

# 18. Reward

## `rl/reward.py`

Mit möglichst einfachem Reward beginnen.

### Variante A – Win/Loss

```text
Sieg          +1
Niederlage    -1
```

- [ ] implementieren
- [ ] Training testen

### Variante B – Score Difference

```python
reward = (
    player_total_score
    - best_opponent_total_score
)
```

- [ ] Reward normalisieren

### Reward Shaping

Nur falls notwendig:

- [ ] Punktegewinn
- [ ] Bust
- [ ] Flip 7
- [ ] Rundengewinn
- [ ] Spielgewinn

Wichtig:

> Nicht vorschnell Reward Shaping hinzufügen. Der Agent soll möglichst das eigentliche Spielziel lernen.

---

# 19. Erste PPO-Baseline

Setup:

```text
1 PPO Agent

gegen

3 Threshold Agents
```

- [ ] PPO trainieren
- [ ] mehrere Seeds verwenden
- [ ] Checkpoints speichern
- [ ] Training Reward plotten
- [ ] Evaluation getrennt vom Training durchführen

Evaluation:

- [ ] PPO vs Random
- [ ] PPO vs Conservative
- [ ] PPO vs Normal
- [ ] PPO vs Aggressive

Metriken:

- [ ] Win Rate
- [ ] Score
- [ ] Bust Rate
- [ ] Hit Rate
- [ ] durchschnittliche Anzahl Karten vor Stay

---

# 20. Probability Agent

Eine analytische Baseline bauen.

## `agents/probability_agent.py`

- [ ] bekannte Karten berücksichtigen
- [ ] Bust-Wahrscheinlichkeit berechnen

```python
def calculate_bust_probability(
    player,
    known_cards,
) -> float:
    ...
```

Entscheidung beispielsweise:

```python
if bust_probability > maximum_accepted_risk:
    return STAY

return HIT
```

Damit kann später geprüft werden:

> Lernt PPO tatsächlich eine sinnvolle Risikostrategie oder nur einen simplen Punkte-Threshold?

---

# 21. Spielverhalten analysieren

Nach erfolgreichem Training untersuchen:

- [ ] Stay-Wahrscheinlichkeit nach Rundenscore
- [ ] Stay-Wahrscheinlichkeit nach Anzahl Karten
- [ ] Stay-Wahrscheinlichkeit nach Bust-Wahrscheinlichkeit
- [ ] Verhalten bei Führung
- [ ] Verhalten bei Rückstand
- [ ] Verhalten kurz vor Spielende
- [ ] Nutzung von Freeze
- [ ] Nutzung von Flip Three
- [ ] Zielauswahl bei Aktionskarten

Interessante Frage:

> Wird der Agent aggressiver, wenn er deutlich hinten liegt?

---

# 22. Kartenhistorie

Erst später erweitern.

## Experiment A

Agent sieht nur aktuellen Spielzustand.

## Experiment B

Agent erhält bekannte Kartenhistorie:

```text
seen_number_0_count
seen_number_1_count
...
seen_number_12_count
```

Vergleichen:

- [ ] Win Rate
- [ ] Bust Rate
- [ ] Score
- [ ] Risikoverhalten

---

# 23. Recurrent Agent

Optional:

```text
PPO + LSTM
```

Der Agent erhält nicht explizit die Kartenhistorie, sondern muss relevante Informationen selbst speichern.

Vergleich:

```text
PPO
PPO + explizite Kartenhistorie
PPO + LSTM
```

---

# 24. Self-Play

Erst wenn Single-Agent-RL stabil funktioniert.

- [ ] mehrere RL-Agenten unterstützen
- [ ] Shared Policy testen
- [ ] getrennte Policies testen
- [ ] historische Checkpoints als Gegner verwenden
- [ ] Gegnerpopulation verwenden
- [ ] Sitzposition randomisieren

Mögliche Population:

```text
RandomAgent
ConservativeAgent
NormalAgent
AggressiveAgent
ProbabilityAgent
OldPPOCheckpoint
CurrentPPO
```

---

# Code Guidelines

## Variablennamen

Gut:

```python
current_round_score
remaining_card_count
number_of_unique_cards
target_player
current_player
bust_probability
```

Nicht:

```python
crs
cnt
n
p
x
tmp
```

---

## Funktionsnamen

Eine Funktion = möglichst eine Aufgabe.

Gut:

```python
draw_card_for_player()
calculate_round_score()
check_for_bust()
check_for_flip_seven()
choose_target_player()
```

Nicht:

```python
handle_game()
process_everything()
do_stuff()
```

---

## Klassenverantwortung

```text
Card
    beschreibt eine Karte

Deck
    verwaltet Karten

Player
    verwaltet Spielerzustand

GameRound
    verwaltet eine Runde

Flip7Game
    verwaltet ein vollständiges Spiel

BaseAgent
    definiert die Entscheidungsschnittstelle

Simulator
    führt viele Spiele aus

Flip7Environment
    verbindet Game Engine und RL
```

---

## Type Hints

Konsequent verwenden:

```python
def has_number(self, number: int) -> bool:
    ...

def draw_card(self) -> Card:
    ...

def calculate_round_score(player: Player) -> int:
    ...
```

---

## Dataclasses

Für reine Datenobjekte bevorzugen:

```python
from dataclasses import dataclass

@dataclass
class NumberCard:
    number: int
```

---

## Keine Magic Numbers

Nicht:

```python
if score >= 200:
```

Sondern:

```python
WINNING_SCORE = 200

if score >= WINNING_SCORE:
    ...
```

Spielkonstanten zentral definieren.

Optional:

```text
game/constants.py
```

---

# Empfohlene Reihenfolge

```text
01 Card
02 Deck
03 Player
04 Scoring
05 GameRound
06 Flip7Game
07 RandomAgent
08 ThresholdAgent
09 Simulator
10 Statistics
11 Action Cards
12 ProbabilityAgent
13 Observation
14 Action Space
15 Gymnasium Environment
16 Reward
17 PPO
18 Behaviour Analysis
19 Card History
20 LSTM
21 Self-Play
```

---

# Definition of Done – Game Engine V1

Folgender Code soll am Ende möglich sein:

```python
agents = [
    ThresholdAgent(
        player_name="Alice",
        stay_threshold=30,
    ),
    RandomAgent(
        player_name="Bob",
    ),
    ThresholdAgent(
        player_name="Charlie",
        stay_threshold=25,
    ),
]

simulator = Flip7Simulator(agents)

results = simulator.run_games(
    number_of_games=10_000,
)

print(results.win_rates)
```

---

# Architekturziel

```text
               Flip-7-Regeln
                     │
                     ▼
                Game Engine
                     │
                     ▼
              Agent Interface
              /      |       \\
             /       |        \\
            ▼        ▼         ▼
         Random   Threshold    RL
          Agent     Agent     Agent
```

Die **Game Engine darf nicht wissen**, ob eine Entscheidung von:

- einem Random Agent
- einer festen Regel
- einem Menschen
- PPO
- einem anderen RL-Verfahren

kommt.

Dadurch bleibt die Simulation einfach, testbar und später ohne Umbau für RL verwendbar.