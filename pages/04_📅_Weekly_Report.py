import streamlit as st
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from highlight_text import fig_text
import sys
import base64
from matplotlib.backends.backend_pdf import PdfPages
import requests
from dateutil import parser
from pathlib import Path
import math
file = Path(__file__).resolve()
root = file.parents[1]
sys.path.append(str(root))

from utils.metadata import (men_daily_volume_parameters, men_daily_volume_plot_names,
                            women_daily_volume_parameters, women_daily_volume_plot_names,
                            weekly_daily_plot_parameters, men_weekly_volume_parameters, men_weekly_volume_plot_names,
                            women_weekly_volume_parameters, women_weekly_volume_plot_names, colors)

from polar_api import POLAR_API
from polar_api import (clean_df, 
                    preprocess, 
                    extract_team_id,
                    get_day_sessions_name_id_dict, 
                    get_interval_sessions_name_id_dict,
                    extract_players, 
                    get_player_session_ids, 
                    get_player_session_details_trimmed)

from kitbag.plots.bar_charts import plot_physical_volume, plot_bars
from kitbag.plots.tables import plot_table
from kitbag.plots.altair_plot import plot_altair_scatter

st.set_page_config(page_title="Weekly Report", page_icon="📅", layout="wide")
st.sidebar.markdown("## 📅 Weekly Report")

client_id = st.secrets['client_id']
client_secret = st.secrets['client_secret']

authorize_url = 'https://auth.polar.com/oauth/authorize'
access_token_url = 'https://auth.polar.com/oauth/token'
authorize_params = {'client_id': client_id,
                                'response_type': 'code',
                                'scope': 'team_read'}

encoding = client_id+':'+ client_secret
message_bytes = encoding.encode('ascii')
base64_bytes = base64.b64encode(message_bytes)
base64_encoding = base64_bytes.decode('ascii')
headers = {'Authorization': 'Basic '+ base64_encoding}
r = requests.get(authorize_url, params=authorize_params)

# st.write(r.history[0].url)
# webbrowser.open(r.history[0].url, new=2)
link = r.history[0].url

def get_all_player_session_details_trimmed(player_session_ids):
    player_data_id_dct = {}
    for player_id, player_session_id in player_session_ids.items():
        player_data = api.get_trimmed_player_session_details(tokens,player_session_id)
        df_session_player = get_player_session_details_trimmed(
            player_data)
        df_session_player.insert(loc=0, column='player_id', value=player_id)
        player_data_id_dct[player_id] = df_session_player
    
    df_all_players = pd.concat(list(player_data_id_dct.values())).reset_index(drop=True)
    return df_all_players


def session_data(selected_session_id, selected_session_name, activity_data=False):
    session = api.get_players_session_data(tokens, session_id = selected_session_id)
    date = session['data']['record_start_time']
    date_time = parser.parse(session['data']['record_start_time'])
    player_session_ids = get_player_session_ids(session)
    session_data = get_all_player_session_details_trimmed(player_session_ids)
    session_data = preprocess(session_data, date_time, players, selected_session_name, account)

    if activity_data == False:
        session_data = session_data.drop(["Session name", "Start time"], axis=1)
    else:
        pass

    return session_data


with st.sidebar.form("my_form"):
    chosen_team = st.selectbox("Choose Account", options=["Superliga", "RTD senior", "U19", "U17", 'U15', "Kvindeliga", 'Girls U18', "U16W"], index=3)
    today_date = datetime.today()
    seven_days_ago = today_date - timedelta(7)
    date_range = st.date_input(label="Select date range", value=[seven_days_ago, today_date])
    st.markdown("Open the [link](%s) and copy the code" % link, unsafe_allow_html=True)
    authorization_code = st.text_input('Input the Polar authentication token below')
    submitted = st.form_submit_button("Submit")

if chosen_team in ["Superliga", "RTD senior", "U19", "U17", 'U15']:
        account = "M"
        daily_volume_parameters = men_daily_volume_parameters
        daily_volume_plot_names = men_daily_volume_plot_names
        weekly_volume_parameters = men_weekly_volume_parameters
        weekly_volume_plot_names = men_weekly_volume_plot_names
        if chosen_team == 'Superliga':
            chosen_team_long = "FC Nordsjaelland"
        elif chosen_team == "U19":
            chosen_team_long = "FC Nordsjaelland U19"
        elif chosen_team == 'U17':
            chosen_team_long = "FC Nordsjaelland U17"
        elif chosen_team == 'U15':
            chosen_team_long = "FC Nordsjaelland U15"
elif chosen_team in ["Kvindeliga", 'Girls U18', "U16W"]:
        account = 'W'
        daily_volume_parameters = women_daily_volume_parameters
        daily_volume_plot_names = women_daily_volume_plot_names
        weekly_volume_parameters = women_weekly_volume_parameters
        weekly_volume_plot_names = women_weekly_volume_plot_names
        if chosen_team == 'Kvindeliga':
            chosen_team_long = "FC Nordsjaelland Women"
        elif chosen_team == "Girls U18":
            chosen_team_long = "FC Nordsjaelland Girls U18"
        elif chosen_team == "U16W":
            chosen_team_long = "FC Nordsjaelland Girls U16"



def transform_date(dt):
    x = str(dt).split("-")
    year = x[0]
    month = x[1]
    day = x[2]
    dt = day + "-" + month + "-" + year
    return dt

date1 = transform_date(date_range[0])
date2 = transform_date(date_range[1])



if authorization_code:
    st.cache()
    access_token_data = {'grant_type': 'authorization_code',
                            'code': authorization_code}
    r_post = requests.post(access_token_url,
    data=access_token_data,
    headers=headers)
    tokens = r_post.json()
    api = POLAR_API(client_id, client_secret, team=chosen_team)
    try:
        team_info = api.get_teams_info(tokens)
    except:
        st.sidebar.markdown("### Copy and paste a new token")
        st.stop()
    team_id = extract_team_id(team_info, chosen_team)
    team_players = api.get_team_players(tokens, team_id=team_id)
    players = extract_players(team_players)
    sessions_data = api.get_sessions(tokens=tokens, team_id=team_id, dates=[date1, date2])
    sessions_interval_dict = get_interval_sessions_name_id_dict(sessions_data)


    sessions_dfs_lst = []
    for i, j in sessions_interval_dict.items():
        if type(j) != str:
            st.sidebar.markdown(f"### At least one session in that range is not named. Please name the session in Polar.")
            st.stop()

        s_df = session_data(i, j, activity_data=True)
        # df_plot_clean = clean_df(s_df)
        sessions_dfs_lst.append(s_df)

    merged_sessions_dfs = pd.concat(sessions_dfs_lst)

     ## -------- INDIVIDUAL AND POSITIONAL OVERVIEW --------- ##
    df_stats_clean_previous = merged_sessions_dfs.copy()
    df_stats_clean_previous['Sessions'] = 1
    df_stats_gameweek_daily = df_stats_clean_previous.groupby(["position_name", "athlete_name"]).sum()
    df_stats_gameweek_daily = df_stats_gameweek_daily.drop("Maximum speed [km/h]", axis=1)
    df_stats_gameweek_daily['Total Distance (km)'] = (df_stats_gameweek_daily['Total Distance'] / 1000)
    df_stats_gameweek_daily['Total Distance (km)'] = df_stats_gameweek_daily['Total Distance (km)'].round(1)
    df_stats_gameweek_daily = df_stats_gameweek_daily.drop("Total Distance", axis=1)
    df_stats_gameweek_daily = df_stats_gameweek_daily[weekly_volume_parameters]
    df_stats_gameweek_daily.columns = weekly_volume_plot_names

    df_plot_clean_previous = clean_df(df_stats_gameweek_daily, volume=True)
    position_order = ["Avg. Team", "Centre Back", "Full Back", "Midfielder", "Attacker"]
    df_plot_clean_previous = df_plot_clean_previous.reindex(position_order, axis=0, level=0)

    # prep dataframe for table
    df_team_volume_table = df_plot_clean_previous.reset_index().drop("position_name", axis=1)
    df_team_volume_table = df_team_volume_table[~df_team_volume_table.iloc[:, 0].str.contains("Åvg.|Avg.")]
    
    # clean decimals
    df_team_volume_table.iloc[:, :-1] = df_team_volume_table.iloc[:, :-1].astype(int, errors="ignore")
    df_team_volume_table.iloc[:,-1] = df_team_volume_table.iloc[:,-1].round(1)
    
   
    ## -------- DAILY LOAD DURING THE WEEK --------- ##
    
    df_plot_previous_daily = merged_sessions_dfs.copy()

    name_time_session_map_df = df_plot_previous_daily[['Session name', 'Start time']]
    name_time_session_map_df = name_time_session_map_df.reset_index()
    name_time_session_map_df = name_time_session_map_df.drop(['position_name', 'athlete_name'], axis=1)
    name_time_session_map_df = name_time_session_map_df.drop_duplicates(subset=['Session name'])

    df_stats_gameweek_daily = df_plot_previous_daily.groupby(by=['Session name']).mean()
    df_stats_gameweek_daily = df_stats_gameweek_daily.reset_index()
    df_stats_gameweek_daily = pd.merge(df_stats_gameweek_daily, name_time_session_map_df, how='inner', on = 'Session name')
    df_stats_gameweek_daily.set_index("Session name", inplace=True)
    df_stats_gameweek_daily.sort_values("Start time", inplace=True)
    
    df_plot_weekly = df_stats_gameweek_daily.drop(['Maximum speed [km/h]', 'Start time'], axis=1)
    df_plot_weekly.columns = weekly_daily_plot_parameters
    # df_plot_weekly["Average Duration (Session)"] = df_plot_weekly["Average Duration (Session)"] / 60
    df_plot_weekly = df_plot_weekly.round(1)


    ## ------- PLOTTING MAIN PAGE ------- ##
    st.write("### **Weekly Physical Report**")

    col1, col2 = st.columns(2)
    with PdfPages(f"Weekly Physical Report {date1} to {date2}.pdf") as pdf:
        plot_previous = plot_physical_volume(df_plot_clean_previous,
                                                   f"Physical Load\n{date1} to {date2}",
                                                   team=chosen_team_long)
        col1.pyplot(plot_previous)
        pdf.savefig(bbox_inches='tight')
        
        plot_weekly_daily_load = plot_bars(df_plot_weekly,
                                           title=f"Daily Physical Load\n{date1} to {date2}",
                                           color="#4285F4")
        col2.pyplot(plot_weekly_daily_load)
        pdf.savefig(bbox_inches='tight')
        
        # # ## TABLES
        # # # volume table
        volume_table = plot_table(df_team_volume_table,
                                  main_col="Total Distance (km)",
                                  title=f"Physical Volume\n{date1} to {date2}")
        col1.pyplot(volume_table)
        pdf.savefig(bbox_inches='tight')

    with open(f"Weekly Physical Report {date1} to {date2}.pdf", "rb") as report:
        st.download_button("Download Report", report, f"Weekly Physical Report {date1} to {date2}.pdf")
        

    if account == 'M':
        ## ----- ALTAIR PLOT ------ ##
        st.write("### **Weekly Physical Exploration**")
        alt_col1, alt_col2 = st.columns(2)
        df_altair_plot = df_plot_clean_previous.reset_index()
        # Set colors
        domain = list(colors.keys())
        range_  = list(colors.values())
        
        # Volume
        altair_weekly_volume = plot_altair_scatter(df_altair_plot, title="Weekly Volume Load",
                                                x="Total Distance (km):Q", y="HSR distance (>20km/h):Q",
                                                tooltip=["athlete_name:N", "Total Distance (km):Q", "HSR distance (>20km/h):Q"],
                                                color='position_name:N', label="athlete_name:N",
                                                width=600, height=600, size=200)
        alt_col1.altair_chart(altair_weekly_volume)
        # Intensity
        altair_intensity_plot = plot_altair_scatter(df_altair_plot, title="Weekly Intensity Load",
                                                    x="Sprint distance (>25km/h):Q", y="Sprint efforts (>25km/h):Q",
                                                    tooltip=["athlete_name:N", "Sprint distance (>25km/h):Q", "Sprint efforts (>25km/h):Q", "Max Speed (km/h):Q"],
                                                    color="position_name:N", width=600, height=600, label="athlete_name:N", size=200)
        alt_col2.altair_chart(altair_intensity_plot)
        # Mechanical
        altair_mechanical_plot = plot_altair_scatter(df_altair_plot, title="Weekly Intensity Load",
                                                    x="Acc (>3m/s):Q", y="Dec (>-3m/s):Q",
                                                    tooltip=["athlete_name:N", "Acc (>3m/s):Q", "Dec (>-3m/s):Q", "Max Speed (km/h):Q"],
                                                    color="position_name:N", width=600, height=600, label="athlete_name:N", size=200)
        alt_col1.altair_chart(altair_mechanical_plot)
    
    elif account == 'W':
        ## ----- ALTAIR PLOT ------ ##
        st.write("### **Weekly Physical Exploration**")
        alt_col1, alt_col2 = st.columns(2)
        df_altair_plot = df_plot_clean_previous.reset_index()
        # Set colors
        domain = list(colors.keys())
        range_  = list(colors.values())
        
        # Volume
        altair_weekly_volume = plot_altair_scatter(df_altair_plot, title="Weekly Volume Load",
                                                x="Total Distance (km)", y="HSR distance (>19km/h)",
                                                tooltip=["athlete_name:N", "Total Distance (km):Q", "HSR distance (>19km/h):Q"],
                                                color='position_name:N', label="athlete_name:N",
                                                width=600, height=600, size=200)
        alt_col1.altair_chart(altair_weekly_volume)
        # Intensity
        altair_intensity_plot = plot_altair_scatter(df_altair_plot, title="Weekly Intensity Load",
                                                    x="Sprint distance (>22.5km/h):Q", y="Sprint efforts (>22.5km/h):Q",
                                                    tooltip=["athlete_name:N", "Sprint distance (>22.5km/h):Q", "Sprint efforts (>22.5km/h):Q", "Max Speed (km/h):Q"],
                                                    color="position_name:N", width=600, height=600, label="athlete_name:N", size=200)
        alt_col2.altair_chart(altair_intensity_plot)
        # Mechanical
        altair_mechanical_plot = plot_altair_scatter(df_altair_plot, title="Weekly Intensity Load",
                                                    x="Acc (>3m/s):Q", y="Dec (>-3m/s):Q",
                                                    tooltip=["athlete_name:N", "Acc (>3m/s):Q", "Dec (>-3m/s):Q", "Max Speed (km/h):Q"],
                                                    color="position_name:N", width=600, height=600, label="athlete_name:N", size=200)
        alt_col1.altair_chart(altair_mechanical_plot)


else:
    pass
