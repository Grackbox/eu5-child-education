# Child Education (EU5 mod)

`cea_build.py` builds the Europa Universalis V mod Child Education.

## Child Education
Brings back the alert for children who could get a better education (EU5 1.4 dropped it for anyone but the heir),
with automatic education. Needs the Community Mod Framework (alert bar and mod menu).

- Alert on the CMF alert bar listing the children (links to their cards); clicks open their cards in turn.
- Mod menu settings: alert on/off, who counts (heirs in the first N places of the line of succession and their
  children and grandchildren, or the whole family at court), include girls, only the future royal estate,
  auto-education (off / by traits / administrative / diplomatic / military).
- Paid in-depth education per trait, separately for boys and girls; when the country can't afford it, a cheaper
  education is set and switched to the paid one once it can.
- A right click on the education button in the character window (the action row or the icon in the header) opens
  this mod's page of the mod menu. This overrides the vanilla `character_lateralview.gui`, patched at build time from
  the game folder (`GAME` in the script).
- Children under 3 are left alone (the game's `EDUCATION_AGE` and `CHILD_TRAIT_AGE`).

## Build

```
python cea_build.py    # writes mod/child_education_alert in the EU5 mod folder
```

Needs Pillow (`pip install pillow`) and the game folder (`GAME` in the script): the character window and the trait
icons of the paid-education list are built from the game's files.

- `src/`: the mod's script and GUI files as they go into the mod, except that a line holding only a NAME in capitals
  (`PAID_TRAITS`, `PAID_SYNC`, `PAID_REGISTER`) is filled in by the build with the parts made per paid trait.
- `parts/open_settings.gui`: the right click put into the game's character window.

Notes: settings are copied into global variables when CMF calls back on a change, because the menu's country need not be
the player's. Scripted triggers must live in `scripted_triggers/` (in an effects file the game took one for an effect).
