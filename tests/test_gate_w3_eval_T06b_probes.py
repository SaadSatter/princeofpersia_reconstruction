"""Gate 2 (Evaluation Specialist) probes for T06b: can the other seat learn a rig?"""

from __future__ import annotations

from pop import arena
from pop.versus import VersusEpisode


def episode(a, b, disguised_b=False, disguised_a=False):
    e = VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=a, B=b), 0, guard_posts=None)
    e._duel.rivals["B"].disguised = disguised_b
    e._duel.rivals["A"].disguised = disguised_a
    return e


def test_a_disguised_jump_that_changes_the_others_rig_legality_is_visible_in_that_view():
    """RIG legality reads the other seat's landing cell (`claimed`). A disguised
    jumper's landing must therefore already be shown as motion, or legality would
    tell a guard from a disguised rival."""
    shown = 0
    for bcol in range(2, 10):
        for jump in ("JUMP_LEFT", "RUN_JUMP_LEFT"):
            for acol in range(0, 8):
                e = episode((2, 0, acol, +1), (2, 0, bcol, -1), disguised_b=True)
                c = episode((2, 0, acol, +1), (2, 0, bcol, -1), disguised_b=True)
                if not e.step("B", jump)["accepted"]:
                    continue
                for t in range(40):
                    e.tick(); c.tick()
                    if e.legal_actions("A") != c.legal_actions("A"):
                        figs = e.observe("A")["figures"]
                        b_cell_unchanged = figs and (figs[0]["row"], figs[0]["col"]) == (0, bcol)
                        if b_cell_unchanged:           # still mid-flight, not landed
                            assert figs[0]["motion"] is not None, (bcol, jump, acol, t)
                            shown += 1
                        break
    assert shown > 5


def test_an_undisguised_kneel_is_visible_with_facing_but_a_disguised_one_is_not_and_the_tile_never_changes():
    """Documents TRAPS_SPEC 'does not see which cell': facing plus the visible kneel
    already point at the cell ahead for an undisguised rival (a human sees the same)."""
    for disguised in (False, True):
        e = episode((2, 0, 1, +1), (2, 0, 8, -1), disguised_a=disguised)
        before = e.observe("B")["tiles"]
        assert e.step("A", "RIG")["accepted"]
        for _ in range(4):
            e.tick()
        fig = e.observe("B")["figures"][0]
        if disguised:
            assert fig["kind"] == "guard" and fig["motion"] is None
        else:
            assert fig["kind"] == "rival" and fig["motion"]["effect"] == "kneeled"
        for _ in range(20):
            e.tick()
        assert e.observe("B")["tiles"] == before
