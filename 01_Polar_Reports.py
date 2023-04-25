import sys

import streamlit as st
from PIL import Image

from utils.cleaning2 import init_api

st.set_page_config(page_title="Polar Reports", page_icon="📝", layout="wide")

st.markdown("# Polar Reports")
st.sidebar.markdown("# 📝 Polar Reports")


# Login to Polar
client_id = st.secrets["POLAR_CLIENT_ID"]
client_secret = st.secrets["POLAR_CLIENT_SECRET"]
redirect_uri = st.secrets["POLAR_REDIRECT_URI"]

login_button = st.button(label="Login")
if login_button:
    client = init_api(client_id, client_secret, redirect_uri)
    sys.stdin = st.text_input(label="Authentication Code")

# Introduction
st.markdown(
    "##### This app contains standardized reports from Polar for FC Nordsjælland and RTD"
)

# Feedback/issues link
st.markdown(
    "###### Please provide any big or small issues and/or feedback in the link below\n[**Submit feedback or issues**](https://forms.office.com/r/tU6nUsQ8Un) or [**see status of your issue**](https://fcndk.sharepoint.com/sites/PhysicalPerformance2/Shared%20Documents/Forms/AllItems.aspx?newTargetListUrl=%2Fsites%2FPhysicalPerformance2%2FShared%20Documents&viewpath=%2Fsites%2FPhysicalPerformance2%2FShared%20Documents%2FForms%2FAllItems%2Easpx&id=%2Fsites%2FPhysicalPerformance2%2FShared%20Documents%2FGeneral%2FSport%20%26%20Data%20Science%2FFeedback%20and%20issues&viewid=81b5fbda%2D97c6%2D46fe%2D82ec%2D1bc1980ba9cc)"
)

# Logos
try:
    fcn_logo = Image.open("utils/logos/fcn_logos/FCN Logo R&Y.png")
    rtd_logo = Image.open("utils/logos/rtd_logos/rtd_logo.png")
    st.image([fcn_logo, rtd_logo], width=50)
except:
    pass
