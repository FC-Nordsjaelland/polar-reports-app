from datetime import datetime

import pandas as pd
import streamlit as st
from polar_api.PolarAPI import PolarTeamproAPI

# Page config
st.set_page_config(page_title="Database", page_icon="💾", layout="wide")
st.markdown("# 💾 Database")

# Set variables
teams = ["U17", "U15", "U14", "Girls U18", "U16W", "U14W"]

# Setup API
client_id = st.secrets["client_id"]
client_secret = st.secrets["client_secret"]
redirect_uri = "http://localhost:8080"
client = PolarTeamproAPI(
    client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri
)

## -------- PAGE FORM ------- ##
with st.sidebar.form("auth_form"):
    # User authorization
    auth_url = client.create_authorization_url()
    st.markdown("### Authentication")
    st.markdown(
        "Please verify through [this link](%s)" % auth_url, unsafe_allow_html=True
    )
    auth_code_url = st.text_input("Insert redirect url")
    auth_code = client.fetch_authorization_code(url=auth_code_url)
    try:
        client.set_access_token(authorization_code=auth_code)
    except:
        st.write("")
    st.markdown("### User selection")
    # User select team
    selected_team = st.selectbox(label="Select team", options=teams)
    # User select dates to fetch sessions
    start_date, end_date = st.date_input(
        label="Select date range", value=(datetime.now(), datetime.now())
    )
    # reformat selected dates
    since = datetime(
        year=start_date.year, month=start_date.month, day=start_date.day
    ).isoformat()
    until = datetime(
        year=end_date.year, month=end_date.month, day=end_date.day
    ).isoformat()

    auth_form_submit = st.form_submit_button(label="Submit")
## -------- PAGE FORM END ------- ##


## -------- MAIN PAGE -------- ##
if not auth_form_submit:
    st.markdown("##### Please authenticate in the sidebar!")

if auth_form_submit:
    try:
        # Team id
        team = client.get_team()
        team_id = [t["id"] for t in team["data"] if t["name"] == selected_team][0]
        # Get sessions from the specified date range
        sessions = client.get_team_training_session(
            team_id=team_id, since=since, until=until
        )

        # User select sessions to be inserted
        with st.form("database_form"):
            # Select sessions
            session_dict = {
                session["id"]: session["created"] for session in sessions["data"]
            }
            st.multiselect(
                label="Select sessions to upload",
                options=list(session_dict.values()),
                default=list(session_dict.values()),
            )
            # Select upload update or delete
            st.radio(label="Select action", options=["Upload", "Update", "Delete"])
            # Submit
            database_form_submit = st.form_submit_button("Upload sessions")

    except AttributeError:
        st.warning("Please authenticate again!")  # , icon="⚠️")
