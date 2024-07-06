from flask import Flask, render_template, request
import pandas as pd
import mysql.connector
import numpy as np

app = Flask(__name__)

# MySQL configuration
mysql_host = '192.168.227.34'
mysql_user = 'public'
mysql_password = '1234'
mysql_database = 'rough_dept'

# Excel file upload route
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        sheet = request.form['sheet']
        table = request.form['table']

        # Read Excel file into a pandas DataFrame
        df = pd.read_excel(file, sheet_name=sheet)

        # Replace NaN values with None
        df = df.replace({np.nan: None})
    

        # Modify column names: replace spaces, dashes, and percentage signs with underscores or appropriate replacements
        # df.columns = [col.replace(" ", "_").replace("-", "_").replace("%", "_SCORE") for col in df.columns]
        # # Define the conditions for assigning values to TAG_NAM
        # conditions = (df['MAIN_PKTNO'] == 0) | (df['STONE_STATUS'] == 'Rough Stock')
        # # # Assign sequential numbers starting from 1 to TAG_NAME where conditions are met
        # df.loc[conditions, 'TAG_NAME'] = np.arange(1, np.sum(conditions) + 1)
        # # # Update 'SIDTYPE' column value
        # df.loc[df['STONE_STATUS'] == 'Rough Stock', 'SIDTYPE'] = 'InProcess'
        # # # Update 'FLR' column value
        # df.loc[(df['MAIN_PKTNO'] != 0) & (df['FLR'].isnull()), 'FLR'] = "None"
        
        
            # Connect to MySQL database
        mydb = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        cursor = mydb.cursor()

        # Get the column names from the selected table
        cursor.execute(f"SELECT * FROM {table} LIMIT 1")
        columns = [column[0] for column in cursor.description]

        # Fetch and discard any unread result sets
        cursor.fetchall()

        # Filter out columns that exist both in Excel and MySQL table
        common_columns = list(set(df.columns) & set(columns))
        df = df[common_columns]

        # Insert data into the MySQL table
        for _, row in df.iterrows():
            query_columns = [f"`{col}`" if col.lower() == "table" else col for col in common_columns]
            query = f"INSERT INTO {table} ({', '.join(query_columns)}) VALUES ({', '.join(['%s'] * len(common_columns))})"
            values = tuple(row[column] for column in common_columns)
            try:
                cursor.execute(query, values)
            except Exception as e:
                print("Error Inserting Data:", e)

        # Commit changes and close the connection
        mydb.commit()
        cursor.close()
        mydb.close()

        return 'Data uploaded successfully!'

    return render_template('uploadkevin.html')


# Retrieve available sheet names from the uploaded Excel file
@app.route('/get_sheets', methods=['POST'])
def get_sheets():
    if 'file' in request.files:
        file = request.files['file']
        excel_data = pd.ExcelFile(file)
        sheets = excel_data.sheet_names
        return {'sheets': sheets}
    return {'sheets': []}


# Retrieve available table names from the MySQL database
@app.route('/get_tables', methods=['POST'])
def get_tables():
    mydb = mysql.connector.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database
    )
    cursor = mydb.cursor()

    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor]

    cursor.close()
    mydb.close()

    return {'tables': tables}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
