import streamlit as st
import pandas as pd
from streamlit_server_state import server_state, server_state_lock
import time
from streamlit_gsheets import GSheetsConnection

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "DM"
   
mode = st.toggle("DM Mode")
st.session_state.view_mode = mode

ini_mode = st.toggle("Initiative Mode")
st.session_state.ini_mode = ini_mode

exp_mode = st.toggle("Expert Mode")
st.session_state.exp_mode = exp_mode

st.markdown(
    """
    <style>
    /* General button styling */
    div.stButton > button {
        font-size: 18px;
        padding: 10px 20px;
        border-radius: 8px;
        min-width: 150px;
        min-height: 50px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
        server_state.creature_temp_pool = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints"])

if "initiative_list" not in server_state:
    with server_state_lock["initiative_list"]:
        server_state.initiative_list = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints", "Initiative", "Indicator"])

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
        server_state.prev_ini_list = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints", "Initiative", "Indicator"])
        
if "button_pressed" not in st.session_state:
    st.session_state.button_pressed = False
    
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

if not st.session_state.ini_mode and not st.session_state.view_mode or (st.session_state.view_mode and st.session_state.exp_mode):
    st.header("Character Selection")
    col1, col2 = st.columns([0.25, 0.5])
    with col1:
        character_names = ["All"] + list(server_state.pool["Name"])
        selected_character = st.selectbox("Choose your character:", character_names, key="character_select")
    
    if selected_character != "All":
        filtered_pool = server_state.pool[server_state.pool["Name"] == selected_character]
    else:
        filtered_pool = server_state.pool

def save_character_pool():
    with server_state_lock["pool"]:
        df = server_state.pool
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(data=df, worksheet="Characters")
        
def save_creature_pool():
    with server_state_lock["dmpool"]:
        df = server_state.dmpool
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(data=df, worksheet="Creatures")
        server_state.creature_temp_pool = df.copy(deep=True).to_dict('records')

        
def load_character_pool():
    with server_state_lock["pool"]:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Characters", ttl="0")
        df["Armor Class"] = df["Armor Class"].astype(int)
        df["Hitpoints"] = df["Hitpoints"].astype(int)
        df["ID"] = df["ID"].astype(int)
        server_state.pool = df
        
def load_creature_pool():
    with server_state_lock["dmpool"]:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Creatures", ttl="0")
        df["Armor Class"] = df["Armor Class"].astype(int)
        df["Hitpoints"] = df["Hitpoints"].astype(int)
        df["ID"] = df["ID"].astype(int)
        server_state.dmpool = df
        server_state.creature_temp_pool = df.copy(deep=True).to_dict('records')

def add_to_initiative(character_id, initiative):
    with server_state_lock["pool"], server_state_lock["initiative_list"], server_state_lock["initiative"]:
        character = server_state.pool.loc[server_state.pool["ID"] == character_id].iloc[0]
        server_state.pool = server_state.pool[server_state.pool["ID"] != character_id]
        new_row = {"ID": character_id, "Name": character["Name"], "Armor Class": character["Armor Class"], "Hitpoints": character["Hitpoints"], "Initiative": initiative, "Indicator": ""}
        server_state.initiative_list = pd.concat(
            [server_state.initiative_list, pd.DataFrame([new_row])], ignore_index=True
        )
        server_state.initiative_list.sort_values(by="Initiative", ascending=False, inplace=True)
        
def add_creature_to_initiative(creature_id, initiative):
    with server_state_lock["dmpool"], server_state_lock["initiative_list"], server_state_lock["initiative"]:
        creature = server_state.dmpool.loc[server_state.dmpool["ID"] == creature_id].iloc[0]
        server_state.dmpool = server_state.dmpool[server_state.dmpool["ID"] != creature_id]
        new_row = {"ID": str(creature_id) + "C", "Name": creature["Name"], "Armor Class": creature["Armor Class"], "Hitpoints": creature["Hitpoints"], "Initiative": initiative, "Indicator": ""}
        server_state.initiative_list = pd.concat(
            [server_state.initiative_list, pd.DataFrame([new_row])], ignore_index=True
        )
        server_state.initiative_list.sort_values(by="Initiative", ascending=False, inplace=True)

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

def add_new_creature(new_name, new_ac, new_hp):
    with server_state_lock["dmpool"], server_state_lock["pool"], server_state_lock["initiative_list"]:
        id_initiative_list = server_state.initiative_list["ID"].apply(lambda x: int(x.rstrip("C")) if isinstance(x, str) else x)
        id_pool = server_state.pool["ID"]
        id_dmpool = server_state.dmpool["ID"]
        try:
            max_id = pd.concat([id for id in [id_initiative_list, id_pool, id_dmpool] if not id.empty], ignore_index=True).dropna().max()
        except ValueError:
            max_id = 0
        new_id = max_id + 1
        new_row = {"ID": new_id, "Name": new_name, "Armor Class": new_ac, "Hitpoints": new_hp}
        server_state.dmpool = pd.concat(
            [server_state.dmpool, pd.DataFrame([new_row])], ignore_index=True
        )

def delete_creature(creature_id):
    with server_state_lock["dmpool"]:
        server_state.dmpool = server_state.dmpool.loc[server_state.dmpool["ID"] != creature_id]

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

if not st.session_state.ini_mode and not st.session_state.view_mode or (st.session_state.view_mode and st.session_state.exp_mode):
    st.header("Characters")
    for index, row in filtered_pool.iterrows():
        col1, col2, col3 = st.columns([0.5, 1, 1], gap="medium", vertical_alignment="center")
        with col1:
            st.markdown(f"<p style='font-size: 20px; text-align: center;'>{row['Name']} <br>(🛡️{row['Armor Class']}, ❤️{row['Hitpoints']})</p>", unsafe_allow_html=True)
        with col2:
            initiative = st.slider(
                f"Initiative for {row['Name']}", 1, 30, key=f"slider_{row['ID']}", label_visibility="collapsed"
            )
        with col3:
            st.button(
                f"Enter {row['Name']}",
                key=f"enter_{row['ID']}",
                on_click=add_to_initiative,
                args=(row["ID"], initiative),
                use_container_width=True,
            )

if not st.session_state.ini_mode and (st.session_state.view_mode or st.session_state.exp_mode or (st.session_state.view_mode and st.session_state.exp_mode)) or (st.session_state.ini_mode and st.session_state.view_mode and st.session_state.exp_mode):
    st.header("Creatures")
    for index, row in server_state.dmpool.iterrows():
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1], gap="medium", vertical_alignment="center" )
        with col1:
            st.markdown(f"<p style='font-size: 20px; text-align: center;'>{row['Name']} <br>(🛡️{row['Armor Class']}, ❤️{row['Hitpoints']})</p>", unsafe_allow_html=True)
        with col2:
            initiative = st.slider(
                f"Initiative for {row['Name']}", 1, 30, key=f"slider_{row['ID']}", label_visibility="collapsed"
            )
        with col3:
            st.button(
                f"Enter {row['Name']}",
                key=f"enter_{row['ID']}",
                on_click=add_creature_to_initiative,
                args=(row["ID"], initiative),
                use_container_width=True,
            )
        with col4:
            st.button(
                f"Delete {row['Name']}",
                key=f"remove_pool_{index}_{row['ID']}",
                on_click=lambda creature_id=row["ID"]: delete_creature(creature_id),
                use_container_width=True,
            )

if st.session_state.ini_mode or st.session_state.exp_mode:
    st.header("Initiative - Round " + str(server_state.current_round))
    for index, row in server_state.initiative_list.iterrows():
        col1, col2, col3, col4, col5 = st.columns([0.15, 1.6, 0.4, 0.8, 0.8], gap="medium", vertical_alignment="center")
        with col1:
            st.markdown(f"<p style='font-size: 22px;'>{row['Indicator']}</p>", unsafe_allow_html=True)
        with col2:
            if row['Hitpoints'] > 0:
                st.markdown(f"<p style='font-size: 22px;'>{row['Name']} (🛡️{row['Armor Class']}, ❤️{row['Hitpoints']})</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='font-size: 22px;'>{row['Name']} (🛡️{row['Armor Class']}, 💀)</p>", unsafe_allow_html=True)

        with col3:
            st.markdown(f"<p style='font-size: 30px; text-align: left;'><span style='color: blue;'>{row['Initiative']}</span></p>", unsafe_allow_html=True)
        with col4:
            st.button(
                f"Remove {row['Name']}",
                key=f"remove_{index}_{row['ID']}",
                on_click=remove_from_initiative,
                args=(row["ID"],),
                use_container_width=True
            )
        with col5:
            st.session_state.edit_hp_values[row['ID']] = row["Hitpoints"]
            hp_change = st.number_input(
                f"Edit HP for {row['Name']}",
                key=f"edit_hp_{row['ID']}",
                label_visibility="collapsed",
                step=1
            )
            st.session_state.edit_hp_values[row['ID']] = hp_change
      
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
            
def reset():
    with server_state_lock["pool"], server_state_lock["initiative_list"], server_state_lock["initiative"], server_state_lock["dmpool"]:
        initialize_pool.clear()
        initialize_pool()
        load_character_pool()
        load_creature_pool()
        server_state.initiative_list = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints", "Initiative", "Indicator"])
        server_state.initiative = 0
        server_state.ini_length = 0
        server_state.next_initiative = 0
        server_state.current_character_id = None
        server_state.previous_character_id = None
        server_state.prev_ini = []
        server_state.prev_ini_list = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints", "Initiative", "Indicator"])
        server_state.current_round = 1

def clear():
    st.session_state.new_name = st.session_state.new_character_name
    st.session_state.new_ac = st.session_state.new_character_ac
    st.session_state.new_hp = st.session_state.new_character_hp
    st.session_state.new_character_name = ""
    st.session_state.new_character_ac = 10
    st.session_state.new_character_hp = 10

if (not st.session_state.ini_mode and (st.session_state.view_mode or st.session_state.exp_mode)) or (st.session_state.ini_mode and st.session_state.view_mode and st.session_state.exp_mode):
    st.header("Add Creatures")
    st.text_input("Character Name", key="new_character_name")
    st.number_input("Armor Class", min_value=1, max_value=30, value=10, key="new_character_ac")
    st.number_input("Hitpoints", min_value=0, value=10, key="new_character_hp")

    col1, col2, col3 = st.columns([1, 1, 0.75], gap="large")
    with col1:
        if st.button("Add Creature", on_click=clear) and not st.session_state.button_pressed:
            new_name = st.session_state.new_name
            new_ac = st.session_state.new_ac
            new_hp = st.session_state.new_hp
            st.session_state.button_pressed = True
            add_new_creature(new_name, new_ac, new_hp)
        st.session_state.button_pressed = False
    with col2:
        if st.button("Reset", on_click=clear):
            reset()
    with col3:
        if st.button("Initiative") and not st.session_state.ini_pressed:
            st.session_state.ini_pressed = True
            ini_cycle()
        st.session_state.ini_pressed = False

    col1, col2, col3 = st.columns([1, 1, 0.75], gap="large")
    with col1:
        if st.button("Save Characters"):
            if not server_state.initiative_list.empty:
                error = st.error("Clear the initiative list before saving.")
                time.sleep(3)
                error.empty()
            else:
                if not st.session_state.show_input:
                    st.session_state.show_input = True
                elif st.session_state.verification == "Apfeltaschen":
                    save_character_pool()
                    save_creature_pool()
                    saved = st.success("Characters saved successfully!")
                    time.sleep(3)
                    saved.empty()
                    st.session_state.show_input = False
                elif st.session_state.verification != "Apfeltaschen":
                    error = st.error("Incorrect verification code. Please try again.")
                    time.sleep(3)
                    error.empty()
                    st.session_state.show_input = False
        if st.session_state.show_input:
            st.session_state.verification = st.text_input("Verification Code")
    with col2:
        if st.button("Load Characters"):
            if not server_state.initiative_list.empty:
                error = st.error("Clear the initiative list before loading.")
                time.sleep(3)
                error.empty()
            else:
                initialize_pool.clear()
                initialize_pool()
                load_creature_pool()
                load_character_pool()
                loaded = st.success("Characters loaded successfully!")
                time.sleep(3)
                loaded.empty()
    with col3:
        st.button("Edit HP", key="toggle_edit_hp", on_click=toggle_edit_hp)
    
if st.session_state.ini_mode and not (st.session_state.ini_mode and st.session_state.view_mode and st.session_state.exp_mode):
    col1, col2 = st.columns([0.2, 0.6])
    with col1:
        if st.button("Initiative") and not st.session_state.ini_pressed:
            st.session_state.ini_pressed = True
            ini_cycle()
        st.session_state.ini_pressed = False
    with col2:
        st.button("Edit HP", key="toggle_edit_hp", on_click=toggle_edit_hp)
