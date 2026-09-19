import time

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_server_state import server_state, server_state_lock

#------------------------------
# CONTROLS AND SETUP
#------------------------------

st.set_page_config(page_title="D&D Initiative Tracker", layout="wide", initial_sidebar_state="collapsed")

if "view_mode" not in st.session_state:
    st.session_state.view_mode = False

if "ini_mode" not in st.session_state:
    st.session_state.ini_mode = False
    
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

with st.sidebar:
    st.title("⚙️ Modes")
    mode = st.radio("Select Mode", ["Player Mode", "DM Mode", "Initiative Mode", "Edit Mode"], key="mode_radio")
    if mode == "Player Mode":
        st.session_state.edit_mode = False
        st.session_state.view_mode = False
        st.session_state.ini_mode = False
    elif mode == "DM Mode":
        st.session_state.edit_mode = False
        st.session_state.view_mode = True
        st.session_state.ini_mode = False
    elif mode == "Initiative Mode":
        st.session_state.edit_mode = False
        st.session_state.view_mode = False
        st.session_state.ini_mode = True
    elif mode == "Edit Mode":
        st.session_state.edit_mode = True
        st.session_state.view_mode = False
        st.session_state.ini_mode = False
    
    #mode = st.toggle("DM Mode", key="view_mode")
    #ini_mode = st.toggle("Initiative Mode", key="ini_mode")
    
#------------------------------
# INITIALIZATION
#------------------------------

dnd_conditions = [
    "Blessed", "Blinded", "Bleeding", "Charmed", "Concentrating", "Cursed",
    "Deafened", "Enlarged", "Exhausted", "Frightened", "Grappled", "Hastened",
    "Hexed", "Hunter's Mark", "Incapacitated", "Invisible", "Magical Effect",
    "Paralyzed", "Petrified", "Poisoned", "Prone", "Raging", "Reduced",
    "Restrained", "Stunned", "Unconscious"
]

condition_symbols = {
    "Blessed": "😇", "Blinded": "👁️", "Bleeding": "🩸", "Charmed": "💕", "Concentrating": "🔮",
    "Cursed": "☠️", "Deafened": "👂", "Enlarged": "🔼", "Exhausted": "🥱", "Frightened": "😱",
    "Grappled": "🤼", "Hastened": "⚡", "Hexed": "🕸️", "Hunter's Mark": "🎯", "Incapacitated": "🛑",
    "Invisible": "👻", "Magical Effect": "✨", "Paralyzed": "🧍‍♂️","Petrified": "🗿", "Poisoned": "🤢",
    "Prone": "🧎", "Raging": "🔥", "Reduced": "🔽", "Restrained": "⛓️", "Stunned": "💫", "Unconscious": "😴",
}

condition_colors = {
    "Blessed": "red", "Blinded": "orange", "Bleeding": "yellow", "Charmed": "blue", "Concentrating": "green",
    "Cursed": "violet", "Deafened": "red", "Enlarged": "orange", "Exhausted": "yellow", "Frightened": "blue",
    "Grappled": "green", "Hastened": "violet", "Hexed": "red", "Hunter's Mark": "orange", "Incapacitated": "yellow",
    "Invisible": "blue", "Magical Effect": "green", "Paralyzed": "violet", "Petrified": "red", "Poisoned": "orange",
    "Prone": "yellow", "Raging": "blue", "Reduced": "green", "Restrained": "violet", "Stunned": "red", "Unconscious": "orange",
}

dnd_conditions_display = [f"{condition_symbols[condition]} {condition}" for condition in dnd_conditions]

@st.cache_data
def initialize_pool():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Characters", ttl="0")
    df["Armor Class"] = df["Armor Class"].astype(int)
    df["Hitpoints"] = df["Hitpoints"].astype(int)
    df["ID"] = df["ID"].astype(int)
    return df.to_dict('records')

initial_pool = initialize_pool()

if "pool" not in server_state:
    with server_state_lock["pool"]:
        server_state.pool = pd.DataFrame(initial_pool)

if "dmpool" not in server_state:
    with server_state_lock["dmpool"]:
        server_state.dmpool = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints"])

if "creature_temp_pool" not in server_state:
    with server_state_lock["creature_temp_pool"]:
        server_state.creature_temp_pool = []

if "initiative_list" not in server_state:
    with server_state_lock["initiative_list"]:
        server_state.initiative_list = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints", "Initiative", "Indicator", "Conditions"])

if "new_character" not in st.session_state:
        st.session_state.new_character = {"Name": "", "Armor Class": 10, "Hitpoints": 10}

if "initiative" not in server_state:
    with server_state_lock["initiative"]:
        server_state.initiative = 0
        
if "prev_ini" not in server_state:
    with server_state_lock["prev_ini"]:
        server_state.prev_ini = []
        
if "prev_ini_list" not in server_state:
    with server_state_lock["prev_ini_list"]:
        server_state.prev_ini_list = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints", "Initiative", "Indicator", "Conditions"])

if "ini_pressed" not in st.session_state:
    st.session_state.ini_pressed = False
    
if "edit_hp_values" not in st.session_state:
    st.session_state.edit_hp_values = {}
    
if "current_round" not in server_state:
    with server_state_lock["current_round"]:
        server_state.current_round = 1
        
if "show_input" not in st.session_state:
    st.session_state.show_input = False
    
if "verification" not in st.session_state:
    st.session_state.verification = ""

if not st.session_state.ini_mode and not st.session_state.view_mode and not st.session_state.edit_mode:
    st.header("Character Selection")
    col1, col2 = st.columns([0.25, 0.5])
    with col1:
        character_names = ["All"] + list(server_state.pool["Name"])
        selected_character = st.selectbox("Choose your character:", character_names, key="character_select", filter_mode=None)
    
    if selected_character != "All":
        filtered_pool = server_state.pool[server_state.pool["Name"] == selected_character]
    else:
        filtered_pool = server_state.pool
        
if not st.session_state.ini_mode and st.session_state.view_mode and not st.session_state.edit_mode:
    st.header("Creature Selection")
    col1, col2 = st.columns([0.25, 0.5])
    with col1:
        creature_names = ["All"] + list(server_state.dmpool["Name"])
        selected_creature = st.selectbox("Choose your creature:", creature_names, key="creature_select")
    
    if selected_creature != "All":
        filtered_dmpool = server_state.dmpool[server_state.dmpool["Name"] == selected_creature]
    else:
        filtered_dmpool = server_state.dmpool

if "autosave_timer" not in server_state:
    with server_state_lock["autosave_timer"]:
        server_state.autosave_timer = None
        
if "delete_mode" not in st.session_state:
    st.session_state.delete_mode = False
    
if "symbol_mode" not in st.session_state:
    st.session_state.symbol_mode = False

#------------------------------
# FUNCTIONS
#------------------------------

@st.fragment(run_every=60)
def autosave():
    with server_state_lock["autosave_timer"]:
        if server_state.autosave_timer is None:
            return
        if time.time() - server_state.autosave_timer < 60:
            return
        with server_state_lock["initiative_list"]:
            if server_state.initiative_list.empty:
                return
            ini_df = server_state.initiative_list.copy()
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(data=ini_df, worksheet="Initiative")
        server_state.autosave_timer = time.time()

def normalize_dmpool():
    with server_state_lock["dmpool"]:
        server_state.dmpool.sort_values(by="Name", inplace=True, key=lambda x: x.str.lower())
        server_state.dmpool.reset_index(drop=True, inplace=True)
        dmpool_first_id = server_state.pool["ID"].max() + 1
        server_state.dmpool["ID"] = range(dmpool_first_id, dmpool_first_id + len(server_state.dmpool))
        server_state.creature_temp_pool = server_state.dmpool.copy(deep=True).to_dict('records')

def save_pools():
    with server_state_lock["dmpool"] and server_state_lock["pool"]:
        normalize_dmpool()
        df_pool = server_state.pool
        df_dmpool = server_state.dmpool
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(data=df_pool, worksheet="Characters")
        time.sleep(0.5)
        conn.update(data=df_dmpool, worksheet="Creatures")
    
@st.dialog("Save Characters", icon="💾", on_dismiss="rerun")
def save_pools_dialog():
    st.write("Please enter the Password")
    password = st.text_input("Password")
    if st.button("Save"):
        if not server_state.initiative_list.empty:
            st.toast("Clear the initiative list before saving.", icon="⚠️", duration=3)
            st.rerun()
        else:
            if password == "Apfeltaschen":
                st.toast("Characters saved successfully!", icon="✅", duration=3)
                save_pools()
                st.rerun()
            else:
                st.toast("Incorrect verification code. Please try again.", icon="❌", duration=3)
                st.rerun()

def load_pools():
    with server_state_lock["pool"] and server_state_lock["dmpool"]:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_pool = conn.read(worksheet="Characters", ttl="0")
        df_dmpool = conn.read(worksheet="Creatures", ttl="0")
        df_pool["Armor Class"] = df_pool["Armor Class"].astype(int)
        df_pool["Hitpoints"] = df_pool["Hitpoints"].astype(int)
        df_pool["ID"] = df_pool["ID"].astype(int)
        df_dmpool["Armor Class"] = df_dmpool["Armor Class"].astype(int)
        df_dmpool["Hitpoints"] = df_dmpool["Hitpoints"].astype(int)
        df_dmpool["ID"] = df_dmpool["ID"].astype(int)
        server_state.pool = df_pool
        server_state.dmpool = df_dmpool
        normalize_dmpool()
        
def load_pools_dialog():
    if not server_state.initiative_list.empty:
        st.toast("Clear the initiative list before loading.", icon="⚠️", duration=3)
    else:
        st.toast("Characters loaded successfully!", icon="✅", duration=3)
        initialize_pool.clear()
        initialize_pool()
        load_pools()

def reset_initiative():
    with server_state_lock["initiative_list"]:
        ini_reset = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints", "Initiative", "Indicator", "Conditions"])
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(data=ini_reset, worksheet="Initiative")
        
def load_initiative():
    with server_state_lock["initiative_list"], server_state_lock["pool"], server_state_lock["dmpool"]:
        conn = st.connection("gsheets", type=GSheetsConnection)
        loaded_ini = conn.read(worksheet="Initiative", ttl="0")
        loaded_ini["Indicator"] = loaded_ini["Indicator"].fillna("")
        loaded_ini["Conditions"] = loaded_ini["Conditions"].fillna("")
        loaded_ini["Armor Class"] = loaded_ini["Armor Class"].astype(int)
        loaded_ini["Hitpoints"] = loaded_ini["Hitpoints"].astype(int)
        loaded_ini["Initiative"] = loaded_ini["Initiative"].astype(int)
        for index, row in loaded_ini.iterrows():
            char_id = row["ID"]
            if isinstance(char_id, str) and char_id[-1] == "C":
                creature_id = int(char_id[:-1])
                server_state.dmpool = server_state.dmpool[server_state.dmpool["ID"] != creature_id]
            else:
                character_id = int(char_id)
                server_state.pool = server_state.pool[server_state.pool["ID"] != character_id]
        server_state.initiative_list = loaded_ini

def add_to_initiative(character_id, initiative):
    with server_state_lock["pool"], server_state_lock["initiative_list"], server_state_lock["initiative"]:
        character = server_state.pool.loc[server_state.pool["ID"] == character_id].iloc[0]
        server_state.pool = server_state.pool[server_state.pool["ID"] != character_id]
        new_row = {"ID": character_id, "Name": character["Name"], "Armor Class": character["Armor Class"], "Hitpoints": character["Hitpoints"], "Initiative": initiative, "Indicator": "", "Conditions": ""}
        server_state.initiative_list = pd.concat(
            [server_state.initiative_list, pd.DataFrame([new_row])], ignore_index=True
        )
        server_state.initiative_list.sort_values(by="Initiative", ascending=False, inplace=True)
    with server_state_lock["autosave_timer"]:
        server_state.autosave_timer = time.time()

def add_creature_to_initiative(creature_id, initiative):
    with server_state_lock["dmpool"], server_state_lock["initiative_list"], server_state_lock["initiative"]:
        creature = server_state.dmpool.loc[server_state.dmpool["ID"] == creature_id].iloc[0]
        server_state.dmpool = server_state.dmpool[server_state.dmpool["ID"] != creature_id]
        new_row = {"ID": str(int(creature_id)) + "C", "Name": creature["Name"], "Armor Class": creature["Armor Class"], "Hitpoints": creature["Hitpoints"], "Initiative": initiative, "Indicator": "", "Conditions": ""}
        server_state.initiative_list = pd.concat(
            [server_state.initiative_list, pd.DataFrame([new_row])], ignore_index=True
        )
        server_state.initiative_list.sort_values(by="Initiative", ascending=False, inplace=True)
        with server_state_lock["autosave_timer"]:
            server_state.autosave_timer = time.time()

def remove_from_initiative(character_id):
    with server_state_lock["pool"], server_state_lock["initiative_list"], server_state_lock["dmpool"]:
        character = server_state.initiative_list.loc[server_state.initiative_list["ID"] == character_id].iloc[0]
        server_state.initiative_list = server_state.initiative_list[server_state.initiative_list["ID"] != character_id]
        for char in initial_pool:
            if char['ID'] == character_id:
                character['Hitpoints'] = char['Hitpoints']
        if isinstance(character_id, str) and character_id[-1] == "C":
            creature_id = int(character_id[:-1])
            for char in server_state.creature_temp_pool:
                if char['ID'] == creature_id:
                    character['Hitpoints'] = char['Hitpoints']
            server_state.dmpool = pd.concat(
                [server_state.dmpool, pd.DataFrame([{"ID": int(character_id[0:-1]), "Name": character["Name"], "Armor Class": character["Armor Class"], "Hitpoints": character["Hitpoints"]}])],
                ignore_index=True,
            )
            server_state.dmpool.sort_values(by="ID", ascending=True, inplace=True)
        else:
            server_state.pool = pd.concat(
                [server_state.pool, pd.DataFrame([{"ID": character_id, "Name": character["Name"], "Armor Class": character["Armor Class"], "Hitpoints": character["Hitpoints"]}])],
                ignore_index=True,
            )
            server_state.pool.sort_values(by="ID", ascending=True, inplace=True)
        if server_state.initiative_list.empty:
            server_state.current_round = 1

def add_new_creature(new_name, new_ac, new_hp, new_amount):
    with server_state_lock["dmpool"], server_state_lock["pool"], server_state_lock["initiative_list"]:
        id_initiative_list = server_state.initiative_list["ID"].apply(lambda x: int(x.rstrip("C")) if isinstance(x, str) else x)
        id_pool = server_state.pool["ID"]
        id_dmpool = server_state.dmpool["ID"]
        try:
            max_id = pd.concat([id for id in [id_initiative_list, id_pool, id_dmpool] if not id.empty], ignore_index=True).dropna().max()
        except ValueError:
            max_id = 0
        new_id = int(max_id) + 1
        for i in range(new_amount):
            new_row = {"ID": new_id + i, "Name": f"{new_name} {i+1}" if new_amount > 1 else new_name, "Armor Class": new_ac, "Hitpoints": new_hp}
            server_state.dmpool = pd.concat(
                [server_state.dmpool, pd.DataFrame([new_row])], ignore_index=True
            )
        server_state.dmpool.sort_values(by="Name", inplace=True, key=lambda x: x.str.lower())
        server_state.creature_temp_pool.append(new_row)
        
@st.dialog("Add Creature", icon="➕", on_dismiss="rerun")
def add_dialog():
    with st.form("add_creature_form"):
        name = st.text_input("Creature Name")
        ac = st.number_input("Armor Class", min_value=1, max_value=30, value=10)
        hp = st.number_input("Hitpoints", min_value=0, value=10)
        amount = st.number_input("Amount", min_value=1, value=1)
        submitted = st.form_submit_button("Add")
    if submitted:
        add_new_creature(name, ac, hp, amount)
        st.rerun()

def delete_creature(creature_id):
    with server_state_lock["dmpool"]:
        server_state.dmpool = server_state.dmpool.loc[server_state.dmpool["ID"] != creature_id]

def toggle_edit_hp():
    with server_state_lock["initiative_list"]:
        for row_id, hp_change in st.session_state.edit_hp_values.items():
            if row_id is not None and hp_change is not None:
                hitpoints = server_state.initiative_list.loc[server_state.initiative_list["ID"] == row_id, "Hitpoints"]
                if not hitpoints.empty:
                    current_hp = hitpoints.iloc[0]
                    if hp_change < 0 and current_hp <= abs(hp_change):
                        hp_change = 0
                    else:
                        hp_change = current_hp + hp_change
                    server_state.initiative_list.loc[server_state.initiative_list["ID"] == row_id, "Hitpoints"] = hp_change
    for row_id in st.session_state.edit_hp_values:
        st.session_state[f"edit_hp_{row_id}"] = 0

@st.dialog("Edit Initiative", icon="✏️", on_dismiss="rerun")
def edit_initiative(row_id):
    with st.form("edit_initiative_form"):
        new_initiative = st.slider("New Initiative Value", min_value=1, max_value=30)
        submitted = st.form_submit_button("Save")
    if submitted:
        with server_state_lock["initiative_list"]:
            if row_id in server_state.initiative_list["ID"].values:
                server_state.initiative_list.loc[server_state.initiative_list["ID"] == row_id, "Initiative"] = new_initiative
                server_state.initiative_list.sort_values(by="Initiative", ascending=False, inplace=True)
        st.rerun()

def display_conditions(conditions):
    if not conditions:
        return ""
    condition_list = conditions.split(", ")
    if st.session_state.symbol_mode:
        return " ".join(condition_symbols.get(s, s) for s in condition_list)
    return " ".join(
        f":{condition_colors.get(condition, condition)}-badge[{condition}]"
        for condition in condition_list
    )

@st.dialog("Manage Conditions", icon="🧪", on_dismiss="rerun")
def manage_conditions(row_id):
    with st.form("manage_conditions_form"):
        new_conditions = st.multiselect("Conditions:", dnd_conditions_display, key="condition_select", select_all=False, filter_mode=None)
        submitted = st.form_submit_button("Save")
    if submitted:
        with server_state_lock["initiative_list"]:
            if row_id in server_state.initiative_list["ID"].values:
                added_conditions = [condition.split(" ", 1)[1] for condition in new_conditions]
                server_state.initiative_list.loc[server_state.initiative_list["ID"] == row_id, "Conditions"] = ", ".join(added_conditions)
        st.rerun()

def ini_cycle():
    with server_state_lock["initiative"], server_state_lock["initiative_list"]:
        if not server_state.initiative_list.empty:
            server_state.initiative_list.sort_values(by="Initiative", ascending=False, inplace=True)
            if server_state.initiative >= len(server_state.initiative_list):
                server_state.initiative = 0
                server_state.current_round += 1
            if len(server_state.initiative_list) > 2:
                current_character_id = server_state.initiative_list.iloc[server_state.initiative]["ID"] 
                if server_state.initiative + 2 >= len(server_state.initiative_list):
                    if server_state.initiative + 1 == len(server_state.initiative_list):
                        skip_character_id = server_state.initiative_list.iloc[1]["ID"]  
                    else:
                        skip_character_id = server_state.initiative_list.iloc[0]["ID"]
                else:
                    skip_character_id = server_state.initiative_list.iloc[server_state.initiative + 2]["ID"]
                if "previous_character_id" not in server_state:
                    server_state.previous_character_id = None
                if current_character_id == server_state.previous_character_id:
                    server_state.initiative -= 1
                server_state.previous_character_id = skip_character_id
                server_state.next_initiative = server_state.initiative + 1
            else:
                if "next_initiative" not in server_state:
                    server_state.next_initiative = 0
                if server_state.next_initiative == 2:
                    server_state.initiative = 1
                    server_state.next_initiative = 0
                if server_state.next_initiative == 1:
                    server_state.initiative = 0
                    server_state.next_initiative = 0
            if server_state.prev_ini != server_state.initiative_list['ID'].values.tolist():
                server_state.initiative_list = server_state.initiative_list.reset_index(drop=True)
                indicator_id = next((entry[0] for entry in server_state.prev_ini_list if entry[1] == '➤'), None)
                if any('➤' in entry for entry in server_state.initiative_list['Indicator'].values.tolist()):
                    if indicator_id in server_state.initiative_list['ID'].values:
                        for pos, row in server_state.initiative_list.iterrows():
                            if row['ID'] == indicator_id:
                                server_state.initiative = pos + 1
            server_state.initiative_list["Indicator"] = ""
            server_state.initiative = min(server_state.initiative, len(server_state.initiative_list) - 1)
            server_state.initiative_list.iloc[
                server_state.initiative, server_state.initiative_list.columns.get_loc("Indicator")
            ] = '➤'
            for Ident, Indicat in zip(server_state.initiative_list[['ID', 'Indicator']].values.tolist(), server_state.prev_ini_list):
                if Ident[0] == Indicat[0] and Ident[1] == Indicat[1] == '➤':
                    server_state.initiative_list["Indicator"] = ""
                    if len(server_state.initiative_list) > 1:
                        server_state.initiative += 1
                    else:
                        server_state.initiative = 0
                    server_state.initiative_list.iloc[
                    server_state.initiative, server_state.initiative_list.columns.get_loc("Indicator")
                    ] = '➤'
            server_state.initiative += 1
            server_state.prev_ini = server_state.initiative_list['ID'].values.tolist()
            server_state.prev_ini_list = server_state.initiative_list[['ID', 'Indicator']].values.tolist()

autosave()

#------------------------------
# UI - VIEW MODES
#------------------------------

if not st.session_state.ini_mode and not st.session_state.view_mode and not st.session_state.edit_mode:
    st.header("Characters")
    for index, row in filtered_pool.iterrows():
        with st.container(horizontal=True, border=True):
            c1, c2, c3 = st.columns([1, 1, 1], gap="xsmall", vertical_alignment="center")
            c1.markdown(f"<p style='font-size: 20px; text-align: center;'>{row['Name']} (🛡️{row['Armor Class']} | ❤️{row['Hitpoints']})</p>", unsafe_allow_html=True)
            ini_val = c2.slider(
                    "Initiative", 1, 30, key=f"slider_{row['ID']}", label_visibility="collapsed"
                )
            c3.button(
                    f"Enter {row['Name']}",
                    key=f"enter_{row['ID']}",
                    on_click=add_to_initiative,
                    args=(row["ID"], ini_val),
                    width="stretch",
                )

if not st.session_state.ini_mode and st.session_state.view_mode and not st.session_state.edit_mode:
    st.header("Creatures")
    if server_state.dmpool.empty:
        st.info("No creatures currently in the pool. Add creatures below.")
    for index, row in filtered_dmpool.iterrows():
        with st.container(horizontal=True, border=True):
            c1, c2, c3 = st.columns([1, 1, 1], gap="xsmall", vertical_alignment="center")
            c1.markdown(f"<p style='font-size: 20px; text-align: center;'>{row['Name']} <br>(🛡️{row['Armor Class']} | ❤️{row['Hitpoints']})</p>", unsafe_allow_html=True)
            initiative = c2.slider(
                    "Initiative", 1, 30, key=f"slider_{row['ID']}", label_visibility="collapsed"
                )
            if not st.session_state.delete_mode:
                c3.button(
                        f"Enter {row['Name']}",
                        key=f"enter_{row['ID']}",
                        on_click=add_creature_to_initiative,
                        args=(row["ID"], initiative),
                        width="stretch",
                    )
            else:
                c3.button(
                    f"Delete {row['Name']}",
                    key=f"remove_pool_{index}_{row['ID']}",
                    on_click=lambda creature_id=row["ID"]: delete_creature(creature_id),
                    width="stretch",
                )

if st.session_state.ini_mode and not st.session_state.edit_mode:
    st.header("Initiative - Round " + str(server_state.current_round))
    if server_state.initiative_list.empty:
        st.info("No combatants currently in initiative. Add characters or creatures.")
    for index, row in server_state.initiative_list.iterrows():
        with st.container(horizontal=True, border=True):
            c1, c2, c3, c4, c5, c6 = st.columns([0.5, 1.4, 0.4, 0.8, 0.3, 0.6], gap="xsmall", vertical_alignment="center")
            displayed_conditions = display_conditions(row['Conditions'])
            with c1:
                centered = st.container(horizontal=True, horizontal_alignment="center")
                centered.markdown(displayed_conditions)
            with c2:
                if row['Hitpoints'] > 0:
                    st.markdown(f"<p style='font-size: 20px; text-align: center;'>{row['Name']} <br>(🛡️{row['Armor Class']} | ❤️{row['Hitpoints']})</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='font-size: 20px; text-align: center;'>{row['Name']} <br>(🛡️{row['Armor Class']} |💀)</p>", unsafe_allow_html=True)
            c3.markdown(f"<p style='font-size: 30px; text-align: center;'><span style='color: blue;'>{row['Initiative']}</span></p>", unsafe_allow_html=True)
            with c4:
                st.session_state.edit_hp_values[row['ID']] = row["Hitpoints"]
                hp_change = st.number_input(
                    f"Edit HP for {row['Name']}",
                    key=f"edit_hp_{row['ID']}",
                    label_visibility="collapsed",
                    step=1
                )
                st.session_state.edit_hp_values[row['ID']] = hp_change
            with c5:
                st.button("💾", key=f"toggle_edit_hp_{row['ID']}", on_click=toggle_edit_hp, width="stretch")
            with c6:
                action = st.menu_button(
                        "Options",
                        options=["Remove", "Edit Ini", "Conditions"],
                        key=f"action_{index}_{row['ID']}",
                        width="stretch"
                    )
                if action == "Remove":
                    remove_from_initiative(row["ID"])
                if action == "Edit Ini":
                    edit_initiative(row["ID"])
                if action == "Conditions":
                    manage_conditions(row["ID"])

if st.session_state.edit_mode:
    c1, c2 = st.columns(2)
    with c1:
        st.header("**Edit Characters**")
        edited_pool = st.data_editor(server_state.pool, num_rows="dynamic", width="stretch", key="char_pool_editor", column_config={col: st.column_config.Column(alignment="center") for col in server_state.pool.columns})
        if st.button("Save Character Roster Changes"):
            with server_state_lock["pool"]:
                server_state.pool = edited_pool
    with c2:
        st.header("**Edit Creatures**")
        edited_dmpool = st.data_editor(server_state.dmpool, num_rows="dynamic", width="stretch", key="creature_pool_editor", column_config={col: st.column_config.Column(alignment="center") for col in server_state.pool.columns})
        if st.button("Save Creature Pool Changes"):
            with server_state_lock["dmpool"]:
                server_state.dmpool = edited_dmpool

#------------------------------
# FUNCTION - RESET
#------------------------------
    
def reset():
    with server_state_lock["pool"], server_state_lock["initiative_list"], server_state_lock["initiative"], server_state_lock["dmpool"]:
        initialize_pool.clear()
        initialize_pool()
        time.sleep(0.5)
        load_pools()
        time.sleep(0.5)
        reset_initiative()
        time.sleep(0.5)
        server_state.initiative_list = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints", "Initiative", "Indicator", "Conditions"])
        server_state.initiative = 0
        server_state.ini_length = 0
        server_state.next_initiative = 0
        server_state.current_character_id = None
        server_state.previous_character_id = None
        server_state.prev_ini = []
        server_state.prev_ini_list = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints", "Initiative", "Indicator", "Conditions"])
        server_state.current_round = 1
        server_state.autosave_timer = None
        st.toast("Initiative has been reset.", icon="✅", duration=3)

#------------------------------
# UI - BOTTOM MENU
#------------------------------

with st.bottom:
    if st.session_state.ini_mode and not st.session_state.view_mode:
        ini_menu = st.container(horizontal=True, horizontal_alignment="center")
        #if ini_menu.button("Initiative"):
        #    if server_state.initiative_list.empty:
        #        load_initiative()
        #    else:
        #        ini_cycle()
        if not st.session_state.symbol_mode:
            if ini_menu.button("Show Symbols"):
                st.session_state.symbol_mode = True
                st.rerun()
        else:
            if ini_menu.button("Show Text"):
                st.session_state.symbol_mode = False
                st.rerun()
    if not st.session_state.ini_mode and st.session_state.view_mode and not st.session_state.edit_mode:
        dm_menu = st.container(horizontal=True, horizontal_alignment="center")
        if dm_menu.button("Add"):
            add_dialog()
        if dm_menu.button("Save"):
            save_pools_dialog()
        if dm_menu.button("Load"):
            load_pools_dialog()
        if dm_menu.button("Reset"):
            reset()
        if not st.session_state.delete_mode:
            if dm_menu.button("Delete"):
                st.session_state.delete_mode = True
                st.rerun()
        else:
            if dm_menu.button("Enter"):
                st.session_state.delete_mode = False
                st.rerun()
