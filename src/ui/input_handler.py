from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.models.game_state import GameState
from src.models.npc import NPC
from src.models.player import Player
from src.persistence.save_manager import delete_save, load_game, list_saves
from src.systems.delegation import (
    TASKS,
    get_available_for_delegation,
    get_delegated_npcs,
    get_max_delegation_slots,
    get_npc_task_impression,
)


console = Console()

ATTRIBUTE_DESCRIPTIONS = {
    "rhetoric": "Persuasion and speechcraft — convince, inspire, defuse",
    "wisdom": "Philosophical insight — plan, foresee, understand",
    "courage": "Boldness — lead from the front, take risks, endure",
    "authority": "Command presence — intimidate, order, enforce",
    "pragmatism": "Practical problem-solving — build, organize, ration",
}

TOTAL_POINTS = 15
ATTRIBUTES = ["rhetoric", "wisdom", "courage", "authority", "pragmatism"]


def get_difficulty() -> str:
    """Let player choose difficulty mode."""
    console.print("\n[bold]Choose your path:[/bold]\n")
    options = [
        ("1", "Easy", "Milestones act as checkpoints — restart from the last one on defeat"),
        ("2", "Normal", "One life. No checkpoints. The standard experience."),
        ("3", "Hard", "No checkpoints, harsher chaos, less forgiveness."),
    ]
    for num, label, desc in options:
        console.print(f"  [bold]{num}.[/bold] {label} — [dim]{desc}[/dim]")

    while True:
        console.print()
        choice = console.input("[bold gold1]Choose (1-3): [/bold gold1]").strip()
        mapping = {"1": "easy", "2": "normal", "3": "hard"}
        if choice in mapping:
            return mapping[choice]
        console.print("[red]Please enter 1, 2, or 3.[/red]")


def ask_restart_from_checkpoint() -> bool:
    """On defeat in easy mode, ask if player wants to restart from checkpoint."""
    console.print()
    choice = console.input("[bold yellow]Restart from last milestone checkpoint? (y/n): [/bold yellow]").strip().lower()
    return choice in ("y", "yes")


def get_narrative_depth() -> str:
    """Let player choose narrative depth."""
    console.print("\n[bold]How much narrative detail do you want?[/bold]\n")
    options = [
        ("1", "Low", "Terse and functional"),
        ("2", "Medium", "Scene-setting paragraphs"),
        ("3", "High", "Rich descriptions and dialogue"),
        ("4", "Very High", "Full literary passages"),
    ]
    for num, label, desc in options:
        console.print(f"  [bold]{num}.[/bold] {label} — [dim]{desc}[/dim]")

    while True:
        console.print()
        choice = console.input("[bold gold1]Choose (1-4): [/bold gold1]").strip()
        mapping = {"1": "low", "2": "medium", "3": "high", "4": "very_high"}
        if choice in mapping:
            return mapping[choice]
        console.print("[red]Please enter 1, 2, 3, or 4.[/red]")


def allocate_attributes() -> Player:
    """Interactive attribute allocation."""
    console.print(Panel(
        f"[bold]You are Plato.[/bold]\n\n"
        f"Before you lead, you must know yourself.\n"
        f"Distribute [bold gold1]{TOTAL_POINTS}[/bold gold1] points across your attributes.\n"
        f"Each starts at 1. Minimum 1, maximum 10.",
        title="[bold gold1]Character Creation[/bold gold1]",
        border_style="gold1",
    ))

    console.print()
    for attr in ATTRIBUTES:
        console.print(f"  [bold]{attr.capitalize():12}[/bold] — [dim]{ATTRIBUTE_DESCRIPTIONS[attr]}[/dim]")

    values = {attr: 1 for attr in ATTRIBUTES}
    remaining = TOTAL_POINTS - len(ATTRIBUTES)  # 15 - 5 = 10 bonus points

    console.print(f"\n[dim]You have {remaining} bonus points to distribute (base of 1 already assigned).[/dim]\n")

    for attr in ATTRIBUTES:
        while True:
            current_display = ", ".join(f"{a}: {values[a]}" for a in ATTRIBUTES)
            console.print(f"  [dim]Current: {current_display} | Remaining: {remaining}[/dim]")
            raw = console.input(f"  [bold]{attr.capitalize()}[/bold] (add 0-{min(9, remaining)}): ").strip()
            try:
                bonus = int(raw)
                if bonus < 0 or bonus > min(9, remaining):
                    console.print(f"  [red]Enter a number between 0 and {min(9, remaining)}.[/red]")
                    continue
                values[attr] = 1 + bonus
                remaining -= bonus
                break
            except ValueError:
                console.print("  [red]Enter a number.[/red]")

    # Dump remaining points into the last attribute if any left
    if remaining > 0:
        values[ATTRIBUTES[-1]] = min(10, values[ATTRIBUTES[-1]] + remaining)
        console.print(f"  [dim]Remaining {remaining} points added to {ATTRIBUTES[-1]}.[/dim]")

    player = Player(**values)

    console.print()
    table = Table(title="Plato", box=box.ROUNDED, border_style="gold1")
    table.add_column("Attribute", style="bold")
    table.add_column("Value", justify="center")
    for attr in ATTRIBUTES:
        val = player.get_attribute(attr)
        bar = "█" * val + "░" * (10 - val)
        table.add_row(attr.capitalize(), f"{bar} {val}")
    console.print(table)

    return player


def get_choice(num_choices: int) -> int:
    """Get a numbered choice from the player. Returns 0-indexed."""
    while True:
        raw = console.input("[bold gold1]Your choice: [/bold gold1]").strip()
        try:
            choice = int(raw)
            if 1 <= choice <= num_choices:
                return choice - 1
            console.print(f"[red]Enter a number between 1 and {num_choices}.[/red]")
        except ValueError:
            console.print("[red]Enter a number.[/red]")


def delegation_menu(state: GameState) -> bool:
    """Show the delegation management menu. Returns True if any changes were made."""
    max_slots = get_max_delegation_slots(state)
    if max_slots == 0:
        return False

    delegated = get_delegated_npcs(state)
    available = get_available_for_delegation(state)
    used_slots = len(delegated)

    console.print()
    console.print(Panel(
        f"[bold]Delegation[/bold] — {used_slots}/{max_slots} slots used\n"
        f"[dim]Entrust your people with ongoing tasks. They work each turn automatically.[/dim]",
        border_style="yellow",
    ))

    # Show current delegations
    if delegated:
        table = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
        table.add_column("#", style="bold", width=3)
        table.add_column("Name", style="bold")
        table.add_column("Task", style="cyan")
        table.add_column("Impression")
        for i, npc in enumerate(delegated, 1):
            task = TASKS[npc.role]
            impression = get_npc_task_impression(npc, npc.role)
            table.add_row(str(i), npc.name, task["label"], impression)
        console.print(table)

    console.print()
    console.print("  [bold]A.[/bold] Assign someone to a task")
    if delegated:
        console.print("  [bold]R.[/bold] Remove someone from their task")
    console.print("  [bold]D.[/bold] Done — continue to next event")
    console.print()

    changed = False
    while True:
        raw = console.input("[bold yellow]Delegation > [/bold yellow]").strip().lower()

        if raw == "d":
            return changed

        if raw == "a":
            if used_slots >= max_slots:
                console.print("[red]All delegation slots are full.[/red]")
                continue
            unassigned = [n for n in available if n.role is None or n.role not in TASKS]
            if not unassigned:
                console.print("[red]No one is available for delegation.[/red]")
                continue
            npc = _pick_npc(unassigned, "assign")
            if npc:
                task_id = _pick_task()
                if task_id:
                    npc.role = task_id
                    impression = get_npc_task_impression(npc, task_id)
                    console.print(f"  [green]{npc.name} assigned to {TASKS[task_id]['label']}.[/green]")
                    console.print(f"  [dim]{impression}[/dim]")
                    used_slots += 1
                    changed = True

        elif raw == "r" and delegated:
            npc = _pick_npc(delegated, "remove")
            if npc:
                old_task = TASKS[npc.role]["label"]
                npc.role = None
                console.print(f"  [yellow]{npc.name} removed from {old_task}.[/yellow]")
                delegated = get_delegated_npcs(state)
                used_slots = len(delegated)
                changed = True

        else:
            console.print("[dim]Enter A, R, or D.[/dim]")


def _pick_npc(npcs: list[NPC], action: str) -> NPC | None:
    """Let player pick an NPC from a list."""
    console.print()
    for i, npc in enumerate(npcs, 1):
        loyalty_color = "green" if npc.loyalty >= 0.6 else "yellow" if npc.loyalty >= 0.4 else "red"
        role_info = f" [cyan]({TASKS[npc.role]['label']})[/cyan]" if npc.role in TASKS else ""
        console.print(f"  [bold]{i}.[/bold] {npc.name}{role_info} — [{loyalty_color}]{npc.personality}[/{loyalty_color}]")
    console.print(f"  [bold]0.[/bold] [dim]Cancel[/dim]")
    console.print()

    while True:
        raw = console.input(f"  [yellow]Who to {action} (0 to cancel): [/yellow]").strip()
        try:
            idx = int(raw)
            if idx == 0:
                return None
            if 1 <= idx <= len(npcs):
                return npcs[idx - 1]
            console.print(f"  [red]Enter 0-{len(npcs)}.[/red]")
        except ValueError:
            console.print("  [red]Enter a number.[/red]")


def _pick_task() -> str | None:
    """Let player pick a delegation task."""
    console.print()
    task_ids = list(TASKS.keys())
    for i, task_id in enumerate(task_ids, 1):
        task = TASKS[task_id]
        console.print(f"  [bold]{i}.[/bold] {task['label']} — [dim]{task['description']}[/dim]")
    console.print(f"  [bold]0.[/bold] [dim]Cancel[/dim]")
    console.print()

    while True:
        raw = console.input("  [yellow]Which task (0 to cancel): [/yellow]").strip()
        try:
            idx = int(raw)
            if idx == 0:
                return None
            if 1 <= idx <= len(task_ids):
                return task_ids[idx - 1]
            console.print(f"  [red]Enter 0-{len(task_ids)}.[/red]")
        except ValueError:
            console.print("  [red]Enter a number.[/red]")


def main_menu(saves: list[dict]) -> "GameState":
    """Show the main menu with option to continue, load, or start new."""
    from src.main import new_game

    console.print("[bold]What would you do?[/bold]\n")
    console.print("  [bold]1.[/bold] Continue — [dim]resume your most recent game[/dim]")
    console.print("  [bold]2.[/bold] New Game — [dim]begin a new journey[/dim]")
    if len(saves) > 1:
        console.print("  [bold]3.[/bold] Load Save — [dim]choose from your saved games[/dim]")
    console.print()

    while True:
        raw = console.input("[bold gold1]Choose: [/bold gold1]").strip()

        if raw == "1":
            # Load most recent save
            state = load_game(saves[0]["slot"])
            if state:
                slot = saves[0]["slot"]
                turn = saves[0]["turn"]
                console.print(f"\n[dim]Resuming from {slot} save (turn {turn})...[/dim]\n")
                return state
            console.print("[red]Save file corrupted. Starting new game.[/red]")
            return new_game()

        if raw == "2":
            return new_game()

        if raw == "3" and len(saves) > 1:
            return _load_save_menu(saves)

        max_opt = "3" if len(saves) > 1 else "2"
        console.print(f"[red]Enter 1-{max_opt}.[/red]")


def _load_save_menu(saves: list[dict]) -> "GameState":
    """Show a list of saves and let the player pick one."""
    from src.main import new_game

    console.print()
    table = Table(title="Saved Games", box=box.ROUNDED, border_style="dim")
    table.add_column("#", style="bold", width=3)
    table.add_column("Slot", style="cyan")
    table.add_column("Turn", justify="center")
    table.add_column("Pop.", justify="center")
    table.add_column("Difficulty")
    table.add_column("Saved At", style="dim")

    for i, s in enumerate(saves, 1):
        saved_at = s["saved_at"][:16].replace("T", " ") if s["saved_at"] != "unknown" else "?"
        table.add_row(str(i), s["slot"], str(s["turn"]), str(s["population"]), s["difficulty"], saved_at)

    console.print(table)
    console.print(f"  [bold]0.[/bold] [dim]Back[/dim]")
    console.print()

    while True:
        raw = console.input("[bold gold1]Load which save (0 to go back): [/bold gold1]").strip()
        try:
            idx = int(raw)
            if idx == 0:
                return main_menu(saves)
            if 1 <= idx <= len(saves):
                state = load_game(saves[idx - 1]["slot"])
                if state:
                    console.print(f"\n[dim]Loaded {saves[idx - 1]['slot']} save.[/dim]\n")
                    return state
                console.print("[red]Save file corrupted.[/red]")
            else:
                console.print(f"[red]Enter 0-{len(saves)}.[/red]")
        except ValueError:
            console.print("[red]Enter a number.[/red]")


def turn_end_prompt() -> str:
    """Prompt at the end of each turn. Returns 'continue', 'save', or 'save_quit'."""
    console.print()
    console.print("[dim]Enter[/dim] continue   [dim]S[/dim] save   [dim]Q[/dim] save & quit")
    raw = console.input("[dim]> [/dim]").strip().lower()

    if raw in ("s", "save"):
        return "save"
    if raw in ("q", "quit", "sq"):
        return "save_quit"
    return "continue"
