import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen
from folium import FeatureGroup

st.set_page_config(page_title="York Region Police Coverage", layout="wide")

stations = gpd.read_file("PoliceStation.geojson").to_crs(epsg=4326)
isochrones = gpd.read_file("isochrones.geojson").to_crs(epsg=4326)
summary = pd.read_csv("coverage_summary.csv")
york_boundary = gpd.read_file("YorkRegionBoundary.json").to_crs(epsg=4326)

st.title("York Region Police Response Coverage")
st.markdown("Open-data analysis of drive-time coverage from YRP district stations.")

total_pop = int(summary["Population.sum"].sum())
pop_5 = int(summary.loc[summary["minutes"] == 5, "Population.sum"].values[0])
pop_10 = int(summary.loc[summary["minutes"] == 10, "Population.sum"].values[0])
pop_15 = int(summary.loc[summary["minutes"] == 15, "Population.sum"].values[0])
pop_gap = int(summary.loc[summary["minutes"] == 999, "Population.sum"].values[0])

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f"""
### 5 Minute Coverage
# {pop_5:,}
<span style='color:green'>{pop_5/total_pop*100:.1f}% of population</span>
""", unsafe_allow_html=True)

c2.markdown(f"""
### 10 Minute Coverage
# {pop_10:,}
<span style='color:green'>{pop_10/total_pop*100:.1f}% of population</span>
""", unsafe_allow_html=True)

c3.markdown(f"""
### 15 Minute Coverage
# {pop_15:,}
<span style='color:green'>{pop_15/total_pop*100:.1f}% of population</span>
""", unsafe_allow_html=True)

c4.markdown(f"""
### Beyond 15 Minutes
# {pop_gap:,}
<span style='color:green'>{pop_gap/total_pop*100:.1f}% of population</span>
""", unsafe_allow_html=True)
c5, c6, c7, c8 = st.columns(4)

coverage_rate = ((total_pop - pop_gap) / total_pop) * 100
covered_pop = total_pop - pop_gap

c5.metric("Total Population", f"{total_pop:,}")
c6.metric("Covered Population", f"{covered_pop:,}")
c7.metric("Coverage Rate", f"{coverage_rate:.1f}%")
c8.metric("Police Stations", f"{len(stations)}")

st.subheader("Coverage Map")

m = folium.Map(
    location=[44.05, -79.45],
    zoom_start=9,
    tiles="CartoDB positron"
)
Fullscreen().add_to(m)

stations_layer = FeatureGroup(name="Police Stations")
iso_5_layer = FeatureGroup(name="5 Minute Drive Time")
iso_10_layer = FeatureGroup(name="10 Minute Drive Time")
iso_15_layer = FeatureGroup(name="15 Minute Drive Time")
boundary_layer = FeatureGroup(name="York Region Boundary")

folium.GeoJson(
    york_boundary,
    style_function=lambda x: {
        "fillOpacity": 0,
        "color": "#777777",
        "weight": 2,
        "dashArray": "8,8"
    }
).add_to(boundary_layer)

colors = {
    5: "#2ecc71",
    10: "#f1c40f",
    15: "#e74c3c"
}
for _, row in isochrones.iterrows():
    c = colors.get(row["minutes"], "gray")

    if row["minutes"] == 5:
        folium.GeoJson(
            row.geometry,
            style_function=lambda x, c=c: {
                "fillColor": c,
                "color": c,
                "weight": 1,
                "fillOpacity": 0.15
            }
        ).add_to(iso_5_layer)

    elif row["minutes"] == 10:
        folium.GeoJson(
            row.geometry,
            style_function=lambda x, c=c: {
                "fillColor": c,
                "color": c,
                "weight": 1,
                "fillOpacity": 0.15
            }
        ).add_to(iso_10_layer)

    else:
        folium.GeoJson(
            row.geometry,
            style_function=lambda x, c=c: {
                "fillColor": c,
                "color": c,
                "weight": 1,
                "fillOpacity": 0.15
            }
        ).add_to(iso_15_layer)

for _, row in stations.iterrows():
    police_icon = folium.CustomIcon(
        "police-station.png",
        icon_size=(28, 28)
    )

    folium.Marker(
        [row.geometry.y, row.geometry.x],
        popup=folium.Popup(
            f"<b>{row['NAME']}</b><br>{row['ADDRESS']}",
            max_width=300
        ),
        icon=police_icon
    ).add_to(stations_layer)
legend_html = """
<div style="
position: fixed;
bottom: 30px;
left: 30px;
width: 260px;
background-color: white;
border: 2px solid grey;
z-index:9999;
padding: 10px;
font-size:14px;
color:black;
">

<b>Legend</b><br><br>

 ⛊✪ Police Station

 
<span style="color:#2ecc71;">■</span> 5 Minute Drive Time<br>
<span style="color:#f1c40f;">■</span> 10 Minute Drive Time<br>
<span style="color:#e74c3c;">■</span> 15 Minute Drive Time<br><br>

<span style="color:#777777;">- - -</span> York Region Boundary<br>

</div>
"""

stations_layer.add_to(m)
iso_5_layer.add_to(m)
iso_10_layer.add_to(m)
iso_15_layer.add_to(m)
boundary_layer.add_to(m)

folium.LayerControl().add_to(m)

m.get_root().html.add_child(folium.Element(legend_html))
st_folium(m, width=1200, height=500)

st.info(
    f"{covered_pop:,} residents ({coverage_rate:.1f}%) live within a 15-minute drive of a York Regional Police district station. "
    f"In contrast, {pop_gap:,} residents ({pop_gap/total_pop*100:.1f}%) live beyond 15 minutes."
)

chart_data = summary.copy()
chart_data["minutes"] = chart_data["minutes"].astype(int)

chart_data["Label"] = chart_data["minutes"].map({
5: "5 min",
10: "10 min",
15: "15 min",
999: "Beyond 15 Minutes"
})

st.bar_chart(chart_data.set_index("Label")["Population.sum"])
