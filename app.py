
import streamlit as st
import pandas as pd
import plotly.express as px

# Load the data
acs_bloom_city = pd.read_csv('acs_bloom_city.csv')
acs_bloom_msa = pd.read_csv('acs_bloom_msa.csv')
acs_in = pd.read_csv('acs_in.csv')
bls_bloom = pd.read_csv('bls_bloom.csv')

# Add dataset labels
acs_bloom_city['dataset'] = 'Bloomington City'
acs_bloom_msa['dataset'] = 'Bloomington Metro'
acs_in['dataset'] = 'Indiana'

occ_types = bls_bloom[~bls_bloom["OCC_CODE"].str.endswith("0000")].copy()
occ_types["A_MEDIAN"] = pd.to_numeric(occ_types["A_MEDIAN"], errors="coerce")

median_rent_2023 = acs_bloom_msa[acs_bloom_msa['year'] == 2023]['median_rent'].iloc[0]
annual_rent = median_rent_2023 * 12
annual_income = occ_types['A_MEDIAN']

occ_types['percent_rent_burdened'] = (annual_rent / annual_income) * 100
occ_types['percent_rent_burdened'] = occ_types['percent_rent_burdened'].where(
    occ_types['percent_rent_burdened'] > 30, 0
)
rent_burdened_occupations = occ_types[occ_types['percent_rent_burdened'] > 0]

# Combine into a single DataFrame
combined_df = pd.concat([acs_bloom_city, acs_bloom_msa, acs_in], ignore_index=True)
combined_df['year'] = combined_df['year'].astype(int)

# Color map for custom styling
color_map = {
    'Indiana': '#8B0000',
    'Bloomington City': '#003366',
    'Bloomington Metro': '#800080'
}

# Streamlit app
def main():
    st.title('City of Bloomington Housing Trends')

    view = st.sidebar.radio("Select View", ['Housing Cost', 'Rent-Burdened Occupations'])

    if view == 'Housing Cost':
        metric = st.sidebar.selectbox("Select Visual", ['Median Rent', 'Median Home Value'])
        st.subheader(f"{metric} Over Time by Location")

        st.sidebar.header("Filters")
        min_year = combined_df['year'].min()
        max_year = combined_df['year'].max()
        year_range = st.sidebar.slider("Select Year Range", min_year, max_year, (2018, 2023))

        metric_column = 'median_rent' if metric == 'Median Rent' else 'median_hval'
        y_label = 'Median Rent ($)' if metric == 'Median Rent' else 'Median Home Value ($)'

        selected_datasets = st.sidebar.multiselect(
            "Select Area",
            options=combined_df['dataset'].unique(),
            default=combined_df['dataset'].unique()
        )

        filtered_df = combined_df[
            (combined_df['year'] >= year_range[0]) &
            (combined_df['year'] <= year_range[1]) &
            (combined_df['dataset'].isin(selected_datasets))
        ]

        tick_vals = list(range(year_range[0], year_range[1] + 1))

        fig = px.line(
            filtered_df,
            x='year',
            y=metric_column,
            color='dataset',
            markers=True,
            color_discrete_map=color_map,
            labels={
                'year': 'Year',
                metric_column: y_label,
                'dataset': 'Region'
            },
            width=1000,
            height=600
        )
        fig.update_layout(xaxis=dict(tickmode='array', tickvals=tick_vals))
        st.plotly_chart(fig, use_container_width=True)

    elif view == 'Rent-Burdened Occupations':
        st.subheader("Which workers are rent-burdened in Bloomington?")

        top_15_by_employees = rent_burdened_occupations.nlargest(15, "TOT_EMP")[[
            "OCC_TITLE", "TOT_EMP", "A_MEDIAN", "percent_rent_burdened"
        ]]
        top_15_by_employees = top_15_by_employees.sort_values("TOT_EMP", ascending=True)

        fig = px.bar(
            top_15_by_employees,
            x="TOT_EMP",
            y="OCC_TITLE",
            orientation="h",
            color="percent_rent_burdened",
            color_continuous_scale="Blues",
            labels={
                "OCC_TITLE": "Occupation",
                "TOT_EMP": "Number of Employees",
                "percent_rent_burdened": "Percent rent-burdened"
            },
            title="Top 15 Rent-Burdened Occupations by Employment",
        )

        fig.update_traces(marker_line_color="gray", marker_line_width=1)

        fig.update_layout(
            height=800,
            xaxis_title="Number of Employees",
            yaxis_title="",
            coloraxis_colorbar=dict(title="Percent rent-burdened"),
            template="plotly_white",
            bargap=0.1
        )

        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
