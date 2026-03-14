# Kaboom Game Rules

## Purpose

This document describes the intended game rules for Kaboom.

It is the canonical rules reference for:

* engine development
* CLI and UI behavior reviews
* simulation design
* bug triage against expected gameplay
* anyone who just wants to play (lol)

Implementation details and API contracts are documented separately in:

* [`ENGINE_FLOW.md`](./ENGINE_FLOW.md)
* [`GAME_ENGINE_API.md`](./GAME_ENGINE_API.md)

## Objective

Kaboom is a memory card game where players try to win with the lowest total score.

There are two win conditions:

1. End the game with the lowest total score.
2. Instantly win by getting rid of all cards in hand.

## Setup

### Players

* Default player count: 4
* Recommended player count: 4
* Maximum player count: 6

The practical limit comes from a standard 52-card deck and the default hand size.

### Starting Hand

* Each player starts with 4 face-down cards by default.
* Cards are placed face down in front of the player.
* Cards remain separate and individually addressable. They are not stacked into one pile.

### Opening Peek

Before normal play begins:

* each player may look at any 2 of their own cards
* those cards are then returned face down
* this opening peek happens once only
* players may not repeatedly peek at the same cards unless a later power allows it

## Card Values

Scoring is based on the cards still in a player's hand when the game ends.

### Numeric Cards

* Ace = 1 point
* 2 through 10 = face value

### Face Cards

* Jack = 10 points
* Queen = 10 points
* King = 10 points

### Exception

* Red king = 0 points
* Red king means king of hearts or king of diamonds

## Powers

Only some cards have powers.

### 7 or 8

Power: see one of your own cards

Rules:

* any suit
* choose exactly 1 of your own cards
* look at it once
* return it face down

### 9 or 10

Power: see one of another player's cards

Rules:

* any suit
* choose exactly 1 card
* target must be another player, not yourself
* look at it once
* return it face down

### Jack or Queen

Power: blind swap

Rules:

* any suit
* swap 1 of your own cards with 1 card from another player
* no peeking is allowed during this action

### Black King

Power: see and swap

Rules:

* only king of spades or king of clubs
* look at the 2 cards involved in the swap
* once seen, the swap is mandatory
* you may not inspect and then cancel midway

## How Powers Are Used

A power is available only if the player draws that card from the deck during their turn.

To use a power:

1. draw a power card from the deck
2. discard that drawn power card to the discard pile
3. resolve the power from that discarded card instead of putting it into hand

Important constraints:

* using a power is optional
* a player may discard the drawn power card without using its power
* if a power card ever enters a player's hand, it behaves only as a normal scoring card
* cards in hand do not retain power functionality

## Turn Structure

On a normal turn, the player draws one card from the deck.

After drawing, the player chooses one of the following:

1. Discard the drawn card.
2. Replace one card in hand with the drawn card.
3. If the drawn card has a valid power, use the power and discard that drawn card.

## Reactions and Getting Rid of Cards

Kaboom allows players to get rid of cards when a matching rank enters the discard pile.

### When Reactions Are Triggered

As soon as a card enters the discard pile, players may attempt to react to that rank.

This can happen because of:

* a normal discard
* a replace action, where the replaced hand card goes to the discard pile
* a power use, where the drawn power card is first discarded and then its power resolves

### Power And Reaction Timing

Using a power card and opening a reaction window happen simultaneously from the same discard event.

That means:

* the drawn power card is discarded to the discard pile
* the card's power becomes available
* the reaction window for that discarded rank also becomes available

The acting player may choose to use the power.
Other players may choose to react if they know a matching rank.

If both a power use and a reaction compete over the same discarded card event:

* priority goes to whoever touched it first

This priority rule is intended to model real-table simultaneous claims.

### What Players May React With

If a player knows the location of a card with the same rank as the newly discarded card, they may try to discard that matching card.

Suit does not matter for the reaction. Only rank matters.

Example:

* if a 5 is discarded
* any known 5 may be thrown, regardless of suit or ownership

### Reacting With Your Own Card

If a player discards their own matching card:

* that card is discarded
* that player now has one fewer card
* each reaction claim discards only one card

### Reacting With Another Player's Card

If a player discards another player's matching card:

* the target card is discarded
* the reacting player must give any 1 of their own cards to that player
* the reacting player ends with one fewer card overall
* each reaction claim discards only one card

### Priority

Only one successful reaction is resolved for each discard event.

The practical rule is first come, first served:

* multiple players may want to react
* only one claim is actually resolved
* once a valid reaction is accepted, the reaction opportunity is over

### Wrong Guess Penalty

If a player reacts with the wrong card:

* the attempted card is revealed to all players at its current location
* that card stays in the same hand position
* the reacting player draws 1 facedown penalty card into hand
* the reaction window stays open for other valid claims

To avoid degenerate spam:

* each player is limited to 1 wrong reaction attempt per discard event

## Worked Example

Two-player example:

* P1 starts with `3, 5, 7, 9`
* P2 starts with `7, J, Q, 2`

Suppose:

* P1 remembers `3, 5, x, x`
* P2 remembers `x, J, x, 2`

If P1 draws a jack and uses its power:

* that jack is discarded first
* its power and the reaction window begin from that same discard event
* because a jack entered the discard pile, reactions become possible
* P2 may react by discarding the jack they know about

If P1 had instead replaced with the drawn jack:

* the replaced hand card would be the one entering the discard pile
* reaction eligibility would depend on the replaced card's rank, not the hidden drawn jack now in hand

## Kaboom

After round 1, a player may call Kaboom at the start of their turn.

Rules:

* Kaboom can only be called on that player's turn
* the player must choose Kaboom instead of making any other move
* the calling player reveals their hand and score
* the calling player is effectively out of future interaction

### Final Round After Kaboom

Once Kaboom is called:

* the rest of the table gets one final round
* the game ends when turn order comes back to the player who called Kaboom

During that final round:

* the Kaboom caller's cards are locked
* other players cannot interact with those cards anymore

## End of Game

The game ends in either of these cases:

1. A player gets rid of all cards and wins instantly.
2. Kaboom finishes its final round and scores are compared.

### Score Resolution

At score-based game end:

* sum the values of the cards still in each player's hand
* the player with the minimum total score wins

## Rule Notes For Engine Audits

The following points are especially important when validating engine behavior:

* the opening two-card peek is mandatory setup behavior
* powers only work from the drawn card, never from a card already in hand
* red kings are scoring-only cards and do not grant black-king power
* only one reaction should resolve per discard event
* power-use discard and reaction eligibility begin from the same discard event
* if power resolution and a reaction compete on that same event, priority goes to first touch
* wrong reaction guesses reveal information and apply penalty, but do not consume the discard event
* reacting with another player's card always requires giving back one of your own cards
* instant win is based on zero cards, not zero points
* Kaboom caller cards become non-interactable during the final round
