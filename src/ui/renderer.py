from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from src.models.game_state import GameState


console = Console()


TITLE_ART = r"""
        ___________________
       /                   \
      /    OUT OF THE CAVE   \
     /                         \
    |   ▓▓▓▓▓▓▓░░░░░░░░░░░░    |
    |   ▓▓▓▓▓░░░░  ☀  ░░░░░    |
    |   ▓▓▓░░░░░░░░░░░░░░░░    |
    |   ▓▓░░░░░ ~ ~ ~ ░░░░░    |
    |   ▓░░░░░░░░░░░░░░░░░░    |
    |___________________________|
    |///////////////////////////|
    |////// THE CAVE ///////////|
    \///////////////////////////
"""


def show_title() -> None:
    console.print(Text(TITLE_ART, style="bold yellow"), justify="center")
    console.print()
    console.print(
        Panel(
            "[italic]You have shown them the sun.\n"
            "Now you must show them how to live beneath it.[/italic]",
            style="dim white",
            box=box.SIMPLE,
        ),
        justify="center",
    )
    console.print()


def _bar(value: int, max_val: int = 10, fill: str = "█", empty: str = "░") -> str:
    """Render a visual bar."""
    filled = min(value, max_val)
    return fill * filled + empty * (max_val - filled)


def show_status(state: GameState) -> None:
    """Display a full dashboard: resources, attributes, and key NPCs."""
    from rich.columns import Columns

    # --- Resources panel ---
    res = Table(box=None, show_header=False, padding=(0, 1), expand=True)
    res.add_column("stat", style="bold", min_width=12)
    res.add_column("value")

    chaos_colors = {"Calm": "green", "Uneasy": "yellow", "Simmering": "dark_orange", "Volatile": "red", "Anarchy": "bold red"}
    stab_colors = {"Flourishing": "bold green", "Organized": "green", "Fragile": "yellow", "Unstable": "dark_orange", "Chaos": "bold red"}

    chaos_style = chaos_colors.get(state.chaos_label, "white")
    stab_style = stab_colors.get(state.civilization.stability_label, "white")

    res.add_row("Turn", str(state.turn + 1))
    res.add_row("Population", f"{state.civilization.population} people")
    res.add_row("Stability", f"[{stab_style}]{_bar(int(state.civilization.stability * 10))} {state.civilization.stability:.0%} ({state.civilization.stability_label})[/{stab_style}]")
    res.add_row("Chaos", f"[{chaos_style}]{_bar(int(state.chaos * 10))} {state.chaos:.0%} ({state.chaos_label})[/{chaos_style}]")
    res.add_row("Food", f"{_bar(state.civilization.food, max_val=20)} {state.civilization.food}")
    res.add_row("Shelter", f"{_bar(state.civilization.shelter, max_val=10)} {state.civilization.shelter}")
    res.add_row("Knowledge", f"{_bar(state.civilization.knowledge, max_val=12)} {state.civilization.knowledge}")

    if state.civilization.laws:
        for i, law in enumerate(state.civilization.laws):
            label = "Laws" if i == 0 else ""
            res.add_row(label, f"[dim italic]{law}[/dim italic]")

    # --- Attributes panel ---
    attrs = Table(box=None, show_header=False, padding=(0, 1), expand=True)
    attrs.add_column("attr", style="bold", min_width=12)
    attrs.add_column("value")

    for attr_name in ["rhetoric", "wisdom", "courage", "authority", "pragmatism"]:
        val = state.player.get_attribute(attr_name)
        attrs.add_row(attr_name.capitalize(), f"{_bar(val)} {val}")

    # --- People summary ---
    alive_npcs = [n for n in state.npcs if n.alive]
    people = Table(box=None, show_header=False, padding=(0, 1), expand=True)
    people.add_column("name", style="bold", min_width=12)
    people.add_column("impression")

    for npc in alive_npcs[:6]:  # show top 6 to keep it compact
        loyalty_color = "green" if npc.loyalty >= 0.6 else "yellow" if npc.loyalty >= 0.4 else "red"
        role_tag = f" [cyan]({npc.role})[/cyan]" if npc.role else ""
        people.add_row(
            f"{npc.name}{role_tag}",
            f"[{loyalty_color}]{npc.personality}[/{loyalty_color}]"
        )
    if len(alive_npcs) > 6:
        people.add_row(f"[dim]+{len(alive_npcs) - 6} others[/dim]", "")

    # --- Milestones panel ---
    tier_names = {1: "Survival", 2: "Organization", 3: "Society", 4: "The Republic", 5: "Legacy"}
    ms_table = Table(box=None, show_header=False, padding=(0, 1), expand=True)
    ms_table.add_column("milestone", min_width=20)
    ms_table.add_column("status", min_width=4)

    for tier in range(1, 6):
        tier_milestones = [m for m in state.milestones if m.tier == tier]
        if not tier_milestones:
            continue
        tier_done = all(m.achieved for m in tier_milestones)
        tier_style = "bold green" if tier_done else "bold white" if tier == state.current_tier else "dim"
        ms_table.add_row(f"[{tier_style}]— {tier_names[tier]} —[/{tier_style}]", "")
        for m in tier_milestones:
            if m.achieved:
                ms_table.add_row(f"  [green]{m.name}[/green]", "[green]✓[/green]")
            elif tier == state.current_tier:
                ms_table.add_row(f"  [white]{m.name}[/white]", "[dim]○[/dim]")
            else:
                ms_table.add_row(f"  [dim]{m.name}[/dim]", "[dim]·[/dim]")

    # --- Compose dashboard ---
    top_left = Panel(res, title="[bold gold1]Resources[/bold gold1]", border_style="gold1", expand=True)
    top_mid = Panel(attrs, title="[bold cyan]Plato[/bold cyan]", border_style="cyan", expand=True)
    top_right = Panel(people, title="[bold white]Your People[/bold white]", border_style="white", expand=True)

    console.print()
    console.print(Columns([top_left, top_mid, top_right], equal=True, expand=True))

    # Milestones below as a full-width bar
    console.print(Panel(ms_table, title=f"[bold yellow]Milestones — Tier {state.current_tier}: {tier_names[state.current_tier]}[/bold yellow]", border_style="yellow", expand=True))


def show_event(text: str) -> None:
    """Display an event narrative."""
    console.print()
    console.print(Panel(text, border_style="cyan", padding=(1, 2)))


def show_choices(choices: list[dict]) -> None:
    """Display numbered choices."""
    console.print()
    for i, choice in enumerate(choices, 1):
        if choice.get("special") == "retreat":
            style = "dim red italic"
        else:
            style = "white"
        console.print(f"  [{style}][bold]{i}.[/bold] {choice['text']}[/{style}]")
    console.print()


def show_outcome(text: str, info: dict) -> None:
    """Display the outcome of a choice."""
    if info.get("roll"):
        roll_text = f"  [dim](Roll: {info['roll']} vs target {info['target']} — {'[green]Success[/green]' if info['success'] else '[red]Failure[/red]'})[/dim]"
        console.print(roll_text)

    style = "green" if info.get("success", True) else "red"
    console.print(Panel(text, border_style=style, padding=(1, 2)))

    if info.get("civ_changes"):
        for change in info["civ_changes"]:
            console.print(f"  [dim]→ {change}[/dim]")


def show_delegation_results(results: list) -> None:
    """Show what delegated NPCs accomplished this turn."""
    if not results:
        return
    console.print()
    console.print("[bold yellow]Delegation Reports:[/bold yellow]")
    for r in results:
        if r.success:
            console.print(f"  [green]✓[/green] [dim]{r.description}[/dim]")
        else:
            console.print(f"  [red]✗[/red] [dim]{r.description}[/dim]")


def show_fortune(fortune_type: str, name: str, text: str) -> None:
    """Display a miracle or curse."""
    console.print()
    if fortune_type == "miracle":
        console.print(Panel(
            f"[bold green]{name}[/bold green]\n\n[italic]{text}[/italic]",
            title="[bold green]★ Miracle ★[/bold green]",
            border_style="green",
            padding=(1, 2),
        ))
    else:
        console.print(Panel(
            f"[bold red]{name}[/bold red]\n\n[italic]{text}[/italic]",
            title="[bold red]☠ Curse ☠[/bold red]",
            border_style="red",
            padding=(1, 2),
        ))


def show_milestone_achieved(name: str, description: str) -> None:
    """Announce a milestone achievement."""
    console.print()
    console.print(Panel(
        f"[bold gold1]{name}[/bold gold1]\n[italic]{description}[/italic]",
        title="[bold yellow]★ Milestone Achieved ★[/bold yellow]",
        border_style="yellow",
        padding=(1, 2),
    ))


def show_retreat() -> None:
    console.print()
    console.print(Panel(
        "[italic]You turn back toward the darkness. The cave mouth swallows you whole.\n\n"
        "The shadows on the wall dance as they always have. Familiar. Safe. Small.\n\n"
        "Perhaps this is enough. Perhaps truth was never meant for everyone.[/italic]",
        title="[bold red]Retreat[/bold red]",
        border_style="red",
        padding=(1, 2),
    ))


def show_victory(state: GameState) -> None:
    console.print()
    console.print(Panel(
        f"[bold green]Against all odds, stability holds.[/bold green]\n\n"
        f"A population of {state.civilization.population} has found a way to live in the light.\n"
        f"Laws govern: {', '.join(state.civilization.laws) if state.civilization.laws else 'none yet, but custom serves'}.\n"
        f"It took {state.turn + 1} turns of struggle.\n\n"
        f"[italic]It is not the Republic you imagined. It is messier, louder, more human.\n"
        f"But they are free. And they chose to stay.[/italic]",
        title="[bold gold1]✦ A Fragile Civilization ✦[/bold gold1]",
        border_style="gold1",
        padding=(1, 2),
    ))


def show_defeat(state: GameState) -> None:
    console.print()
    if state.civilization.population <= 0:
        reason = "There is no one left to lead. The last of them returned to the cave, or worse."
    else:
        reason = "Chaos consumed everything. Violence, fear, and blame — the very shadows you sought to escape now live in the open air."

    console.print(Panel(
        f"[bold red]{reason}[/bold red]\n\n"
        f"[italic]Perhaps the cave was not the prison. Perhaps the prison was the belief\n"
        f"that freedom could be given rather than grown.[/italic]",
        title="[bold red]The Republic Falls[/bold red]",
        border_style="red",
        padding=(1, 2),
    ))


def show_npc_roster(npcs: list) -> None:
    """Show the current NPCs."""
    table = Table(title="Your People", box=box.ROUNDED, border_style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Impression")
    table.add_column("Role", style="cyan")

    for npc in npcs:
        if npc.alive:
            table.add_row(npc.name, npc.description, npc.role or "—")

    console.print(table)
