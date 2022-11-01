men_daily_volume_parameters = [
                'Minutes',
                'Total Distance',
                'Distance in Speed zone 4 [m] (25.20 - 29.99 km/h)', 
                'Distance in Speed zone 5 [m] (30.00- km/h)',
                'Sprints',
                'Number of accelerations (-50.00 - -9.00 m/s²)',
                'Number of accelerations (9.00 - 50.00 m/s²)',
                'HR (>85%)',
                'Maximum speed [km/h]'
        ]
        

women_daily_volume_parameters = [
                'Minutes', 
                'Total Distance',
                'Distance in Speed zone 4 [m] (24.00 - 26.99 km/h)',
                'Distance in Speed zone 5 [m] (27.00- km/h)',
                'Sprints',
                'Number of accelerations (-50.00 - -2.70 m/s²)',
                'Number of accelerations (2.70 - 50.00 m/s²)',
                'HR (>85%)',
                'Maximum speed [km/h]'
        ]


men_daily_volume_plot_names = [
                "Minutes", 
                "Total Distance",
                "HSR distance (>20km/h)",
                "Sprint distance (>25km/h)", 
                "Sprint efforts (>25km/h)",
                "Acc (>3m/s)", 
                "Dec (>-3m/s)",
                "HR (>85%)", 
                "Max Speed (km/h)"
                ]


women_daily_volume_plot_names = [
                "Minutes", 
                "Total Distance",
                "HSR distance (>19km/h)",
                "Sprint distance (>22.5km/h)", 
                "Sprint efforts (>22.5km/h)",
                "Acc (>3m/s)", 
                "Dec (>-3m/s)",
                "HR (>85%)", 
                "Max Speed (km/h)"
                ]


## --------- 03 WEEKLY REPORT -------- ##

men_weekly_volume_parameters = [
                'Minutes',
                'Sessions',
                'Total Distance (km)',
                'Distance in Speed zone 4 [m] (25.20 - 29.99 km/h)', 
                'Distance in Speed zone 5 [m] (30.00- km/h)',
                'Sprints',
                'Number of accelerations (-50.00 - -9.00 m/s²)',
                'Number of accelerations (9.00 - 50.00 m/s²)',
                'HR (>85%)',
        ]

women_weekly_volume_parameters = [
                'Minutes',
                'Sessions',
                'Total Distance (km)',
                'Distance in Speed zone 4 [m] (24.00 - 26.99 km/h)', 
                'Distance in Speed zone 5 [m] (27.00- km/h)',
                'Sprints',
                'Number of accelerations (-50.00 - -2.70 m/s²)',
                'Number of accelerations (2.70 - 50.00 m/s²)',
                'HR (>85%)',
        ]

men_weekly_volume_plot_names = [
                "Minutes", 
                "Sessions", 
                "Total Distance (km)",
                "HSR distance (>20km/h)",
                "Sprint distance (>25km/h)", 
                "Sprint efforts (>25km/h)",
                "Acc (>3m/s)", 
                "Dec (>-3m/s)",
                "HR >85% (min.)"
                ]

women_weekly_volume_plot_names = [
                "Minutes", 
                "Sessions", 
                "Total Distance (km)",
                "HSR distance (>19km/h)",
                "Sprint distance (>22.5km/h)", 
                "Sprint efforts (>22.5km/h)",
                "Acc (>2.5m/s)", 
                "Dec (>-2.5m/s)",
                "HR >85% (min.)"
                ]


weekly_daily_plot_parameters = ["Average Duration (Session)", 
                                "Average Distance (Session)", 
                                "Average High Speed Running (Session)",
                                "Average Sprinting (Session)",
                                "Average no. of sprints (Session)",
                                "Acceleration Average Efforts (Session)", 
                                "Deceleration Average Efforts (Session)", 
                                "Average Heart rate Duration in Red Zone (Session)"]


colors = {"Centre Back": "#4285F4", "Full Back": "#34A853",
          "Midfielder": "#FBBC04", "Attacker": "#EA4335"}