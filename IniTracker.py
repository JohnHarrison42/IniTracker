import streamlit as st
import pandas as pd
from streamlit_server_state import server_state, server_state_lock
import time


if "view_mode" not in st.session_state:
    st.session_state.view_mode = "DM"
   
mode = st.toggle("DM Mode")
st.session_state.view_mode = mode

ini_mode = st.toggle("Initiative Mode")
st.session_state.ini_mode = ini_mode

# CSS for button styling
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

# Initial data for the pool of characters
initial_pool = [
    {"ID": 1, "Name": "Zeno", "Armor Class": 16, "Hitpoints": 20},
    {"ID": 2, "Name": "Berinel", "Armor Class": 15, "Hitpoints": 30},
    {"ID": 3, "Name": "Ludovika", "Armor Class": 17, "Hitpoints": 40},
    {"ID": 4, "Name": "Elris", "Armor Class": 12, "Hitpoints": 50},
    {"ID": 5, "Name": "Francesco", "Armor Class": 14, "Hitpoints": 60},
    {"ID": 6, "Name": "Taja", "Armor Class": 13, "Hitpoints": 70},
    {"ID": 7, "Name": "Niemand", "Armor Class": 14, "Hitpoints": 80},
]
try:
    if "pool" not in server_state:
        with server_state_lock["pool"]:
            server_state.pool = pd.DataFrame(initial_pool)
except server_state.session_info.NoSessionError:
    pass

if "initiative_list" not in server_state:
    with server_state_lock["initiative_list"]:
        server_state.initiative_list = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints", "Initiative", "Indicator"])

if "new_character" not in server_state:
    with server_state_lock["new_character"]:
        server_state.new_character = {"Name": "", "Armor Class": 10, "Hitpoints": 10}

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

if "edit_hp" not in st.session_state:
    st.session_state.edit_hp = False

if not st.session_state.ini_mode:
    st.header("Character Selection")
    col1, col2 = st.columns([0.25, 0.5])
    with col1:
        character_names = ["All"] + list(server_state.pool["Name"])  # Add "All" to show all characters
        selected_character = st.selectbox("Choose your character:", character_names, key="character_select")
    
    if selected_character != "All":
        filtered_pool = server_state.pool[server_state.pool["Name"] == selected_character]
    else:
        filtered_pool = server_state.pool

def save_character_pool():
    with server_state_lock["pool"]:
        server_state.pool.to_csv("character_pool.csv", index=False)
        
def load_character_pool():
    with server_state_lock["pool"]:
        server_state.pool = pd.read_csv("character_pool.csv")


# Function to add a character to the initiative list
def add_to_initiative_callback(character_id, initiative):
    with server_state_lock["pool"], server_state_lock["initiative_list"], server_state_lock["initiative"]:
        character = server_state.pool.loc[server_state.pool["ID"] == character_id].iloc[0]
        server_state.pool = server_state.pool[server_state.pool["ID"] != character_id]
        new_row = {"ID": character_id, "Name": character["Name"], "Armor Class": character["Armor Class"], "Hitpoints": character["Hitpoints"], "Initiative": initiative, "Indicator": ""}
        server_state.initiative_list = pd.concat(
            [server_state.initiative_list, pd.DataFrame([new_row])], ignore_index=True
        )
        server_state.initiative_list.sort_values(by="Initiative", ascending=False, inplace=True)

# Function to remove a character from the initiative list
def remove_from_initiative_callback(character_id):
    with server_state_lock["pool"], server_state_lock["initiative_list"]:
        character = server_state.initiative_list.loc[server_state.initiative_list["ID"] == character_id].iloc[0]
        server_state.initiative_list = server_state.initiative_list[server_state.initiative_list["ID"] != character_id]
        server_state.pool = pd.concat(
            [server_state.pool, pd.DataFrame([{"ID": character_id, "Name": character["Name"], "Armor Class": character["Armor Class"], "Hitpoints": character["Hitpoints"]}])],
            ignore_index=True,
        )

# Add a new character to the pool
def add_new_character(new_name, new_ac, new_hp):
    with server_state_lock["pool"], server_state_lock["new_character"]:
        new_id = server_state.pool["ID"].max() + 1 if not server_state.pool.empty else server_state.initiative_list["ID"].max() + 1
        new_row = {"ID": new_id, "Name": new_name, "Armor Class": new_ac, "Hitpoints": new_hp}
        server_state.pool = pd.concat(
            [server_state.pool, pd.DataFrame([new_row])], ignore_index=True
        )
        server_state.new_character = {"Name": "", "Armor Class": 10, "Hitpoints": 10}  # Reset form inputs

def ini_cycle():
    with server_state_lock["initiative"], server_state_lock["initiative_list"]:
        if not server_state.initiative_list.empty:
            server_state.initiative_list.sort_values(by="Initiative", ascending=False, inplace=True)
            if server_state.initiative >= len(server_state.initiative_list):
                server_state.initiative = 0
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
            server_state.initiative_list.iloc[
                server_state.initiative, server_state.initiative_list.columns.get_loc("Indicator")
            ] = '➤'
            for l1, l2 in zip(server_state.initiative_list[['ID', 'Indicator']].values.tolist(), server_state.prev_ini_list):
                if l1[0] == l2[0] and l1[1] == l2[1] == '➤':
                    server_state.initiative_list["Indicator"] = ""
                    server_state.initiative += 1
                    server_state.initiative_list.iloc[
                    server_state.initiative, server_state.initiative_list.columns.get_loc("Indicator")
                    ] = '➤'
            server_state.initiative += 1
            server_state.prev_ini = server_state.initiative_list['ID'].values.tolist()
            server_state.prev_ini_list = server_state.initiative_list[['ID', 'Indicator']].values.tolist()

# Pool of characters
if not st.session_state.ini_mode:
    st.header("Character Pool")
    for index, row in filtered_pool.iterrows():
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1], gap="medium", vertical_alignment="center")
        with col1:
            st.markdown(f"<p style='font-size: 20px; text-align: center;'>{row['Name']} <br>(🛡️{row['Armor Class']}, ❤️{row['Hitpoints']})</p>", unsafe_allow_html=True)
        with col2:
            initiative = st.slider(
                f"Initiative for {row['Name']}", 1, 30, key=f"slider_{row['ID']}"
            )
        with col3:
            st.button(
                f"Enter {row['Name']}",
                key=f"enter_{row['ID']}",
                on_click=add_to_initiative_callback,
                args=(row["ID"], initiative),
                use_container_width=True,
            )
        with col4:
            st.button(
                f"Delete {row['Name']}",
                key=f"remove_pool_{index}_{row['ID']}",
                on_click=lambda character_id=row["ID"]: server_state.pool.drop(
                    server_state.pool[server_state.pool["ID"] == character_id].index,
                    inplace=True,
                ),
                use_container_width=True,
            )
        

# Initiative list
if st.session_state.view_mode:
    st.header("Initiative List")
    for index, row in server_state.initiative_list.iterrows():
        col1, col2, col3, col4, col5 = st.columns([0.2, 1.3, 0.6, 0.8, 0.8], gap="medium", vertical_alignment="center")
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
                on_click=remove_from_initiative_callback,
                args=(row["ID"],),
                use_container_width=True
            )
        with col5:
            if st.session_state.edit_hp:
                new_hp = st.number_input(
                    f"Edit HP for {row['Name']}",
                    min_value=0,
                    value=row["Hitpoints"],
                    key=f"edit_hp_{row['ID']}",
                    label_visibility="collapsed"
                )
                if new_hp != row["Hitpoints"]:
                    with server_state_lock["initiative_list"]:
                        server_state.initiative_list.loc[server_state.initiative_list["ID"] == row["ID"], "Hitpoints"] = new_hp
                        st.rerun()
            
def toggle_edit_hp():
    st.session_state.edit_hp = not st.session_state.edit_hp
    for key in st.session_state.keys():
        if key.startswith("edit_hp_"):
            del st.session_state[key]
           
def reset():
    with server_state_lock["pool"], server_state_lock["initiative_list"], server_state_lock["new_character"], server_state_lock["Initiative"]:
        server_state.pool = pd.DataFrame(initial_pool)
        server_state.initiative_list = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints", "Initiative", "Indicator"])
        server_state.new_character = {"Name": "", "Armor Class": 10, "Hitpoints": 10}
        server_state.initiative = 0
        server_state.ini_length = 0
        server_state.next_initiative = 0
        server_state.current_character_id = None
        server_state.previous_character_id = None
        server_state.prev_ini = []
        server_state.prev_ini_list = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints", "Initiative", "Indicator"])

# This block handles user inputs
if not st.session_state.ini_mode:
    st.header("Manage Character Pool")
    new_name = st.text_input("Character Name", key="new_character_name")
    new_ac = st.number_input("Armor Class", min_value=1, max_value=30, value=10, key="new_character_ac")
    new_hp = st.number_input("Hitpoints", min_value=0, value=10, key="new_character_hp")

    col1, col2, col3 = st.columns([1, 1, 0.75], gap="large")
    with col1:
    # This block adds the new character to the pool when the button is pressed
        if st.button("Add Character") and not st.session_state.button_pressed:
            st.session_state.button_pressed = True  # Set flag to True to prevent re-triggering
            with server_state_lock["new_character"]:
                server_state.new_character["Name"] = new_name
                server_state.new_character["Armor Class"] = new_ac
                server_state.new_character["Hitpoints"] = new_hp
                add_new_character(new_name, new_ac, new_hp)  # Pass the values to the function
        st.session_state.button_pressed = False  # Reset flag after the logic completes
    with col2:
        if st.button("Reset"):
            reset()
    with col3:
        if st.button("Initiative") and not st.session_state.ini_pressed:
            st.session_state.ini_pressed = True
            ini_cycle()
        st.session_state.ini_pressed = False

    col1, col2, col3 = st.columns([1, 1, 0.75], gap="large")
    with col1:
        if st.button("Save Characters"):
            save_character_pool()
            saved = st.success("Character pool saved successfully!")
            time.sleep(3)
            saved.empty()
    with col2:
        if st.button("Load Characters"):
            load_character_pool()
            loaded = st.success("Character pool loaded successfully!")
            time.sleep(3)
            loaded.empty()
    with col3:
        st.button("Edit HP", key="toggle_edit_hp", on_click=toggle_edit_hp)
    
if st.session_state.ini_mode:
    col1, col2 = st.columns([0.2, 0.6])
    with col1:
        if st.button("Initiative") and not st.session_state.ini_pressed:
            st.session_state.ini_pressed = True
            ini_cycle()
        st.session_state.ini_pressed = False
    with col2:
        st.button("Edit HP", key="toggle_edit_hp", on_click=toggle_edit_hp)
