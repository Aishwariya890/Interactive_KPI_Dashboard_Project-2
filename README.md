# Interactive KPI Dashboard

Interactive retail business dashboard using Streamlit, Pandas and Plotly.

## KPIs
- Total Revenue
- Total Orders
- Average Order Value
- Customers
- Quantity Sold

## Interactive visuals
- Year and Country filters
- Monthly Revenue Trend
- Top 10 Countries by Revenue
- Top 10 Products by Revenue
- Quantity vs Unit Price

## Run
```powershell
& "C:\Program Files\Python312\python.exe" -m pip install -r requirements.txt
& "C:\Program Files\Python312\python.exe" -m streamlit run app.py
```

## Use the real cleaned dataset
Put your file here:
`Data/clean_dataset.csv`

The app will automatically use it instead of the included demo dataset.

## Power BI
`Dashboard/PowerBI_DAX_Measures.txt` contains the measures for a Power BI version.

CAC and Churn Rate are not calculated because the Online Retail dataset does not contain the required marketing-cost or churn fields.
