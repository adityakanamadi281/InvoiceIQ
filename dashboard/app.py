import streamlit as st
import pandas as pd

df = pd.read_csv("invoices.csv")

st.title("Invoice Analytics")

vendor = st.selectbox("Vendor", df.vendor.unique())
st.write(df[df.vendor == vendor])

st.bar_chart(df.groupby("vendor")["total"].sum())
