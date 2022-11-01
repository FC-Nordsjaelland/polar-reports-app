import requests
import webbrowser
import base64
import pandas as pd
import isodate

from utils.polar_IO import (flatten_list,
                            daterange,
                            get_key)
# POLAR API DOCUMENTATION
# https://www.polar.com/teampro-api/?python#teampro-api

# -------- AUTHORIZATION AND ACCESS TOKENS --------- #


class POLAR_API:
    def __init__(self, client_id, client_secret, team):

        self.client_id = client_id
        self.client_secret = client_secret
        self.team = team
        self.authorize_url = 'https://auth.polar.com/oauth/authorize'
        self.access_token_url = 'https://auth.polar.com/oauth/token'
        self.authorize_params = {'client_id': self.client_id,
                                 'response_type': 'code',
                                 'scope': 'team_read'}

    def _extract_team_id(self, teams_info, team):
        teams_data = teams_info['data']
        for data in teams_data:
            if data['name'] == self.team:
                print(data['name'])
                team_id = data['id']

                return team_id

    def extract_players(self, players_and_staff):
        # extract only players
        players = players_and_staff['data']['players']
        # convert to dataframe
        df_players = pd.json_normalize(players)
        # remove staff
        df_players = df_players[df_players['player_number'] < 100]

        return df_players

    def retrieve_authorization_code(self):
        r = requests.get(self.authorize_url, params=self.authorize_params)

        webbrowser.open(r.history[0].url, new=2)
        authorization_code = input("Authorization Code: ")

        return authorization_code

    def retrieve_tokens(self):

        encoding = self.client_id+':'+self.client_secret
        message_bytes = encoding.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_encoding = base64_bytes.decode('ascii')
        headers = {'Authorization': 'Basic '+base64_encoding}

        authorization_code = self.retrieve_authorization_code()

        # POST request to get access token
        access_token_data = {'grant_type': 'authorization_code',
                             'code': authorization_code}
        r_post = requests.post(self.access_token_url,
                               data=access_token_data,
                               headers=headers)
        tokens = r_post.json()

        return tokens

    def get_teams_info(self, tokens, get_team_id=False):
        access_token = tokens['access_token']
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer '+access_token
        }
        r = requests.get('https://teampro.api.polar.com/v1/teams',
                         params={},
                         headers=headers)
        teams_info = r.json()
        if get_team_id:
            return self._extract_team_id(teams_info, self.team)

        return teams_info

    def get_team_players(self, tokens, team_id):
        access_token = tokens['access_token']
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer '+access_token
        }
        r = requests.get(f'https://teampro.api.polar.com/v1/teams/{team_id}',
                         params={},
                         headers=headers)
        players_and_staff = r.json()

        return players_and_staff

    def get_sessions(self, tokens, team_id, date):
        access_token = tokens['access_token']
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer '+access_token
        }
        day, month, year = date.split('-')
        r = requests.get(f'https://teampro.api.polar.com/v1/teams/{team_id}/training_sessions',
                         params={'since': f'{year}-{month}-{day}T00:00:00',
                                 'until': f'{year}-{month}-{day}T23:59:59',
                                 'per_page': '100'},
                         headers=headers)
        sessions_metadata = r.json()
        return sessions_metadata

    def get_players_session_data(self, tokens, session_id):
        access_token = tokens['access_token']
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer '+access_token
        }
        r = requests.get(f'https://teampro.api.polar.com/v1/teams/training_sessions/{session_id}',
                         params={}, headers=headers)
        session_data = r.json()

        return session_data

    def get_player_session_details(self, tokens, player_session_id):
        access_token = tokens['access_token']
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer '+access_token
        }
        r = requests.get(f'https://teampro.api.polar.com/v1/training_sessions/{player_session_id}',
                         params={'samples': 'all'}, headers=headers)
        player_session_details = r.json()

        return player_session_details

    def get_trimmed_player_session_details(self, tokens, player_session_id):
        access_token = tokens['access_token']
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer '+access_token
        }
        r = requests.get(f'https://teampro.api.polar.com/v1/training_sessions/{player_session_id}/session_summary',
                         params={}, headers=headers)
        session_details = r.json()

        return session_details
    

    # --------------- CLEANING --------------- #
    def get_sessions_multiple(self, date, tokens, team_id):
        """Get information from session(s). Can get sessions from the daterange or all available dates

            Args:
                tokens (json object): tokens json object
                team_id (str): team name from Polar
                date (str or list, optional): date or date range to get sessions from
                                            (e.g. date -> "12-08-2021" or "["01-08-2021", "12-08-2021"]").
                                            Defaults to None.

            Returns:
                DataFrame: information from the sessions (id, team_id, created, modified etc.)
        """

        access_token = tokens['access_token']
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer '+access_token
        }

        # return sessions dependent on date specifics
        # Get session data within a date range
        if type(date) == list:
            day1, month1, year1 = date[0].split('-')
            day2, month2, year2 = date[1].split('-')
            r_new = requests.get(f'https://teampro.api.polar.com/v1/teams/{team_id}/training_sessions',
                                params={'since': f'{year1}-{month1}-{day1}T00:00:00',
                                        'until': f'{year2}-{month2}-{day2}T23:59:59'},
                                headers=headers)
            # get total session in order to load all sessions
            session_data = r_new.json()
            total_pages = session_data['page']['total_pages']
            # if more than one page of data, then iterate through
            if total_pages > 0:
                all_sessions = []
                for i in range(total_pages):
                    r_new = requests.get(f'https://teampro.api.polar.com/v1/teams/{team_id}/training_sessions?page={i}',
                                        params={'since': f'{year1}-{month1}-{day1}T00:00:00',
                                                'until': f'{year2}-{month2}-{day2}T23:59:59'},
                                        headers=headers)

                    page_data = r_new.json()
                    session_data = page_data['data']
                    all_sessions.append(session_data)
                # concatenate list of sessions
                all_sessions = flatten_list(all_sessions)
                # convert to dataframe
                df_sessions = pd.json_normalize(all_sessions)

                return df_sessions

            page_data = r_new.json()
            session_data = page_data['data']
            df_sessions = pd.json_normalize(session_data)

            return df_sessions

        # Get session data from a single date
        if type(date) == str:
            day1, month1, year1 = date.split('-')
            r_new = requests.get(f'https://teampro.api.polar.com/v1/teams/{team_id}/training_sessions',
                                params={'since': f'{year1}-{month1}-{day1}T00:00:00',
                                        'until': f'{year1}-{month1}-{day1}T23:59:59'},
                                headers=headers)
            page_data = r_new.json()
            session_data = page_data['data']
            df_sessions = pd.json_normalize(session_data)

            return df_sessions

        # Get session data from all sessions
        if date == None:
            r = requests.get(f'https://teampro.api.polar.com/v1/teams/{team_id}/training_sessions',
                            params={}, headers=headers)

            # get total session in order to load all sessions
            session_data = r.json()
            total_pages = session_data['page']['total_pages']

            all_sessions = []
            # iterate through all pages
            for i in range(total_pages):
                r_new = requests.get(f'https://teampro.api.polar.com/v1/teams/{team_id}/training_sessions?page={i}',
                                    params={}, headers=headers)
                page_data = r_new.json()
                session_data = page_data['data']
                all_sessions.append(session_data)
            # concatenate list of sessions
            all_sessions = flatten_list(all_sessions)
            # convert to dataframe
            df_sessions = pd.json_normalize(all_sessions)

            return df_sessions

    def get_player_session_ids(self, tokens, session_id):
        """Get session ids from all players from a session

            Args:
                tokens (json object): tokens json object
                session_id (str): id from session

            Returns:
                dict: dictionary of mapping between player id and session id
        """
        access_token = tokens['access_token']
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer '+access_token
        }
        r = requests.get(f'https://teampro.api.polar.com/v1/teams/training_sessions/{session_id}',
                        params={}, headers=headers)

        # get session data
        session_data = r.json()
        # get player session id
        participants = session_data['data']['participants']
        df_participants = pd.json_normalize(participants)

        # create dictionary of session ids and player ids
        player_ids = list(df_participants['player_id'])
        player_session_ids = list(df_participants['player_session_id'])

        zip_iterator = zip(player_ids, player_session_ids)
        session_ids_dict = dict(zip_iterator)

        return session_ids_dict

    # ------ TRAINING SESSION TRIMMED ------- #


    def clean_zone_df(self, df, zone):
        """Clean columns that are divided into zones (e.g. heart rate, acceleration, running distance)

            Args:
                df (DataFrame): DataFrame with Polar data to be cleaned
                zone (str): which zone to be cleaned, "hr", "speed" or "acceleration"

            Returns:
                DataFrame: clean dataframe
        """
        cols_to_drop = ['lower_limit_1', 'lower_limit_2', 'lower_limit_3', 'lower_limit_4', 'lower_limit_5',
                        'higher_limit_1', 'higher_limit_2', 'higher_limit_3', 'higher_limit_4', 'higher_limit_5']
        hr_cols_to_keep = ['in_zone_1', 'in_zone_2',
                        'in_zone_3', 'in_zone_4', 'in_zone_5']
        speed_cols_to_keep = ['in_zone_meters_1', 'in_zone_meters_2',
                            'in_zone_meters_3', 'in_zone_meters_4', 'in_zone_meters_5']
        if zone == 'hr':
            cols_to_keep = hr_cols_to_keep
        elif zone == 'speed':
            cols_to_keep = speed_cols_to_keep
        elif zone == 'acceleration':
            # Convert row into columns
            df = df.pivot(index='player_session_id', columns='limit').reset_index()
            # Collapse columns
            df.columns = df.columns.to_flat_index()
            df.rename(columns=lambda x: '_'.join(map(str, x)), inplace=True)
            return df
        else:
            print('Not a valid zone')
            return None
        # Convert row into columns
        df = df.pivot(index='player_session_id', columns='index').reset_index()
        # Collapse columns
        df.columns = df.columns.to_flat_index()
        df.rename(columns=lambda x: '_'.join(map(str, x)), inplace=True)
        df.drop(cols_to_drop, axis=1, inplace=True)  # drop higher and lower limits
        # Parse times and rename columns
        if zone == 'hr':
            for col in cols_to_keep:
                df[col] = df[col].apply(isodate.parse_duration)
                # Remove days from time zones
                df[col] = df[col].astype(str).str.split('0 days ').str[-1]
                # entries with 0 minutes show 0 days, thus replace with 00:00:00
                df[col].replace('0 days', '00:00:00', inplace=True)
        return df


    def get_player_session_details_trimmed(self, tokens, player_session_id):
        """Get trimmed values for a player

            Args:
                tokens (json object): tokens json object
                player_session_id (str): session id from a player

            Returns:
                DataFrame: trimmed training session values (formatted like the "Export" function in teampro.polar.com)
        """
        access_token = tokens['access_token']
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer '+access_token
        }
        r = requests.get(f'https://teampro.api.polar.com/v1/training_sessions/{player_session_id}/session_summary',
                        params={}, headers=headers)
        session_details = r.json()
        # time.sleep(2)

        # Split columns with zones into multiple dataframe and merge them in get_all function
        # ------ Heart Rate Zones ------- #
        # heart_rate_zones	speed_zones_kmh	acceleration_zones_ms2
        df_hr_zones = pd.json_normalize(session_details['data'], record_path='heart_rate_zones',
                                        meta='player_session_id')
        df_hr_zones = self.clean_zone_df(df_hr_zones, zone='hr')
        hr_cols = ['player_session_id', 'Time in HR zone 1 (50 - 59 %)', 'Time in HR zone 2 (60 - 69 %)',
                'Time in HR zone 3 (70 - 79 %)', 'Time in HR zone 4 (80 - 89 %)', 'Time in HR zone 5 (90 - 100 %)']
        df_hr_zones.columns = hr_cols
        # ------ Speed Zones ------- #
        df_speed_zones = pd.json_normalize(session_details['data'], record_path='speed_zones_kmh',
                                        meta='player_session_id')
        df_speed_zones = self.clean_zone_df(df_speed_zones, zone='speed')
        speed_cols = ['player_session_id', 'Distance in Speed zone 1 [m] (12.00 - 20.99 km/h)', 'Distance in Speed zone 2 [m] (21.00 - 23.99 km/h)',
                    'Distance in Speed zone 3 [m] (24.00 - 25.19 km/h)', 'Distance in Speed zone 4 [m] (25.20 - 29.99 km/h)', 'Distance in Speed zone 5 [m] (30.00- km/h)']
        df_speed_zones.columns = speed_cols
        # ------ Acceleration Zones ------- #
        df_acceleration_zones = pd.json_normalize(session_details['data'], record_path='acceleration_zones_ms2',
                                                meta='player_session_id')
        df_acceleration_zones = self.clean_zone_df(
            df_acceleration_zones, zone='acceleration')
        acceleration_cols = ['player_session_id', 'Number of accelerations (-50.00 - -9.00 m/s²)', 'Number of accelerations (-8.99 - -6.00 m/s²)', 'Number of accelerations (-5.99 - -3.00 m/s²)',
                            'Number of accelerations (-2.99 - -0.50 m/s²)', 'Number of accelerations (0.50 - 2.99 m/s²)', 'Number of accelerations (3.00 - 5.99 m/s²)',
                            'Number of accelerations (6.00 - 8.99 m/s²)', 'Number of accelerations (9.00 - 50.00 m/s²)']
        df_acceleration_zones.columns = acceleration_cols

        # ---- Merge zones dataframes with original dataframe ----- #
        df_all_details = pd.json_normalize(session_details['data'])

        # Modify time columns (duration, start_time, end_time)
        df_all_details['trimmed_start_time'] = isodate.parse_datetime(
            df_all_details['trimmed_start_time'][0])
        df_all_details['trimmed_start_time'] = df_all_details['trimmed_start_time'].dt.time
        df_all_details['duration_ms'] = pd.to_datetime(
            df_all_details['duration_ms'], unit='ms').dt.time
        # Calculate distance per min.
        df_all_details['distance_per_min'] = df_all_details['distance_meters'] / \
            df_all_details['duration_ms'].astype(str).str.split(
                ':').apply(lambda x: int(x[0]) * 60 + int(x[1]))
        # Calculate end time
        df_all_details['end_time'] = (pd.to_timedelta(df_all_details['trimmed_start_time'].astype(str))
                                    + pd.to_timedelta(df_all_details['duration_ms'].astype(str)))
        df_all_details['end_time'] = df_all_details['end_time'].astype(
            str).str.split('0 days ').str[-1]

        # Remove and rename columns
        df_all_details.drop(['heart_rate_zones', 'speed_zones_kmh', 'acceleration_zones_ms2'],
                            axis=1, inplace=True)
        df_all = [df_all_details.set_index('player_session_id'), df_hr_zones.set_index('player_session_id'),
                df_speed_zones.set_index('player_session_id'), df_acceleration_zones.set_index('player_session_id')]

        df_final = pd.concat(df_all, axis=1).reset_index()
        # Drop and rename columns
        cols_to_drop = ['created', 'modified',
                        'player_session_id', 'cadence_avg', 'cadence_max']
        cols_to_rename = {'duration_ms': 'Duration',
                        'trimmed_start_time': 'Start time',
                        'end_time': 'End time',
                        'heart_rate_min': 'HR min [bpm]',
                        'heart_rate_avg': 'HR avg [bpm]',
                        'heart_rate_max': 'HR max [bpm]',
                        'heart_rate_min_percent': 'HR min [%]',
                        'heart_rate_avg_percent': 'HR avg [%]',
                        'heart_rate_max_percent': 'HR max [%]',
                        'distance_meters': 'Total distance [m]',
                        'distance_per_min': 'Distance / min [m/min]',
                        'speed_max_kmh': 'Maximum speed [km/h]',
                        'speed_avg_kmh': 'Average speed [km/h]',
                        'sprint_counter': 'Sprints',
                        'kilo_calories': 'Calories [kcal]',
                        'training_load': 'Training load score'
                        }
        df_final.drop(cols_to_drop, axis=1, inplace=True)
        df_final.rename(columns=cols_to_rename, inplace=True)

        # ------ Clean top speeds ------- #
        #df_top_speed = pd.read_csv('utils/top_speeds.csv')
        top_speed = 37
        df_final['Maximum speed [km/h]'] = df_final['Maximum speed [km/h]'].apply(
            lambda x: x if x <= top_speed else top_speed)

        # Calculate times in minutes
        # cols_to_convert = ['Duration', 'Time in HR zone 1 (50 - 59 %)', 'Time in HR zone 2 (60 - 79 %)',
        #                   'Time in HR zone 3 (80 - 84 %)', 'Time in HR zone 4 (85 - 94 %)', 'Time in HR zone 5 (95 - 100 %)']

        #df_final = pd.concat([df_final, df_converted])

        return df_final


    def get_all_player_session_details_trimmed(self, tokens, player_session_ids, team_id,
                                            save_as_csv=False, path=None):
        """Get trimmed values from multiple players

            Args:
                tokens (json object): tokens json object
                player_session_ids (dictionary): player ids and player session ids
                team_id (str): id for a team
                save_as_csv (bool, optional): True/False option to save as csv file. Defaults to False.
                path (str, optional): If save as csv, then provide path and filename. Defaults to None.

            Returns:
                DataFrame: All trimmed values from all players for a session
        """
        # go through all session ids and get_player_session_details
        df_all = []
        for player_id, player_session_id in player_session_ids.items():
            df_session_player = self.get_player_session_details_trimmed(
                tokens, player_session_id)
            df_session_player.insert(loc=0, column='player_id', value=player_id)

            df_all.append(df_session_player)
        # Concatenate all players into 1 dataframe
        df_all_players = pd.concat(df_all).reset_index(drop=True)

        # Make heart_rate_zones, speed_zones and distance into different columns/zones
        #df_all_players = df_all_players.pivot(index='player_id', columns='index').reset_index()
        #df_all_players.columns = df_all_players.columns.to_flat_index()

        # save as csv
        if save_as_csv:
            df_all_players.to_csv(
                f'{path}/{player_id}_trimmed_data.csv', index=False)

        return df_all_players