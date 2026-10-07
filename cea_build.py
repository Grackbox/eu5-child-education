"""Builds the EU5 mod "Child Education" into the local mod folder.

* An alert (through the Community Mod Framework alert bar) for children on the balanced education or none yet:
  1.4 dropped the game's own alert for the dynasty's children.
* Settings in the CMF mod menu: the alert on/off, which children count, and automatic education.
* Kipsta's education fix (Paradox forum, "Education bugged, all characters now idiots") goes into a mod of its own,
  so it can be used without the alert.
"""
import json
import os
import re
import shutil

OUT = os.path.expanduser("~/Documents/Paradox Interactive/Europa Universalis V/mod/child_education_alert")
FIX_OUT = os.path.expanduser("~/Documents/Paradox Interactive/Europa Universalis V/mod/education_fix_kipsta")
GAME = r"E:\SteamLibrary\steamapps\common\Europa Universalis V\game"   # the vanilla character window is patched from here
CMF = r"E:\SteamLibrary\steamapps\workshop\content\3450310\3692202776"   # Community Mod Framework, for its alert tooltip fix
LANGS = ["english", "russian", "german", "french", "spanish", "braz_por", "polish", "turkish", "japanese", "korean", "simp_chinese"]

PAID_TRIGGER = """# Scope: character. Has a trait the player picked for the paid in-depth education.
cea_wants_paid_education = {
	OR = {
PAID_TRAITS	}
}
"""

TRIGGERS = """# Scope: character, root is the country. A child the alert and the auto-education look at, by the "who" setting:
# 1 (default) heirs in the line of succession, and the children and grandchildren of anyone in the line, men only unless
# the "women" setting is on;
# 2 every child of the ruler's dynasty at court.
cea_is_tracked_child = {
	is_alive = yes
	is_adult = no
	age_in_years >= 3		# EDUCATION_AGE and CHILD_TRAIT_AGE in the game's defines: before 3 there is no education and no child trait yet
	owner ?= root
	# "women" off: boys only, whichever children the "who" setting picks
	trigger_if = {
		limit = { NOT = { has_global_variable = cea_women } }
		is_female = no
	}
	# "future_royals": only those still in the crown estate once the first heir rules. The game puts the ruler and the
	# ruler's close relatives in that estate; the rest become nobles.
	trigger_if = {
		limit = { has_global_variable = cea_future_royals }
		root = { exists = heir }
		OR = {
			this = root.heir
			is_close_relative = root.heir
		}
	}
	# the heirs and their children and grandchildren count with either option; "all" (2) adds the ruler's dynasty and
	# the ruler's own children and grandchildren, who may be of another dynasty (a daughter's children)
	OR = {
		cea_is_counted_heir = yes
		any_parent = { cea_is_counted_heir = yes }
		any_parent = {
			any_parent = { cea_is_counted_heir = yes }
		}
		AND = {
			global_var:cea_who ?= 2
			OR = {
				AND = {
					exists = dynasty
					root.ruler ?= { exists = dynasty }
					dynasty = root.ruler.dynasty
				}
				any_parent = { this = root.ruler }
				any_parent = {
					any_parent = { this = root.ruler }
				}
			}
		}
	}
}

# Scope: character, root is the country. In the first "depth" places of the line of succession; with "all" (2), anywhere in it.
cea_is_counted_heir = {
	# the first heir is told by is_heir: the game may count the places from 0, which left that heir's children out
	OR = {
		is_heir = yes
		AND = {
			heir_position > 0
			# "all" (2) counts every place: "places in line" is greyed out then, so it must not count
			OR = {
				global_var:cea_who ?= 2
				heir_position <= global_var:cea_depth
			}
		}
	}
}

# Scope: character. Gets the balanced education or none yet.
cea_can_have_better_education = {
	OR = {
		has_child_education = balanced_education
		has_child_education_selected = no
	}
}
"""

EFFECTS = """# Scope: country. Runs $effect$ on every child the settings track: the ruler's dynasty, and the heir's family
# when the heir is of another dynasty.
cea_for_each_tracked_child = {
	every_character = {
		limit = {
			owner ?= root
			cea_is_tracked_child = yes
		}
		$effect$ = yes
	}
}

# Scope: character. The education of the best of its skills.
cea_set_best_skill_education = {
	if = {
		limit = {
			adm >= dip
			adm >= mil
		}
		set_child_education = child_education:administrative_education
	}
	else_if = {
		limit = { dip >= mil }
		set_child_education = child_education:diplomatic_education
	}
	else = {
		set_child_education = child_education:military_education
	}
}

# Scope: character. The education its child trait points to; a two-skill trait takes the higher of its two skills,
# any other child the best of its skills.
cea_set_trait_education = {
	if = {
		limit = { has_trait = child_intelligent }
		set_child_education = child_education:administrative_education
	}
	else_if = {
		limit = { has_trait = child_gregarious }
		set_child_education = child_education:diplomatic_education
	}
	else_if = {
		limit = { has_trait = child_rowdy }
		set_child_education = child_education:military_education
	}
	else_if = {
		limit = { has_trait = child_ambitious }
		if = {
			limit = { adm >= dip }
			set_child_education = child_education:administrative_education
		}
		else = {
			set_child_education = child_education:diplomatic_education
		}
	}
	else_if = {
		limit = { has_trait = child_gallant }
		if = {
			limit = { dip >= mil }
			set_child_education = child_education:diplomatic_education
		}
		else = {
			set_child_education = child_education:military_education
		}
	}
	else_if = {
		limit = { has_trait = child_shrewd }
		if = {
			limit = { mil >= adm }
			set_child_education = child_education:military_education
		}
		else = {
			set_child_education = child_education:administrative_education
		}
	}
	else = {
		cea_set_best_skill_education = yes
	}
}

# Scope: character. Auto-education: first the paid in-depth education for the picked traits (paid like the game does,
# skipped when the country can't afford it), then the "auto" setting: 2 by traits, 3 administrative, 4 diplomatic,
# 5 military.
cea_auto_educate = {
	# cea_waits_for_paid marks a child that got a cheaper education only because the paid one wasn't affordable; it is
	# moved to the paid one once it is, while educations the player chose stay untouched
	if = {
		limit = {
			OR = {
				cea_can_have_better_education = yes
				has_variable = cea_waits_for_paid
			}
			cea_wants_paid_education = yes
			root = { can_pay_price = price:select_expensive_child_education }
		}
		root = { pay_price = price:select_expensive_child_education }
		set_child_education = child_education:expensive_in_depth_education
		if = {
			limit = { has_variable = cea_waits_for_paid }
			remove_variable = cea_waits_for_paid
		}
	}
	# else: the new education only shows once the effect is done, so a separate check here would still see the old
	# one and replace the paid education just set
	else_if = {
		limit = { cea_can_have_better_education = yes }
		if = {
			limit = { cea_wants_paid_education = yes }
			set_variable = { name = cea_waits_for_paid value = yes }
		}
		if = {
			limit = { global_var:cea_auto ?= 3 }
			set_child_education = child_education:administrative_education
		}
		else_if = {
			limit = { global_var:cea_auto ?= 4 }
			set_child_education = child_education:diplomatic_education
		}
		else_if = {
			limit = { global_var:cea_auto ?= 5 }
			set_child_education = child_education:military_education
		}
		else_if = {
			limit = { global_var:cea_auto ?= 2 }
			cea_set_trait_education = yes
		}
	}
}

# Scope: character. Marks the country when this child could get a better education.
cea_flag_if_needs_education = {
	if = {
		limit = { cea_can_have_better_education = yes }
		root = {
			set_variable = { name = cea_found value = yes }
			change_variable = { name = cea_n add = 1 }
		}
		# the first 8 children are listed in the alert's tooltip, and its clicks open their cards in turn
		save_temporary_scope_as = cea_kid
				if = {
				limit = { root = { var:cea_n ?= 1 } }
				root = { set_variable = { name = cea_child_1 value = scope:cea_kid } }
			}
			else_if = {
				limit = { root = { var:cea_n ?= 2 } }
				root = { set_variable = { name = cea_child_2 value = scope:cea_kid } }
			}
			else_if = {
				limit = { root = { var:cea_n ?= 3 } }
				root = { set_variable = { name = cea_child_3 value = scope:cea_kid } }
			}
			else_if = {
				limit = { root = { var:cea_n ?= 4 } }
				root = { set_variable = { name = cea_child_4 value = scope:cea_kid } }
			}
			else_if = {
				limit = { root = { var:cea_n ?= 5 } }
				root = { set_variable = { name = cea_child_5 value = scope:cea_kid } }
			}
			else_if = {
				limit = { root = { var:cea_n ?= 6 } }
				root = { set_variable = { name = cea_child_6 value = scope:cea_kid } }
			}
			else_if = {
				limit = { root = { var:cea_n ?= 7 } }
				root = { set_variable = { name = cea_child_7 value = scope:cea_kid } }
			}
			else_if = {
				limit = { root = { var:cea_n ?= 8 } }
				root = { set_variable = { name = cea_child_8 value = scope:cea_kid } }
			}
	}
}

# Scope: country. Points cea_current at the next listed child (wrapping round); the alert's click opens it.
cea_advance_current = {
	change_variable = { name = cea_idx add = 1 }
	if = {
		limit = { var:cea_idx > var:cea_n_listed }
		set_variable = { name = cea_idx value = 1 }
	}
	if = {
		limit = { var:cea_idx ?= 1 }
		set_variable = { name = cea_current value = var:cea_child_1 }
	}
	else_if = {
		limit = { var:cea_idx ?= 2 }
		set_variable = { name = cea_current value = var:cea_child_2 }
	}
	else_if = {
		limit = { var:cea_idx ?= 3 }
		set_variable = { name = cea_current value = var:cea_child_3 }
	}
	else_if = {
		limit = { var:cea_idx ?= 4 }
		set_variable = { name = cea_current value = var:cea_child_4 }
	}
	else_if = {
		limit = { var:cea_idx ?= 5 }
		set_variable = { name = cea_current value = var:cea_child_5 }
	}
	else_if = {
		limit = { var:cea_idx ?= 6 }
		set_variable = { name = cea_current value = var:cea_child_6 }
	}
	else_if = {
		limit = { var:cea_idx ?= 7 }
		set_variable = { name = cea_current value = var:cea_child_7 }
	}
	else_if = {
		limit = { var:cea_idx ?= 8 }
		set_variable = { name = cea_current value = var:cea_child_8 }
	}
}

# Scope: country. Forgets last month's list.
cea_clear_list = {
	set_variable = { name = cea_n value = 0 }
	set_variable = { name = cea_idx value = 0 }
	if = { limit = { exists = var:cea_child_1 } remove_variable = cea_child_1 }
	if = { limit = { exists = var:cea_child_2 } remove_variable = cea_child_2 }
	if = { limit = { exists = var:cea_child_3 } remove_variable = cea_child_3 }
	if = { limit = { exists = var:cea_child_4 } remove_variable = cea_child_4 }
	if = { limit = { exists = var:cea_child_5 } remove_variable = cea_child_5 }
	if = { limit = { exists = var:cea_child_6 } remove_variable = cea_child_6 }
	if = { limit = { exists = var:cea_child_7 } remove_variable = cea_child_7 }
	if = { limit = { exists = var:cea_child_8 } remove_variable = cea_child_8 }
	if = { limit = { exists = var:cea_current } remove_variable = cea_current }
}

# Scope: country. Copies the settings into the variables this mod reads.
# Scope: the country the CMF menu reads and writes (it calls cmf_on_callback there). The settings are copied into
# global variables: the monthly check runs on the player's country, which need not be the one holding the menu's values.
cea_copy_bool = {
	set_local_variable = { name = cea_tmp_flag value = flag:$setting$ }
	if = {
		limit = { "variable_map(cmm|local_var:cea_tmp_flag)" >= 1 }
		set_global_variable = { name = $alias$ value = yes }
	}
	else_if = {
		limit = { has_global_variable = $alias$ }
		remove_global_variable = $alias$
	}
}

cea_copy_value = {
	set_local_variable = { name = cea_tmp_flag value = flag:$setting$ }
	set_global_variable = { name = $alias$ value = "variable_map(cmm|local_var:cea_tmp_flag)" }
}

cea_sync_settings = {
	cea_copy_bool = { setting = cea__alert_enabled alias = cea_alert_enabled }
	cea_copy_value = { setting = cea__who alias = cea_who }
	cea_copy_value = { setting = cea__depth alias = cea_depth }
	cea_copy_bool = { setting = cea__women alias = cea_women }
	cea_copy_bool = { setting = cea__future_royals alias = cea_future_royals }
	cea_copy_value = { setting = cea__auto alias = cea_auto }
PAID_SYNC}

# Scope: country. The settings in the CMF mod menu.
cea_register_cmf_mod = {
	cmm_register_bool_setting = { mod_id = cea setting_id = alert_enabled tab_id = settings group_id = settings default_value = 1 }
	cmm_register_dropdown_setting = { mod_id = cea setting_id = who tab_id = settings group_id = settings default_index = 1 option_count = 2 }
	cmm_register_slider_setting = { mod_id = cea setting_id = depth tab_id = settings group_id = settings default_value = 3 min_value = 1 max_value = 20 step_value = 1 }
	cmm_add_scripted_gui = { mod_id = cea setting_id = depth }
	cmm_register_bool_setting = { mod_id = cea setting_id = women tab_id = settings group_id = settings default_value = 0 }
	cmm_register_bool_setting = { mod_id = cea setting_id = future_royals tab_id = settings group_id = settings default_value = 0 }
	cmm_register_dropdown_setting = { mod_id = cea setting_id = auto tab_id = settings group_id = settings default_index = 1 option_count = 5 }
PAID_REGISTER	cea_sync_settings = yes
}
"""

ON_ACTIONS = """cmf_on_mod_registration = {
	on_actions = {
		cea_on_register_cmf_mod
	}
}

cea_on_register_cmf_mod = {
	effect = {
		cea_register_cmf_mod = yes
	}
}

# CMF calls this on the country holding the menu's values whenever a setting changes (also on a reset)
cmf_on_callback = {
	on_actions = {
		cea_on_cmf_callback
	}
}

cea_on_cmf_callback = {
	effect = {
		cea_sync_settings = yes
	}
}

monthly_country_pulse = {
	on_actions = {
		cea_monthly_check
	}
}

# Auto-education first, then the alert for whoever is left, through the Community Mod Framework alert bar.
# Scope: country
cea_monthly_check = {
	trigger = {
		is_ai = no
	}
	effect = {
		# once per save: earlier versions may have put the alert in CMF's list many times
		if = {
			limit = { NOT = { exists = var:cea_list_cleaned } }
			while = {
				limit = { cmf_is_alert_active = { alert = cea_child_education } }
				cmf_remove_alert = { alert = cea_child_education }
			}
			set_variable = { name = cea_list_cleaned value = yes }
		}
		cea_for_each_tracked_child = { effect = cea_auto_educate }
		if = {
			limit = { exists = var:cea_found }
			remove_variable = cea_found
		}
		cea_clear_list = yes
		cea_for_each_tracked_child = { effect = cea_flag_if_needs_education }
		set_variable = { name = cea_n_listed value = var:cea_n }
		if = {
			limit = { var:cea_n_listed > 8 }
			set_variable = { name = cea_n_listed value = 8 }
		}
		cea_advance_current = yes
		if = {
			limit = {
				has_global_variable = cea_alert_enabled
				exists = var:cea_found
			}
			# shown once while it's up: earlier versions showed it again every month, which may be what left its
			# tooltip empty
			if = {
				limit = { NOT = { cmf_is_alert_active = { alert = cea_child_education } } }
				cmf_set_alert_open_window = { alert = cea_child_education window = cea_open_child }
				cmf_show_alert = { alert = cea_child_education }
			}
		}
		else = {
			cmf_remove_alert = { alert = cea_child_education }
		}
	}
}
"""

# A right click on the education buttons of the character window (the action row and the icon in the header) opens our
# page of the CMF mod menu, as Construction Manager does on its auto-expand row. The registration pass runs first, as in
# CMF's own menu button. Kept off when the game has a right click there itself.
OPEN_SETTINGS = """action_tooltip = {
	click_type = right
	click_mode = single
	visible = "[Not(UIActionProvider.IsRightClickVisible)]"
	title = "CEA_OPEN_SETTINGS"
	on_action = "[GetScriptedGui(Select_CString(Or(Not(GameIsMultiplayer), IsHost), 'CMM_SetHostAndRegisterCoreMod', 'CMM_RegisterCoreMod')).Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"
	on_action = "[GetVariableSystem.Set('cmm_window_open', 'true')]"
	on_action = "[GetVariableSystem.Set('cmm_selected_mod', 'cea')]"
	on_action = "[GetVariableSystem.Set('cmm_selected_tab', 'cea__settings')]"
}
"""

PAID = ["child_prodigy", "child_gifted", "healthy", "child_intelligent", "child_gregarious", "child_rowdy",
        "child_ambitious", "child_gallant", "child_shrewd", "child_slow", "child_idiot", "sickly"]   # every trait that changes education

LISTED = 8   # children named in the alert's tooltip

# The CMF alert's click sets the GUI variable cea_open_child; this widget then opens the current child's card and moves on.
WIDGET = """widget = {
	name = "cea_open_child_widget"
	size = { 0 0 }
	datacontext = "[GetPlayer.MakeScope.GetVariable('cea_current').GetCharacter]"
	visible = "[GetVariableSystem.Exists('cea_open_child')]"
	state = {
		name = _show
		next = cea_next_child
		on_start = "[ShowCharacter(Character.Self)]"
	}
	state = {
		name = cea_next_child
		next = cea_done
		on_start = "[GetScriptedGui('cea_show_next_child').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"
	}
	state = {
		name = cea_done
		on_start = "[GetVariableSystem.Clear('cea_open_child')]"
	}
}
"""

SCRIPTED_GUI = """# Scope: country (CMF's home country). "Places in line" is greyed out unless "Who counts" is the heirs option; CMF reads
# is_valid from <mod>__<setting>_on_changed. Not is_shown: hiding the row right under the "Who counts" dropdown re-laid
# the menu out while the dropdown was closing, and it then showed the old option and would not open again.
cea__depth_on_changed = {
	scope = country
	is_valid = {
		NOT = { global_var:cea_who ?= 2 }
	}
}

# Scope: country (CMF's home country). CMF needs this for a list setting: it applies the click, then the settings are
# copied as on any other change.
cea__paid_traits_on_changed = {
	scope = country
	effect = {
		cmm_apply_list_change = { setting = cea__paid_traits }
		cea_sync_settings = yes
	}
}

# Scope: country. After a click opened a child's card, the next click opens the next one.
cea_show_next_child = {
	effect = {
		cea_advance_current = yes
	}
}
"""

TRAITS = [  # Kipsta's values: (trait, modifier lines, chance base)
    ("child_prodigy", ["character_child_education = 0.8"], 1),
    ("child_gifted", ["character_child_education = 0.6"], 1),
    ("child_slow", ["character_child_education = 0"], 1),
    ("child_idiot", ["character_child_education = -0.3"], 1),
    ("child_intelligent", ["character_adm_child_education = 0.66", "character_dip_child_education = 0.22", "character_mil_child_education = 0.22"], 3),
    ("child_gregarious", ["character_adm_child_education = 0.22", "character_dip_child_education = 0.66", "character_mil_child_education = 0.22"], 3),
    ("child_rowdy", ["character_adm_child_education = 0.22", "character_dip_child_education = 0.22", "character_mil_child_education = 0.66"], 3),
    ("child_ambitious", ["character_adm_child_education = 0.66", "character_dip_child_education = 0.66"], 2),
    ("child_gallant", ["character_dip_child_education = 0.66", "character_mil_child_education = 0.66"], 2),
    ("child_shrewd", ["character_mil_child_education = 0.66", "character_adm_child_education = 0.66"], 2),
]

EDUCATIONS = """# Education fix by Kipsta (Paradox forum, "Education bugged, all characters now idiots"):
# educations give twice the vanilla 1.4 effect.
REPLACE:balanced_education = {
	allow = {
	}
	modifier = {
		character_child_education_modifier = 1
	}
}

REPLACE:administrative_education = {
	allow = {
	}
	modifier = {
		character_child_education_modifier = 0.5
		character_adm_child_education_modifier = 1.5
	}
}

REPLACE:diplomatic_education = {
	allow = {
	}
	modifier = {
		character_child_education_modifier = 0.5
		character_dip_child_education_modifier = 1.5
	}
}

REPLACE:military_education = {
	allow = {
	}
	modifier = {
		character_child_education_modifier = 0.5
		character_mil_child_education_modifier = 1.5
	}
}

REPLACE:expensive_in_depth_education = {
	allow = {
	}
	price_to_select = select_expensive_child_education
	price_to_deselect = deselect_expensive_child_education
	modifier = {
		character_child_education_modifier = 2.0
	}
	country_modifier = {
		court_spending_efficiency = -0.05
	}
}
"""

TEXT = {
    "russian": {
        "cea_name": "Образование детей",
        "cea_desc": "Уведомление о детях, которым можно дать образование получше, и автоматическое образование.",
        "cea__settings_name": "Настройки",
        "cea__settings__settings_name": "Образование детей",
        "cea__settings__settings_desc": "Уведомление и автообразование проверяются раз в месяц.",
        "cea__alert_enabled_name": "Уведомление",
        "cea__alert_enabled_desc": "Показывать уведомление, когда у ребёнка сбалансированное образование или его ещё нет.",
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
        "cea__auto_desc": "Раз в месяц ставит образование детям со сбалансированным образованием или без него. Выбранное вручную не трогает.",
        "cea__auto_option_1_name": "Выключено", "cea__auto_option_1_desc": "Образование выбираете вы.",
        "cea__auto_option_2_name": "По трейтам", "cea__auto_option_2_desc": "Незаурядный ум — административное, коммуникабельность — дипломатическое, непоседливость — военное; честолюбие, благородство и цепкий ум — тот из двух навыков, что выше; остальные — по лучшему навыку.",
        "cea__auto_option_3_name": "Административное", "cea__auto_option_3_desc": "Всем административное образование.",
        "cea__auto_option_4_name": "Дипломатическое", "cea__auto_option_4_desc": "Всем дипломатическое образование.",
        "cea__auto_option_5_name": "Военное", "cea__auto_option_5_desc": "Всем военное образование.",
        "CEA_OPEN_SETTINGS": "Настройки Child Education",
        "cea_child_education_name": "Детям можно дать более качественное образование",
        "cea_child_education_tooltip": "Один или несколько детей получают сбалансированное образование или ещё не начали учиться. "
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
        "cea__alert_enabled_desc": "Show an alert when a child gets the balanced education or none yet.",
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
        "cea__auto_desc": "Once a month, sets an education for children on the balanced education or none. Educations you chose yourself are kept.",
        "cea__auto_option_1_name": "Off", "cea__auto_option_1_desc": "You pick the education.",
        "cea__auto_option_2_name": "By traits", "cea__auto_option_2_desc": "Intelligent: administrative, gregarious: diplomatic, rowdy: military; ambitious, gallant and shrewd: the higher of their two skills; anyone else: the best skill.",
        "cea__auto_option_3_name": "Administrative", "cea__auto_option_3_desc": "An administrative education for every child.",
        "cea__auto_option_4_name": "Diplomatic", "cea__auto_option_4_desc": "A diplomatic education for every child.",
        "cea__auto_option_5_name": "Military", "cea__auto_option_5_desc": "A military education for every child.",
        "CEA_OPEN_SETTINGS": "Child Education settings",
        "cea_child_education_name": "Children can have a better education",
        "cea_child_education_tooltip": "One or more children get the balanced education or haven't started one yet. "
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


def character_window():
    """The vanilla character window with OPEN_SETTINGS on both education buttons."""
    with open(os.path.join(GAME, "in_game", "gui", "character_lateralview.gui"), encoding="utf-8-sig") as fh:
        text = fh.read()
    anchor = re.compile(r'(using = button_action_provider(?:_base)?\n(\t+)datacontext = "\[Character\.GetEducation\]"\n)')
    text, n = anchor.subn(lambda m: m.group(1) + "".join(m.group(2) + line + "\n" for line in OPEN_SETTINGS.splitlines()), text)
    if n != 2:   # a game patch moved the buttons: check the file before building
        raise SystemExit(f"character_lateralview.gui: {n} education buttons found, expected 2")
    return text


def traits():
    out = ["# Education fix by Kipsta (Paradox forum, \"Education bugged, all characters now idiots\"):",
           "# the 1.4 child traits gave too little education, so most children grew up with low skills.", ""]
    for name, mods, base in TRAITS:
        body = "\n".join("\t\t" + m for m in mods)
        out.append(f"REPLACE:{name} = {{\n\tcategory = child\n\tmodifier = {{\n{body}\n\t}}\n\tchance = {{\n\t\tbase = {base}\n\t}}\n}}\n")
    return "\n".join(out)


def main():
    for d in (OUT, FIX_OUT):
        if os.path.isdir(d):
            shutil.rmtree(d)
    # one tab, a row per trait (paid_traits list item n = PAID[n-1]) with a box for boys (field slot 1) and for girls (slot 2)
    paid_traits = "".join(f"\t\tAND = {{\n\t\t\tis_female = {'yes' if x == 'f' else 'no'}\n\t\t\thas_trait = {t}\n"
                          f"\t\t\thas_global_variable = cea_paid{x}_{t}\n\t\t}}\n" for x in "mf" for t in PAID)
    # a scripted trigger has to live with the triggers: in the effects file the game took it for an effect, and as a
    # condition it always passed, so every child got the paid education
    write("in_game/common/scripted_triggers/cea_triggers.txt", TRIGGERS + "\n" + PAID_TRIGGER.replace("PAID_TRAITS", paid_traits))
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
    paid_debug = ""
    paid_state = ""
    effects = EFFECTS.replace("PAID_DEBUG", paid_debug).replace("PAID_TRAITS", paid_traits).replace("PAID_SYNC", paid_sync).replace("PAID_REGISTER", paid_register)
    write("in_game/common/scripted_effects/cea_effects.txt", effects)
    write("in_game/common/on_action/cea_on_actions.txt", ON_ACTIONS.replace("PAID_STATE_LOG", paid_state))
    write("in_game/gui/cea_open_child.gui", WIDGET)
    # @cea_<trait>! in the paid list's row names: the game has no text icons for traits, and a text icon is one picture,
    # so each is the trait's icon put on its background as the character window shows it
    trait_icons()
    write("in_game/gui/cea_trait_texticons.gui", "".join(
        f"texticon = {{\n\ticon = cea_{t}\n\ticonsize = {{\n\t\ttexture = \"gfx/interface/icons/cea_traits/{t}.dds\"\n"
        f"\t\tsize = {{ 28 28 }}\n\t\toffset = {{ 0 7 }}\n\t\tfontsize = 16\n\t}}\n}}\n\n" for t in PAID))
    write("in_game/gui/scripted_widgets/cea_scripted_widgets.txt", "gui/cea_open_child.gui = cea_open_child_widget\n")
    write("in_game/common/scripted_guis/cea_scripted_guis.txt", SCRIPTED_GUI)
    write("in_game/gui/character_lateralview.gui", character_window())
    alerts = cmf_alert_manager()
    if alerts:
        write("in_game/gui/cmf/cmf_alert_manager.gui", alerts)
    write("in_game/common/traits/kef_child_traits_fix.txt", traits(), FIX_OUT)
    write("in_game/common/child_educations/kef_education_fix.txt", EDUCATIONS, FIX_OUT)
    fix_meta = {"name": "Education Fix (Kipsta)", "id": "grackbox.education_fix_kipsta", "version": "1.0.0", "game_id": "eu5",
                "supported_game_version": "1.4.*",
                "short_description": "Kipsta's fix for 1.4 child education: stronger educations and rebalanced child traits.",
                "tags": ["Balance", "1.4"], "relationships": [], "game_custom_data": {}}
    write(".metadata/metadata.json", json.dumps(fix_meta, indent=4, ensure_ascii=False) + "\n", FIX_OUT)
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
    meta = {"name": "Child Education", "id": "grackbox.child_education_alert", "version": "1.0.0", "game_id": "eu5",
            "supported_game_version": "1.4.*",
            "short_description": "Alert and auto-education for heirs and their children.",
            "tags": ["Utilities", "1.4"],
            "relationships": [{"rel_type": "dependency", "id": "community_mod_framework", "display_name": "Community Mod Framework",
                               "resource_type": "mod", "version": "2.*"}],
            "game_custom_data": {}}
    write(".metadata/metadata.json", json.dumps(meta, indent=4, ensure_ascii=False) + "\n")
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "thumbnail.png"), os.path.join(OUT, ".metadata", "thumbnail.png"))
    print("->", OUT)


if __name__ == "__main__":
    main()
