"""
Make sure you have the following installed:
- pandas
- streamlit
Run the command: /opt/anaconda3/bin/python -m streamlit run "WhereShouldYouLive.py" to boot up the application
"""

# Import libraries
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Load data once at the top and format it
df = pd.read_excel('Data/CPI % Change for Metro Cities.xlsx')
item_df = pd.read_excel('Data/Item_prices.xlsx')
sports_df = pd.read_excel('Data/Sports_bars.xlsx')

cpi_city_columns = df.columns[1:].tolist()
city_columns = item_df.columns[2:].tolist()

# –– City select
st.set_page_config(layout="wide")
st.title("Where Should You Live?")
st.subheader("Filter to any city to see their detailed information")

selected_city = st.selectbox("Select a city", cpi_city_columns, index=None)

# Function for later
def males_to_split(ratio):
    male_pct = ratio / (ratio + 100) * 100
    return round(male_pct, 1), round(100 - male_pct, 1)

# –– Introduction to finance
if selected_city:
    st.subheader("Financial Information")
    st.markdown("""
                > Finances and costs are a big part of living in any city. Here we look at how the cost of living has changed over time in your selected city. 
                > After that you may explore other aspects of living in your selected city in comparison to other cities as well as the US average. 
                > Both visuals are interactive, so to maximize the experience you are encouraged to drag and explore the data.
            """, unsafe_allow_html=True)

# ── Graph 1: CPI Over Time 
    st.subheader(f"Consumer Price Index Over Time for {selected_city}")

    city_data = (
        df[['Month', selected_city]]
        .copy()
        .rename(columns={selected_city: 'CPI % Change'})
        .assign(Month=lambda d: pd.to_datetime(d['Month']))
        .sort_values('Month')
        .dropna(subset=['CPI % Change'])
    )

    if city_data.empty:
        st.warning("No data available for the selected city.")
    else:
        col_chart, col_text = st.columns([2.75, 1])

        with col_chart:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=city_data['Month'],
                y=city_data['CPI % Change'],
                mode='lines',
                line=dict(color='red', width=2),
                name='CPI % Change',
                hovertemplate="CPI Change: %{y:.2f}%<extra></extra>"
            ))
            fig.add_hline(y=0, line=dict(color='gray', width=1.5, dash='dash'))
            fig.update_layout(
                xaxis_title='Month',
                yaxis_title='CPI % Change',
                hovermode='x unified',
                margin=dict(t=30, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_text:
            st.markdown("""
                The **Consumer Price Index ([CPI](https://www.bls.gov/cpi/questions-and-answers.htm))** measures the
                average change in prices consumers pay for goods and services over time.

                - **Above 0%** — prices are rising (inflation)
                - **Below 0%** — prices are falling (deflation)
                - **At 0%** — prices remain unchanged

                The dashed line marks the **baseline (0%)**.
                Values further from it indicate stronger inflationary or deflationary pressure.

                <br><br><br><br>

                *Timelines and frequencies may vary by city*
            """, unsafe_allow_html=True)

# ── Graph 2: Parallel Coordinates 
    if selected_city in city_columns:
        st.subheader("Item Prices Comparison Across Cities")

        transposed_data = (
            item_df[city_columns]
            .T
            .set_axis(item_df.iloc[:, 0].tolist(), axis=1)
            .reset_index()
            .rename(columns={'index': 'City'})
        )

        for col in transposed_data.columns[1:]:
            transposed_data[col] = pd.to_numeric(transposed_data[col], errors='coerce')

        value_cols = transposed_data.columns[1:]
        clean_cols = [
            col for col in value_cols
            if not (transposed_data[col].isna().all() or (transposed_data[col] == 0).all())
        ]
        desired_cols = [col for col in clean_cols[:11] if col != "Males to 100 Females" and col != "Link to City" and col!= "Median Age"]

        axis_ranges = {
            "Cup of Coffee ($)": [2.75, 5],
            "Gas ($)": [3.5, 6],
            "Median Rent ($)": [900, 3800],
            "Median Salary ($)": [60000, 125000],
            "Unemployment Rate (%)": [2, 5],
            "Walkability Score": [30, 90],
            "Transit Score": [3, 10],
            "Avg. Years of Residency": [4, 20],
            "Population": [400000, 20000000]
        }

        def get_city_color(city):
            if city == selected_city:
                return 1
            elif city == city_columns[-1]:
                return 0
            else:
                return 0.5

        transposed_data['Color_Value'] = transposed_data['City'].apply(get_city_color)

        fig = px.parallel_coordinates(
            transposed_data,
            dimensions=desired_cols,
            color='Color_Value',
            color_continuous_scale=[[0, 'black'], [0.5, 'rgba(209,209,209, 0.05)'], [1, 'red']]
        )
        fig.update_layout(
            coloraxis_showscale=False,
            title=dict(
                text=f"<span style='color:red'>| {selected_city}</span>  |  <span style='color:black'>US Average</span>",
                font=dict(size=16)
            ),
            height=650,
            font=dict(size=12.5),
            margin=dict(l=80, r=40, t=100, b=40)
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown(
            f"<div style='text-align: left; font-size: 0.75rem; font-style: italic;'>Feel free to drag around items!</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='text-align: right; font-size: 0.75rem; font-style: italic;'>Showing {len(transposed_data)-1} cities across {len(desired_cols)} items</div>",
            unsafe_allow_html=True
        )

# ── Graph 3: Gender Donut 
        st.subheader("Social Information")
        st.markdown("""
            > A city's demographics can impact social dynamics, economic opportunities, and cultural norms. 
            > Here you may explore and measure how life might look like in your selected city so you can get an accurate picture of what society values.
            > These are not fully interactive but have hover capabilities.
        """, unsafe_allow_html=True)
        
        males_idx = item_df[item_df.iloc[:, 0] == "Males to 100 Females"].index[0]
        city_val = pd.to_numeric(item_df.at[males_idx, selected_city], errors='coerce')
        us_avg_val = pd.to_numeric(item_df.at[males_idx, city_columns[-1]], errors='coerce')

        city_male, city_female = males_to_split(city_val)
        us_male, us_female = males_to_split(us_avg_val)

        fig_donut = go.Figure(data=[
            # Inner ring – city data
            go.Pie(
                values=[city_male, city_female],
                labels=['Male', 'Female'],
                domain={'x': [0.15, 0.85], 'y': [0.1, 0.9]},
                hole=0.55,
                direction='clockwise',
                sort=False,
                marker={'colors': ['#5DADE2', '#ed80cb']},
                textinfo='percent',
                textfont=dict(size=13, color='white'),
                insidetextorientation='horizontal',
                showlegend=False,
                hovertemplate="<b>%{label}</b><br>" + selected_city + "<extra></extra>"
            ),
            # Outer ring – US average
            go.Pie(
                values=[us_male, us_female],
                labels=['Male (US Avg)', 'Female (US Avg)'],
                domain={'x': [0.05, 0.95], 'y': [0.0, 1.0]},
                hole=0.82,
                direction='clockwise',
                sort=False,
                marker={'colors': ['#9ed4f7', '#f5bae2']},
                showlegend=False,
                textinfo='none',
                hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>", 
                
            )
        ])

        fig_donut.update_layout(
            title="",
            height=400,
            margin=dict(t=0, b=0, l=10, r=10),
            annotations=[
                # City name + F/M label inside the hole
                dict(
                    text=(
                        f"<b><span style='color:#ed80cb'>Female</span>"
                        f" / "
                        f"<span style='color:#5DADE2'>Male</span></b>"
                        f"<br><span style='font-size:10.6px; color:red'>Inner Ring: Chosen City</span>"
                    ),
                    x=0.5, y=0.5,
                    font=dict(size=14),
                    showarrow=False,
                    xanchor="center",
                    yanchor="middle"
                ),
                # Outer ring label – sits just above the chart
                dict(
                    text="<span style='color:gray; font-size:11px'>Outer Ring: US Average</span>",
                    x=0.5, y=0.85,
                    font=dict(size=10),
                    showarrow=False,
                    xanchor="center",
                    yanchor="bottom"
                )
            ]
        )

        # Splitting the size of graph into 3 columns
        col_donut, col_sports, col_bars = st.columns([0.85, 1.15, 1])

        with col_donut:
            st.plotly_chart(fig_donut, use_container_width=True)

        with col_sports:

# –– Sports Teams

            sports_order = ['Baseball', 'Football', 'Hockey', 'Basketball']

            city_sports = sports_df[sports_df['Sport'].isin(sports_order)][['Sport', selected_city]].copy()
            city_sports.columns = ['Sport', 'Teams']

            sport_colors = {
                'Baseball':   '#2CA02C',
                'Basketball': '#ff7f0e',
                'Football':   '#b45c1f',
                'Hockey':     '#1fb4a7'
            }

            fig_sports = px.bar(
                city_sports,
                x='Sport',
                y='Teams',
                color='Sport',
                color_discrete_map=sport_colors,
                text='Teams'
            )

            fig_sports.update_traces(
                textposition='outside',
                width=0.85,
                hovertemplate="<b>%{x}</b><br>Teams: %{y}<extra></extra>"
            )

            fig_sports.update_layout(
                yaxis=dict(
                    title='Professional Teams',
                    tickformat='d',
                    dtick=1,
                    range=[0, 2.5]
                ),
                xaxis=dict(title=None),
                showlegend=False,
                height=350,
                margin=dict(t=60, b=40, l=40, r=20)
            )

            st.plotly_chart(fig_sports, use_container_width=True)

# –– Bars
            with col_bars:
                # Pull Total Bars row
                bars_row = sports_df[sports_df['Sport'] == 'Total Bars'].iloc[0]
                city_bars = int(bars_row[selected_city])
                us_avg_bars = 1183.0            #Hard code in
                diff = city_bars - us_avg_bars

                # Number and context
                st.markdown(
                    f"<div style='text-align:center; padding-top:30px'>"
                    f"<span style='font-size:48px; font-weight:bold'>{city_bars} Bars</span>"
                    f"<br><span style='font-size:12px; color:gray'>Total Bars in {selected_city}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                if diff >= 0:
                    st.markdown(
                        f"<div style='text-align:center'>"
                        f"<span style='color:green; font-size:14px'>▲ {diff:.0f} above Average ({us_avg_bars:.1f})</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div style='text-align:center'>"
                        f"<span style='color:red; font-size:14px'>▼ {abs(diff):.0f} below Average ({us_avg_bars:.1f})</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                # Divider
                st.markdown("<hr style='margin: 20px 0; border-color: #e0e0e0;'>", unsafe_allow_html=True)

# –– Median Age
                age_idx = item_df[item_df.iloc[:, 0] == "Median Age"].index[0]
                city_age = pd.to_numeric(item_df.at[age_idx, selected_city], errors='coerce')

                # Number and context
                if not pd.isna(city_age):
                    st.markdown(
                        f"<div style='text-align:center; padding-top:20px'>"
                        f"<span style='font-size:48px; font-weight:bold'>{city_age:.1f}</span>"
                        f"<br><span style='font-size:12px; color:gray'>Median Age in {selected_city}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div style='text-align:center; padding-top:10px'>"
                        f"<span style='font-size:14px; color:gray'>Median Age data unavailable</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

# Sources section
        st.markdown("---")
        col_src1, col_src2 = st.columns(2)
        with col_src1:
            st.markdown("""
                    <div style='font-size: 0.7rem; color: gray;'>
                        <strong>Sources for Reference</strong><br><br>
                        <a href='https://www.bls.gov/charts/consumer-price-index/consumer-price-index-by-metro-area.htm' target='_blank'>U.S. Bureau of Labor Statistics — Consumer Price Index</a><br>
                        <a href='https://www.axios.com/local/columbus/2024/07/08/cost-of-coffee-in-ohio-map' target='_blank'>Axios — Cup of Coffee</a><br>
                        <a href='https://gasprices.aaa.com/state-gas-price-averages/' target='_blank'>AAA — Gas</a><br>
                        <a href='https://www.apartmentadvisor.com/national-rent-report' target='_blank'>Apartment Advisor — Median Rent</a><br>
                        <a href='https://en.wikipedia.org/wiki/List_of_United_States_metropolitan_areas_by_per_capita_income' target='_blank'>Wikipedia — Median Salary</a><br>
                        <a href='https://www.bls.gov/web/metro/laummtrk.htm' target='_blank'>U.S. Bureau of Labor Statistics — Unemployment Rate</a><br>
                    </div>
                """, unsafe_allow_html=True)
        with col_src2:
            st.markdown("""
                    <div style='font-size: 0.7rem; color: gray;'>
                        <br><br>
                        <a href='https://www.walkscore.com/cities-and-neighborhoods/' target='_blank'>Walkscore — Walkability Score</a><br>
                        <a href='https://alltransit.cnt.org/metrics/' target='_blank'>All Transit — Transit Score</a><br>
                        <a href='https://www.newgeography.com/content/006115-residential-tenure' target='_blank'>New Geography — Average Years Residency</a><br>
                        <a href='https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population_density' target='_blank'>Wikipedia — Population</a><br>
                        <a href='https://rentechdigital.com/smartscraper/business-report-details/list-of-bars-in-united-states' target='_blank'>Smartscrapers — Estimated Bars</a><br>
                        <a href='https://documentation-resources.opendatasoft.com/explore/embed/dataset/us-cities-demographics/analyze/?dataChart=eyJxdWVyaWVzIjpbeyJjb25maWciOnsiZGF0YXNldCI6InVzLWNpdGllcy1kZW1vZ3JhcGhpY3MiLCJvcHRpb25zIjp7fX0sImNoYXJ0cyI6W3siYWxpZ25Nb250aCI6dHJ1ZSwidHlwZSI6ImNvbHVtbiIsImZ1bmMiOiJBVkciLCJ5QXhpcyI6Im1lZGlhbl9hZ2UiLCJzY2llbnRpZmljRGlzcGxheSI6dHJ1ZSwiY29sb3IiOiIjNjZjMmE1In1dLCJ4QXhpcyI6ImNpdHkiLCJtYXhwb2ludHMiOjUwLCJzb3J0IjoiIn1dLCJ0aW1lc2NhbGUiOiIiLCJkaXNwbGF5TGVnZW5kIjp0cnVlLCJhbGlnbk1vbnRoIjp0cnVlfQ%3D%3D' target='_blank'>Opendata — Median Age</a><br>
                    </div>
                """, unsafe_allow_html=True)
