import streamlit as st
import requests
import base64
import sys

sys.path.insert(1, '/Users/franekl/Desktop/FCN')
from polar_api.polar_api.polar_api import POLAR_API

st.set_page_config(page_title="Individual Report", page_icon="👤", layout="wide")
st.sidebar.markdown("## 👤 Individual Report")

client_id = "e6e9caed-4705-4991-97c2-b0c9b66cff67"
client_secret = "b1adec70-302e-4209-adae-e031ecfd03fa"

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