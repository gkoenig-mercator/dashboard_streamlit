import streamlit as st

def time_selector(time_steps):
    """Show a selectbox for time steps and return the selected value."""
    if time_steps is None:
        return None
    selected = st.selectbox("Select time step", time_steps)
    return selected
