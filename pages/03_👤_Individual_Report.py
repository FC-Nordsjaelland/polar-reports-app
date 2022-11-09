import streamlit as st
import requests
import base64
import sys

from polar_api import POLAR_API

st.set_page_config(page_title="Individual Report", page_icon="👤", layout="wide")
st.sidebar.markdown("## 👤 Individual Report")

st.markdown("## 👀 Coming soon")
client_id = st.secrets['client_id']
client_secret = st.secrets['client_secret']
players = st.secrets['players']
usernames = st.secrets['usernames']

username_dict = dict(zip(players, usernames))

st.write(username_dict)


# authorize_url = 'https://auth.polar.com/oauth/authorize'
# access_token_url = 'https://auth.polar.com/oauth/token'
# authorize_params = {'client_id': client_id,
#                                 'response_type': 'code',
#                                 'scope': 'team_read'}

# encoding = client_id+':'+ client_secret
# message_bytes = encoding.encode('ascii')
# base64_bytes = base64.b64encode(message_bytes)
# base64_encoding = base64_bytes.decode('ascii')
# headers = {'Authorization': 'Basic '+ base64_encoding}
# r = requests.get(authorize_url, params=authorize_params)

# # st.write(r.history[0].url)
# # webbrowser.open(r.history[0].url, new=2)
# link = r.history[0].url

#tests