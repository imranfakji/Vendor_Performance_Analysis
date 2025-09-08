import sqlite3
import logging
import pandas as pd
import time

logging.basicConfig(
    filename='logs/get_vendor_summary.log',
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)

def create_vendor_summary(con):
    ''' THis Function will merge all the nessessay tables into a one table that can be used to for analysis and dashboarding'''
    vendor_sales_summary = pd.read_sql_query(
        """
        WITH FreightSummary AS (
        SELECT    
            VendorNumber,
            SUM(Freight) AS FreightCost
            FROM
            vendor_invoice 
            GROUP BY
            VendorNumber         
        ),
                
        SalesSummary AS (
            SELECT
                VendorNo,
                Brand,
                SUM(SalesQuantity) as TotalSalesQuantity,
                SUM(SalesDollars) as TotalSalesDollars,
                SUM(SalesPrice) as TotalSalesPrice,
                SUM(ExciseTax) as TotalExciseTax
            FROM
                sales
            GROUP BY
                VendorNo, Brand              
        ),
                
        PurchaseSummary AS (
            SELECT
                p.VendorNumber,
                p.VendorName,
                p.Description,
                p.Brand,
                p.PurchasePrice,
                pp.Price AS ActualPrice,
                pp.Volume,
                SUM(p.Quantity) AS TotalPurchaseQuantity,
                SUM(p.Dollars) AS TotalPurchaseDollars
            FROM
                purchases p
            JOIN
                purchase_prices pp
            ON
                p.Brand = pp.Brand
            WHERE
                p.PurchasePrice > 0
            GROUP BY
                p.VendorNumber, p.VendorName, p.Brand, p.Description, p.PurchasePrice, pp.Price, pp.Volume
        )

        SELECT
            ps.VendorNumber,
            ps.VendorName,
            ps.Brand,
            ps.Description,
            ps.PurchasePrice,
            ps.ActualPrice,
            ps.Volume,
            ps.TotalPurchaseQuantity,
            ps.TotalPurchaseDollars,
            ss.TotalSalesQuantity,
            ss.TotalSalesPrice,
            ss.TotalSalesDollars,
            ss.TotalExciseTax,
            fs.FreightCost
        FROM
            PurchaseSummary ps
        LEFT JOIN
            SalesSummary ss
        ON
            ps.VendorNumber = ss.VendorNo AND ps.Brand = ss.Brand
        LEFT JOIN
            FreightSummary fs
        ON
            ps.VendorNumber = fs.VendorNumber
        ORDER BY
            ps.TotalPurchaseDollars DESC       
        """, con)
    
    return vendor_sales_summary

def clean_data(df):
    df['Volume'] = df['Volume'].astype('Float64')
    df.fillna(0, inplace=True)

    df['VendorName'] = df['VendorName'].str.strip()
    df['Description'] = df['Description'].str.strip()

    df['GrossProfit'] = df['TotalSalesDollars'] - df['TotalPurchaseDollars']
    df['ProfitMargin'] = (df['GrossProfit'] / df['TotalSalesDollars']) *  100
    df['StockTurnover'] = df['TotalSalesQuantity'] / df['TotalPurchaseQuantity']
    df['SalestoPurchaseRatio'] = df['TotalSalesDollars'] / df['TotalPurchaseDollars']

    return df

def ingest_data(df, table_name, engine):
    """This function loads data into SQLite Database"""
    df.to_sql(table_name, con=engine, if_exists='replace', index=False)


if __name__ == '__main__':
    con = sqlite3.connect('inventory.db')

    logging.info("Creating Vendor Summary Table.....")
    summary_df = create_vendor_summary(con)
    logging.info("Created Vendor Summary Table")
    logging.info(summary_df.head())

    logging.info("Cleaning Data......")
    clean_df = clean_data(summary_df)
    logging.info("Cleaned Data")

    logging.info("Ingesting Data into DB......")
    ingest_data(clean_df, "VendorSalesSummary", con)
    logging.info("Ingested Data into DB")