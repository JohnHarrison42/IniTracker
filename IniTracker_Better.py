import streamlit as st
import pandas as pd

# Initial data for the pool of characters
initial_pool = [
    {"Name": "Aragorn", "Armor Class": 16},
    {"Name": "Legolas", "Armor Class": 15},
    {"Name": "Gimli", "Armor Class": 17},
    {"Name": "Frodo", "Armor Class": 12},
    {"Name": "Gandalf", "Armor Class": 14},
]

# Initialize session state
if "pool" not in st.session_state:
    st.session_state.pool = pd.DataFrame(initial_pool)

if "initiative_list" not in st.session_state:
    st.session_state.initiative_list = pd.DataFrame(columns=["Name", "Armor Class", "Initiative"])

# Function to add a character to the initiative list
def add_to_initiative_callback(name, ac, initiative):
    st.session_state.pool = st.session_state.pool[st.session_state.pool["Name"] != name]
    new_row = {"Name": name, "Armor Class": ac, "Initiative": initiative}
    st.session_state.initiative_list = pd.concat(
        [st.session_state.initiative_list, pd.DataFrame([new_row])], ignore_index=True
    )
    st.session_state.initiative_list.sort_values(by="Initiative", ascending=False, inplace=True)

# Function to remove a character from the initiative list
def remove_from_initiative_callback(name, ac):
    st.session_state.initiative_list = st.session_state.initiative_list[
        st.session_state.initiative_list["Name"] != name
    ]
    st.session_state.pool = pd.concat(
        [st.session_state.pool, pd.DataFrame([{"Name": name, "Armor Class": ac}])], ignore_index=True
    )

# Pool of characters
st.header("Character Pool")
st.write("Click a character to add them to the initiative list.")
for index, row in st.session_state.pool.iterrows():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**{row['Name']}** (AC: {row['Armor Class']})")
    with col2:
        initiative = st.slider(f"Initiative for {row['Name']}", 1, 30, key=f"ini_{row['Name']}")
        st.button(
            f"Enter {row['Name']}",
            key=f"enter_{row['Name']}",
            on_click=add_to_initiative_callback,
            args=(row["Name"], row["Armor Class"], initiative),
        )

# Initiative list
st.header("Initiative List")
st.write("Click 'Remove' to send a character back to the pool.")
for index, row in st.session_state.initiative_list.iterrows():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**{row['Name']}** (AC: {row['Armor Class']}, Initiative: {row['Initiative']})")
    with col2:
        st.button(
            f"Remove {row['Name']}",
            key=f"remove_{row['Name']}",
            on_click=remove_from_initiative_callback,
            args=(row["Name"], row["Armor Class"]),
        )

# Add or remove characters from the pool
st.header("Manage Character Pool")
with st.form("add_character"):
    new_name = st.text_input("Character Name")
    new_ac = st.number_input("Armor Class", min_value=1, max_value=30, value=10)
    if st.form_submit_button("Add Character"):
        new_row = {"Name": new_name, "Armor Class": new_ac}
        st.session_state.pool = pd.concat(
            [st.session_state.pool, pd.DataFrame([new_row])], ignore_index=True
        )
