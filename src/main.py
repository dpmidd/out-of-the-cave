import random
import sys

from src.ai import narrator
from src.models.game_state import GameState
from src.persistence.save_manager import (
    delete_save,
    list_saves,
    load_checkpoint,
    load_game,
    save_checkpoint,
    save_game,
)
from src.systems.delegation import get_max_delegation_slots, process_delegations
from src.systems.events import select_event, resolve_choice
from src.systems.fortune import roll_fortune
from src.systems.milestones import check_milestones
from src.systems.npc_generator import generate_npcs
from src.ui import renderer, input_handler


def startup() -> GameState:
    """Show title and offer new game or continue from a save."""
    renderer.show_title()

    saves = list_saves()
    if saves:
        return input_handler.main_menu(saves)

    return new_game()


def new_game() -> GameState:
    """Character creation and initial world generation."""
    difficulty = input_handler.get_difficulty()
    depth = input_handler.get_narrative_depth()
    player = input_handler.allocate_attributes()

    npc_count = random.randint(8, 15)
    npcs = generate_npcs(npc_count)

    state = GameState(
        player=player,
        npcs=npcs,
        civilization=_make_civilization(npc_count),
        narrative_depth=depth,
        difficulty=difficulty,
    )

    renderer.console.print()
    renderer.console.print(
        f"[bold]You emerge from the cave with {npc_count} souls behind you.[/bold]"
    )
    renderer.console.print("[dim]They are blinking. Afraid. Looking to you.[/dim]")
    renderer.console.print()

    renderer.show_npc_roster(npcs)

    renderer.console.input("\n[dim]Press Enter to begin...[/dim]")
    return state


def _make_civilization(population: int):
    from src.models.civilization import Civilization
    return Civilization(population=population)


def game_loop(state: GameState) -> None:
    """Main event loop."""
    hard_mode = state.difficulty == "hard"

    while True:
        renderer.show_status(state)

        # Check end conditions
        if state.is_victory:
            renderer.show_victory(state)
            delete_save("autosave")
            return
        if state.is_defeat:
            renderer.show_defeat(state)

            # Easy mode: offer restart from checkpoint
            if state.difficulty == "easy":
                restored = load_checkpoint()
                if restored and input_handler.ask_restart_from_checkpoint():
                    renderer.console.print("\n[bold yellow]The vision fades. You find yourself back at a familiar moment...[/bold yellow]\n")
                    state.__dict__.update(restored.__dict__)
                    continue
            delete_save("autosave")
            return

        # Delegation management (if slots are unlocked)
        if get_max_delegation_slots(state) > 0:
            input_handler.delegation_menu(state)

        # Process delegation results from last turn's assignments
        delegation_results = process_delegations(state)
        if delegation_results:
            renderer.show_delegation_results(delegation_results)

        # Select and display event
        event = select_event(state)
        if event is None:
            renderer.console.print("\n[bold yellow]The days blur together. There are no more crises to face.[/bold yellow]")
            if state.civilization.stability >= 0.5:
                renderer.show_victory(state)
            else:
                renderer.show_defeat(state)
            return

        # Substitute a random NPC name into the event text
        alive_npcs = [n for n in state.npcs if n.alive]
        npc_name = random.choice(alive_npcs).name if alive_npcs else "a stranger"
        event_text = event["text"].replace("{npc}", npc_name)

        if narrator.should_use_ai(state):
            event_text = narrator.enhance_event(event_text, state, npc_name)

        renderer.show_event(event_text)
        renderer.show_choices(event["choices"])

        choice_idx = input_handler.get_choice(len(event["choices"]))
        chosen = event["choices"][choice_idx]

        outcome_text, info = resolve_choice(chosen, state)

        if outcome_text == "retreat":
            renderer.show_retreat()
            return

        if narrator.should_use_ai(state):
            outcome_text = narrator.enhance_outcome(outcome_text, info["success"], state)

        renderer.show_outcome(outcome_text, info)

        # Record and advance
        state.event_history.append(event["id"])
        state.turn += 1

        # --- Per-turn mechanics ---

        # Stability erosion (the core balance fix)
        state.decay_stability()

        # Chaos decay
        state.decay_chaos()

        # Random minor chaos spike (15% chance — petty disputes)
        if random.random() < 0.15:
            state.apply_chaos(0.03)
            renderer.console.print("  [dim]A petty dispute flares and dies.[/dim]")

        # Food consumption (pop // 3, harsher than before)
        food_needed = max(1, state.civilization.population // 3)
        state.civilization.food = max(0, state.civilization.food - food_needed)
        if state.civilization.food == 0:
            state.civilization.starvation_turns += 1
            renderer.console.print("  [bold red]Hunger gnaws at your people.[/bold red]")
            hunger_chaos = 0.08 if hard_mode else 0.05
            state.apply_chaos(hunger_chaos)
            state.civilization.stability = max(0.0, state.civilization.stability - 0.05)
            # Prolonged starvation kills
            if state.civilization.starvation_turns >= 2:
                state.civilization.population = max(0, state.civilization.population - 1)
                renderer.console.print("  [bold red]Someone has died of hunger.[/bold red]")
        else:
            state.civilization.starvation_turns = 0

        # Roll for miracles/curses
        fortune = roll_fortune(state)
        if fortune:
            fortune_type, fortune_name, fortune_text = fortune
            renderer.show_fortune(fortune_type, fortune_name, fortune_text)

        # Check milestones
        turn_deaths = info.get("deaths", 0)
        newly_achieved = check_milestones(state, turn_deaths)
        for ms_id in newly_achieved:
            ms = next(m for m in state.milestones if m.id == ms_id)
            milestone_desc = ms.description
            if narrator.should_use_ai(state):
                milestone_desc = narrator.enhance_milestone(ms.name, ms.description, ms.tier, state)
            renderer.show_milestone_achieved(ms.name, milestone_desc)

        # Easy mode: save checkpoint on milestone achievement
        if newly_achieved and state.difficulty == "easy":
            save_checkpoint(state)
            renderer.console.print("  [dim yellow]Checkpoint saved.[/dim yellow]")

        # Autosave every turn
        save_game(state, slot="autosave")

        # Offer save/continue prompt
        action = input_handler.turn_end_prompt()
        if action == "save":
            save_game(state, slot="manual")
            renderer.console.print("[dim yellow]Game saved.[/dim yellow]")
            renderer.console.input("\n[dim]Press Enter to continue...[/dim]")
        elif action == "save_quit":
            save_game(state, slot="manual")
            renderer.console.print("[dim yellow]Game saved. Until next time, philosopher.[/dim yellow]")
            return


def main():
    try:
        state = startup()
        game_loop(state)
    except KeyboardInterrupt:
        renderer.console.print("\n\n[dim]The philosopher sets down his pen.[/dim]\n")
        sys.exit(0)

    renderer.console.print("\n[dim]Thank you for playing Out of the Cave.[/dim]\n")


if __name__ == "__main__":
    main()
