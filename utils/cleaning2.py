import pandas as pd
import streamlit as st
from polar_api import PolarTeamproAPI


def init_api(client_id, client_secret, redirect_uri):
    client = PolarTeamproAPI(
        client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri
    )
    return client


def hms_to_m(s):
    t = 0
    for u in s.split(":"):
        t = 60 * t + int(float(u))
    return int(t / 60)


def clean_players_df(players):
    map_positions = {
        "Forsvar": "Centre Back",
        "Midtbane": "Midfielder",
        "Angriber": "Attacker",
    }
    players["role"] = players["role"].map(map_positions)
    players.dropna()
    return players


def clean_sessions(sessions_json):
    sessions = {}
    for i in sessions_json["data"]:
        name = i["name"]
        start_time = i["record_start_time"].split("T")[1][:5]
        end_time = i["record_end_time"].split("T")[1][:5]
        session = name + " (" + start_time + "-" + end_time + ")"
        id = i["id"]
        sessions[session] = id
    return sessions


def get_player_session_ids(session_data):
    participants = session_data["data"]["participants"]
    df_participants = pd.json_normalize(participants)

    # create dictionary of session ids and player ids
    player_ids = list(df_participants["player_id"])
    player_session_ids = list(df_participants["player_session_id"])

    zip_iterator = zip(player_ids, player_session_ids)
    session_ids_dict = dict(zip_iterator)
    return session_ids_dict


def preprocess(data, set_date, team_players, session_name, account):
    data["Start time"] = data["Start time"].astype(str)
    data["Start time"] = set_date + " " + data["Start time"]
    data["End time"] = set_date + " " + data["End time"]

    id_df = team_players
    id_df["full_name"] = id_df["first_name"] + " " + id_df["last_name"]
    id_name = dict(zip(list(id_df["player_id"]), list(id_df["full_name"])))

    data["Player name"] = data["player_id"]
    data.replace({"Player name": id_name}, inplace=True)
    id_df = id_df[["player_id", "player_number"]]

    data = pd.merge(data, id_df, how="inner", on="player_id")
    data.rename(
        columns={"player_number": "Player number", "cardio_load": "Cardio load"},
        inplace=True,
    )
    data["Recovery time [h]"] = 0

    data["Session name"] = session_name
    data["Type"] = "Training"
    data["Phase name"] = "Whole session"

    if account == "M":
        data.rename(
            columns={
                "Time in HR zone 1 (50 - 69 %)": "Time in HR zone 1 (50 - 59 %)",
                "Time in HR zone 2 (60 - 69 %)": "Time in HR zone 2 (60 - 79 %)",
                "Time in HR zone 3 (70 - 79 %)": "Time in HR zone 3 (80 - 84 %)",
                "Time in HR zone 4 (80 - 89 %)": "Time in HR zone 4 (85 - 94 %)",
                "Time in HR zone 5 (90 - 100 %)": "Time in HR zone 5 (95 - 100 %)",
            },
            inplace=True,
        )

        # final_columns = list(template.columns.values)
        final_columns = [
            "Player number",
            "Player name",
            "Session name",
            "Type",
            "Phase name",
            "Duration",
            "Start time",
            "End time",
            "HR min [bpm]",
            "HR avg [bpm]",
            "HR max [bpm]",
            "HR min [%]",
            "HR avg [%]",
            "HR max [%]",
            "Time in HR zone 1 (50 - 59 %)",
            "Time in HR zone 2 (60 - 79 %)",
            "Time in HR zone 3 (80 - 84 %)",
            "Time in HR zone 4 (85 - 94 %)",
            "Time in HR zone 5 (95 - 100 %)",
            "Total distance [m]",
            "Distance / min [m/min]",
            "Maximum speed [km/h]",
            "Average speed [km/h]",
            "Sprints",
            "Distance in Speed zone 1 [m] (12.00 - 20.99 km/h)",
            "Distance in Speed zone 2 [m] (21.00 - 23.99 km/h)",
            "Distance in Speed zone 3 [m] (24.00 - 25.19 km/h)",
            "Distance in Speed zone 4 [m] (25.20 - 29.99 km/h)",
            "Distance in Speed zone 5 [m] (30.00- km/h)",
            "Number of accelerations (-50.00 - -9.00 m/s²)",
            "Number of accelerations (-8.99 - -6.00 m/s²)",
            "Number of accelerations (-5.99 - -3.00 m/s²)",
            "Number of accelerations (-2.99 - -0.50 m/s²)",
            "Number of accelerations (0.50 - 2.99 m/s²)",
            "Number of accelerations (3.00 - 5.99 m/s²)",
            "Number of accelerations (6.00 - 8.99 m/s²)",
            "Number of accelerations (9.00 - 50.00 m/s²)",
            "Calories [kcal]",
            "Training load score",
            "Cardio load",
            "Recovery time [h]",
            "Duration_min",
            "Time in HR zone 1 (50 - 59 %)",
            "Time in HR zone 2 (60 - 69 %)",
            "Time in HR zone 3 (70 - 79 %)",
            "Time in HR zone 4 (80 - 89 %)",
            "Time in HR zone 5 (90 - 100 %)",
        ]

        columns_before_calc = final_columns[:-6]
        data = data[columns_before_calc]

        # additional_columns = ['Duration',
        # 'Time in HR zone 1 (50 - 59 %)',
        # 'Time in HR zone 2 (60 - 69 %)',
        # 'Time in HR zone 3 (70 - 79 %)',
        # 'Time in HR zone 4 (80 - 89 %)',
        # 'Time in HR zone 5 (90 - 100 %)']

        data = pd.concat(
            [
                data,
                pd.Series(
                    data["Duration"].astype(str).apply(hms_to_m), name="Duration_min"
                ),
            ],
            axis=1,
        )
        data = pd.concat(
            [
                data,
                pd.Series(
                    data["Time in HR zone 1 (50 - 59 %)"].apply(hms_to_m),
                    name="Time in HR zone 1 (50 - 59 %)",
                ),
            ],
            axis=1,
        )
        data = pd.concat(
            [
                data,
                pd.Series(
                    data["Time in HR zone 2 (60 - 79 %)"].apply(hms_to_m),
                    name="Time in HR zone 2 (60 - 69 %)",
                ),
            ],
            axis=1,
        )
        data = pd.concat(
            [
                data,
                pd.Series(
                    data["Time in HR zone 3 (80 - 84 %)"].apply(hms_to_m),
                    name="Time in HR zone 3 (70 - 79 %)",
                ),
            ],
            axis=1,
        )
        data = pd.concat(
            [
                data,
                pd.Series(
                    data["Time in HR zone 4 (85 - 94 %)"].apply(hms_to_m),
                    name="Time in HR zone 4 (80 - 89 %)",
                ),
            ],
            axis=1,
        )
        data = pd.concat(
            [
                data,
                pd.Series(
                    data["Time in HR zone 5 (95 - 100 %)"].apply(hms_to_m),
                    name="Time in HR zone 5 (90 - 100 %)",
                ),
            ],
            axis=1,
        )
        data["Maximum speed [km/h]"] = data["Maximum speed [km/h]"].round(decimals=1)
        data["Average speed [km/h]"] = data["Average speed [km/h]"].round(decimals=1)

        columns_dec_0 = [
            "Total distance [m]",
            "Distance / min [m/min]",
            "Distance in Speed zone 1 [m] (12.00 - 20.99 km/h)",
            "Distance in Speed zone 2 [m] (21.00 - 23.99 km/h)",
            "Distance in Speed zone 3 [m] (24.00 - 25.19 km/h)",
            "Distance in Speed zone 4 [m] (25.20 - 29.99 km/h)",
            "Distance in Speed zone 5 [m] (30.00- km/h)",
        ]
        data[columns_dec_0] = data[columns_dec_0].round(decimals=0)
        data[columns_dec_0] = data[columns_dec_0].astype(int)

        data = data[
            [
                "Player name",
                "Duration",
                "Total distance [m]",
                "Distance in Speed zone 4 [m] (25.20 - 29.99 km/h)",
                "Distance in Speed zone 5 [m] (30.00- km/h)",
                "Sprints",
                "Number of accelerations (-50.00 - -9.00 m/s²)",
                "Number of accelerations (9.00 - 50.00 m/s²)",
                "Time in HR zone 4 (80 - 89 %)",
                "Time in HR zone 5 (90 - 100 %)",
                "Maximum speed [km/h]",
                "Duration_min",
            ]
        ]

        data = pd.merge(
            data,
            team_players[["full_name", "role"]],
            left_on="Player name",
            right_on="full_name",
        )
        data = data.drop(["full_name"], axis=1)
        data = data.rename(
            columns={
                "role": "position_name",
                "Player name": "athlete_name",
                "Duration_min": "Minutes",
                "Total distance [m]": "Total Distance",
            }
        )
        sum_hr = (
            data["Time in HR zone 4 (80 - 89 %)"]
            + data["Time in HR zone 5 (90 - 100 %)"]
        )
        data["HR (>85%)"] = sum_hr
        data = data.drop(
            ["Time in HR zone 4 (80 - 89 %)", "Time in HR zone 5 (90 - 100 %)"], axis=1
        )
        data = data[
            [
                "athlete_name",
                "position_name",
                "Minutes",
                "Total Distance",
                "Distance in Speed zone 4 [m] (25.20 - 29.99 km/h)",
                "Distance in Speed zone 5 [m] (30.00- km/h)",
                "Sprints",
                "Number of accelerations (-50.00 - -9.00 m/s²)",
                "Number of accelerations (9.00 - 50.00 m/s²)",
                "HR (>85%)",
                "Maximum speed [km/h]",
            ]
        ]

        data = data.set_index(["position_name", "athlete_name"])

    elif account == "W":
        # data.rename(columns={"Time in HR zone 2 (60 - 69 %)":"Time in HR zone 2 (60 - 69 %)",
        #                     "Time in HR zone 3 (70 - 79 %)":"Time in HR zone 3 (70 - 79 %)",
        #                     "Time in HR zone 4 (80 - 89 %)":"Time in HR zone 4 (80 - 89 %)",
        #                     "Time in HR zone 5 (90 - 100 %)":"Time in HR zone 5 (90 - 100 %)"}, inplace=True)

        data.rename(
            columns={
                "Distance in Speed zone 1 [m] (12.00 - 20.99 km/h)": "Distance in Speed zone 1 [m] (10.00 - 17.99 km/h)",
                "Distance in Speed zone 2 [m] (21.00 - 23.99 km/h)": "Distance in Speed zone 2 [m] (18.00 - 20.99 km/h)",
                "Distance in Speed zone 3 [m] (24.00 - 25.19 km/h)": "Distance in Speed zone 3 [m] (21.00 - 23.99 km/h)",
                "Distance in Speed zone 4 [m] (25.20 - 29.99 km/h)": "Distance in Speed zone 4 [m] (24.00 - 26.99 km/h)",
                "Distance in Speed zone 5 [m] (30.00- km/h)": "Distance in Speed zone 5 [m] (27.00- km/h)",
            },
            inplace=True,
        )

        data.rename(
            columns={
                "Number of accelerations (-50.00 - -9.00 m/s²)": "Number of accelerations (-50.00 - -2.70 m/s²)",
                "Number of accelerations (-8.99 - -6.00 m/s²)": "Number of accelerations (-2.69 - -2.00 m/s²)",
                "Number of accelerations (-5.99 - -3.00 m/s²)": "Number of accelerations (-1.99 - -1.00 m/s²)",
                "Number of accelerations (-2.99 - -0.50 m/s²)": "Number of accelerations (-0.99 - -0.50 m/s²)",
                "Number of accelerations (0.50 - 2.99 m/s²)": "Number of accelerations (0.50 - 0.99 m/s²)",
                "Number of accelerations (3.00 - 5.99 m/s²)": "Number of accelerations (1.00 - 1.99 m/s²)",
                "Number of accelerations (6.00 - 8.99 m/s²)": "Number of accelerations (2.00 - 2.69 m/s²)",
                "Number of accelerations (9.00 - 50.00 m/s²)": "Number of accelerations (2.70 - 50.00 m/s²)",
            },
            inplace=True,
        )

        # final_columns = list(girls_template.columns.values)
        final_columns = [
            "Player number",
            "Player name",
            "Session name",
            "Type",
            "Phase name",
            "Duration",
            "Start time",
            "End time",
            "HR min [bpm]",
            "HR avg [bpm]",
            "HR max [bpm]",
            "HR min [%]",
            "HR avg [%]",
            "HR max [%]",
            "Time in HR zone 1 (50 - 59 %)",
            "Time in HR zone 2 (60 - 69 %)",
            "Time in HR zone 3 (70 - 79 %)",
            "Time in HR zone 4 (80 - 89 %)",
            "Time in HR zone 5 (90 - 100 %)",
            "Total distance [m]",
            "Distance / min [m/min]",
            "Maximum speed [km/h]",
            "Average speed [km/h]",
            "Sprints",
            "Distance in Speed zone 1 [m] (10.00 - 17.99 km/h)",
            "Distance in Speed zone 2 [m] (18.00 - 20.99 km/h)",
            "Distance in Speed zone 3 [m] (21.00 - 23.99 km/h)",
            "Distance in Speed zone 4 [m] (24.00 - 26.99 km/h)",
            "Distance in Speed zone 5 [m] (27.00- km/h)",
            "Training load score",
            "Cardio load",
            "Recovery time [h]",
            "Calories [kcal]",
            "Number of accelerations (-50.00 - -2.70 m/s²)",
            "Number of accelerations (-2.69 - -2.00 m/s²)",
            "Number of accelerations (-1.99 - -1.00 m/s²)",
            "Number of accelerations (-0.99 - -0.50 m/s²)",
            "Number of accelerations (0.50 - 0.99 m/s²)",
            "Number of accelerations (1.00 - 1.99 m/s²)",
            "Number of accelerations (2.00 - 2.69 m/s²)",
            "Number of accelerations (2.70 - 50.00 m/s²)",
            "Duration_min",
            "Time in HR zone 1 (50 - 59 %)",
            "Time in HR zone 2 (60 - 69 %)",
            "Time in HR zone 3 (70 - 79 %)",
            "Time in HR zone 4 (80 - 89 %)",
            "Time in HR zone 5 (90 - 100 %)",
        ]

        columns_before_calc = final_columns[:-6]
        data = data[columns_before_calc]

        data = pd.concat(
            [
                data,
                pd.Series(
                    data["Duration"].astype(str).apply(hms_to_m), name="Duration_min"
                ),
            ],
            axis=1,
        )
        data = pd.concat(
            [
                data,
                pd.Series(
                    data["Time in HR zone 1 (50 - 59 %)"].apply(hms_to_m),
                    name="Time in HR zone 1 (50 - 59 %)",
                ),
            ],
            axis=1,
        )
        data = pd.concat(
            [
                data,
                pd.Series(
                    data["Time in HR zone 2 (60 - 69 %)"].apply(hms_to_m),
                    name="Time in HR zone 2 (60 - 69 %)",
                ),
            ],
            axis=1,
        )
        data = pd.concat(
            [
                data,
                pd.Series(
                    data["Time in HR zone 3 (70 - 79 %)"].apply(hms_to_m),
                    name="Time in HR zone 3 (70 - 79 %)",
                ),
            ],
            axis=1,
        )
        data = pd.concat(
            [
                data,
                pd.Series(
                    data["Time in HR zone 4 (80 - 89 %)"].apply(hms_to_m),
                    name="Time in HR zone 4 (80 - 89 %)",
                ),
            ],
            axis=1,
        )
        data = pd.concat(
            [
                data,
                pd.Series(
                    data["Time in HR zone 5 (90 - 100 %)"].apply(hms_to_m),
                    name="Time in HR zone 5 (90 - 100 %)",
                ),
            ],
            axis=1,
        )
        data["Maximum speed [km/h]"] = data["Maximum speed [km/h]"].round(decimals=1)
        data["Average speed [km/h]"] = data["Average speed [km/h]"].round(decimals=1)
        columns_dec_0 = [
            "Total distance [m]",
            "Distance / min [m/min]",
            "Distance in Speed zone 1 [m] (10.00 - 17.99 km/h)",
            "Distance in Speed zone 2 [m] (18.00 - 20.99 km/h)",
            "Distance in Speed zone 3 [m] (21.00 - 23.99 km/h)",
            "Distance in Speed zone 4 [m] (24.00 - 26.99 km/h)",
            "Distance in Speed zone 5 [m] (27.00- km/h)",
        ]
        data[columns_dec_0] = data[columns_dec_0].round(decimals=0)
        data[columns_dec_0] = data[columns_dec_0].astype(int)

        data = data[
            [
                "Player name",
                "Duration",
                "Total distance [m]",
                "Distance in Speed zone 4 [m] (24.00 - 26.99 km/h)",
                "Distance in Speed zone 5 [m] (27.00- km/h)",
                "Sprints",
                "Number of accelerations (-50.00 - -2.70 m/s²)",
                "Number of accelerations (2.70 - 50.00 m/s²)",
                "Time in HR zone 4 (80 - 89 %)",
                "Time in HR zone 5 (90 - 100 %)",
                "Maximum speed [km/h]",
                "Duration_min",
            ]
        ]

        data = pd.merge(
            data,
            team_players[["full_name", "role"]],
            left_on="Player name",
            right_on="full_name",
        )
        data = data.drop(["full_name"], axis=1)
        data = data.rename(
            columns={
                "role": "position_name",
                "Player name": "athlete_name",
                "Duration_min": "Minutes",
                "Total distance [m]": "Total Distance",
            }
        )

        sum_hr = (
            data["Time in HR zone 4 (80 - 89 %)"]
            + data["Time in HR zone 5 (90 - 100 %)"]
        )
        data["HR (>85%)"] = sum_hr
        data = data.drop(
            ["Time in HR zone 4 (80 - 89 %)", "Time in HR zone 5 (90 - 100 %)"], axis=1
        )

        data = data[
            [
                "athlete_name",
                "position_name",
                "Minutes",
                "Total Distance",
                "Distance in Speed zone 4 [m] (24.00 - 26.99 km/h)",
                "Distance in Speed zone 5 [m] (27.00- km/h)",
                "Sprints",
                "Number of accelerations (-50.00 - -2.70 m/s²)",
                "Number of accelerations (2.70 - 50.00 m/s²)",
                "HR (>85%)",
                "Maximum speed [km/h]",
            ]
        ]

        data = data.set_index(["position_name", "athlete_name"])

    return data


def clean_df(df, volume=False, intensity=False):
    try:
        # remove goalkeepers
        df.drop("Goal Keeper", level=0, axis=0, inplace=True)
    except KeyError:
        df = df

    positions = df.index.get_level_values("position_name").unique()

    # calculate total distance in km
    # df["Total Distance"] = df["Total Distance"] / 1000

    # add average for team
    df.loc[("Avg. Team", "Avg. Team"), :] = df.mean(axis=0)

    # add average for groups
    df_group = df.groupby("position_name").mean().reset_index()
    df_group["athlete_name"] = "Åvg. Position"
    df_group = df_group.set_index(["position_name", "athlete_name"])
    for pos in positions:
        df.loc[(f"{pos}", f"Åvg. {pos}"), :] = df_group.loc[
            (f"{pos}", "Åvg. Position"), :
        ]

    # convert duration to minutes
    #     df["Minutes"] = df["Minutes"] / 60

    # format decimals
    if volume:
        df.iloc[:, :-1] = df.iloc[:, :-1].round(0)
        df.iloc[:, -1] = df.iloc[:, -1].round(1)
    if intensity:
        df.iloc[:, 0] = df.iloc[:, 0].round(0)
        df.iloc[:, 1:] = df.iloc[:, 1:].round(1)
    # df = df.round(1)

    # sort position
    position_order = ["Avg. Team", "Centre Back", "Full Back", "Midfielder", "Attacker"]
    df = df.reindex(position_order, axis=0, level=0)
    return df
