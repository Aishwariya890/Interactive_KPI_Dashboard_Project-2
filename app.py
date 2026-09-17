import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from io import BytesIO
import tempfile
import os

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


# =========================================================
# PAGE SETUP
# =========================================================

st.set_page_config(
    page_title="Retail KPI Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Retail Business KPI Dashboard")
st.caption("Interactive KPI dashboard for the cleaned Online Retail dataset")


# =========================================================
# DATA FILE
# =========================================================

real_file = Path("Data/clean_dataset.csv")
demo_file = Path("Data/demo_clean_dataset.csv")


@st.cache_data
def load_data():

    path = real_file if real_file.exists() else demo_file

    df = pd.read_csv(path)

    df["invoicedate"] = pd.to_datetime(
        df["invoicedate"],
        errors="coerce"
    )

    for c in [
        "quantity",
        "unitprice",
        "total_sales",
        "customerid"
    ]:
        if c in df:
            df[c] = pd.to_numeric(
                df[c],
                errors="coerce"
            )

    df["total_sales"] = df["total_sales"].fillna(
        df["quantity"] * df["unitprice"]
    )

    df["year"] = df["invoicedate"].dt.year
    df["month_num"] = df["invoicedate"].dt.month
    df["month"] = df["invoicedate"].dt.strftime("%b")

    return df, path.name


df, source = load_data()


# =========================================================
# FILTERS
# =========================================================

st.sidebar.header("Filters")

years = sorted(
    df["year"]
    .dropna()
    .astype(int)
    .unique()
)

sel_years = st.sidebar.multiselect(
    "Year",
    years,
    default=list(years)
)

countries = sorted(
    df["country"]
    .dropna()
    .astype(str)
    .unique()
)

sel_countries = st.sidebar.multiselect(
    "Country",
    countries,
    default=list(countries)
)


# =========================================================
# FILTER DATA
# =========================================================

f = df[
    df["year"].isin(sel_years)
    & df["country"].isin(sel_countries)
].copy()


# =========================================================
# KPI CALCULATIONS
# =========================================================

revenue = f["total_sales"].sum()

orders = f["invoiceno"].nunique()

qty = f["quantity"].sum()

customers = f.loc[
    f["customerid"].fillna(0) != 0,
    "customerid"
].nunique()

aov = revenue / orders if orders else 0


# =========================================================
# KPI CARDS
# =========================================================

a, b, c, e, g = st.columns(5)

a.metric(
    "Total Revenue",
    f"£{revenue:,.0f}"
)

b.metric(
    "Total Orders",
    f"{orders:,.0f}"
)

c.metric(
    "Average Order Value",
    f"£{aov:,.2f}"
)

e.metric(
    "Customers",
    f"{customers:,.0f}"
)

g.metric(
    "Quantity Sold",
    f"{qty:,.0f}"
)


# =========================================================
# MONTHLY REVENUE
# =========================================================

monthly = (
    f.groupby(
        ["year", "month_num", "month"],
        as_index=False
    )["total_sales"]
    .sum()
    .sort_values(
        ["year", "month_num"]
    )
)

monthly_fig = px.line(
    monthly,
    x="month",
    y="total_sales",
    color="year",
    markers=True,
    title="Monthly Revenue Trend"
)

monthly_fig.update_layout(
    template="plotly_white",
    height=450
)

st.plotly_chart(
    monthly_fig,
    use_container_width=True
)


# =========================================================
# COUNTRY REVENUE
# =========================================================

left, right = st.columns(2)

cs = (
    f.groupby(
        "country",
        as_index=False
    )["total_sales"]
    .sum()
    .sort_values(
        "total_sales",
        ascending=False
    )
    .head(10)
)

country_fig = px.bar(
    cs,
    x="total_sales",
    y="country",
    orientation="h",
    title="Top 10 Countries by Revenue"
)

country_fig.update_layout(
    template="plotly_white",
    height=500
)

left.plotly_chart(
    country_fig,
    use_container_width=True
)


# =========================================================
# PRODUCT REVENUE
# =========================================================

ps = (
    f.groupby(
        "description",
        as_index=False
    )["total_sales"]
    .sum()
    .sort_values(
        "total_sales",
        ascending=False
    )
    .head(10)
)

product_fig = px.bar(
    ps,
    x="total_sales",
    y="description",
    orientation="h",
    title="Top 10 Products by Revenue"
)

product_fig.update_layout(
    template="plotly_white",
    height=500
)

right.plotly_chart(
    product_fig,
    use_container_width=True
)


# =========================================================
# SCATTER CHART
# =========================================================

sample = (
    f.sample(
        min(5000, len(f)),
        random_state=42
    )
    if len(f)
    else f
)

scatter_fig = None

if len(sample):

    scatter_fig = px.scatter(
        sample,
        x="quantity",
        y="unitprice",
        size="total_sales",
        hover_data=[
            "description",
            "country"
        ],
        title="Quantity vs Unit Price"
    )

    scatter_fig.update_layout(
        template="plotly_white",
        height=500
    )

    st.plotly_chart(
        scatter_fig,
        use_container_width=True
    )


# =========================================================
# INFORMATION
# =========================================================

st.info(
    f"Data source: {source}"
)

st.markdown(
    "**Note:** CAC and Churn Rate are not calculated because "
    "the Online Retail dataset does not contain marketing-cost "
    "or explicit churn fields."
)


# =========================================================
# PDF CREATION FUNCTION
# =========================================================

def create_pdf():

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()

    story = []

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "<b>Retail Business KPI Dashboard</b>",
            styles["Title"]
        )
    )

    story.append(
        Spacer(1, 10)
    )

    story.append(
        Paragraph(
            "Interactive KPI Dashboard - Online Retail Dataset",
            styles["Normal"]
        )
    )

    story.append(
        Spacer(1, 15)
    )


    # -----------------------------------------------------
    # KPI TABLE
    # -----------------------------------------------------

    kpi_data = [
        [
            "Total Revenue",
            "Total Orders",
            "Average Order Value",
            "Customers",
            "Quantity Sold"
        ],
        [
            f"£{revenue:,.0f}",
            f"{orders:,.0f}",
            f"£{aov:,.2f}",
            f"{customers:,.0f}",
            f"{qty:,.0f}"
        ]
    ]

    kpi_table = Table(
        kpi_data,
        colWidths=[
            2.0 * inch,
            1.7 * inch,
            2.1 * inch,
            1.7 * inch,
            1.7 * inch
        ]
    )

    kpi_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.black
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                10
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.25,
                colors.grey
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8
            )
        ])
    )

    story.append(kpi_table)

    story.append(
        Spacer(1, 20)
    )


    # -----------------------------------------------------
    # SAVE PLOTLY FIGURES AS PNG
    # -----------------------------------------------------

    temp_files = []

    figures = [
        monthly_fig,
        country_fig,
        product_fig
    ]

    if scatter_fig is not None:
        figures.append(scatter_fig)


    try:

        for i, fig in enumerate(figures):

            temp_path = os.path.join(
                tempfile.gettempdir(),
                f"retail_dashboard_chart_{i}.png"
            )

            fig.write_image(
                temp_path,
                width=1200,
                height=650,
                scale=1
            )

            temp_files.append(temp_path)


        # -------------------------------------------------
        # CHARTS
        # -------------------------------------------------

        for i, temp_path in enumerate(temp_files):

            story.append(
                Image(
                    temp_path,
                    width=9.5 * inch,
                    height=5.1 * inch
                )
            )

            story.append(
                Spacer(1, 10)
            )

            if i < len(temp_files) - 1:

                story.append(
                    PageBreak()
                )


        # -------------------------------------------------
        # NOTE
        # -------------------------------------------------

        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                f"<b>Data source:</b> {source}",
                styles["Normal"]
            )
        )

        story.append(
            Spacer(1, 10)
        )

        story.append(
            Paragraph(
                "<b>Note:</b> CAC and Churn Rate are not calculated "
                "because the Online Retail dataset does not contain "
                "marketing-cost or explicit churn fields.",
                styles["Normal"]
            )
        )

        story.append(
            Spacer(1, 10)
        )

        story.append(
            Paragraph(
                "Dashboard generated from the cleaned Online Retail dataset.",
                styles["Normal"]
            )
        )


        # -------------------------------------------------
        # BUILD PDF
        # -------------------------------------------------

        doc.build(story)

        buffer.seek(0)

        return buffer.getvalue()


    finally:

        for file_path in temp_files:

            try:
                os.remove(file_path)

            except Exception:
                pass


# =========================================================
# PDF EXPORT SECTION
# =========================================================

st.divider()

st.subheader("📄 Export Dashboard PDF")

st.write(
    "Generate a PDF containing the KPI cards and dashboard charts."
)

if st.button(
    "📄 Generate Dashboard PDF",
    type="primary"
):

    try:

        with st.spinner(
            "Creating PDF..."
        ):

            pdf_data = create_pdf()

        st.success(
            "PDF created successfully! ✅"
        )

        st.download_button(
            label="⬇️ Download Dashboard PDF",
            data=pdf_data,
            file_name="Retail_KPI_Dashboard.pdf",
            mime="application/pdf"
        )

    except Exception as error:

        st.error(
            "PDF creation failed."
        )

        st.code(
            str(error)
        )