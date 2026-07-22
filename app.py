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
muni = pd.read_csv("municipality_coverage_summary.csv")
york_boundary = gpd.read_file("YorkRegionBoundary.json").to_crs(epsg=4326)
municipal_boundaries = gpd.read_file("muniboundary.json").to_crs(epsg=4326)

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
municipal_layer = FeatureGroup(name="Municipal Boundaries")

folium.GeoJson(
    municipal_boundaries,
    style_function=lambda x: {
        "fillOpacity": 0,
        "color": "#D0D0D0",
        "weight": 1,
        "dashArray": "4,4"
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["CSDNAME"],
        aliases=["Municipality:"]
    )
).add_to(municipal_layer)

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
width: 220px;
background-color: white;
border: 2px solid grey;
z-index:9999;
padding: 10px;
font-size:14px;
color:black;
">

<b>Legend</b><br><br>

<span style="font-size:16px;">⛊✪</span> Police Station<br>

<span style="color:#2ecc71;">■</span> 5 Minute Drive Time<br>
<span style="color:#f1c40f;">■</span> 10 Minute Drive Time<br>
<span style="color:#e74c3c;">■</span> 15 Minute Drive Time<br><br>
<span style="color:#777777;">---</span> York Region Boundary
<br>
<span style="color:#D0D0D0;">- - -</span> Municipal Boundaries

</div>
"""

stations_layer.add_to(m)
iso_5_layer.add_to(m)
iso_10_layer.add_to(m)
iso_15_layer.add_to(m)
municipal_layer.add_to(m)
boundary_layer.add_to(m)

folium.LayerControl().add_to(m)

m.get_root().html.add_child(folium.Element(legend_html))
st_folium(m, width=1200, height=500)

st.info(
    f"{covered_pop:,} residents ({coverage_rate:.1f}%) live within a 15-minute drive of a York Regional Police district station. "
    f"In contrast, {pop_gap:,} residents ({pop_gap/total_pop*100:.1f}%) live beyond 15 minutes."
)
st.subheader("Municipality Coverage Ranking")
st.caption("Municipalities ranked by share of residents within 15-minute drive-time coverage.")

muni["minutes"] = muni["minutes"].astype(int)
muni = muni[muni["CSDNAME"].notna()]
muni = muni[muni["CSDNAME"] != ""]

total_by_muni = muni.groupby("CSDNAME")["Population.sum"].sum().reset_index()
total_by_muni = total_by_muni.rename(columns={"Population.sum": "Total Population"})

gap_by_muni = muni[muni["minutes"] == 999].groupby("CSDNAME")["Population.sum"].sum().reset_index()
gap_by_muni = gap_by_muni.rename(columns={"Population.sum": "Gap Population"})

ranking = total_by_muni.merge(gap_by_muni, on="CSDNAME", how="left")
ranking["Gap Population"] = ranking["Gap Population"].fillna(0)

ranking["Covered Population"] = ranking["Total Population"] - ranking["Gap Population"]
ranking["Coverage Rate"] = ranking["Covered Population"] / ranking["Total Population"] * 100

def get_score(rate):
    if rate >= 98:
        return "A+"
    elif rate >= 95:
        return "A"
    elif rate >= 90:
        return "A-"
    elif rate >= 85:
        return "B"
    elif rate >= 80:
        return "C"
    else:
        return "D"

ranking["Coverage Score"] = ranking["Coverage Rate"].apply(get_score)

ranking = ranking.sort_values("Coverage Rate", ascending=False).reset_index(drop=True)
ranking["Rank"] = ranking.index + 1

ranking_display = ranking[[
    "Rank",
    "CSDNAME",
    "Coverage Rate",
    "Coverage Score",
    "Gap Population"
]]

ranking_display = ranking_display.rename(columns={
    "CSDNAME": "Municipality"
})

ranking_display["Coverage Rate"] = ranking_display["Coverage Rate"].map(lambda x: f"{x:.1f}%")
ranking_display["Gap Population"] = ranking_display["Gap Population"].map(lambda x: f"{int(x):,}")

st.dataframe(
    ranking_display,
    hide_index=True,
    use_container_width=True
)

