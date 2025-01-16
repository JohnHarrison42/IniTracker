import streamlit as st
import pandas as pd
from streamlit_server_state import server_state, server_state_lock

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

    /* Small buttons */
    .small-button > button {
        font-size: 12px;
        padding: 6px 12px;
        border-radius: 5px;
    }

    /* Large buttons */
    .large-button > button {
        font-size: 20px;
        padding: 12px 24px;
        border-radius: 10px;
    }

    /* Ensure text inside buttons resizes properly */
    div.stButton > button > span {
        font-size: 18px;
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

# Initialize global states if not already present
with server_state_lock["pool"]:
    if "pool" not in server_state:
        server_state.pool = pd.DataFrame(initial_pool)

with server_state_lock["initiative_list"]:
    if "initiative_list" not in server_state:
        server_state.initiative_list = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints", "Initiative"])

with server_state_lock["new_character"]:
    if "new_character" not in server_state:
        server_state.new_character = {"Name": "", "Armor Class": 10, "Hitpoints": 10}

# Function to add a character to the initiative list
def add_to_initiative_callback(character_id, initiative):
    with server_state_lock["pool"], server_state_lock["initiative_list"]:
        character = server_state.pool.loc[server_state.pool["ID"] == character_id].iloc[0]
        server_state.pool = server_state.pool[server_state.pool["ID"] != character_id]
        new_row = {"ID": character_id, "Name": character["Name"], "Armor Class": character["Armor Class"], "Hitpoints": character["Hitpoints"], "Initiative": initiative}
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
        new_id = server_state.pool["ID"].max() + 1 if not server_state.pool.empty else 1
        new_row = {"ID": new_id, "Name": new_name, "Armor Class": new_ac, "Hitpoints": new_hp}
        server_state.pool = pd.concat(
            [server_state.pool, pd.DataFrame([new_row])], ignore_index=True
        )
        server_state.new_character = {"Name": "", "Armor Class": 10, "Hitpoints": 10}  # Reset form inputs
        
# Pool of characters
st.header("Character Pool")
for index, row in server_state.pool.iterrows():
    col1, col2, col3, col4 = st.columns([1.3, 2, 1, 0.1], gap="medium", vertical_alignment="center")  # Add a fourth column for remove button
    with col1:
        st.write(f"**{row['Name']}** (AC {row['Armor Class']}, HP {row['Hitpoints']})")
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
            f"Remove {row['Name']}",
            key=f"remove_pool_{index}_{row['ID']}",
            on_click=lambda character_id=row["ID"]: server_state.pool.drop(
                server_state.pool[server_state.pool["ID"] == character_id].index,
                inplace=True,
            ),
            use_container_width=True,
        )

# Initiative list
st.header("Initiative List")
for index, row in server_state.initiative_list.iterrows():
    col1, col2, col3 = st.columns([0.5, 0.2, 0.4], vertical_alignment="center")
    with col1:
        st.markdown(f"<p style='font-size: 22px; vertical-align: middle;'>{row['Name']} (AC <span style='color: green;'>{row['Armor Class']}</span>, HP <span style='color: red;'>{row['Hitpoints']}</span>)</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='font-size: 30px; vertical-align: middle;'><span style='color: blue;'>{row['Initiative']}</span></p>", unsafe_allow_html=True)
    with col3:
        st.button(
            f"Remove {row['Name']}",
            key=f"remove_{index}_{row['ID']}",
            on_click=remove_from_initiative_callback,
            args=(row["ID"],),
            use_container_width=True  # Forces the button to stretch within the column
        )


# This block handles user inputs
st.header("Manage Character Pool")
new_name = st.text_input("Character Name", key="new_character_name")
new_ac = st.number_input("Armor Class", min_value=1, max_value=30, value=10, key="new_character_ac")
new_hp = st.number_input("Hitpoints", min_value=1, value=10, key="new_character_hp")

# This block adds the new character to the pool when the button is pressed
if st.button("Add Character") and not st.session_state.button_pressed:
    st.session_state.button_pressed = True  # Set flag to True to prevent re-triggering
    with server_state_lock["new_character"]:
        server_state.new_character["Name"] = new_name
        server_state.new_character["Armor Class"] = new_ac
        server_state.new_character["Hitpoints"] = new_hp
        add_new_character(new_name, new_ac, new_hp)  # Pass the values to the function
st.session_state.button_pressed = False  # Reset flag after the logic completes
