import streamlit as st
import pandas as pd
import random

# Initialize session state if not already initialized
if 'initiative_list' not in st.session_state:
    st.session_state.initiative_list = pd.DataFrame(columns=["Player Name", "Initiative Roll"])

def add_initiative_roll():
    player_name = st.text_input("Enter Player Name")
    initiative_roll = st.number_input("Enter Initiative Roll", min_value=1, max_value=30)
    
    if st.button("Add Roll"):
        if player_name and initiative_roll:
            new_entry = pd.DataFrame({"Player Name": [player_name], "Initiative Roll": [initiative_roll]})
            st.session_state.initiative_list = pd.concat([st.session_state.initiative_list, new_entry], ignore_index=True)
            st.success(f"{player_name}'s initiative roll added!")
        else:
            st.error("Please enter both player name and initiative roll")

def display_initiative_order():
    if len(st.session_state.initiative_list) > 0:
        st.session_state.initiative_list = st.session_state.initiative_list.sort_values("Initiative Roll", ascending=False)
        st.session_state.initiative_list.reset_index(drop=True, inplace=True)
        st.table(st.session_state.initiative_list)
    else:
        st.warning("No entries yet!")

# Streamlit app layout
st.title("D&D Initiative Tracker")

st.header("Add Your Initiative Rolls")
add_initiative_roll()

st.header("Current Initiative Order")
display_initiative_order()

# Button to reset all rolls (for testing or resetting the tracker)
if st.button("Reset Tracker"):
    st.session_state.initiative_list = pd.DataFrame(columns=["Player Name", "Initiative Roll"])
    st.success("Tracker reset!")
