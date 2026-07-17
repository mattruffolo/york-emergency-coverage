import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="York Region Police Coverage", layout="wide")

stations = gpd.read_file("PoliceStation.geojson").to_crs(epsg=4326)
isochrones = gpd.read_file("isochrones.geojson").to_crs(epsg=4326)
summary = pd.read_csv("coverage_summary.csv")
da_coverage = gpd.read_file("Da_Coverage.json").to_crs(epsg=4326)


st.title("York Region Police Response Coverage")
st.markdown("Open-data analysis of drive-time coverage from YRP district stations.")

total_pop = int(summary["Population.sum"].sum())
pop_5 = int(summary.loc[summary["minutes"] == 5, "Population.sum"].values[0])
pop_10 = int(summary.loc[summary["minutes"] == 10, "Population.sum"].values[0])
pop_15 = int(summary.loc[summary["minutes"] == 15, "Population.sum"].values[0])
pop_gap = int(summary.loc[summary["minutes"] == 999, "Population.sum"].values[0])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Within 5 min", f"{pop_5:,}")
c2.metric("Within 10 min", f"{pop_10:,}")
c3.metric("Within 15 min", f"{pop_15:,}")
c4.metric("Outside Coverage", f"{pop_gap:,}")

st.subheader("Coverage Map")
m = folium.Map(
coverage_colors = {
    5: "#2ecc71",
    10: "#f1c40f",
    15: "#e74c3c",
    999: "#7f8c8d"
}

for _, row in da_coverage.iterrows():
    c = coverage_colors.get(row["minutes"], "#cccccc")

    folium.GeoJson(
        row.geometry,
        style_function=lambda x, c=c: {
            "fillColor": c,
            "color": c,
            "weight": 0.25,
            "fillOpacity": 0.25
        }
    ).add_to(m)

for _, row in isochrones.iterrows():
    c = colors.get(row["minutes"], "gray")
    folium.GeoJson(row.geometry, style_function=lambda x, c=c: {"fillColor": c, "color": c, "weight": 1, "fillOpacity": 0.15}).add_to(m)

for _, row in stations.iterrows():
    folium.Marker(
        [row.geometry.y, row.geometry.x],
        popup=folium.Popup(
            f"<b>{row['NAME']}</b><br>{row['ADDRESS']}",
            max_width=300
        )
).add_to(m)

st_folium(m, width=1200, height=500)

st.subheader("Population by Coverage Bucket")

chart_data = summary.copy()
chart_data["minutes"] = chart_data["minutes"].astype(int)

chart_data["Label"] = chart_data["minutes"].map({
5: "5 min",
10: "10 min",
15: "15 min",
999: "Outside Coverage"
})

st.bar_chart(chart_data.set_index("Label")["Population.sum"])
