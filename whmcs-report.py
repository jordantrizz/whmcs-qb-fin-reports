#!/usr/bin/python3
import os
import sys
import argparse
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
from tabulate import tabulate
import inspect
load_dotenv()

def error(text):
    # Print an error message with color red background and white text
    print("\033[41m\033[37m" + text + "\033[0m")
def debug(text):
    # Print a debug message with color blue background and white text
    if args.debug:
        print("\033[44m\033[37m" + text + "\033[0m")
def debug_arg():
    # include the name of the def and the arguments passed where debug_arg() is called
    frame = inspect.currentframe()
    caller_frame = frame.f_back
    func_name = caller_frame.f_code.co_name
    args, _, _, values = inspect.getargvalues(caller_frame)
    arg_star = ', '.join([f"{arg}={values[arg]}" for arg in args])
    debug("\033[44m\033[37m" + f"{func_name}({arg_star})" + "\033[0m")
    
# ========================================
# -- header
# ========================================
def header(text):
    # Print a header with color yellow background and black text
    print("\033[43m\033[30m" + text + "\033[0m")
    print("=" * len(text))

def header2(text):
    # Print a header with green background and black text
    print("\033[42m\033[30m" + text + "\033[0m")
    print("=" * len(text))

def header3(text):
    # Print a header with grey background and black text
    print("\033[47m\033[30m" + text + "\033[0m")
    print("=" * len(text))
    
# ========================================
# -- get_db_connection
# ========================================
def get_db_connection():
    # Connect to the database
    mydb = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )
    return mydb

# ========================================
# -- test_db_connection
# ========================================
def test_db_connection():
    try:
        mydb = get_db_connection()
        print("Database connection successful")
        mydb.close()
    except Exception as e:
        print("Database connection failed: ", e)
        sys.exit(1)

# ========================================
# -- get_invoice_data
# ========================================
def get_invoice_data(start_date, end_date, invoice_status="all"):
    """
    Get all invoices with status using the date range provided and return them in an array
    id, invoicenum, total, subtotal, fees, tax, status, date, datepaid, userid

    Args:
        status (str): The status of the invoice
        start_date (datetime): The start date of the date range
        end_date (datetime): The end date of the date range

    Returns:
        totalrows(int): The total number of rows fetched
        invoices(array): An array of invoices
    """
    debug_arg()
    
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    
    # Generate the query
    query = """
    SELECT id, invoicenum, subtotal, total, tax, status, date, datepaid, userid
    FROM tblinvoices
    WHERE date >= %s
    AND date <= %s
    """
    
    # Parameters list
    params = [start_date, end_date]
    
    # Conditionally add the status filter
    if invoice_status not in ["all", "All"]:
        query += "AND status = %s"
        params.append(invoice_status)
    
    # Execute the query
    debug(f"Executing query: {query} with parameters: {params}\n")
    try:
        mycursor.execute(query, params)
    except Exception as e:
        print("Error executing query: ", e)
        print("Query: ", query)
        sys.exit(1)
    
    # Print out sql query
    debug("Query: " + mycursor.statement)
    
    # Fetch all rows
    rows = mycursor.fetchall()
    
    # Count the total number of invoices
    totalrows = len(rows)
    
    # Put all invoices into an array and return it
    invoices = []
    for row in rows:
        #id, invoicenum, subtotal, total, tax, status, date, datepaid, userid
        debug(f"Row: {row}")        
        id = row[0]
        invoicenum = row[1]        
        subtotal = row[2]
        total = row[3]
        tax = row[4]
        fees = 0
        if row[5] == "Paid":
            fees = get_invoice_fees(id)
        status = row[5]
        date = row[6]
        datepaid = row[7]
        userid = row[8]
            
        invoices.append([id, invoicenum, subtotal, total, fees, tax, status, date, datepaid, userid])
    
    return totalrows, invoices

# ========================================
# -- get_invoice_fees
# ========================================
def get_invoice_fees(invoiceid):
    debug_arg()
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    
    # Query the database for fees
    query = """
    SELECT SUM(fees) as fees
    FROM tblaccounts
    WHERE invoiceid = %s
    """
    
    # Execute the query
    mycursor.execute(query, (invoiceid,))
    
    # Fetch the fees
    fees = mycursor.fetchone()[0] or 0
    
    mycursor.close()
    mydb.close()
    
    return fees

# ========================================
# -- get_client_name
# ========================================
def get_client_name(clientid):
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    
    # Query the database for the client name
    query = """
    SELECT companyname
    FROM tblclients
    WHERE id = %s
    """
    
    # Execute the query
    mycursor.execute(query, (clientid,))
    
    # Fetch the client name
    name = mycursor.fetchone()[0]
    
    mycursor.close()
    mydb.close()
    
    return name

# ========================================
# -- all_invoices
# ========================================
def all_invoices(month=None, status="all"):
    """Fetch all invoices for the previous month and return them in a table."""
    debug_arg()
    current_month = datetime.today().month
    if month is None or month == "last":
        start_date = datetime(datetime.today().year, current_month - 1, 1)
        end_date = datetime(datetime.today().year, current_month, 1)
        month = start_date.strftime("%B %Y")
    elif month == "this":
        start_date = datetime(datetime.today().year, current_month, 1)
        end_date = datetime(datetime.today().year, current_month + 1, 1)
        month = start_date.strftime("%B %Y")
    else:
        # check if month is a valid month and year aug-2021
        try:
            month, year = month.split("-")
            month = datetime.strptime(month, "%b").month
            start_date = datetime(int(year), month, 1)
            end_date = datetime(int(year), month + 1, 1)
        except Exception as e:
            error("Invalid month provided, use the format 'MMM-YYYY'")
            sys.exit(1)

    print(f"Invoices from Month: {month}")

    invoice_data = get_invoice_data(start_date, end_date, status)
    total_numberof_invoices, invoices = invoice_data


    # Debug: Print the number of rows fetched
    header(f"Number of rows fetched: {total_numberof_invoices}")

    # Create a table with the required columns
    table = []
    table.append(["ID","Invoice Number", "Sub Total", "Total", "Tax", "Fees", "Status", "Date", "Date Paid", "User ID", "Client Name"])

    # Populate the table with the fetched data
    for invoice in invoices:
        id, invoicenum, subtotal, total, fees, tax, status, date, datepaid, userid = invoice
        clientname = get_client_name(userid)
        table.append([id, invoicenum, subtotal, total, tax, fees, status, date, datepaid, userid, clientname])
    
    # Total up the column subtotal, total, tax, fees
    total_invoices = len(invoices)
    total_subtotal = sum([i[2] for i in invoices])
    total_total = sum([i[3] for i in invoices])
    total_tax = sum([i[4] for i in invoices])
    total_fees = sum([i[5] for i in invoices])
    table.append([total_invoices, "", total_subtotal, total_total, total_tax, total_fees, "", "", "", ""]) 

    print(tabulate(table, headers="firstrow", tablefmt="grid"))
    
    # Print a summary
    print_summary(month)
    
    
# ========================================
# -- print_summary
# ========================================
def print_summary(month,status="Paid"):
    """Print a summary of the invoices for the passed month.

    Args:
        month (str): The month to get the summary for format "MMM YYYY"
        status (str): The status of the invoices to get the summary for
    """
    debug_arg()
    # Get the time range for the passed month
    month, year = month.split(" ")
    month = datetime.strptime(month, "%B").month
    start_date = datetime(int(year), month, 1)
    end_date = datetime(int(year), month + 1, 1)

    invoice_data = get_invoice_data(start_date, end_date, status)
    total_numberof_invoices, invoices = invoice_data
                
    # Total up the column subtotal, total, tax, fees
    total_subtotal = sum([i[2] for i in invoices])
    total_total = sum([i[3] for i in invoices])
    total_tax = sum([i[4] for i in invoices])
    total_fees = sum([i[5] for i in invoices])
    
    month_text = start_date.strftime("%B %Y")
    header2(f"Summary for {month_text}")
    print(f"{'Invoices':<25}: {total_numberof_invoices:>10}")
    print(f"{'Subtotal':<25}: {total_subtotal:>10.2f}")
    print(f"{'Fees':<25}: {total_fees:>10.2f}")
    print(f"{'Tax':<25}: {total_tax:>10.2f}")
    print("=====================================")
    print(f"{'Net = Total - Fees - Tax':<25}: {total_total - total_fees - total_tax:>10.2f}")
    print(f"{'Taxes to be paid':<25}: {total_tax:>10.2f}")
    print()

# ========================================
# -- print_summary_year
# ========================================
def print_summary_year(year):
    debug_arg()
    # Get current year
    current_year = datetime.today().year
    if year is None:
        year = current_year
    else:
        try:
            year = int(year)
        except Exception as e:
            error("Invalid year provided")
            sys.exit(1)
    
    # Get all months in the year up to last month
    months = range(1, datetime.today().month)
    
    # Get month by month summary for the year
    for month in months:
        month = datetime(current_year, month, 1).strftime("%B %Y")
        print_summary(month,status="Paid")
    

# ========================================
# -- get_invoice_statuses
# ========================================
def get_invoice_statuses():
    # Get unique status values from the database
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    
    # Query the database for unique status values
    query = """
    SELECT DISTINCT status
    FROM tblinvoices
    """
    
    mycursor.execute(query)
    rows = mycursor.fetchall()
    # turn rows into a list
    everyStatus = [row[0] for row in rows]

    mycursor.close()
    mydb.close()

    return everyStatus

# ========================================
# -- get_invoice
# ========================================
def get_invoice(invoice_number):
    mydb = get_db_connection()
    mycursor = mydb.cursor()

    # Get all invoices for the previous month
    # invoice number, total, tax, status.
    # no fees
    query = """
    SELECT id,invoicenum, total, subtotal, tax, status, date, datepaid, userid 
    FROM tblinvoices
    WHERE date >= %s
    AND date <= %s
    AND invoicenum = %s
    """

    # Execute the query
    mycursor.execute(query, (first_of_last_month, first_of_this_month, invoice_number))
    
    # Fetch all rows
    rows = mycursor.fetchall()
    
    # Count totall number of invoices
    total_numberof_invoices = len(rows)
    
    # Put all invoices into an array and return it
    # invoice number, subtotal, total, tax, status, date, datepaid, userid
    invoices = []
    for row in rows:
        fees = 0
        if row[5] == "Paid":
            query = """
            SELECT SUM(fees) as fees
            FROM tblaccounts
            WHERE invoiceid = %s
            """
            mycursor.execute(query, (row[1],))
            fees = mycursor.fetchone()[0] or 0
        invoices.append([row[0], row[1], row[2], row[3], fees, row[4], row[5], row[6], row[7], row[8]])
            
    mycursor.close()
    mydb.close()
    return total_numberof_invoices

# ========================================
# -- invoice_report
# ========================================
def invoice_report():
    everyStatus = get_invoice_statuses()
    # Print out the statuses
    header("Invoice Statuses")
    for status in everyStatus:
        print(status)
    print() 
    
    header(f"Invoice Totals for {first_of_last_month.strftime('%B %Y')}")
    print ()
    # Loop through paid and unpaid invoices using the template below
    for status in everyStatus:
        total_numberof_invoices, invoice = get_invoice_data(status)
        if total_numberof_invoices == 0:
            header3(f"No {status} invoices in {first_of_last_month.strftime('%B %Y')}")
            print()
            continue
        
        
        # total up all the invoices
        invoice_total = 0
        total_before_tax_minus_fees = 0
        total_tax = 0
        fees = 0
        for i in invoice:
            invoice_total += i[2]
            total_before_tax_minus_fees += i[3]
            total_tax += i[4]
            fees += i[5]
        
        header2(f"{status} invoices in {first_of_last_month.strftime('%B %Y')}")
        # Print a table
        print(f"{'Invoices':<25}: {total_numberof_invoices:>10}")
        print(f"{'Before Tax/Fees':<25}: {total_before_tax_minus_fees:>10.2f}")
        print(f"{'Fees':<25}: {fees:>10.2f}")    
        print(f"{'Total tax':<25}: {total_tax:>10.2f}")
        print()
    print()

def print_report():
    # Print invoice report
    invoice_report()
    
    # Print Invoice Table
    all_invoices()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process invoice data and calculate totals.")
    parser.add_argument('--force', action='store_true', help="Run the script regardless of the date")
    parser.add_argument('--cron', action='store_true', help="Run the script if the day is the first of the month")
    parser.add_argument('--all-invoices', action='store', nargs='?',const='last', help="Get all invoices for the specified month")
    parser.add_argument('--paid-invoices', action='store', nargs='?',const='last', help="Get a specific invoice")
    parser.add_argument('--summary-year', action='store', help="Get a summary of the year")
    parser.add_argument('--invoice', action='store', help="Get a specific invoice")
    parser.add_argument('--debug', action='store_true', help="Print debug information")
    
    args = parser.parse_args()

    if args.force:
        print_report()
    elif args.cron:
        if datetime.today().day == 1:
            print_report()
    elif args.all_invoices:
        all_invoices(args.all_invoices)
    elif args.paid_invoices:
        all_invoices(args.paid_invoices, "Paid")
    elif args.summary_year:
        print_summary_year(args.summary_year)
    elif args.invoice:
        invoice_number = args.invoice
        if get_invoice(invoice_number) == 0:
            header3(f"No invoice {invoice_number}")
        else:
            header2(f"Invoice {invoice_number}")
    else:
        error("No arguments provided")
        parser.print_help()