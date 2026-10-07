# Child Education + Education Fix (EU5 mods)

`cea_build.py` builds two Europa Universalis V mods:

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

## Education Fix (Kipsta)
Kipsta's fix from the Paradox forum thread "Education bugged, all characters now idiots": rebalanced child traits and
educations twice as strong as in vanilla 1.4. No dependencies.

## Build

```
python cea_build.py    # writes mod/child_education_alert and mod/education_fix_kipsta in the EU5 mod folder
```

Needs Pillow (`pip install pillow`) and the game folder (`GAME` in the script): the character window and the trait
icons of the paid-education list are built from the game's files.

Notes: settings are copied into global variables when CMF calls back on a change, because the menu's country need not be
the player's. Scripted triggers must live in `scripted_triggers/` (in an effects file the game took one for an effect).
