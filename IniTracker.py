import streamlit as st
import pandas as pd

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

# Initialize session state
if "pool" not in st.session_state:
    st.session_state.pool = pd.DataFrame(initial_pool)

if "initiative_list" not in st.session_state:
    st.session_state.initiative_list = pd.DataFrame(columns=["ID", "Name", "Armor Class", "Hitpoints", "Initiative"])

if "new_character" not in st.session_state:
    st.session_state.new_character = {"Name": "", "Armor Class": 10, "Hitpoints": 10}

# Function to add a character to the initiative list
def add_to_initiative_callback(character_id, initiative):
    character = st.session_state.pool.loc[st.session_state.pool["ID"] == character_id].iloc[0]
    st.session_state.pool = st.session_state.pool[st.session_state.pool["ID"] != character_id]
    new_row = {"ID": character_id, "Name": character["Name"], "Armor Class": character["Armor Class"], "Hitpoints": character["Hitpoints"], "Initiative": initiative}
    st.session_state.initiative_list = pd.concat(
        [st.session_state.initiative_list, pd.DataFrame([new_row])], ignore_index=True
    )
    st.session_state.initiative_list.sort_values(by="Initiative", ascending=False, inplace=True)

# Function to remove a character from the initiative list
def remove_from_initiative_callback(character_id):
    character = st.session_state.initiative_list.loc[st.session_state.initiative_list["ID"] == character_id].iloc[0]
    st.session_state.initiative_list = st.session_state.initiative_list[st.session_state.initiative_list["ID"] != character_id]
    st.session_state.pool = pd.concat(
        [st.session_state.pool, pd.DataFrame([{"ID": character_id, "Name": character["Name"], "Armor Class": character["Armor Class"], "Hitpoints": character["Hitpoints"]}])], 
        ignore_index=True
    )

# Add a new character to the pool
def add_new_character():
    new_id = st.session_state.pool["ID"].max() + 1 if not st.session_state.pool.empty else 1
    new_name = st.session_state.new_character["Name"]
    new_ac = st.session_state.new_character["Armor Class"]
    new_hp = st.session_state.new_character["Hitpoints"]
    new_row = {"ID": new_id, "Name": new_name, "Armor Class": new_ac, "Hitpoints": new_hp}
    st.session_state.pool = pd.concat(
        [st.session_state.pool, pd.DataFrame([new_row])], ignore_index=True
    )
    st.session_state.new_character = {"Name": "", "Armor Class": 10, "Hitpoints": 10}  # Reset form inputs
    st.rerun()  # Force UI refresh

# Pool of characters
st.header("Character Pool")
for index, row in st.session_state.pool.iterrows():
    col1, col2, col3, col4 = st.columns([0.9, 2, 1, 0.1], gap="medium", vertical_alignment="center")  # Add a fourth column for remove button
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
            on_click=lambda character_id=row["ID"]: st.session_state.pool.drop(
                st.session_state.pool[st.session_state.pool["ID"] == character_id].index,
                inplace=True,
            ),
            use_container_width=True,
        )


# Initiative list
st.header("Initiative List")
for index, row in st.session_state.initiative_list.iterrows():
    col1, col2, col3 = st.columns([0.4, 0.25, 0.5], vertical_alignment="center")
    with col1:
        st.write(f"**{row['Name']}** (AC {row['Armor Class']}, HP {row['Hitpoints']})")
    with col2:
        st.markdown(f"<p style='font-size: 30px;  vertical-align: middle; '>{row['Initiative']}</p>", unsafe_allow_html=True)
    with col3:
        st.button(
            f"Remove {row['Name']}",
            key=f"remove_{index}_{row['ID']}",
            on_click=remove_from_initiative_callback,
            args=(row["ID"],),
            use_container_width=True  # Forces the button to stretch within the column
        )

# Add or remove characters from the pool
st.header("Manage Character Pool")
st.text_input("Character Name", key="new_character_name", on_change=lambda: st.session_state.new_character.update({"Name": st.session_state.new_character_name}))
st.number_input("Armor Class", min_value=1, max_value=30, value=10, key="new_character_ac", on_change=lambda: st.session_state.new_character.update({"Armor Class": st.session_state.new_character_ac}))
st.number_input("Hitpoints", min_value=1, value=10, key="new_character_hp", on_change=lambda: st.session_state.new_character.update({"Hitpoints": st.session_state.new_character_ac}))
if st.button("Add Character"):
    add_new_character()
