"""Builds the EU5 mod "Child Education" into the local mod folder.

* An alert (through the Community Mod Framework alert bar) for children on the balanced education or none yet:
  1.4 dropped the game's own alert for the dynasty's children.
* Settings in the CMF mod menu: the alert on/off, which children count, and automatic education.
* Kipsta's education fix (Paradox forum, "Education bugged, all characters now idiots") goes into a mod of its own,
  so it can be used without the alert.
"""
import json
import os
import shutil

OUT = os.path.expanduser("~/Documents/Paradox Interactive/Europa Universalis V/mod/child_education_alert")
FIX_OUT = os.path.expanduser("~/Documents/Paradox Interactive/Europa Universalis V/mod/education_fix_kipsta")
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

# Scope: character, root is the country. In the first "depth" places of the line of succession.
cea_is_counted_heir = {
	# the first heir is told by is_heir: the game may count the places from 0, which left that heir's children out
	OR = {
		is_heir = yes
		AND = {
			heir_position > 0
			heir_position <= global_var:cea_depth
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

SCRIPTED_GUI = """# Scope: country. After a click opened a child's card, the next click opens the next one.
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
        "cea__who_option_1_desc": "Наследники из очереди престолонаследия, их дети и внуки. Женщины — по настройке «Учитывать женщин».",
        "cea__who_option_2_name": "Все дети семьи при дворе",
        "cea__who_option_2_desc": "Наследники, их дети и внуки, а также вся династия правителя и его дети и внуки, даже из другой династии.",
        "cea__depth_name": "Мест в очереди",
        "cea__depth_desc": "Сколько первых мест очереди престолонаследия учитывать (для варианта с наследниками). Например, 3: первые три наследника, мужчины из них и их дети и внуки.",
        "cea__women_name": "Учитывать женщин",
        "cea__women_desc": "Учитывать также девочек. Выключено — только мальчики. Действует на уведомление, автообразование и платное образование, при любом варианте «Кого учитывать».",
        "cea__future_royals_name": "Только будущее сословие правителей",
        "cea__future_royals_desc": "Учитывать только тех, кто останется в сословии правителей, когда править начнёт первый в очереди: его самого и его близких родственников (детей, внуков, братьев и сестёр, племянников, родителей, дядь и тёть). Остальные при смене правителя станут дворянами.",
        "cea__auto_name": "Автообразование",
        "cea__auto_desc": "Раз в месяц ставит образование детям со сбалансированным образованием или без него. Выбранное вручную не трогает.",
        "cea__auto_option_1_name": "Выключено", "cea__auto_option_1_desc": "Образование выбираете вы.",
        "cea__auto_option_2_name": "По трейтам", "cea__auto_option_2_desc": "Незаурядный ум — административное, коммуникабельность — дипломатическое, непоседливость — военное; честолюбие, благородство и цепкий ум — тот из двух навыков, что выше; остальные — по лучшему навыку.",
        "cea__auto_option_3_name": "Административное", "cea__auto_option_3_desc": "Всем административное образование.",
        "cea__auto_option_4_name": "Дипломатическое", "cea__auto_option_4_desc": "Всем дипломатическое образование.",
        "cea__auto_option_5_name": "Военное", "cea__auto_option_5_desc": "Всем военное образование.",
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
        "cea__who_option_1_desc": "Heirs in the line of succession, their children and grandchildren. Women only with Include women on.",
        "cea__who_option_2_name": "All family children at court",
        "cea__who_option_2_desc": "The heirs, their children and grandchildren, plus the ruler's dynasty and the ruler's children and grandchildren, even of another dynasty.",
        "cea__depth_name": "Places in line",
        "cea__depth_desc": "How many first places of the line of succession count (for the heirs option). For example 3: the first three heirs, the men among them, and their children and grandchildren.",
        "cea__women_name": "Include women",
        "cea__women_desc": "Also count girls. Off: boys only. Applies to the alert, the auto-education and the paid education, with either Who counts option.",
        "cea__future_royals_name": "Future royals only",
        "cea__future_royals_desc": "Count only those who stay in the crown estate once the first heir rules: the heir and the heir's close relatives (children, grandchildren, siblings, nephews and nieces, parents, aunts and uncles). The rest become nobles when the ruler changes.",
        "cea__auto_name": "Auto-education",
        "cea__auto_desc": "Once a month, sets an education for children on the balanced education or none. Educations you chose yourself are kept.",
        "cea__auto_option_1_name": "Off", "cea__auto_option_1_desc": "You pick the education.",
        "cea__auto_option_2_name": "By traits", "cea__auto_option_2_desc": "Intelligent: administrative, gregarious: diplomatic, rowdy: military; ambitious, gallant and shrewd: the higher of their two skills; anyone else: the best skill.",
        "cea__auto_option_3_name": "Administrative", "cea__auto_option_3_desc": "An administrative education for every child.",
        "cea__auto_option_4_name": "Diplomatic", "cea__auto_option_4_desc": "A diplomatic education for every child.",
        "cea__auto_option_5_name": "Military", "cea__auto_option_5_desc": "A military education for every child.",
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
    # a box per trait and per sex: tab paid_m for boys, paid_f for girls
    paid_traits = "".join(f"\t\tAND = {{\n\t\t\tis_female = {'yes' if x == 'f' else 'no'}\n\t\t\thas_trait = {t}\n"
                          f"\t\t\thas_global_variable = cea_paid{x}_{t}\n\t\t}}\n" for x in "mf" for t in PAID)
    # a scripted trigger has to live with the triggers: in the effects file the game took it for an effect, and as a
    # condition it always passed, so every child got the paid education
    write("in_game/common/scripted_triggers/cea_triggers.txt", TRIGGERS + "\n" + PAID_TRIGGER.replace("PAID_TRAITS", paid_traits))
    paid_sync = "".join(f"\tcea_copy_bool = {{ setting = cea__paid{x}_{t} alias = cea_paid{x}_{t} }}\n" for x in "mf" for t in PAID)
    paid_register = "".join(f"\tcmm_register_bool_setting = {{ mod_id = cea setting_id = paid{x}_{t} tab_id = paid_{x} group_id = paid_{x} default_value = 0 }}\n"
                            for x in "mf" for t in PAID)
    paid_debug = ""
    paid_state = ""
    effects = EFFECTS.replace("PAID_DEBUG", paid_debug).replace("PAID_TRAITS", paid_traits).replace("PAID_SYNC", paid_sync).replace("PAID_REGISTER", paid_register)
    write("in_game/common/scripted_effects/cea_effects.txt", effects)
    write("in_game/common/on_action/cea_on_actions.txt", ON_ACTIONS.replace("PAID_STATE_LOG", paid_state))
    write("in_game/gui/cea_open_child.gui", WIDGET)
    write("in_game/gui/scripted_widgets/cea_scripted_widgets.txt", "gui/cea_open_child.gui = cea_open_child_widget\n")
    write("in_game/common/scripted_guis/cea_scripted_guis.txt", SCRIPTED_GUI)
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
        for x, ru_n, en_n in (("m", "мальчики", "boys"), ("f", "девочки", "girls")):
            lines[f"cea__paid_{x}_name"] = f"Платное: {ru_n}" if ru else f"Paid: {en_n}"
            lines[f"cea__paid_{x}__paid_{x}_name"] = (f"Платное углублённое образование: {ru_n}" if ru else f"Expensive in-depth education: {en_n}")
            lines[f"cea__paid_{x}__paid_{x}_desc"] = paid_desc
        # the children's names, as links to them
        lines["cea_child_education_tooltip"] += "\\n" + "".join(
            f"[AddLocalizationIf(GetPlayer.MakeScope.GetVariable('cea_child_{k}').IsSet, 'CEA_CHILD_{k}')]" for k in range(1, LISTED + 1))
        for k in range(1, LISTED + 1):
            lines[f"CEA_CHILD_{k}"] = f"\\n• [GetPlayer.MakeScope.GetVariable('cea_child_{k}').GetCharacter.GetName]"
        for x in "mf":
            for t in PAID:
                lines[f"cea__paid{x}_{t}"] = f"cea__paid{x}_{t}"
                lines[f"cea__paid{x}_{t}_name"] = f"[ShowTraitName('{t}')]"
                lines[f"cea__paid{x}_{t}_desc"] = ("Платное образование детям с чертой" if ru else "Paid education for children with") + f" ${t}$."
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
    print("->", OUT)


if __name__ == "__main__":
    main()
