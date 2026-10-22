"""Large ASCII art matrices for bonsai trees in a ceramic pot.
All arts are strictly 29 columns wide and 13 lines high.
"""
from vimgarden.enums import GrowthStage, HealthState

POT_BASE: list[str] = [
    "  [=======================]  ",
    "   \\                     /   ",
    "    \\__===_________===__/    ",
]

EMPTY_POT: list[str] = [
    "                             ",
    "                             ",
    "                             ",
    "                             ",
    "                             ",
    "                             ",
    "                             ",
    "                             ",
    "                             ",
    "          . ~ . ~ .          ",
] + POT_BASE


def _pad_art(lines: list[str]) -> list[str]:
    """Ensure all lines are strictly 29 characters wide."""
    result = []
    for line in lines:
        if len(line) < 29:
            line = line.ljust(29)
        elif len(line) > 29:
            line = line[:29]
        result.append(line)
    return result


# Juniper Bonsai
JUNIPER_ART: dict[GrowthStage, dict[HealthState, list[str]]] = {
    GrowthStage.SEED: {
        HealthState.HEALTHY: _pad_art([
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "             \\|/             ",
            "             |||             ",
            "          . ~ . ~ .          ",
        ] + POT_BASE),
        HealthState.THIRSTY: _pad_art([
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "             -|-             ",
            "             |||             ",
            "          . - . - .          ",
        ] + POT_BASE),
        HealthState.WILTING: _pad_art([
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "             /|\\             ",
            "             |||             ",
            "          . ~ . ~ .          ",
        ] + POT_BASE),
        HealthState.DEAD: _pad_art([
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "             \\x/             ",
            "             |||             ",
            "          . x . x .          ",
        ] + POT_BASE),
    },
    GrowthStage.SPROUT: {
        HealthState.HEALTHY: _pad_art([
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "            .---.            ",
            "           ( @@@ )           ",
            "            '\\|/'            ",
            "             _||_            ",
            "            / || \\           ",
            "          . ~ . ~ .          ",
        ] + POT_BASE),
        HealthState.THIRSTY: _pad_art([
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "            .---.            ",
            "           ( ~~~ )           ",
            "            '-|-'            ",
            "             _||_            ",
            "            / || \\           ",
            "          . - . - .          ",
        ] + POT_BASE),
        HealthState.WILTING: _pad_art([
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "            .   .            ",
            "           ( ... )           ",
            "            '/|\\'            ",
            "             _||_            ",
            "            / || \\           ",
            "          . ~ . ~ .          ",
        ] + POT_BASE),
        HealthState.DEAD: _pad_art([
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "            . x .            ",
            "           ( xxx )           ",
            "            '\\x/'            ",
            "             _||_            ",
            "            / || \\           ",
            "          . x . x .          ",
        ] + POT_BASE),
    },
    GrowthStage.ADULT: {
        HealthState.HEALTHY: _pad_art([
            "                             ",
            "            .@@@.            ",
            "         .@@@@@@@@.          ",
            "       .@@@@@@@@@@@@.        ",
            "      (@@@@)  '\\@@@@)        ",
            "       '--'   / || \\         ",
            "            .-' || '-.       ",
            "           / .--||--. \\      ",
            "             '--||--'        ",
            "          . ~ . ||. ~ .      ",
        ] + POT_BASE),
        HealthState.THIRSTY: _pad_art([
            "                             ",
            "            .---.            ",
            "         .~~~~~~~~.          ",
            "       .~~~~~~~~~~~~.        ",
            "      (~~~~)  '\\~~~~)        ",
            "       '--'   / || \\         ",
            "            .-' || '-.       ",
            "           / .--||--. \\      ",
            "             '--||--'        ",
            "          . - . ||. - .      ",
        ] + POT_BASE),
        HealthState.WILTING: _pad_art([
            "                             ",
            "            . : .            ",
            "         . :::::: .          ",
            "       . : : : : : :.        ",
            "      ( :  )  '\\:   )        ",
            "       '--'   / || \\         ",
            "            .-' || '-.       ",
            "           / .--||--. \\      ",
            "             '--||--'        ",
            "          . . . ||. . .      ",
        ] + POT_BASE),
        HealthState.DEAD: _pad_art([
            "                             ",
            "            . x .            ",
            "         . xxxxxxx .         ",
            "       . x x x x x x.        ",
            "      ( x  )  '\\x   )        ",
            "       '--'   / || \\         ",
            "            .-' || '-.       ",
            "           / .--||--. \\      ",
            "             '--||--'        ",
            "          . x . ||. x .      ",
        ] + POT_BASE),
    },
    GrowthStage.MATURE: {
        HealthState.HEALTHY: _pad_art([
            "          _ . - - . _        ",
            "      . '  @@@@@@@@@  ' .    ",
            "    (  @@@@@@@@@@@@@@@@@  )  ",
            "   ( @@@@@@@@@@@@@@@@@@@@@ ) ",
            "    (@@@@@@)    (@@@@@@@@)   ",
            "      '--'  \\  /   '---'     ",
            "           .-'/\\'-.          ",
            "         / .-'  '-. \\        ",
            "           '--||--'          ",
            "          . ~ ||  . ~ .      ",
        ] + POT_BASE),
        HealthState.THIRSTY: _pad_art([
            "          _ . - - . _        ",
            "      . '  ~~~~~~~~~  ' .    ",
            "    (  ~~~~~~~~~~~~~~~~~  )  ",
            "   ( ~~~~~~~~~~~~~~~~~~~~~ ) ",
            "    (~~~~~~)    (~~~~~~~~)   ",
            "      '--'  \\  /   '---'     ",
            "           .-'/\\'-.          ",
            "         / .-'  '-. \\        ",
            "           '--||--'          ",
            "          . - ||  . - .      ",
        ] + POT_BASE),
        HealthState.WILTING: _pad_art([
            "          _ .     . _        ",
            "      . '  : : : : :  ' .    ",
            "    (  : : : : : : : : :  )  ",
            "   ( : : : : : : : : : : : ) ",
            "    ( : :  )    ( : : :  )   ",
            "      '--'  \\  /   '---'     ",
            "           .-'/\\'-.          ",
            "         / .-'  '-. \\        ",
            "           '--||--'          ",
            "          . . ||  . . .      ",
        ] + POT_BASE),
        HealthState.DEAD: _pad_art([
            "          _ .  x  . _        ",
            "      . '  x x x x x  ' .    ",
            "    (  x x x x x x x x x  )  ",
            "   ( x x x x x x x x x x x ) ",
            "    ( x x  )    ( x x x  )   ",
            "      '--'  \\  /   '---'     ",
            "           .-'/\\'-.          ",
            "         / .-'  '-. \\        ",
            "           '--||--'          ",
            "          . x ||  . x .      ",
        ] + POT_BASE),
    },
}

# Sakura Bonsai
SAKURA_ART: dict[GrowthStage, dict[HealthState, list[str]]] = {
    GrowthStage.SEED: JUNIPER_ART[GrowthStage.SEED],
    GrowthStage.SPROUT: {
        HealthState.HEALTHY: _pad_art([
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "            .***.            ",
            "           ( *o* )           ",
            "            '\\|/'            ",
            "             _||_            ",
            "            / || \\           ",
            "          . ~ . ~ .          ",
        ] + POT_BASE),
        HealthState.THIRSTY: JUNIPER_ART[GrowthStage.SPROUT][HealthState.THIRSTY],
        HealthState.WILTING: JUNIPER_ART[GrowthStage.SPROUT][HealthState.WILTING],
        HealthState.DEAD:    JUNIPER_ART[GrowthStage.SPROUT][HealthState.DEAD],
    },
    GrowthStage.ADULT: {
        HealthState.HEALTHY: _pad_art([
            "                             ",
            "            .*o*.            ",
            "         .***o*****o.        ",
            "       .o************.       ",
            "      (***o)  '\\**o*)        ",
            "       '--'   / || \\         ",
            "            .-' || '-.       ",
            "           / .--||--. \\      ",
            "             '--||--'        ",
            "          . ~ . ||. ~ .      ",
        ] + POT_BASE),
        HealthState.THIRSTY: JUNIPER_ART[GrowthStage.ADULT][HealthState.THIRSTY],
        HealthState.WILTING: JUNIPER_ART[GrowthStage.ADULT][HealthState.WILTING],
        HealthState.DEAD:    JUNIPER_ART[GrowthStage.ADULT][HealthState.DEAD],
    },
    GrowthStage.MATURE: {
        HealthState.HEALTHY: _pad_art([
            "          _ . * o * . _      ",
            "      . '  *o*o*o*o*  ' .    ",
            "    (  *o***o*o***o*o***  )  ",
            "   ( **o****************o* ) ",
            "    (**o***)    (*o******)   ",
            "      '--'  \\  /   '---'     ",
            "           .-'/\\'-.          ",
            "         / .-'  '-. \\        ",
            "           '--||--'          ",
            "          . ~ ||  . ~ .      ",
        ] + POT_BASE),
        HealthState.THIRSTY: JUNIPER_ART[GrowthStage.MATURE][HealthState.THIRSTY],
        HealthState.WILTING: JUNIPER_ART[GrowthStage.MATURE][HealthState.WILTING],
        HealthState.DEAD:    JUNIPER_ART[GrowthStage.MATURE][HealthState.DEAD],
    },
}

# Maple Bonsai
MAPLE_ART: dict[GrowthStage, dict[HealthState, list[str]]] = {
    GrowthStage.SEED: JUNIPER_ART[GrowthStage.SEED],
    GrowthStage.SPROUT: {
        HealthState.HEALTHY: _pad_art([
            "                             ",
            "                             ",
            "                             ",
            "                             ",
            "            .vvv.            ",
            "           ( v#v )           ",
            "            '\\|/'            ",
            "             _||_            ",
            "            / || \\           ",
            "          . ~ . ~ .          ",
        ] + POT_BASE),
        HealthState.THIRSTY: JUNIPER_ART[GrowthStage.SPROUT][HealthState.THIRSTY],
        HealthState.WILTING: JUNIPER_ART[GrowthStage.SPROUT][HealthState.WILTING],
        HealthState.DEAD:    JUNIPER_ART[GrowthStage.SPROUT][HealthState.DEAD],
    },
    GrowthStage.ADULT: {
        HealthState.HEALTHY: _pad_art([
            "                             ",
            "            .v#v.            ",
            "         .vvv#vvvvvv.        ",
            "       .vvvvvvv#vvvvv.       ",
            "      (vvvv)  '\\#vvv)        ",
            "       '--'   / || \\         ",
            "            .-' || '-.       ",
            "           / .--||--. \\      ",
            "             '--||--'        ",
            "          . ~ . ||. ~ .      ",
        ] + POT_BASE),
        HealthState.THIRSTY: JUNIPER_ART[GrowthStage.ADULT][HealthState.THIRSTY],
        HealthState.WILTING: JUNIPER_ART[GrowthStage.ADULT][HealthState.WILTING],
        HealthState.DEAD:    JUNIPER_ART[GrowthStage.ADULT][HealthState.DEAD],
    },
    GrowthStage.MATURE: {
        HealthState.HEALTHY: _pad_art([
            "          _ . v # v . _      ",
            "      . '  v#vv#vv#v  ' .    ",
            "    (  vvv#vvvvv#vvvvvvv  )  ",
            "   ( vvvv#vvvvvvvvvv#vvvvv ) ",
            "    (vvvvvv)    (vvv#vvvv)   ",
            "      '--'  \\  /   '---'     ",
            "           .-'/\\'-.          ",
            "         / .-'  '-. \\        ",
            "           '--||--'          ",
            "          . ~ ||  . ~ .      ",
        ] + POT_BASE),
        HealthState.THIRSTY: JUNIPER_ART[GrowthStage.MATURE][HealthState.THIRSTY],
        HealthState.WILTING: JUNIPER_ART[GrowthStage.MATURE][HealthState.WILTING],
        HealthState.DEAD:    JUNIPER_ART[GrowthStage.MATURE][HealthState.DEAD],
    },
}

# Pine Bonsai
PINE_ART: dict[GrowthStage, dict[HealthState, list[str]]] = {
    GrowthStage.SEED: JUNIPER_ART[GrowthStage.SEED],
    GrowthStage.SPROUT: JUNIPER_ART[GrowthStage.SPROUT],
    GrowthStage.ADULT: {
        HealthState.HEALTHY: _pad_art([
            "                             ",
            "            /\\/\\/            ",
            "         /\\/\\/\\/\\/\\/\\        ",
            "       /\\/\\/\\/\\/\\/\\/\\/\\      ",
            "      <\\/\\/>  '\\<\\/\\>        ",
            "       '--'   / || \\         ",
            "            .-' || '-.       ",
            "           / .--||--. \\      ",
            "             '--||--'        ",
            "          . ~ . ||. ~ .      ",
        ] + POT_BASE),
        HealthState.THIRSTY: JUNIPER_ART[GrowthStage.ADULT][HealthState.THIRSTY],
        HealthState.WILTING: JUNIPER_ART[GrowthStage.ADULT][HealthState.WILTING],
        HealthState.DEAD:    JUNIPER_ART[GrowthStage.ADULT][HealthState.DEAD],
    },
    GrowthStage.MATURE: {
        HealthState.HEALTHY: _pad_art([
            "          _ /\\/\\/\\/\\_        ",
            "      . '  /\\/\\/\\/\\/  ' .    ",
            "    (  /\\/\\/\\/\\/\\/\\/\\/\\/  )  ",
            "   ( /\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/ ) ",
            "    </\\/\\/>    <\\/\\/\\/\\>     ",
            "      '--'  \\  /   '---'     ",
            "           .-'/\\'-.          ",
            "         / .-'  '-. \\        ",
            "           '--||--'          ",
            "          . ~ ||  . ~ .      ",
        ] + POT_BASE),
        HealthState.THIRSTY: JUNIPER_ART[GrowthStage.MATURE][HealthState.THIRSTY],
        HealthState.WILTING: JUNIPER_ART[GrowthStage.MATURE][HealthState.WILTING],
        HealthState.DEAD:    JUNIPER_ART[GrowthStage.MATURE][HealthState.DEAD],
    },
}

PLANT_ART: dict[str, dict[GrowthStage, dict[HealthState, list[str]]]] = {
    "juniper": JUNIPER_ART,
    "sakura": SAKURA_ART,
    "maple": MAPLE_ART,
    "pine": PINE_ART,
}


def get_plant_art(type_id: str, stage: GrowthStage, health: HealthState) -> list[str]:
    """Retrieve 29x13 art for bonsai tree type, stage, and health."""
    plant_dict = PLANT_ART.get(type_id, JUNIPER_ART)
    stage_dict = plant_dict.get(stage, plant_dict[GrowthStage.MATURE])
    return stage_dict.get(health, stage_dict[HealthState.HEALTHY])
