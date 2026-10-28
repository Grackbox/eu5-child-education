"""Builds the EU5 mod "Child Education" into the local mod folder.

* An alert (through the Community Mod Framework alert bar) for children on the balanced education:
  1.4 dropped the game's own alert for the dynasty's children.
* Settings in the CMF mod menu: the alert on/off, which children count, and automatic education.

src/ holds the mod's own files, written into it as they are, except that a line holding only a NAME in capitals is
filled in by the build (the parts made per paid trait). parts/ holds the right click put into the character window.
"""
import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
PARTS = os.path.join(HERE, "parts")
OUT = os.path.expanduser("~/Documents/Paradox Interactive/Europa Universalis V/mod/child_education_alert")
GAME = r"E:\SteamLibrary\steamapps\common\Europa Universalis V\game"   # the vanilla character window is patched from here
CMF = r"E:\SteamLibrary\steamapps\workshop\content\3450310\3692202776"   # Community Mod Framework, for its alert tooltip fix
LANGS = ["english", "russian", "german", "french", "spanish", "braz_por", "polish", "turkish", "japanese", "korean", "simp_chinese"]

PAID = ["child_prodigy", "child_gifted", "healthy", "child_intelligent", "child_gregarious", "child_rowdy",
        "child_ambitious", "child_gallant", "child_shrewd", "child_slow", "child_idiot", "sickly"]   # every trait that changes education

LISTED = 8   # children named in the alert's tooltip

TEXT = {
    "russian": {
        "cea_name": "Образование детей",
        "cea_desc": "Уведомление о детях, которым можно дать образование получше, и автоматическое образование.",
        "cea__settings_name": "Настройки",
        "cea__settings__settings_name": "Образование детей",
        "cea__settings__settings_desc": "Уведомление и автообразование проверяются раз в месяц.",
        "cea__alert_enabled_name": "Уведомление",
        "cea__alert_enabled_desc": "Показывать уведомление, когда у ребёнка сбалансированное образование.",
        "cea__who_name": "Кого учитывать",
        "cea__who_desc": "Каких детей учитывают уведомление и автообразование.",
        "cea__who_option_1_name": "Наследники, их дети и внуки",
        "cea__who_option_1_desc": "Наследники из первых мест очереди престолонаследия (сколько — задаёт «Мест в очереди»), их дети и внуки.",
        "cea__who_option_2_name": "Все дети семьи при дворе",
        "cea__who_option_2_desc": "Все наследники из очереди при нашем дворе, их дети и внуки, а также вся династия правителя и его дети и внуки, даже из другой династии.",
        "cea__depth_name": "Мест в очереди",
        "cea__depth_desc": "Сколько первых мест очереди престолонаследия учитывать. Только для варианта с наследниками, в остальных неактивно. Например, 3: первые три наследника, мужчины из них и их дети и внуки.",
        "cea__women_name": "Учитывать женщин",
        "cea__women_desc": "Учитывать также девочек. Выключено — только мальчики. Действует на уведомление, автообразование и платное образование, при любом варианте «Кого учитывать».",
        "cea__future_royals_name": "Только будущее сословие правителей",
        "cea__future_royals_desc": "Сужает выбор «Кого учитывать»: из выбранных там детей остаются только те, кто будет в сословии правителей, когда править начнёт первый в очереди, — он сам и его близкие родственники (дети, внуки, братья и сёстры, племянники, родители, дяди и тёти). Например, дети его братьев и сестёр остаются, а двоюродные братья и сёстры и их дети отсеиваются: при смене правителя они станут дворянами.",
        "cea__auto_name": "Автообразование",
        "cea__auto_desc": "Раз в месяц ставит образование детям со сбалансированным образованием. Выбранное вручную не трогает.",
        "cea__auto_option_1_name": "Выключено", "cea__auto_option_1_desc": "Образование выбираете вы.",
        "cea__auto_option_2_name": "По трейтам", "cea__auto_option_2_desc": "Незаурядный ум — административное, коммуникабельность — дипломатическое, непоседливость — военное; честолюбие, благородство и цепкий ум — тот из двух навыков, что выше; остальные — по лучшему навыку.",
        "cea__auto_option_3_name": "Административное", "cea__auto_option_3_desc": "Всем административное образование.",
        "cea__auto_option_4_name": "Дипломатическое", "cea__auto_option_4_desc": "Всем дипломатическое образование.",
        "cea__auto_option_5_name": "Военное", "cea__auto_option_5_desc": "Всем военное образование.",
        "CEA_OPEN_SETTINGS": "Настройки Child Education",
        "cea_child_education_name": "Детям можно дать более качественное образование",
        "cea_child_education_tooltip": "Один или несколько детей получают сбалансированное образование. "
                                       "Административное, дипломатическое или военное образование быстрее развивает навык.\\n\\n"
                                       "Клик открывает карточки детей по очереди. Кого учитывать, задаётся в меню модов. Проверяется раз в месяц.",
    },
    "english": {
        "cea_name": "Child Education",
        "cea_desc": "Alert for children who could get a better education, and automatic education.",
        "cea__settings_name": "Settings",
        "cea__settings__settings_name": "Child Education",
        "cea__settings__settings_desc": "The alert and the auto-education are checked once a month.",
        "cea__alert_enabled_name": "Alert",
        "cea__alert_enabled_desc": "Show an alert when a child is on the balanced education.",
        "cea__who_name": "Who counts",
        "cea__who_desc": "Which children the alert and the auto-education look at.",
        "cea__who_option_1_name": "Heirs, their children and grandchildren",
        "cea__who_option_1_desc": "Heirs in the first places of the line of succession (as many as Places in line), their children and grandchildren.",
        "cea__who_option_2_name": "All family children at court",
        "cea__who_option_2_desc": "Every heir in the line at our court, their children and grandchildren, plus the ruler's dynasty and the ruler's children and grandchildren, even of another dynasty.",
        "cea__depth_name": "Places in line",
        "cea__depth_desc": "How many first places of the line of succession count. Only for the heirs option; greyed out otherwise. For example 3: the first three heirs, the men among them, and their children and grandchildren.",
        "cea__women_name": "Include women",
        "cea__women_desc": "Also count girls. Off: boys only. Applies to the alert, the auto-education and the paid education, with either Who counts option.",
        "cea__future_royals_name": "Future royals only",
        "cea__future_royals_desc": "Narrows Who counts: of the children it picks, only those stay who will be in the crown estate once the first heir rules, the heir and the heir's close relatives (children, grandchildren, siblings, nephews and nieces, parents, aunts and uncles). For example, the children of the heir's siblings stay, while the heir's cousins and their children drop out: they become nobles when the ruler changes.",
        "cea__auto_name": "Auto-education",
        "cea__auto_desc": "Once a month, sets an education for children on the balanced education. Educations you chose yourself are kept.",
        "cea__auto_option_1_name": "Off", "cea__auto_option_1_desc": "You pick the education.",
        "cea__auto_option_2_name": "By traits", "cea__auto_option_2_desc": "Intelligent: administrative, gregarious: diplomatic, rowdy: military; ambitious, gallant and shrewd: the higher of their two skills; anyone else: the best skill.",
        "cea__auto_option_3_name": "Administrative", "cea__auto_option_3_desc": "An administrative education for every child.",
        "cea__auto_option_4_name": "Diplomatic", "cea__auto_option_4_desc": "A diplomatic education for every child.",
        "cea__auto_option_5_name": "Military", "cea__auto_option_5_desc": "A military education for every child.",
        "CEA_OPEN_SETTINGS": "Child Education settings",
        "cea_child_education_name": "Children can have a better education",
        "cea_child_education_tooltip": "One or more children are on the balanced education. "
                                       "An administrative, diplomatic or military education makes that skill grow faster.\\n\\n"
                                       "A click opens the children's cards in turn. Who counts is set in the mod menu. Checked once a month.",
    },
}
COMMON = {  # flag names CMF looks up, and the alert's icon and colour
    "cea__alert_enabled": "cea__alert_enabled", "cea__who": "cea__who", "cea__depth": "cea__depth", "cea__women": "cea__women", "cea__future_royals": "cea__future_royals", "cea__auto": "cea__auto",
    "cea__depth_format": "[CMMV('cea__depth')]",
    "cea_child_education_icon": "@heir!", "cea_child_education_color": "green",
}


def write(path, text, root=None):
    full = os.path.join(root or OUT, *path.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8-sig", newline="\n") as fh:
        fh.write(text)


def part(name):
    """A file of parts/."""
    with open(os.path.join(PARTS, name), encoding="utf-8-sig") as fh:
        return fh.read()


def build_src(fills):
    """Writes every file of src/ into the mod. `fills` maps a file to {NAME: text}: the file's line holding only NAME
    becomes that text."""
    for folder, _, files in os.walk(SRC):
        for name in files:
            path = os.path.relpath(os.path.join(folder, name), SRC).replace(os.sep, "/")
            with open(os.path.join(folder, name), encoding="utf-8-sig") as fh:
                text = fh.read()
            for key, value in fills.pop(path, {}).items():
                text, n = re.subn(rf"^{key}\n", lambda m: value, text, flags=re.M)
                if n != 1:
                    raise SystemExit(f"src/{path}: {n} lines {key}, expected one")
            write(path, text)
    if fills:
        raise SystemExit("not in src/: " + ", ".join(fills))


def cmf_alert_manager():
    """CMF's alert bar with the alert tooltip reading the alert key from Scope, or None once CMF has fixed it.

    CMF 2.5.0 passes the key through the text context into CString, which sometimes stays empty: the tooltip then reads
    "_name" and "_tooltip" (reported as community-mod-framework issue 16). Our mod loads after CMF (it depends on it),
    so this copy replaces CMF's file; drop it once CMF ships the fix.
    """
    with open(os.path.join(CMF, "in_game", "gui", "cmf", "cmf_alert_manager.gui"), encoding="utf-8-sig") as fh:
        text = fh.read()
    if "CString" not in text:
        print("CMF's alert tooltip no longer uses CString: the cmf_alert_manager.gui fix is left out")
        return None
    hook = ('                lowpriotextcontext =  "[Scope.GetFlagName]"\n'
            '                ontextcontextchanged = "[SetCStringFromTextContext(PdxGuiWidget.AccessSelf)]"\n')
    if text.count(hook) != 1 or text.count("CString.GetString") != 2:   # CMF changed the file: check it before building
        raise SystemExit("cmf_alert_manager.gui: the alert tooltip is not where the fix expects it")
    return text.replace(hook, "").replace("CString.GetString", "Scope.GetFlagName")


def trait_icons():
    """Each paid trait's icon on its background (green for child traits, red for health ones), as uncompressed DDS."""
    from PIL import Image   # only the build needs Pillow
    src = os.path.join(GAME, "main_menu", "gfx", "interface", "icons", "traits")
    for t in PAID:
        bg = "health" if t in ("healthy", "sickly") else "child"
        icon = Image.open(os.path.join(src, "background", f"{bg}_background.dds")).convert("RGBA").resize((128, 128), Image.LANCZOS)
        icon.alpha_composite(Image.open(os.path.join(src, f"{t}.dds")).convert("RGBA").resize((88, 88), Image.LANCZOS), (20, 20))
        full = os.path.join(OUT, "in_game", "gfx", "interface", "icons", "cea_traits", f"{t}.dds")
        os.makedirs(os.path.dirname(full), exist_ok=True)
        icon.save(full)


# A right click on the education buttons of the character window (the action row and the icon in the header) opens our
# page of the CMF mod menu, as Construction Manager does on its auto-expand row. The registration pass runs first, as in
# CMF's own menu button. Kept off when the game has a right click there itself.
def character_window():
    """The vanilla character window with parts/open_settings.gui on both education buttons."""
    with open(os.path.join(GAME, "in_game", "gui", "character_lateralview.gui"), encoding="utf-8-sig") as fh:
        text = fh.read()
    anchor = re.compile(r'(using = button_action_provider(?:_base)?\n(\t+)datacontext = "\[Character\.GetEducation\]"\n)')
    text, n = anchor.subn(lambda m: m.group(1) + "".join(m.group(2) + line + "\n" for line in part("open_settings.gui").splitlines()), text)
    if n != 2:   # a game patch moved the buttons: check the file before building
        raise SystemExit(f"character_lateralview.gui: {n} education buttons found, expected 2")
    return text


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    # one tab, a row per trait (paid_traits list item n = PAID[n-1]) with a box for boys (field slot 1) and for girls (slot 2)
    paid_traits = "".join(f"\t\tAND = {{\n\t\t\tis_female = {'yes' if x == 'f' else 'no'}\n\t\t\thas_trait = {t}\n"
                          f"\t\t\thas_global_variable = cea_paid{x}_{t}\n\t\t}}\n" for x in "mf" for t in PAID)
    paid_sync = "".join(f"\tcea_copy_bool = {{ setting = cea__paid_traits_i{n}_f{slot} alias = cea_paid{x}_{t} }}\n"
                        for slot, x in ((1, "m"), (2, "f")) for n, t in enumerate(PAID, 1))
    # earlier versions had a tab per sex with a box per trait (cea__paidm_<trait>, cea__paidf_<trait>): their ticks are
    # moved into the list once per save
    paid_moved = "".join(f"\t\tif = {{\n\t\t\tlimit = {{\n\t\t\t\tis_key_in_variable_map = {{ name = cmm target = flag:cea__paid{x}_{t} }}\n"
                         f"\t\t\t\t\"variable_map(cmm|flag:cea__paid{x}_{t})\" >= 1\n\t\t\t}}\n"
                         f"\t\t\tcmm_set_list_field_value = {{ mod_id = cea setting_id = paid_traits field_id = {field} item = {n} value = 1 }}\n\t\t}}\n"
                         for field, x in (("boys", "m"), ("girls", "f")) for n, t in enumerate(PAID, 1))
    paid_register = (f"\tcmm_register_settings_list = {{ mod_id = cea setting_id = paid_traits tab_id = paid item_count = {len(PAID)} is_ordered = 0 }}\n"
                     "\tcmm_register_list_bool_field = { mod_id = cea setting_id = paid_traits field_id = boys default_value = 0 }\n"
                     "\tcmm_register_list_bool_field = { mod_id = cea setting_id = paid_traits field_id = girls default_value = 0 }\n"
                     "\tif = {\n\t\tlimit = { NOT = { has_variable = cea_paid_moved } }\n" + paid_moved +
                     "\t\tset_variable = { name = cea_paid_moved value = yes }\n\t}\n")
    # a scripted trigger has to live with the triggers: in the effects file the game took it for an effect, and as a
    # condition it always passed, so every child got the paid education
    build_src({
        "in_game/common/scripted_triggers/cea_triggers.txt": {"PAID_TRAITS": paid_traits},
        "in_game/common/scripted_effects/cea_effects.txt": {"PAID_SYNC": paid_sync, "PAID_REGISTER": paid_register},
    })
    # @cea_<trait>! in the paid list's row names: the game has no text icons for traits, and a text icon is one picture,
    # so each is the trait's icon put on its background as the character window shows it
    trait_icons()
    write("in_game/gui/cea_trait_texticons.gui", "".join(
        f"texticon = {{\n\ticon = cea_{t}\n\ticonsize = {{\n\t\ttexture = \"gfx/interface/icons/cea_traits/{t}.dds\"\n"
        f"\t\tsize = {{ 28 28 }}\n\t\toffset = {{ 0 7 }}\n\t\tfontsize = 16\n\t}}\n}}\n\n" for t in PAID))
    write("in_game/gui/character_lateralview.gui", character_window())
    alerts = cmf_alert_manager()
    if alerts:
        write("in_game/gui/cmf/cmf_alert_manager.gui", alerts)
    for lang in LANGS:
        lines = dict(TEXT.get(lang, TEXT["english"]), **COMMON)
        ru = lang == "russian"
        paid_desc = ("Детям с отмеченными чертами раз в месяц ставится дорогое углублённое образование, с оплатой как в игре. Если денег не хватает, ставится обычное по настройке «Автообразование», а платное — когда деньги появятся. Работает и при выключенном автообразовании."
                     if ru else "Children with the checked traits get the expensive in-depth education once a month, paid as in the game. If the country can't afford it, the Auto-education setting applies, and the paid one once it can. Works even with auto-education off.")
        lines["cea__paid_name"] = "Платное образование" if ru else "Paid education"
        for key in ("cea__paid__paid_traits", "cea__paid_traits"):
            lines[f"{key}_name"] = "Дорогое углублённое образование" if ru else "Expensive in-depth education"
            lines[f"{key}_desc"] = paid_desc
        lines["cea__paid_traits"] = "cea__paid_traits"
        lines["cea__paid_traits_item_column_name"] = "Черта" if ru else "Trait"
        for field, ru_name, ru_whom, en_n in (("boys", "Мальчики", "мальчикам", "boys"), ("girls", "Девочки", "девочкам", "girls")):
            lines[f"cea__paid_traits__{field}_name"] = ru_name if ru else en_n.capitalize()
            lines[f"cea__paid_traits__{field}_desc"] = f"Платное образование {ru_whom} с этой чертой." if ru else f"Paid education for {en_n} with this trait."
        # the children's names, as links to them
        lines["cea_child_education_tooltip"] += "\\n" + "".join(
            f"[AddLocalizationIf(GetPlayer.MakeScope.GetVariable('cea_child_{k}').IsSet, 'CEA_CHILD_{k}')]" for k in range(1, LISTED + 1))
        for k in range(1, LISTED + 1):
            lines[f"CEA_CHILD_{k}"] = f"\\n• [GetPlayer.MakeScope.GetVariable('cea_child_{k}').GetCharacter.GetName]"
        for n, t in enumerate(PAID, 1):
            lines[f"cea__paid_traits_i{n}_name"] = f"@cea_{t}! [ShowTraitName('{t}')]"
        write(f"main_menu/localization/{lang}/cea_l_{lang}.yml",
              f"l_{lang}:\n" + "".join(f' {k}: "{v}"\n' for k, v in lines.items()))
    meta = {"name": "Child Education [LOCAL]", "id": "grackbox.child_education_alert", "version": "1.0.2", "game_id": "eu5",
            "supported_game_version": "1.4.*",
            "short_description": "Alert and auto-education for heirs and their children.",
            "tags": ["Utilities", "1.4"],
            "relationships": [{"rel_type": "dependency", "id": "community_mod_framework", "display_name": "Community Mod Framework",
                               "resource_type": "mod", "version": "2.*"}],
            "game_custom_data": {}}
    write(".metadata/metadata.json", json.dumps(meta, indent=4, ensure_ascii=False) + "\n")
    shutil.copy(os.path.join(HERE, "thumbnail.png"), os.path.join(OUT, ".metadata", "thumbnail.png"))
    print("->", OUT)


if __name__ == "__main__":
    main()
