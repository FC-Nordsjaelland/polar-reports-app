#%%
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
file = Path(__file__).resolve()
root = file.parents[1]
sys.path.append(str(root))

from utils.metadata import (men_daily_volume_parameters, men_daily_volume_plot_names,
                            women_daily_volume_parameters, women_daily_volume_plot_names)

from polar_api import POLAR_API
from polar_api import (clean_df, 
                    preprocess, 
                    extract_team_id,
                    get_day_sessions_name_id_dict, 
                    get_interval_sessions_name_id_dict,
                    extract_players, 
                    get_player_session_ids, 
                    get_player_session_details_trimmed)

from kitbag.plots.bar_charts import plot_physical_volume
from kitbag.plots.tables import plot_table
from kitbag.plots.altair_plot import plot_altair_scatter


#%%
st.set_page_config(page_title="Daily Report", page_icon="☀️", layout="wide")
st.sidebar.markdown("## ☀️ Daily Report")

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


def session_data(selected_session_id, selected_session_name):
    session = api.get_players_session_data(tokens, session_id = selected_session_id)
    date = session['data']['record_start_time']
    date_time = parser.parse(session['data']['record_start_time'])
    player_session_ids = get_player_session_ids(session)
    session_data = get_all_player_session_details_trimmed(player_session_ids)
    session_data = preprocess(session_data, date_time, players, selected_session_name, account)
    session_data = session_data.drop(["Session name", "Start time"], axis=1)

    return session_data
#%%

with st.sidebar.form("my_form"):
    chosen_team = st.selectbox("Choose Account", options=["Superliga", "RTD senior", "U19", "U17", 'U15', "Kvindeliga", 'Girls U18', "U16W"], index=3)
    activity_date = st.date_input("Pick training date", value=datetime.today())
    no_of_session = st.selectbox("Session number", ['1','2','3','4'])
    st.markdown("Open the [link](%s) and copy the code" % link, unsafe_allow_html=True)
    st.cache()
    authorization_code = st.text_input('Input the Polar authentication token below')
    submitted = st.form_submit_button("Submit")
# with st.sidebar.form(key='my_form'):
#     st.markdown("Open the [link](%s) and copy the code" % link, unsafe_allow_html=True)
#     authorization_code = st.text_input('Input the Polar authentication token below')
#     st.form_submit_button()

if chosen_team in ["Superliga", "RTD senior", "U19", "U17", 'U15']:
        account = "M"
        daily_volume_parameters = men_daily_volume_parameters
        daily_volume_plot_names = men_daily_volume_plot_names
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
        if chosen_team == 'Kvindeliga':
            chosen_team_long = "FC Nordsjaelland Women"
        elif chosen_team == "Girls U18":
            chosen_team_long = "FC Nordsjaelland Girls U18"
        elif chosen_team == "U16W":
            chosen_team_long = "FC Nordsjaelland Girls U16"


x = str(activity_date).split("-")
year = x[0]
month = x[1]
day = x[2]
selected_date = day + "-" + month + "-" + year


if authorization_code and submitted:
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
    sessions_meta = api.get_session(tokens, team_id=team_id, date=selected_date)
    team_players = api.get_team_players(tokens, team_id=team_id)
    players = extract_players(team_players)
    try:
        sessions_dict = get_day_sessions_name_id_dict(sessions_meta)
    except:
        st.sidebar.markdown("### Session hasn't been named yet. Please name the session in the Polar system.")
        st.stop()
    inv_sessions_dict = {v: k for k, v in sessions_dict.items()}#
    # selected_session_name = st.sidebar.multiselect("Pick training sessions",
    #                                           options=inv_sessions_dict.keys())
    # selected_session_name = st.radio("Available training sessions")
    
   
    #for simplicity
    if len(list(inv_sessions_dict)) == 0:
        st.sidebar.markdown("### No sessions for that day!")
        st.stop()
    else:
        # df_sessions_day  = pd.DataFrame(inv_sessions_dict.keys(), columns=["List of training sessions"])
        # df_sessions_day = df_sessions_day.rename(columns={"0":"List of training sessions"})
        

        time_map_session = []
        for i in list(inv_sessions_dict.keys()):
            time_map_session.append([i,i.split("(")[-1].split(',')[-1].split("-")[0].strip()[0:2], i.split("(")[-1].split(',')[-1].split("-")[0].strip()[3:]])

        df_sessions_day = pd.DataFrame(time_map_session, columns = ['List of training sessions', 'hour', 'minute'])
        df_sessions_day = df_sessions_day.sort_values(['hour', 'minute'])
        df_sessions_day = df_sessions_day.reset_index()
        df_sessions_day = df_sessions_day.drop(['index', 'hour', 'minute'], axis=1)
        df_sessions_day.index += 1 
        st.sidebar.dataframe(df_sessions_day)

        training_sessions_lst = list(df_sessions_day['List of training sessions'])
        no_of_session = int(no_of_session) - 1
        selected_session_name = training_sessions_lst[no_of_session]
        # st.sidebar.dataframe(df_sessions_day)
        # session_id = sessions_meta['data'][-(int(no_of_session))]['id']

        # selected_session_name = list(inv_sessions_dict)[0]
        
        selected_session_id = inv_sessions_dict[selected_session_name]
        # st.write(selected_session_id)
        data = session_data(selected_session_id, selected_session_name)
        df_plot_clean = clean_df(data, volume=True)

        # prep dataframe for table
        df_volume_table = df_plot_clean.reset_index().drop("position_name", axis=1)
        df_volume_table = df_volume_table[~df_volume_table.iloc[:, 0].str.contains("Åvg.|Avg.")]

        # clean decimals
        df_volume_table.iloc[:, :-1] = df_volume_table.iloc[:, :-1].astype(int, errors="ignore")
        df_volume_table.iloc[:,-1] = df_volume_table.iloc[:,-1].round(1)

        daily_volume_parameters_df_volume = daily_volume_parameters.copy()
        daily_volume_parameters_df_volume.insert(0, 'athlete_name')
        daily_volume_plot_names_df_volume = daily_volume_plot_names.copy()
        daily_volume_plot_names_df_volume.insert(0, 'athlete_name')

        df_volume_table = df_volume_table[daily_volume_parameters_df_volume]
        df_volume_table.columns = daily_volume_plot_names_df_volume

        df_plot_clean = df_plot_clean[daily_volume_parameters]
        df_plot_clean.columns = daily_volume_plot_names

        ## --------- ROLLING 7 DAYS --------- ##
        convert_datetime_to_string = lambda dt: dt.strftime("%d-%m-%Y")
        activity_start_time = datetime.strptime(selected_date, '%d-%m-%Y').date()
        previous_activity_start_time = activity_start_time - timedelta(7)

        activity_start_time = convert_datetime_to_string(activity_start_time)
        previous_activity_start_time = convert_datetime_to_string(previous_activity_start_time)

        sessions_data = api.get_sessions(tokens=tokens, team_id=team_id, dates=[previous_activity_start_time, activity_start_time])
        sessions_interval_dict = get_interval_sessions_name_id_dict(sessions_data)
        #%%
        sessions_dfs_lst = []
        for i, j in sessions_interval_dict.items():
            s_df = session_data(i, j)
            # df_plot_clean = clean_df(s_df)
            sessions_dfs_lst.append(s_df)

        df_plot_previous = pd.concat(sessions_dfs_lst)

        

        df_plot_previous.columns = daily_volume_plot_names
        
        df_max_speed = df_plot_previous.copy()
        df_max_speed = df_max_speed['Max Speed (km/h)']
        df_max_speed = df_max_speed.groupby(["position_name", "athlete_name"]).max()
        df_plot_previous = df_plot_previous.drop("Max Speed (km/h)", axis=1)
        df_plot_clean_previous = df_plot_previous.groupby(["position_name", "athlete_name"]).sum().div(len(sessions_interval_dict))

        df_plot_clean_previous = df_plot_clean_previous.join(df_max_speed, on=["position_name", "athlete_name"])

        # sort position
        df_plot_clean_previous = clean_df(df_plot_clean_previous, volume=True)
        position_order = ["Avg. Team", "Centre Back", "Full Back", "Midfielder", "Attacker"]
        df_plot_clean_previous = df_plot_clean_previous.reindex(position_order, axis=0, level=0)

        #%%
        # prep dataframe for table
        df_volume_table_previous = df_plot_clean_previous.reset_index().drop("position_name", axis=1)
        df_volume_table_previous = df_volume_table_previous[~df_volume_table_previous.iloc[:, 0].str.contains("Åvg.|Avg.")]

        # clean decimals
        df_volume_table_previous.iloc[:, :-1] = df_volume_table_previous.iloc[:, :-1].astype(int, errors="ignore")
        df_volume_table_previous.iloc[:,-1] = df_volume_table_previous.iloc[:,-1].round(1)
    

        ## ------- PLOTTING MAIN PAGE ------- ##
        st.write("### **Daily Physical Report**")


        col1, col2 = st.columns(2)
        with PdfPages(f"Physical Report {selected_session_name.split('(')[0]}.pdf") as pdf:
        
            # plot
            plot_day = plot_physical_volume(df_plot_clean, f"Physical Volume\n{selected_session_name.split('(')[0]}", team=chosen_team_long)
            col1.pyplot(plot_day)
            pdf.savefig(bbox_inches='tight')
            
            # plot
            plot_previous = plot_physical_volume(df_plot_clean_previous, f"Rolling 7 days\n{previous_activity_start_time}  to  {activity_start_time}", team=chosen_team_long)
            col2.pyplot(plot_previous)
            pdf.savefig(bbox_inches='tight')        
            
            ## TABLES
            # plot table
            daily_table = plot_table(df_volume_table, main_col = 'Total Distance', title=f"Physical Volume\n{selected_session_name.split('(')[0]}")
            col1.pyplot(daily_table)
            pdf.savefig(bbox_inches='tight')
            
            # plot table
            weekly_table = plot_table(df_volume_table_previous, main_col="Total Distance", title=f"Rolling 7 days\n{previous_activity_start_time}  to  {activity_start_time}")
            col2.pyplot(weekly_table)
            pdf.savefig(bbox_inches='tight')
            
        with open(f"Physical Report {selected_session_name.split('(')[0]}.pdf", "rb") as report:
            st.download_button("Download Report", report, f"Physical Report {selected_session_name.split('(')[0]}.pdf")
        
        # Add interactive tables
        col1.markdown(f"**{selected_session_name.split('(')[0]} Physical Volume**")
        col1.dataframe(df_plot_clean.style.background_gradient().format(precision=1))
        
        col2.markdown(f"**Physical Volume\n{previous_activity_start_time}  to  {activity_start_time}**")
        col2.dataframe(df_plot_clean_previous.style.background_gradient().format(precision=1))
        
        ## ------- ALTAIR PLOT ------- ##
        
        # Volume
        if account == 'M':
            alt_col1, alt_col2 = st.columns(2)
            df_altair_plot = df_plot_clean.reset_index()
            df_altair_plot.columns = [col.strip() for col in df_altair_plot.columns]
            
            altair_volume_plot = plot_altair_scatter(df_altair_plot, title="Daily Volume Load",
                                                        x="Total Distance:Q", y="HSR distance (>20km/h):Q",
                                                        tooltip=["athlete_name:N", "Total Distance:Q", "HSR distance (>20km/h):Q"],
                                                        color="position_name:N", width=600, height=600, label="athlete_name:N", size=100)
            alt_col1.altair_chart(altair_volume_plot)

            # Intensity
            altair_intensity_plot = plot_altair_scatter(df_altair_plot, title="Daily Intensity Load",
                                                        x="Sprint distance (>25km/h):Q", y="Sprint efforts (>25km/h):Q",
                                                        tooltip=["athlete_name:N", "Sprint distance (>25km/h):Q", "Sprint efforts (>25km/h):Q", "Max Speed (km/h):Q"],
                                                        color="position_name:N", width=600, height=600, label="athlete_name:N", size=100)
            alt_col2.altair_chart(altair_intensity_plot)
            # Mechanical
            altair_mechanical_plot = plot_altair_scatter(df_altair_plot, title="Daily Mechanical Load",
                                                        x="Acc (>3m/s):Q", y="Dec (>-3m/s):Q",
                                                        tooltip=["athlete_name:N", "Acc (>3m/s):Q", "Dec (>-3m/s):Q", "Max Speed (km/h):Q"],
                                                        color="position_name:N", width=600, height=600, label="athlete_name:N", size=100)
            alt_col1.altair_chart(altair_mechanical_plot)
            # Internal
            altair_internal_plot = plot_altair_scatter(df_altair_plot, title="Daily Internal Load",
                                                        x="Sprint distance (>25km/h):Q", y="HR (>85%):Q",
                                                        tooltip=["athlete_name:N", "Sprint distance (>25km/h):Q", "Sprint efforts (>25km/h):Q", "Max Speed (km/h):Q"],
                                                        color="position_name:N", width=600, height=600, label="athlete_name:N", size=100)
            alt_col2.altair_chart(altair_internal_plot)
        
        elif account == 'W':
            alt_col1, alt_col2 = st.columns(2)
            df_altair_plot = df_plot_clean.reset_index()
            df_altair_plot.columns = [col.strip() for col in df_altair_plot.columns]

            altair_volume_plot = plot_altair_scatter(df_altair_plot, title="Daily Volume Load",
                                                    x="Total Distance:Q", y="HSR distance (>19km/h):Q",
                                                    tooltip=["athlete_name:N", "Total Distance:Q", "HSR distance (>19km/h):Q"],
                                                    color="position_name:N", width=600, height=600, label="athlete_name:N", size=100)
            alt_col1.altair_chart(altair_volume_plot)

            # # Intensity
            # altair_intensity_plot = plot_altair_scatter(df_altair_plot, title="Daily Intensity Load",
            #                                             x="Sprint distance (>22.5km/h):Q", y="Sprint efforts (>22.5km/h):Q",
            #                                             tooltip=["athlete_name:N", "Sprint distance (>22.5km/h):Q", "Sprint efforts (>22.5km/h):Q", "Max Speed (km/h):Q"],
            #                                             color="position_name:N", width=600, height=600, label="athlete_name:N", size=100)
            # alt_col2.altair_chart(altair_intensity_plot)
            # # Mechanical
            # altair_mechanical_plot = plot_altair_scatter(df_altair_plot, title="Daily Mechanical Load",
            #                                             x="Acc (>2.7m/s):Q", y="Dec (>-2.7m/s):Q",
            #                                             tooltip=["athlete_name:N", "Acc (>2.7m/s):Q", "Dec (>-2.7m/s):Q", "Max Speed (km/h):Q"],
            #                                             color="position_name:N", width=600, height=600, label="athlete_name:N", size=100)
            # alt_col2.altair_chart(altair_mechanical_plot)
            # #Internal
            # altair_internal_plot = plot_altair_scatter(df_altair_plot, title="Daily Internal Load",
            #                                             x="Sprint distance (>22.5km/h):Q", y="HR (>85%):Q",
            #                                             tooltip=["athlete_name:N", "Sprint distance (>22.5km/h):Q", "Sprint efforts (>22.5km/h):Q", "Max Speed (km/h):Q"],
            #                                             color="position_name:N", width=600, height=600, label="athlete_name:N", size=100)
            # alt_col2.altair_chart(altair_internal_plot)


else:
    pass

#%%

#%%