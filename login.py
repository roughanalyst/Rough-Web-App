from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
import pandas as pd
import numpy as np
from datetime import datetime
from decimal import Decimal
import calendar
import MySQLdb 

app = Flask(__name__, template_folder="templates")
app.secret_key = 'rough'

# MySQL configurations
app.config['MYSQL_HOST'] = '192.168.227.34'
app.config['MYSQL_USER'] = 'public'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'rough_dept'
mysql = MySQL(app)


def execute_query(query, *args):
    with mysql.connection.cursor() as cursor:
        cursor.execute(query, args)
        return cursor.fetchall()

def get_nns_lotno():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT DISTINCT LOTNO FROM nns ORDER BY LOTNO")
    lotnos = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return lotnos

# @app.after_request
# def add_header(response):
#     response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#     response.headers['Pragma'] = 'no-cache'
#     response.headers['Expires'] = '0'
#     return response

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT username FROM users WHERE id=%s AND password=%s", (username, password))
    user_data = cursor.fetchone()
    cursor.close()

    if user_data:
        session['username'] = user_data[0]
        return redirect(url_for('home'))
    else:
        return render_template('login.html', message='Invalid username or password')

@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT rights FROM audit_right WHERE uname = %s", (username,))
        user_rights = [right[0] for right in cursor.fetchall()]
        cursor.close()
        return render_template('home.html', username=username, user_rights=user_rights)
    else:
        return redirect(url_for('index'))

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/<page>')
def dynamic_page(page):
    if page == 'favicon.ico':
        return ''
    return render_template(f'{page}.html')

@app.route('/change_password', methods=['POST'])
def change_password():
    
    if request.method == 'POST':
        user_id = request.form['user_id']
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT password FROM users WHERE id=%s", (user_id,))
        row = cursor.fetchone()

        if row:
            stored_password = row[0]
            if current_password == stored_password:
                if new_password == confirm_password:
                    try:
                        cursor.execute("UPDATE users SET password=%s WHERE id=%s", (new_password, user_id))
                        mysql.connection.commit()
                        cursor.close()
                        return jsonify({'success': True, 'message': 'Password changed successfully!'})
                    except Exception as e:
                        return jsonify({'success': False, 'error': 'An error occurred while changing the password.'})
                else:
                    return jsonify({'success': False, 'error': 'New Password and confirm password do not match!'})
            else:
                return jsonify({'success': False, 'error': 'Current password is incorrect!'})
        else:
            return jsonify({'success': False, 'error': 'User not found!'})


@app.route('/NNS', methods=['GET', 'POST'])
def nns_view_data():
    if 'username' in session:
        username = session['username']
        if request.method == 'POST':
            apply_lotno = request.form.get('apply_lotno')
            if apply_lotno:
                table_data = execute_query("SELECT * FROM nns WHERE LOTNO = %s", (apply_lotno,))
                column_names = [i[0] for i in execute_query("DESCRIBE nns")]
                AVG_MPM_PD = execute_query('''WITH CALC AS (
                                                    SELECT n.LOTNO, ROUND(SUM(n.upd_AVG_MPM_PD), 4) AS AMOUNT,
                                                    lm.CTS,
                                                    lm.RGH_RATE,
                                                    ROUND(lm.CTS * lm.RGH_RATE, 4) AS LABOUR
                                                    FROM nns n
                                                    JOIN lot_master_table lm ON n.LOTNO = lm.LOTNO
                                                    WHERE n.LOTNO = %s
                                                    GROUP BY n.LOTNO, lm.RGH_RATE, lm.CTS
                                                ),
                                                calc2 AS (
                                                    SELECT LOTNO, AMOUNT, CTS, RGH_RATE, LABOUR, AMOUNT - LABOUR AS expense FROM CALC
                                                )
                                                SELECT ROUND(expense/CTS, 0) AS avg_ FROM calc2''', (apply_lotno,))
                
                CURR_AVG = execute_query('''WITH CALC AS (
                                                    SELECT n.LOTNO, ROUND(SUM(n.Upd_MAX_CUR_FINAL_RATE_PD), 4) AS AMOUNT,
                                                    lm.CTS,
                                                    lm.RGH_RATE,
                                                    ROUND(lm.CTS * lm.RGH_RATE, 4) AS LABOUR
                                                    FROM nns n
                                                    JOIN lot_master_table lm ON n.LOTNO = lm.LOTNO
                                                    WHERE n.LOTNO = %s
                                                    GROUP BY n.LOTNO, lm.RGH_RATE, lm.CTS
                                                ),
                                                calc2 AS (
                                                    SELECT LOTNO, AMOUNT, CTS, RGH_RATE, LABOUR, AMOUNT - LABOUR AS expense FROM CALC
                                                )
                                                SELECT ROUND(expense/CTS, 0) AS avg_ FROM calc2''', (apply_lotno,))
                avg_mpm_pd_value = AVG_MPM_PD[0][0] if AVG_MPM_PD else None
                curr_pd_value = CURR_AVG[0][0] if CURR_AVG else None

                print("AVG MPM PD:", avg_mpm_pd_value)
                print("Curr PD:", curr_pd_value)

                return render_template('nns.html', column_names=column_names, table_data=table_data, lotnos=get_nns_lotno(),username=username,selected_lotno=apply_lotno, avg_mpm_pd_value=avg_mpm_pd_value, curr_pd_value=curr_pd_value)
            else:
                return redirect('/NNS')
        else:
            # Update the query to select only the specified columns
            table_data = execute_query("SELECT * from raj")
            # Update column names to only include selected fields
            column_names = ['Message']
            lotnos = get_nns_lotno() # Fetch lotnos for dropdown list
            selected_lotno = request.args.get('apply_lotno')
            return render_template('nns.html', column_names=column_names, table_data=table_data, lotnos=lotnos, selected_lotno=selected_lotno, username=username)       

@app.route('/NNS_AUDIT', methods=['GET', 'POST'])
def nns_audit_data():
     if 'username' in session:
        username = session['username']
        if request.method == 'POST':
            apply_lotno = request.form.get('apply_lotno')
            if apply_lotno:
                # Update the query to select only the specified columns
                table_data = execute_query("SELECT DISPLAY_LOTNO, PKTNO, MAIN_PKTNO, LOTNO, TAG_NAME, SIZE_NAME, ROUGH_UNCUT, LBR_RATE, ORG_CTS, STONE_STATUS, STONE_ID, LAB, CTS, SHP, CLA, COL, CUT, NEW_CUT, POL, SYM, FLR, HGT, TBL, LEN, WDTH, DEPTH_MM, CR_ANG, PV_ANG, CR_HGT, PV_HGT, GIRDLE, L_W, PROG_NAME, RAPO_RATE, MPM, PD_PER, PD, PD_CNT, MPM_PD, RATE_TYPE, CURR_PROG_NAME, ARTICLE, TRANS_TYPE, AVG_VALUE, AVG_MPM_PD, STONE_CATEGORY, SIDTYPE, RATE_TYPE_CUR_FINAL_RATE, MAX_CUR_FINAL_RATE_PD, SI2_I1, SALES_AVG_VALUE, RATE_ENTRY, DISC_PER, ISACTIVE_PROG, S_LAB_STD_EXP, PROG_AMOUNT, YNS_STATUS, LSD_SCORE, CSD_SCORE, SALES_CALC_VALUE, IS_SALES_VALUE, upd_AVG_MPM_PD, Upd_MAX_CUR_FINAL_RATE_PD,actions FROM nns WHERE LOTNO = %s", (apply_lotno,))
                # Update column names to only include selected fields
                column_names = ['DISPLAY_LOTNO', 'PKTNO', 'MAIN_PKTNO', 'LOTNO', 'TAG_NAME', 'SIZE_NAME', 'ROUGH_UNCUT', 'LBR_RATE', 'ORG_CTS', 'STONE_STATUS', 'STONE_ID', 'LAB', 'CTS', 'SHP', 'CLA', 'COL', 'CUT', 'NEW_CUT', 'POL', 'SYM', 'Flour', 'HGT', 'TBL', 'LEN', 'WDTH', 'DEPTH_MM', 'CR_ANG', 'PV_ANG', 'CR_HGT', 'PV_HGT', 'GIRDLE', 'L_W', 'PROG_NAME', 'RAPO_RATE', 'MPM', 'PD_PER', 'PD', 'PD_CNT', 'MPM_PD', 'RATE_TYPE', 'CURR_PROG_NAME', 'ARTICLE', 'TRANS_TYPE', 'AVG_VALUE', 'AVG_MPM_PD', 'STONE_CATEGORY', 'SIDTYPE', 'RATE_TYPE_CUR_FINAL_RATE', 'MAX_CUR_FINAL_RATE_PD', 'SI2_I1', 'SALES_AVG_VALUE', 'RATE_ENTRY', 'DISC_PER', 'ISACTIVE_PROG', 'S_LAB_STD_EXP', 'PROG_AMOUNT', 'YNS_STATUS', 'LSD_SCORE', 'CSD_SCORE', 'SALES_CALC_VALUE', 'IS_SALES_VALUE', 'upd_AVG_MPM_PD', 'Upd_MAX_CUR_FINAL_RATE_PD','Flag']


                AVG_MPM_PD = execute_query('''WITH CALC AS (
                                                    SELECT n.LOTNO, ROUND(SUM(n.AVG_MPM_PD), 4) AS AMOUNT,
                                                    lm.CTS,
                                                    lm.RGH_RATE,
                                                    ROUND(lm.CTS * lm.RGH_RATE, 4) AS LABOUR
                                                    FROM nns n
                                                    JOIN lot_master_table lm ON n.LOTNO = lm.LOTNO
                                                    WHERE n.LOTNO = %s
                                                    GROUP BY n.LOTNO, lm.RGH_RATE, lm.CTS
                                                ),
                                                calc2 AS (
                                                    SELECT LOTNO, AMOUNT, CTS, RGH_RATE, LABOUR, AMOUNT - LABOUR AS expense FROM CALC
                                                )
                                                SELECT ROUND(expense/CTS, 0) AS avg_ FROM calc2''', (apply_lotno,))
                
                CURR_AVG = execute_query('''WITH CALC AS (
                                                    SELECT n.LOTNO, ROUND(SUM(n.MAX_CUR_FINAL_RATE_PD), 4) AS AMOUNT,
                                                    lm.CTS,
                                                    lm.RGH_RATE,
                                                    ROUND(lm.CTS * lm.RGH_RATE, 4) AS LABOUR
                                                    FROM nns n
                                                    JOIN lot_master_table lm ON n.LOTNO = lm.LOTNO 
                                                    WHERE n.LOTNO = %s
                                                    GROUP BY n.LOTNO, lm.RGH_RATE, lm.CTS
                                                ),
                                                calc2 AS (
                                                    SELECT LOTNO, AMOUNT, CTS, RGH_RATE, LABOUR, AMOUNT - LABOUR AS expense FROM CALC
                                                )
                                                SELECT ROUND(expense/CTS, 0) AS curr_ FROM calc2''', (apply_lotno,))
                New_AVG_MPM_PD = execute_query('''WITH CALC AS (
                                                    SELECT n.LOTNO, ROUND(SUM(n.upd_AVG_MPM_PD), 4) AS AMOUNT,
                                                    lm.CTS,
                                                    lm.RGH_RATE,
                                                    ROUND(lm.CTS * lm.RGH_RATE, 4) AS LABOUR
                                                    FROM nns n
                                                    JOIN lot_master_table lm ON n.LOTNO = lm.LOTNO
                                                    WHERE n.LOTNO = %s
                                                    GROUP BY n.LOTNO, lm.RGH_RATE, lm.CTS
                                                ),
                                                calc2 AS (
                                                    SELECT LOTNO, AMOUNT, CTS, RGH_RATE, LABOUR, AMOUNT - LABOUR AS expense FROM CALC
                                                )
                                                SELECT ROUND(expense/CTS, 0) AS new_avg_ FROM calc2''', (apply_lotno,))
                
                New_CURR_AVG = execute_query('''WITH CALC AS (
                                                    SELECT n.LOTNO, ROUND(SUM(n.Upd_MAX_CUR_FINAL_RATE_PD), 4) AS AMOUNT,
                                                    lm.CTS,
                                                    lm.RGH_RATE,
                                                    ROUND(lm.CTS * lm.RGH_RATE, 4) AS LABOUR
                                                    FROM nns n
                                                    JOIN lot_master_table lm ON n.LOTNO = lm.LOTNO 
                                                    WHERE n.LOTNO = %s
                                                    GROUP BY n.LOTNO, lm.RGH_RATE, lm.CTS
                                                ),
                                                calc2 AS (
                                                    SELECT LOTNO, AMOUNT, CTS, RGH_RATE, LABOUR, AMOUNT - LABOUR AS expense FROM CALC
                                                )
                                                SELECT ROUND(expense/CTS, 0) AS new_curr_ FROM calc2''', (apply_lotno,))
                new_avg_mpm_pd = New_AVG_MPM_PD[0][0] if New_AVG_MPM_PD else None
                new_curr_pd = New_CURR_AVG[0][0] if New_CURR_AVG else None
                avg_mpm_pd_value = AVG_MPM_PD[0][0] if AVG_MPM_PD else None
                curr_pd_value = CURR_AVG[0][0] if CURR_AVG else None

                return render_template('NNS_AUDIT.html', column_names=column_names, table_data=table_data, lotnos=get_nns_lotno(), selected_lotno=apply_lotno,avg_mpm_pd_value=avg_mpm_pd_value, curr_pd_value=curr_pd_value, new_avg_mpm_pd = new_avg_mpm_pd, new_curr_pd = new_curr_pd, username=username)
            else:
                return redirect('/NNS_AUDIT')
        else:
            table_data = execute_query("SELECT * FROM raj")
            # Update column names to only include selected fields
            column_names = ['Message']
            lotnos = get_nns_lotno()  # Fetch lotnos for dropdown list
            selected_lotno = request.args.get('apply_lotno')
            return render_template('NNS_AUDIT.html', column_names=column_names, table_data=table_data, lotnos=lotnos, selected_lotno=selected_lotno, username=username)
        
@app.route('/update_audit_nns', methods=['POST'])
def update_audit_nns():
        if request.method == 'POST':
            cursor = mysql.connection.cursor()
            try:
                data = request.json
                lotno = data.get('lotno')
                pktno = data.get('pktno')
                tag = data.get('tag')
                avg = data.get('edit1')
                curr = data.get('edit2')
                flag = 1
                user_id = session.get('username')
                current_time = datetime.now()
                print(lotno,pktno,tag,avg,curr,user_id,current_time,flag)
                cursor.execute('''update nns set upd_avg_mpm_pd = %s , upd_MAX_CUR_FINAL_RATE_PD = %s, user_id = %s,upd_time = %s, Actions=%s where DISP_LOTNO = %s and PKTNO = %s and TAG_NAME = %s ''', (avg, curr, user_id,current_time, flag, lotno, pktno, tag))
                mysql.connection.commit()
                cursor.close()

                return jsonify({'message': 'Values updated successfully'}), 200
            except Exception as e:
                return jsonify({'error': 'Error occurred while updating values: ' + str(e)}), 500
        else:
            return jsonify({'error': 'Method not allowed'}), 405
   
@app.route('/LOT MASTER', methods=['GET', 'POST'])
def lot_master_audit_data():
      if 'username' in session:
        username = session['username']
        if request.method == 'POST':
            selected_lotno = request.form['selected_lotno']
            if selected_lotno:
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT * FROM lot_master_table WHERE LOTNO = %s", (selected_lotno,))
                column_names = [i[0] for i in cursor.description]
                table_data = cursor.fetchall()
                cursor.close()
                return render_template('LOT MASTER.html', column_names=column_names, table_data=table_data, select_options=get_lotnos(), selected_lotno=selected_lotno)
            else:
                return redirect('/LOT MASTER')
        else:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM lot_master_table LIMIT 10")
            column_names = [i[0] for i in cursor.description]
            table_data = cursor.fetchall()
            cursor.close()
            return render_template('LOT MASTER.html', column_names=column_names, table_data=table_data, select_options=get_lotnos(),username=username)

def get_lotnos():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT DISTINCT LOTNO FROM lot_master_table ORDER BY LOTNO")
    lotnos = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return lotnos

@app.route('/historyprice', methods=['GET','POST'])
def history_price_data():
      if 'username' in session:
        username = session['username']
        if request.method == 'POST':
            selected_lotno = request.form['selected_lotno']
            if selected_lotno:
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT * FROM history_price where Lotno = %s",(selected_lotno,))
                column_names = [i[0] for i in cursor.description]
                table_data = cursor.fetchall()
                cursor.close()
                return render_template('historyprice.html',column_names=column_names, table_data=table_data, select_options = histroy_lot(),selected_lotno=selected_lotno,username=username)
            else:
                return redirect('/historyprice')
        else:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * from history_price limit 10")
            column_names = [i[0] for i in cursor.description]
            table_data = cursor.fetchall()
            cursor.close()
            return render_template('historyprice.html', column_names=column_names, table_data=table_data, select_options=histroy_lot(),username=username)

def histroy_lot():
    cursor = mysql.connection.cursor()
    cursor.execute("Select DISTINCT LOTNO from history_price ORDER by LOTNO")
    lots = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return lots

@app.route('/missing-stones', methods=['GET'])
def get_missing_stones():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT lotno, pktNo, mainPktNo, pcs, cts, amount, curr_amount, levels, sublevel, remark, user_id FROM missing_stone")
    missing_stones = cursor.fetchall()
    print(missing_stones)
    cursor.close()
    return render_template()

@app.route('/missing-stones', methods=['POST'])
def add_missing_stone():
    data = request.json
    lotno = data['lotno']
    pktNo = data['pktNo']
    mainPktNo = data['mainPktNo']
    pcs = data['pcs']
    cts = data['cts']
    amount = data['amount']
    curr_amount = data['curr_amount']
    levels = data['levels']
    sublevel = data['sublevel']
    remark = data['remark']
    user_id = session.get('username')

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO missing_stone(lotno,MainPktno,Pktno,Pcs,Cts,Amount,Curr_Amount,levels,SubLevel,Remark,User_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",(lotno, pktNo, mainPktNo, pcs, cts, amount, curr_amount, levels, sublevel, remark, user_id))
    mysql.connection.commit()
    new_id = cursor.lastrowid # Get the ID of the newly inserted row
    cursor.close()

    return jsonify({'insertId': new_id}), 201

# Route to update a missing stone
@app.route('/missing-stones/<int:id>', methods=['PUT'])
def update_missing_stone(id):
    data = request.json
    lotno = data['lotno']
    pktNo = data['pktNo']
    mainPktNo = data['mainPktNo']
    pcs = data['pcs']
    cts = data['cts']
    amount = data['amount']
    curr_amount = data['curr_amount']
    levels = data['levels']
    sublevel = data['sublevel']
    remark = data['remark']
    user_id = session.get('username')

    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE missing_stone SET lotno=%s, pktNo=%s, mainPktNo=%s, pcs=%s, cts=%s, amount=%s, curr_amount=%s, levels=%s, sublevel=%s, remark=%s, User_name=%s WHERE id=%s", (lotno, pktNo, mainPktNo, pcs, cts, amount, curr_amount, levels, sublevel, remark, user_id, id))
    mysql.connection.commit()
    cursor.close()

    return 'Missing stone updated successfully'

# Flask route to delete a missing stone
@app.route('/missing-stones/<int:id>', methods=['DELETE'])
def delete_missing_stone(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM missing_stone WHERE id=%s", (id,))
    mysql.connection.commit()
    cursor.close()

    return 'Missing stone deleted successfully'

@app.route('/portfolio', methods=['GET', 'POST'])
def portfolio_user():
      if 'username' in session:
        username = session['username']
        # username = session.get('username')
        updated_row = execute_query("SELECT * FROM portfolio WHERE User_Name = %s ORDER BY Times DESC", (username,))
        column_names = [i[0] for i in execute_query("DESCRIBE portfolio")]

    # Fetch the updated row

        return render_template('portfolio.html', column_names=column_names, updated_row=updated_row,username=username)

@app.route('/update_portfolio', methods=['POST'])
def update_portfolio():
    username = session.get('username')
    data = request.json
    lotno = data['lotno']
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Remove AM/PM designation

    last_user = execute_query("SELECT User_Name FROM portfolio WHERE LOTNO=%s ", (lotno,))
    lastuser = last_user[0][0] if last_user else None

    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE portfolio SET User_Name=%s, Times=%s, Last_User=%s WHERE Lotno=%s", (username, current_time, lastuser, lotno))
    mysql.connection.commit() # Commit the transaction
    cursor.close()
    
    updated_row = execute_query("SELECT * FROM portfolio WHERE User_Name = %s ORDER BY Times DESC", (username,))
    column_names = [i[0] for i in execute_query("DESCRIBE portfolio")]
    
    return jsonify({'message': 'Portfolio updated successfully', 'updated_row': updated_row, 'column_names': column_names})


@app.route('/upload', methods=['POST', 'GET'])
def upload_excel_to_mysql():
    message = None

    if request.method == 'POST':
        file = request.files['file']
        sheet = request.form['sheet']
        table = request.form['table']

        try:
            # Read Excel file into a pandas DataFrame
            df = pd.read_excel(file, sheet_name=sheet)

            # Replace NaN values with None
            df = df.replace({np.nan: None})

            # Modify column names: replace spaces, dashes, and percent signs with underscores
            df.columns = [col.replace(" ", "_").replace("-", "_").replace("%", "_SCORE") for col in df.columns]

            # Connect to MySQL database
            cursor = mysql.connection.cursor()

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
                cursor.execute(query, values)

            print(query)
            cursor.close()

            message = "Data uploaded successfully"
        except Exception as e:
            print("Error:", e)
            message = "Error occurred while uploading data"

    return render_template('upload.html', message=message)

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
    try:
        cursor = mysql.connection.cursor()

        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor]

        cursor.close()

        return {'tables': tables}
    except Exception as e:
        print("Error fetching tables:", e)
        return {'tables': []}

# Global variable initialized
from_month_formatted = None
to_month_formatted = None
from_month_display = None
to_month_display = None
month_pl = []
month_pl_display = []
production = []
pl_type = None

@app.route('/P_AND_L_REPORT', methods=['GET', 'POST'])
def p_l():
    if 'username' in session:
        username = session['username']
        global from_month_formatted, to_month_formatted, from_month, to_month, from_month_display,to_month_display,production,pl_type

        #  retrieves the fromMonth and toMonth values from the form data:
        from_month = request.form.get('fromMonth')
        to_month = request.form.get('toMonth')

        global month_pl,month_pl_display
        month_pl = []
        month_pl_display = []
        results = []
        line = 0
        message = ''
        GPCS = GPOLISH_CTS = GCOGS = GEXPENSE = GPRODUCTION_COST = GPROVISIONAL = GAVG_LOCK = GTOTAL_SALES_VALUE = GNET_PROFIT = GNET_PROFIT_MARGIN = 0

# If both from_month and to_month are provided, they are parsed into datetime objects and formatted as needed:
        if from_month and to_month:
            from_month_dt = datetime.strptime(from_month, "%Y-%m")
            to_month_dt = datetime.strptime(to_month, "%Y-%m")

            from_month_formatted = int(from_month_dt.strftime("%Y%m"))
            to_month_formatted = int(to_month_dt.strftime("%Y%m"))

            from_month_display = from_month_dt.strftime("%b-%Y")
            to_month_display = to_month_dt.strftime("%b-%Y")

# A list of months between from_month_formatted and to_month_formatted is generated:
            for i in range(from_month_formatted, to_month_formatted + 1):
                year = i // 100
                month = i % 100
                if ((1 <= month <= 12) or (year == 401 and 1 <= month <= 5)):
                    month_pl.append(i)
                    month_pl_display.append(datetime(year, month, 1).strftime("%b-%Y")) 

            line = len(month_pl)

# Two queries are defined to check for missing data
            cursor = mysql.connection.cursor()

            check_nns = 'SELECT distinct LOTNO FROM nns;'
            check_production = 'SELECT distinct LOTNO FROM production WHERE PROD_MONTH = %s;'
            cursor.execute(check_nns)
            check_nns_data = cursor.fetchall()

            if i in month_pl:
                cursor.execute(check_production,(i,))
                check_production_data = cursor.fetchall()

                nns_set = set(check_nns_data)
                production_set = set(check_production_data)
                missing_data_pl = production_set - nns_set

            # Determine the appropriate message
                if len(production_set) == 0:
                    message = f"Production Data is Missing for month {i}"
                elif len(missing_data_pl) > 0:
            # Create a message including the missing data
                    message = f"NNS Data is Missing for the following records in month {i}: {missing_data_pl,len(missing_data_pl)}"
                else:
                    message = " "

            print(message)
            print("month pl",month_pl)
            print("month pl display",month_pl_display)

# Based on pl_type from form , to fetch relevant data
            pl_type  =  request.form.get('p_l_type')
            print("pl type",pl_type)

            if pl_type == 'JV' :
                print("part-1")
                query = '''
                WITH ok AS (
                SELECT 
                    p.LOTNO, 
                    p.CTS,
                    p.TOT_PKT_VALUE,
                    l.overall_cost, 
                    m.jv_expense AS Expense, 
                    p.AVG_LOCK_VALUE, 
                    n.running_percent,
                    p.PROVISIONAL_LOCK_VALUE,
                    p.value_status,
                    p.PROD_MONTH,
                    SUM(CASE WHEN p.JV_Status = 'Jv' THEN p.TOT_PKT_VALUE ELSE 0 END) 
                    OVER (PARTITION BY p.PROD_MONTH) AS total_jv_month_value
                FROM 
                    production p 
                JOIN nns n ON p.TAG = n.TAG_NAME AND p.LOTNO = n.LOTNO AND p.MAIN_PKTNO = n.MAIN_PKTNO
                JOIN lot_master_table l ON l.LOTNO = p.LOTNO
                JOIN manufacturing_expense m ON m.Prod_month = p.PROD_MONTH 
                WHERE p.PROD_MONTH BETWEEN %s AND %s AND p.JV_Status = 'Jv'
                ),
                ok2 AS (
                    SELECT 
                        ok.*,
                        (ok.TOT_PKT_VALUE / ok.total_jv_month_value) AS PER_for_jv,
                        (ok.running_percent * ok.overall_cost / 100.00) AS weightage_cogs
                    FROM ok
                ), 
                ok3 AS (
                    SELECT 
                        ok2.*, 
                        (PER_for_jv * Expense) AS Expense_jv
                    FROM ok2
                ),
                ok4 AS (
                    SELECT 
                        COUNT(*) AS Pcs, 
                        ROUND(SUM(CTS), 2) AS Polish_CTS,
                        ROUND(SUM(weightage_cogs)) AS COGS,
            ROUND(SUM(Expense_jv)) AS Expensess,
            ROUND(SUM(CASE WHEN ok3.value_status = 'Provisional' THEN ok3.PROVISIONAL_LOCK_VALUE ELSE 0 END), 0) AS Provisional,
            ROUND(SUM(CASE WHEN ok3.value_status = 'Avg Lock' THEN ok3.AVG_LOCK_VALUE ELSE 0 END), 0) AS Avg_Lock
        FROM ok3)   SELECT * FROM ok4;'''
                production_pc = '''select count(*) from production where PROD_MONTH = %s and JV_Status = 'JV' '''
            elif pl_type == 'NonJV':
                print("part-2")
                query = ''' WITH ok AS (
                        SELECT 
                            p.LOTNO, 
                            p.CTS,
                            p.TAG, 
                            p.TOT_PKT_VALUE,
                            l.overall_cost, 
                            m.non_jv_expense AS Expense, 
                            p.AVG_LOCK_VALUE, 
                            n.running_percent,
                            p.PROVISIONAL_LOCK_VALUE,
                            p.value_status,
                            p.PROD_MONTH,
                            SUM(CASE WHEN p.JV_Status = 'Non Jv' THEN p.TOT_PKT_VALUE ELSE 0 END) 
                            OVER (PARTITION BY p.PROD_MONTH) AS total_non_jv_month_value
                        FROM 
                            production p 
                        JOIN nns n ON p.TAG = n.TAG_NAME AND p.LOTNO = n.LOTNO AND p.MAIN_PKTNO = n.MAIN_PKTNO
                        JOIN lot_master_table l ON l.LOTNO = p.LOTNO
                        JOIN manufacturing_expense m ON m.Prod_month = p.PROD_MONTH 
                        WHERE p.PROD_MONTH BETWEEN %s AND %s AND p.JV_Status = 'Non Jv'
                        ),
                        ok2 AS (
                            SELECT 
                                ok.*,
                                (ok.TOT_PKT_VALUE / ok.total_non_jv_month_value) AS PER_for_non_jv,
                                (ok.running_percent * ok.overall_cost / 100.00) AS weightage_cogs
                            FROM ok
                        ), 
                        ok3 AS (
                            SELECT 
                                ok2.*, 
                                (PER_for_non_jv * Expense) AS Expense_non_jv
                            FROM ok2
                        ),
                        ok4 AS (
                            SELECT 
                                COUNT(*) AS Pcs, 
                                ROUND(SUM(CTS), 2) AS Polish_CTS,
                                ROUND(SUM(weightage_cogs)) AS COGS,
                                ROUND(SUM(Expense_non_jv)) AS Expensess,
                                ROUND(SUM(CASE WHEN ok3.value_status = 'Provisional' THEN ok3.PROVISIONAL_LOCK_VALUE ELSE 0 END), 0) AS Provisional,
                                ROUND(SUM(CASE WHEN ok3.value_status = 'Avg Lock' THEN ok3.AVG_LOCK_VALUE ELSE 0 END), 0) AS Avg_Lock
                            FROM ok3 )
                        SELECT * FROM ok4;'''
                production_pc = '''select count(*) from production where PROD_MONTH = %s and JV_Status = 'Non JV' '''
            else : 
                print("part-3")
                query = ''' WITH ok AS (
                        SELECT 
                            p.LOTNO, 
                            p.CTS,
                            p.TAG, 
                            p.TOT_PKT_VALUE,
                            l.overall_cost, 
                            (m.jv_expense + m.non_jv_expense) AS Expense, 
                            p.AVG_LOCK_VALUE, 
                            n.running_percent,
                            p.PROVISIONAL_LOCK_VALUE,
                            p.value_status,
                            p.PROD_MONTH,
                            SUM(p.TOT_PKT_VALUE) OVER (PARTITION BY p.PROD_MONTH) AS total_month_value
                        FROM 
                            production p 
                        JOIN nns n ON p.TAG = n.TAG_NAME AND p.LOTNO = n.LOTNO AND p.MAIN_PKTNO = n.MAIN_PKTNO
                        JOIN lot_master_table l ON l.LOTNO = p.LOTNO
                        JOIN manufacturing_expense m ON m.Prod_month = p.PROD_MONTH 
                        WHERE p.PROD_MONTH BETWEEN %s AND %s
                        ),
                        ok2 AS (
                            SELECT 
                                ok.*,
                                (ok.TOT_PKT_VALUE / ok.total_month_value) AS PER_for_EXP,
                                (ok.running_percent * ok.overall_cost / 100.00) AS weightage_cogs
                            FROM ok
                        ), 
                        ok3 AS (
                            SELECT 
                                ok2.*, 
                                (PER_for_EXP * Expense) AS Expense_all
                            FROM ok2
                        ),
                        ok4 AS (
                            SELECT 
                                COUNT(*) AS Pcs, 
                                ROUND(SUM(CTS), 2) AS Polish_CTS,
                                ROUND(SUM(weightage_cogs)) AS COGS,
                                ROUND(SUM(Expense_all)) AS Expensess,
                                ROUND(SUM(CASE WHEN ok3.value_status = 'Provisional' THEN ok3.PROVISIONAL_LOCK_VALUE ELSE 0 END), 0) AS Provisional,
                                ROUND(SUM(CASE WHEN ok3.value_status = 'Avg Lock' THEN ok3.AVG_LOCK_VALUE ELSE 0 END), 0) AS Avg_Lock
                            FROM ok3 )
                        SELECT * FROM ok4; '''
                production_pc = '''select count(*) from production where PROD_MONTH = %s '''

            result_for_month = []
            month_result = {}

            production = []

            for i in month_pl:
                cursor.execute(production_pc, (i,))
                count_result = cursor.fetchone()  
                production.append(count_result[0])  

            print(production)

            for month, display_month in zip(month_pl, month_pl_display):
                    cursor.execute(query, (month, month))
                    result_for_month = cursor.fetchall()

                    print("result for month",result_for_month)

                    month_result = {
                    "PCS": result_for_month[0][0] if result_for_month[0][0] is not None else 0,
                    "POLISH_CTS": result_for_month[0][1] if result_for_month[0][1] is not None else 0,
                    "COGS": result_for_month[0][2] if result_for_month[0][2] is not None else 0,
                    "EXPENSES": result_for_month[0][3] if result_for_month[0][3] is not None else 0,
                    "PRODUCTION_COST": int(result_for_month[0][2] or 0) + int(result_for_month[0][3] or 0),
                    "PROVISIONAL": result_for_month[0][4] if result_for_month[0][4] is not None else 0,
                    "AVG_LOCK": result_for_month[0][5] if result_for_month[0][5] is not None else 0,
                    "TOTAL_SALES_VALUE": (result_for_month[0][4] or 0) + (result_for_month[0][5] or 0),
                    "NET_PROFIT": ((result_for_month[0][4] or 0) + (result_for_month[0][5] or 0)) -
                                         ((result_for_month[0][2] or 0) + (result_for_month[0][3] or 0)),
                    "NET_PROFIT_MARGIN": round((((result_for_month[0][4] or 0) + (result_for_month[0][5] or 0)) -
                                                 ((result_for_month[0][2] or 0) + (result_for_month[0][3] or 0))) * 100 /
                                                ((result_for_month[0][4] or 0) + (result_for_month[0][5] or 0)),2) if ((result_for_month[0][4] or 0) + (result_for_month[0][5] or 0)) != 0 else 0,
                    "from_month_display": display_month,
                    "from_month_id": month
                    }
                    results.append(month_result)

            print("month_result",month_result)
            print("result",results)
            print("line",line)

# Grand total of pl is calculated and stored in the variables
            cursor.execute(query, (from_month_formatted, to_month_formatted))
            raj = cursor.fetchall()
            if raj:
                    GPCS = raj[0][0] if raj[0][0] is not None else 0
                    GPOLISH_CTS = raj[0][1] if raj[0][1] is not None else 0
                    GCOGS = raj[0][2] if raj[0][2] is not None else 0
                    GEXPENSE = (raj[0][3]) if raj[0][3] is not None else 0
                    GPRODUCTION_COST = (GCOGS or 0) + (GEXPENSE or 0)
                    GPROVISIONAL = raj[0][4] if raj[0][4] is not None else 0
                    GAVG_LOCK = raj[0][5] if raj[0][5] is not None else 0
                    GTOTAL_SALES_VALUE = (GPROVISIONAL or 0) + (GAVG_LOCK or 0)
                    GNET_PROFIT = GTOTAL_SALES_VALUE - GPRODUCTION_COST if GPRODUCTION_COST is not None else 0
                    GNET_PROFIT_MARGIN = round((GNET_PROFIT * 100 / GTOTAL_SALES_VALUE),2) if GTOTAL_SALES_VALUE != 0 else 0
            cursor.close()

        return render_template('P_AND_L_REPORT.html', results=results, line=line, GPCS=GPCS, GPOLISH_CTS=GPOLISH_CTS, GCOGS=GCOGS, GEXPENSE=GEXPENSE,
                         GPRODUCTION_COST=GPRODUCTION_COST, GPROVISIONAL=GPROVISIONAL, GAVG_LOCK=GAVG_LOCK, GTOTAL_SALES_VALUE=GTOTAL_SALES_VALUE, GNET_PROFIT=GNET_PROFIT, GNET_PROFIT_MARGIN=GNET_PROFIT_MARGIN, from_month_display=from_month_display,to_month_display=to_month_display,pl_type=pl_type,message=message, username=username)

raj_result = {} #Initialize empty dictonary 
@app.route('/month', methods=['GET', 'POST'])
def pl_stone_data_show():
    if 'username' in session:
        username = session['username']
        global from_month_formatted, to_month_formatted
        global month_pl_display, month_pl,raj_result
        global production,pl_type

# This line creates a dictionary production_month where the keys are strings representing months (month_pl).
        production_month = {str(month): i for month, i in zip(month_pl, production)}

        print(production_month)

        raj_result = {str(month): [] for month in month_pl}

        print(raj_result)

        pl_data_show = []
        display_from_month = None
        display_to_month = None

        if from_month_formatted and to_month_formatted:
            display_from_month = datetime.strptime(str(from_month_formatted), "%Y%m").strftime("%b-%Y")
            display_to_month = datetime.strptime(str(to_month_formatted), "%Y%m").strftime("%b-%Y")

            cursor = mysql.connection.cursor()
            print(pl_type)
            if(pl_type == 'JV'):
                print("Part-1")
                query = '''
                WITH r AS (
        SELECT 
            p.PROD_MONTH,
            p.IO_DATE,
            p.LOTNO,
            p.DISP_LOTNO,
            n.ARTICLE,
            p.MAIN_PKTNO,
            p.PKTNO,
            p.TAG, 
            round(p.CTS,2) as CTS,
            p.STONE_ID,
            p.STATUS,
            p.SHAPE,
            p.COLOR,
            p.CLARITY,
            p.cut,
            p.FLOURSCENCE,
            round(SUM(CASE WHEN p.JV_Status = 'Jv' THEN p.TOT_PKT_VALUE ELSE 0 END) 
                OVER (PARTITION BY p.PROD_MONTH),2) AS total_jv_month_value,  
            round(p.TOT_PKT_VALUE,2) as TOT_PKT_VALUE,
            round(m.jv_expense,2) AS Expense,
            l.PL_LOT_GRP,
            round(l.overall_cost,2) as overall_cost, 
            round(n.running_percent,2) as running_percent,
            p.value_status,
            round(p.AVG_LOCK_VALUE,2) as AVG_LOCK_VALUE, 
            round(p.PROVISIONAL_LOCK_VALUE,2) as PROVISIONAL_LOCK_VALUE,
            round((p.PROVISIONAL_LOCK_VALUE - p.AVG_LOCK_VALUE),2) AS DIFF 
        FROM 
            production p 
            JOIN nns n 
                ON p.TAG = n.TAG_NAME 
                AND p.LOTNO = n.LOTNO 
                AND p.MAIN_PKTNO = n.MAIN_PKTNO
            JOIN lot_master_table l 
                ON l.LOTNO = p.LOTNO
            JOIN manufacturing_expense m 
                ON m.Prod_month = p.PROD_MONTH 
        WHERE 
            p.PROD_MONTH BETWEEN %s AND %s  
            AND p.JV_Status = 'Jv'
        ),
        k AS (
            SELECT 
                r.*,
                round((TOT_PKT_VALUE / total_jv_month_value),2) AS PER_for_jv,
                round((running_percent * overall_cost / 100.00),2) AS weightage_cogs 
            FROM r
        ),
        a AS (
            SELECT 
                k.*,
                round((PER_for_jv * Expense),2) AS Expense_jv 
            FROM k
        ),
        h AS (
            SELECT 
                a.*,
                round((weightage_cogs + Expense_jv),2) as Production_cost,
                round((TOT_PKT_VALUE - weightage_cogs - Expense_jv),2) AS P_L 
            FROM a
        ),
        j AS (
            SELECT 
                h.*, 
                round(((100 * P_L) / TOT_PKT_VALUE),2) AS P_L_MARGIN 
            FROM h 
        )
        SELECT * FROM j order by PROD_MONTH asc ;
                    '''
            elif(pl_type == 'NonJV'):
                print("Part-2")
                query = '''
                           WITH r AS (
        SELECT 
            p.PROD_MONTH,
            p.IO_DATE,
            p.LOTNO,
            p.DISP_LOTNO,
            n.ARTICLE,
            p.MAIN_PKTNO,
            p.PKTNO,
            p.TAG, 
            round(p.CTS,2) as CTS,
            p.STONE_ID,
            p.STATUS,
            p.SHAPE,
            p.COLOR,
            p.CLARITY,
            p.cut,
            p.FLOURSCENCE,
            round(SUM(CASE WHEN p.JV_Status = 'Non Jv' THEN p.TOT_PKT_VALUE ELSE 0 END) 
                OVER (PARTITION BY p.PROD_MONTH),2) AS total_non_jv_month_value,  
            round(p.TOT_PKT_VALUE,2) as TOT_PKT_VALUE,
            round(m.non_jv_expense,2) AS Expense,
            l.PL_LOT_GRP,
            round(l.overall_cost,2) as overall_cost, 
            round(n.running_percent,2) as running_percent,
            p.value_status,
            round(p.AVG_LOCK_VALUE,2) as AVG_LOCK_VALUE, 
            round(p.PROVISIONAL_LOCK_VALUE,2) as PROVISIONAL_LOCK_VALUE,
            round((p.PROVISIONAL_LOCK_VALUE - p.AVG_LOCK_VALUE),2) AS DIFF
        FROM 
            production p 
            JOIN nns n 
                ON p.TAG = n.TAG_NAME 
                AND p.LOTNO = n.LOTNO 
                AND p.MAIN_PKTNO = n.MAIN_PKTNO
            JOIN lot_master_table l 
                ON l.LOTNO = p.LOTNO
            JOIN manufacturing_expense m 
                ON m.Prod_month = p.PROD_MONTH 
        WHERE 
            p.PROD_MONTH BETWEEN %s AND %s
            AND p.JV_Status = 'Non Jv'
        ),
        k AS (
            SELECT 
                r.*,
                round((TOT_PKT_VALUE / total_non_jv_month_value),2) AS PER_for_non_jv,
                round((running_percent * overall_cost / 100.00),2) AS weightage_cogs 
            FROM r
        ),
        a AS (
            SELECT 
                k.*,
                round((PER_for_non_jv * Expense),2) AS Expense_non_jv 
            FROM k
        ),
        h AS (
            SELECT 
                a.*,
                round((weightage_cogs + Expense_non_jv),2) as Production_cost,
                round((TOT_PKT_VALUE - weightage_cogs - Expense_non_jv),2) AS P_L 
            FROM a
        ),
        j AS (
            SELECT 
                h.*, 
                round(((100 * P_L) / TOT_PKT_VALUE),2) AS P_L_MARGIN 
            FROM h 
        )
        SELECT * FROM j order by PROD_MONTH asc;
                            '''
            else:
                print("Part-3")
                query = '''
                                WITH r AS (
        SELECT 
            p.PROD_MONTH,
            p.IO_DATE,
            p.LOTNO,
            p.DISP_LOTNO,
            n.ARTICLE,
            p.MAIN_PKTNO,
            p.PKTNO,
            p.TAG, 
            round(p.CTS,2) as CTS,
            p.STONE_ID,
            p.STATUS,
            p.SHAPE,
            p.COLOR,
            p.CLARITY,
            p.cut,
            p.FLOURSCENCE,
            round(SUM(CASE WHEN p.JV_Status = 'Non Jv' THEN p.TOT_PKT_VALUE ELSE 0 END) 
                OVER (PARTITION BY p.PROD_MONTH),2) AS total_month_value,  
            round(p.TOT_PKT_VALUE,2) as TOT_PKT_VALUE,
            round((m.non_jv_expense + m.jv_expense),2) AS Expense,
            l.PL_LOT_GRP,
            round(l.overall_cost,2) as overall_cost, 
            round(n.running_percent,2) as running_percent,
            round(p.value_status,2),
            round(p.AVG_LOCK_VALUE,2), 
            round(p.PROVISIONAL_LOCK_VALUE,2),
            round((p.PROVISIONAL_LOCK_VALUE - p.AVG_LOCK_VALUE),2) AS DIFF
        FROM 
            production p 
            JOIN nns n 
                ON p.TAG = n.TAG_NAME 
                AND p.LOTNO = n.LOTNO 
                AND p.MAIN_PKTNO = n.MAIN_PKTNO
            JOIN lot_master_table l 
                ON l.LOTNO = p.LOTNO
            JOIN manufacturing_expense m 
                ON m.Prod_month = p.PROD_MONTH 
        WHERE 
            p.PROD_MONTH BETWEEN %s AND %s
        ),
        k AS (
            SELECT 
                r.*,
                round((TOT_PKT_VALUE / total_month_value),2) AS PER,
                round((running_percent * overall_cost / 100.00),2) AS weightage_cogs 
            FROM r
        ),
        a AS (
            SELECT 
                k.*,
                round((PER * Expense),2) AS Expense_all 
            FROM k
        ),
        h AS (
            SELECT 
                a.*,
                round((weightage_cogs + Expense_all),2) as Production_cost,
                round((TOT_PKT_VALUE - weightage_cogs - Expense_all),2) AS P_L 
            FROM a
        ),
        j AS (
            SELECT 
                h.*, 
                round(((100 * P_L) / TOT_PKT_VALUE),2) AS P_L_MARGIN 
            FROM h 
        )
        SELECT * FROM j order by PROD_MONTH asc;
                                '''
        month_items = zip(month_pl_display, month_pl)
        cursor.execute(query, (from_month_formatted, to_month_formatted))
        pl_data_show = cursor.fetchall()

# This loop iterates over each month, it checks if there is production data available.
        # print(pl_data_show)
        index = 0
        for i in month_pl:
            if str(i) in production_month:
                index_limit = production_month[str(i)]
                for _ in range(index_limit):
                    raj_result[str(i)].append(tuple(str(item) for item in pl_data_show[index]))
                    index += 1
                    # print(index)

        return render_template('month.html', month_items=month_items, display_from_month=display_from_month, display_to_month=display_to_month, username=username)

@app.route('/month/<month_value>', methods=['GET', 'POST'])
def show_month_data(month_value):
    if 'username' in session:
        username = session['username']
        global raj_result
        pl_stone_data_show()
        print(month_value)
        display_month_stonewise = format_date(month_value)
        return render_template('data.html', month_data=raj_result[month_value],display_month_stonewise=display_month_stonewise, username=username)

# This function takes an input date in the format "YYYYMM" and converts it into a formatted string representing the month and year
def format_date(input_date):
    year = input_date[:4]
    month = input_date[4:]
    month_abbr = {
        "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
        "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
        "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
    }

    month_name = month_abbr.get(month, "Invalid month")

    return f"{month_name}-{year}"

@app.route('/pricechange', methods=['GET', 'POST'])
def price_change():
    select_lotnos = None
    if request.method == 'POST':
        select_lotnos = request.form.getlist('select_lotno')
        if select_lotnos:
            cursor = mysql.connection.cursor()
            formatted_data = []
            grand_total_bid_pred = 0
            grand_total_history = 0
            grand_total_diff = 0
            grand_total_diff_percent = 0
            diff_percent_count = 0

            for lotno in select_lotnos:
                query = '''WITH history_cte AS (
                                SELECT Lotno, SUM(Amount) AS history_total
                                FROM history_price
                                WHERE Lotno = %s
                                GROUP BY Lotno
                            ),
                            bid_pred_cte AS (
                                SELECT Lotno, SUM(Amount) AS bid_pred_total
                                FROM bid_pred
                                WHERE Lotno = %s
                                GROUP BY Lotno
                            )
                            SELECT
                                h.Lotno,
                                h.history_total,
                                b.bid_pred_total,
                                h.history_total - b.bid_pred_total AS diff,
                                ((h.history_total - b.bid_pred_total) * 100.00 / NULLIF(b.bid_pred_total, 0)) AS diff_percent
                            FROM
                                history_cte h
                            JOIN
                                bid_pred_cte b
                            ON h.Lotno = b.Lotno;'''
                cursor.execute(query, (lotno, lotno))
                data = cursor.fetchone()
                if data:
                    bid_pred_total = data[1] if data[1] is not None else 0
                    history_total = data[2] if data[2] is not None else 0
                    diff = data[3] if data[3] is not None else 0
                    diff_percent = data[4] if data[4] is not None else 0

                    grand_total_bid_pred += bid_pred_total
                    grand_total_history += history_total
                    grand_total_diff += diff
                    if diff_percent is not None:
                        grand_total_diff_percent += diff_percent
                        diff_percent_count += 1

                    formatted_row = {
                        'Lotno': data[0],
                        'bid_pred_total': bid_pred_total,
                        'history_total': round(history_total, 3),
                        'diff': Decimal(diff).quantize(Decimal('.01')),
                        'diff_percent': '{:.2f}%'.format(diff_percent) if diff_percent is not None else None
                    }
                    formatted_data.append(formatted_row)
            cursor.close()

             # Calculate average diff_percent
            if diff_percent_count > 0:
                grand_total_diff_percent /= diff_percent_count

            grand_total = {
                'bid_pred_total': grand_total_bid_pred,
                'history_total': round(grand_total_history, 4),
                'diff': Decimal(grand_total_diff).quantize(Decimal('.01')),
                'diff_percent': '{:.2f}%'.format(grand_total_diff_percent) if grand_total_diff_percent is not None else None
            }

            return render_template('pricechange.html', data=formatted_data, grand_total=grand_total, select_options=price_lotno(), select_lotnos=select_lotnos)

    return render_template('pricechange.html', data=[], grand_total=None, select_options=price_lotno(), select_lotnos=select_lotnos)

def price_lotno():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT DISTINCT Lotno FROM history_price ORDER BY Lotno")
    lots = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return lots

# global dictionary to store production data fetched from the database.
pda = {}
# total number of pages 
tp = 0
@app.route('/production_audit', methods=['GET', 'POST'])
def audit_production():
    pro_data_audit = None
    from_month_audit = None
    global pda
    global tp
    if 'username' not in session:
        return redirect(url_for('home'))

    username = session['username']
    
    if request.method == 'POST':
         # Retrieving the selected month for production audit
        from_month_audit = request.form.get('fromMonth')
        
        if from_month_audit:
            # Converting the selected month into YYYYMM format
            production_audit = datetime.strptime(from_month_audit, "%Y-%m")
            audit_production_q = int(production_audit.strftime("%Y%m"))

            cursor = mysql.connection.cursor()
            
             # Counting total rows
            query = 'SELECT COUNT(*) FROM production WHERE PROD_MONTH = %s'
            cursor.execute(query, (audit_production_q,))
            total_rows = cursor.fetchone()[0]
            tp = (total_rows + 749) // 750 # Calculate total pages needed

             # Fetching data
            query = '''SELECT * FROM production WHERE PROD_MONTH = %s ORDER BY PROD_MONTH, LOTNO ASC'''
            cursor.execute(query, (audit_production_q,))

            pro_data_audit = cursor.fetchall()
            
            # Organizing data by pages
            pda = {str(i):[] for i in range(1, tp + 1)}

            index = 1
            limit = 750
            for i, row in enumerate(pro_data_audit):
                if i < limit:
                    pda[str(index)].append(row)
                else:
                    index += 1
                    limit += 750
                    pda[str(index)].append(row)             
            cursor.close()
    
    return render_template('production_audit.html', username=username, from_month_audit=from_month_audit, pro_data_audit=pda, tp=tp)

cps = 0
@app.route('/production_data/<int:page>', methods=['GET'])
def display_prd_data(page):
    global pda
    global tp
    global cps
    cps = page
    if 'username' not in session:
        return redirect(url_for('home'))
    
    username = session['username']
    
    # Ensure the page number is within the valid range
    if page < 1:
        page = 1
    elif page > tp:
        page = tp
    
    # Retrieve the data for the current page
    pro_data_page = pda.get(str(page), [])

    return render_template('production_data.html',
                         pro_data_audit=pro_data_page,
                         username=username,
                         current_page=page,
                         total_pages=tp)

@app.route('/post_alert_action', methods=['GET'])
def post_alert_action():
    try:
        global cps        
        return redirect(url_for('display_prd_data', page=cps))
    except Exception as e:
        return jsonify({'error': f'Error occurred during post-alert action: {str(e)}'}), 500

@app.route('/update_production', methods=['POST'])
def up_value_production():

    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        try:
            data = request.json
            lotno = data.get('lotno')
            pktno = data.get('pktno')
            tag = data.get('tag')
            Provisional = data.get('edit1')
            Avg_Lock = data.get('edit2')
            user_id = session.get('username')
            current_time = datetime.now()

            print(lotno,pktno,tag,Provisional,Avg_Lock,user_id,current_time)
            cursor.execute('''UPDATE production
                             SET UPD_PROVISIONAL = %s, UPD_AVG_LOCK = %s, UPD_USER = %s, UPDATE_DATE = %s
                             WHERE LOTNO = %s AND MAIN_PKTNO = %s AND TAG = %s''',
                         (Provisional, Avg_Lock, user_id, current_time, lotno, pktno, tag))
            mysql.connection.commit()
            cursor.close()
            
            return jsonify({'message': 'Values updated successfully'}), 200
        except Exception as e:
            return jsonify({'error': f'Error occurred while updating values: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Method not allowed'}), 405

@app.route('/Articlewise', methods=['GET','POST'])
def article_pl():
    data_dtc = []
    data_non_dtc = []
    data_single = []
    total_row_dtc = {
        'Pcs': 0,
        'Polish_CTS': 0,
        'COGS': 0,
        'Expensess': 0,
        'Production_cost': 0,
        'Total_sales_values': 0,
        'Profit': 0,
        'Profit_Percent': '0%',
        'ABS_DIFF_VALUE': 0,
        'ABS_DIFF_WTG%': '0%'
    }
    total_row_non_dtc = {
        'Pcs': 0,
        'Polish_CTS': 0,
        'COGS': 0,
        'Expensess': 0,
        'Production_cost': 0,
        'Total_sales_values': 0,
        'Profit': 0,
        'Profit_Percent': '0%',
        'ABS_DIFF_VALUE': 0,
        'ABS_DIFF_WTG%': '0%'
    }
    total_row_single = {
        'Pcs': 0,
        'Polish_CTS': 0,
        'COGS': 0,
        'Expensess': 0,
        'Production_cost': 0,
        'Total_sales_values': 0,
        'Profit': 0,
        'Profit_Percent': '0%',
        'ABS_DIFF_VALUE': 0,
        'ABS_DIFF_WTG%': '0%'
    }

    fMonth = None  # Initialize fMonth with default value
    toMonth = None  # Initialize toMonth with default value
    fmonth_name = ""
    tmonth_name = ""
    grand_total = {
            'Pcs': 0,
            'Polish_CTS': 0,
            'COGS': 0,
            'Expensess': 0,
            'Production_cost': 0,
            'Total_sales_values': 0,
            'Profit': 0,
            'Profit_Percent': '0%',
            'ABS_DIFF_VALUE': 0,
            'ABS_DIFF_WTG%': '0%'
        }
    if request.method == 'POST':
        fMonth = request.form.get('fMonth')
        toMonth = request.form.get('toMonth')

        if fMonth:
            fMonth_year, fMonth_month = map(int, fMonth.split('-'))
            fmonth_name = f"{calendar.month_name[fMonth_month]} {fMonth_year}"

        if toMonth:
            toMonth_year, toMonth_month = map(int, toMonth.split('-'))
            tmonth_name = f"{calendar.month_name[toMonth_month]} {toMonth_year}"

        # Convert the months to the format used in the SQL query
        from_month_int = int(fMonth.replace('-', '')) if fMonth else None
        to_month_int = int(toMonth.replace('-', '')) if toMonth else None

        # Execute the queries
        if from_month_int and to_month_int:
            query_dtc = f"""
            WITH ok AS
            (
            select
            p.LOTNO,
            p.MAIN_PKTNO,
            p.PKTNO,
            p.TAG,
            p.TOT_PKT_VALUE,
            p.CTS,
            l.overall_cost,
            m.non_jv_expense as Expense,
            p.AVG_LOCK_VALUE,
            n.running_percent,
            p.PROVISIONAL_LOCK_VALUE,
            p.value_status,
            p.PROD_MONTH,
            n.amount,
            SUM(CASE WHEN p.JV_Status != 'Jv' THEN p.TOT_PKT_VALUE ELSE 0 END)
            OVER (PARTITION BY p.PROD_MONTH) AS total_non_jv_month_value,
            l.rough_type,
            l.buying_type
            from
            production p
            join nns n
            on
            p.TAG = n.TAG_NAME and
            p.LOTNO = n.LOTNO and
            p.MAIN_PKTNO = n.MAIN_PKTNO
            join lot_master_table l
            on l.LOTNO = p.LOTNO
            join manufacturing_expense m
            on m.Prod_month = p.PROD_MONTH
            where p.PROD_MONTH between {from_month_int} and {to_month_int} and
                 p.JV_Status != 'Jv'
            ),
            ok2 as (
            SELECT
                ok.*,
                ((ok.TOT_PKT_VALUE) / ok.total_non_jv_month_value) AS PER_for_non_jv,
                (ok.running_percent * ok.overall_cost / 100.00) AS weightage_cogs
            FROM
                ok
            ),
            ok3 as (
            SELECT
                ok2.*, (PER_for_non_jv * Expense) AS Expense_non_jv
            FROM
                ok2
            ),
            ok4 as (
            SELECT
                rough_type AS DTC,
                COUNT(*) AS Pcs,
                ROUND(SUM(CTS), 2) AS Polish_CTS,
                ROUND(SUM(weightage_cogs)) AS COGS,
                ROUND(SUM(Expense_non_jv)) AS Expensess,
                ROUND(SUM(CASE
                            WHEN ok3.VALUE_STATUS = 'Provisional' THEN ok3.PROVISIONAL_LOCK_VALUE
                            ELSE 0
                        END),
                        0) AS Provisional,
                ROUND(SUM(CASE
                            WHEN ok3.VALUE_STATUS = 'Avg Lock' THEN ok3.AVG_LOCK_VALUE
                            ELSE 0
                        END),
                        0) AS Avg_Lock
            FROM
                ok3
            WHERE
                buying_type = 'dtc'
            GROUP BY 1),
            ok5 as (
            SELECT
                ok4.*,
                COGS + Expensess AS Production_cost,
                ROUND(Provisional + Avg_Lock, 2) AS Total_sales_values
            FROM
                ok4),
            ok6 as(
            SELECT
                ok5.*, Total_sales_values - Production_cost AS Profit
            FROM
                ok5),
            ok7 as (
            SELECT
                ok6.*,
                ROUND((100.00 * Profit / Total_sales_values),
                        2) AS Profit_Percent
            FROM
                ok6)
            SELECT
                ok7.*,
                ABS(Total_sales_values - Production_cost) AS ABS_DIFF_VALUE
            FROM
                ok7;
            """
            query_non_dtc = f"""
            WITH ok AS
            (
            select
            p.LOTNO,
            p.MAIN_PKTNO,
            p.PKTNO,
            p.TAG,
            p.TOT_PKT_VALUE,
            p.CTS,
            l.overall_cost,
            m.non_jv_expense as Expense,
            p.AVG_LOCK_VALUE,
            n.running_percent,
            p.PROVISIONAL_LOCK_VALUE,
            p.value_status,
            p.PROD_MONTH,
            n.amount,
            SUM(CASE WHEN p.JV_Status != 'Jv' THEN p.TOT_PKT_VALUE ELSE 0 END)
            OVER (PARTITION BY p.PROD_MONTH) AS total_non_jv_month_value,
            l.rough_type,
            l.buying_type
            from
            production p
            join nns n
            on
            p.TAG = n.TAG_NAME and
            p.LOTNO = n.LOTNO and
            p.MAIN_PKTNO = n.MAIN_PKTNO
            join lot_master_table l
            on l.LOTNO = p.LOTNO
            join manufacturing_expense m
            on m.Prod_month = p.PROD_MONTH
            where p.PROD_MONTH between {from_month_int} and {to_month_int} and
                 p.JV_Status != 'Jv'
            ),
            ok2 as (
            SELECT
                ok.*,
                ((ok.TOT_PKT_VALUE) / ok.total_non_jv_month_value) AS PER_for_non_jv,
                (ok.running_percent * ok.overall_cost / 100.00) AS weightage_cogs
            FROM
                ok
            ),
            ok3 as (
            SELECT
                ok2.*, (PER_for_non_jv * Expense) AS Expense_non_jv
            FROM
                ok2
            ),
            ok4 as (
            SELECT
                rough_type AS NON_DTC,
                COUNT(*) AS Pcs,
                ROUND(SUM(CTS), 2) AS Polish_CTS,
                ROUND(SUM(weightage_cogs)) AS COGS,
                ROUND(SUM(Expense_non_jv)) AS Expensess,
                ROUND(SUM(CASE
                            WHEN ok3.VALUE_STATUS = 'Provisional' THEN ok3.PROVISIONAL_LOCK_VALUE
                            ELSE 0
                        END),
                        0) AS Provisional,
                ROUND(SUM(CASE
                            WHEN ok3.VALUE_STATUS = 'Avg Lock' THEN ok3.AVG_LOCK_VALUE
                            ELSE 0
                        END),
                        0) AS Avg_Lock
            FROM
                ok3
            WHERE
                buying_type = 'non dtc'
            GROUP BY 1),
            ok5 as (
            SELECT
                ok4.*,
                COGS + Expensess AS Production_cost,
                ROUND(Provisional + Avg_Lock, 2) AS Total_sales_values
            FROM
                ok4),
            ok6 as(
            SELECT
                ok5.*, Total_sales_values - Production_cost AS Profit
            FROM
                ok5),
            ok7 as (
            SELECT
                ok6.*,
                ROUND((100.00 * Profit / Total_sales_values),
                        2) AS Profit_Percent
            FROM
                ok6)
            SELECT
                ok7.*,
                ABS(Total_sales_values - Production_cost) AS ABS_DIFF_VALUE
            FROM
                ok7;
            """
            query_single = f"""
            WITH ok AS
            (
            select
            p.LOTNO,
            p.MAIN_PKTNO,
            p.PKTNO,
            p.TAG,
            p.TOT_PKT_VALUE,
            p.CTS,
            l.overall_cost,
            m.non_jv_expense as Expense,
            p.AVG_LOCK_VALUE,
            n.running_percent,
            p.PROVISIONAL_LOCK_VALUE,
            p.value_status,
            p.PROD_MONTH,
            n.amount,
            SUM(CASE WHEN p.JV_Status != 'Jv' THEN p.TOT_PKT_VALUE ELSE 0 END)
            OVER (PARTITION BY p.PROD_MONTH) AS total_non_jv_month_value,
            l.rough_type,
            l.buying_type
            from
            production p
            join nns n
            on
            p.TAG = n.TAG_NAME and
            p.LOTNO = n.LOTNO and
            p.MAIN_PKTNO = n.MAIN_PKTNO
            join lot_master_table l
            on l.LOTNO = p.LOTNO
            join manufacturing_expense m
            on m.Prod_month = p.PROD_MONTH
            where p.PROD_MONTH between {from_month_int} and {to_month_int} and
                 p.JV_Status != 'Jv'
            ),
            ok2 as (
            SELECT
                ok.*,
                ((ok.TOT_PKT_VALUE) / ok.total_non_jv_month_value) AS PER_for_non_jv,
                (ok.running_percent * ok.overall_cost / 100.00) AS weightage_cogs
            FROM
                ok
            ),
            ok3 as (
            SELECT
                ok2.*, (PER_for_non_jv * Expense) AS Expense_non_jv
            FROM
                ok2
            ),
            ok4 as (
            SELECT
                rough_type AS Single,
                COUNT(*) AS Pcs,
                ROUND(SUM(CTS), 2) AS Polish_CTS,
                ROUND(SUM(weightage_cogs)) AS COGS,
                ROUND(SUM(Expense_non_jv)) AS Expensess,
                ROUND(SUM(CASE
                            WHEN ok3.VALUE_STATUS = 'Provisional'
                            THEN ok3.PROVISIONAL_LOCK_VALUE
                            ELSE 0
                        END),
                        0) AS Provisional,
                ROUND(SUM(CASE
                            WHEN ok3.VALUE_STATUS = 'Avg Lock' THEN ok3.AVG_LOCK_VALUE
                            ELSE 0
                        END),
                        0) AS Avg_Lock
            FROM
                ok3
            WHERE
                buying_type = 'single'
            GROUP BY 1),
            ok5 as (
            SELECT
                ok4.*,
                COGS + Expensess AS Production_cost,
                ROUND(Provisional + Avg_Lock, 2) AS Total_sales_values
            FROM
                ok4 ),
            ok6 as(
            SELECT
                ok5.*, Total_sales_values - Production_cost AS Profit
            FROM
                ok5),
            ok7 as (
            SELECT
                ok6.*,
                ROUND((100.00 * Profit / Total_sales_values),2) AS Profit_Percent
            FROM
                ok6)
            SELECT
                ok7.*,
                ABS(Total_sales_values - Production_cost) AS ABS_DIFF_VALUE
            FROM
                ok7;
            """   
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Execute the DTC query
            cursor.execute(query_dtc)
            data_dtc = cursor.fetchall()

            # Execute the NON DTC query
            cursor.execute(query_non_dtc)
            data_non_dtc = cursor.fetchall()

            cursor.execute(query_single)
            data_single = cursor.fetchall()

            # print("DTC Data:", data_dtc)
            # print("Non-DTC Data:", data_non_dtc)
            # print("Singles data:", data_single)
            # print(grand_total)

            # Calculate totals for DTC
            if data_dtc:
                for row in data_dtc:
                    row['Pcs'] = int(round(float(row['Pcs'])))
                    row['Polish_CTS'] = float(row['Polish_CTS'])  # Keep Polish_CTS as float
                    row['COGS'] = int(round(float(row['COGS'])))
                    row['Expensess'] = int(round(float(row['Expensess'])))  # Keep Expensess as float
                    row['Production_cost'] = int(round(float(row['Production_cost'])))
                    row['Total_sales_values'] = int(round(float(row['Total_sales_values'])))
                    row['Profit'] = int(round(float(row['Profit'])))
                    row['Profit_Percent'] = f"{row['Profit_Percent']}%"
                    row['ABS_DIFF_VALUE'] = int(round(float(row['ABS_DIFF_VALUE'])))
                   
                for row in data_dtc:
                    total_row_dtc['Pcs'] += row['Pcs']
                    total_row_dtc['Polish_CTS'] += row['Polish_CTS']
                    total_row_dtc['COGS'] += row['COGS']
                    total_row_dtc['Expensess'] += row['Expensess']
                    total_row_dtc['Production_cost'] += row['Production_cost']
                    total_row_dtc['Total_sales_values'] += row['Total_sales_values']
                    total_row_dtc['Profit'] += row['Profit']
                    total_row_dtc['Profit_Percent'] = f"{(100.0 * total_row_dtc['Profit'] / total_row_dtc['Total_sales_values']):.2f}%"
                    total_row_dtc['ABS_DIFF_VALUE'] += row['ABS_DIFF_VALUE']
                    
            # Calculate totals for NON DTC
            if data_non_dtc:
                for row in data_non_dtc:
                    row['Pcs'] = int(round(float(row['Pcs'])))
                    row['Polish_CTS'] = float(row['Polish_CTS'])  # Keep Polish_CTS as float
                    row['COGS'] = int(round(float(row['COGS'])))
                    row['Expensess'] = int(round(float(row['Expensess'])))  # Keep Expensess as float
                    row['Production_cost'] = int(round(float(row['Production_cost'])))
                    row['Total_sales_values'] = int(round(float(row['Total_sales_values'])))
                    row['Profit'] = int(round(float(row['Profit'])))
                    row['Profit_Percent'] = f"{row['Profit_Percent']}%"
                    row['ABS_DIFF_VALUE'] = int(round(float(row['ABS_DIFF_VALUE'])))
                    

                for row in data_non_dtc:
                    total_row_non_dtc['Pcs'] += row['Pcs']
                    total_row_non_dtc['Polish_CTS'] += row['Polish_CTS']
                    total_row_non_dtc['COGS'] += row['COGS']
                    total_row_non_dtc['Expensess'] += row['Expensess']
                    total_row_non_dtc['Production_cost'] += row['Production_cost']
                    total_row_non_dtc['Total_sales_values'] += row['Total_sales_values']
                    total_row_non_dtc['Profit'] += row['Profit']
                    total_row_non_dtc['Profit_Percent'] = f"{(100.0 * total_row_non_dtc['Profit'] / total_row_non_dtc['Total_sales_values']):.2f}%"
                    total_row_non_dtc['ABS_DIFF_VALUE'] += row['ABS_DIFF_VALUE']

            if data_single:
                for row in data_single:
                    row['Pcs'] = int(round(float(row['Pcs'])))
                    row['Polish_CTS'] = float(row['Polish_CTS'])  # Keep Polish_CTS as float
                    row['COGS'] = int(round(float(row['COGS'])))
                    row['Expensess'] = int(round(float(row['Expensess'])))  # Keep Expensess as float
                    row['Production_cost'] = int(round(float(row['Production_cost'])))
                    row['Total_sales_values'] = int(round(float(row['Total_sales_values'])))
                    row['Profit'] = int(round(float(row['Profit'])))
                    row['Profit_Percent'] = f"{row['Profit_Percent']}%"
                    row['ABS_DIFF_VALUE'] = int(round(float(row['ABS_DIFF_VALUE'])))
                
                for row in data_single:
                    total_row_single['Pcs'] += row['Pcs']
                    total_row_single['Polish_CTS'] += row['Polish_CTS']
                    total_row_single['COGS'] += row['COGS']
                    total_row_single['Expensess'] += row['Expensess']
                    total_row_single['Production_cost'] += row['Production_cost']
                    total_row_single['Total_sales_values'] += row['Total_sales_values']
                    total_row_single['Profit'] += row['Profit']
                    total_row_single['Profit_Percent'] = f"{(100.0 * total_row_single['Profit'] / total_row_single['Total_sales_values']):.2f}%"
                    total_row_single['ABS_DIFF_VALUE'] += row['ABS_DIFF_VALUE']

                 # Calculate grand_total
            if grand_total:        
                    grand_total['Pcs'] = total_row_dtc['Pcs'] + total_row_non_dtc['Pcs'] + total_row_single['Pcs']
                    grand_total['Polish_CTS'] = total_row_dtc['Polish_CTS'] + total_row_non_dtc['Polish_CTS'] + total_row_single['Polish_CTS']
                    grand_total['COGS'] = total_row_dtc['COGS'] + total_row_non_dtc['COGS'] + total_row_single['COGS']
                    grand_total['Expensess'] = total_row_dtc['Expensess'] + total_row_non_dtc['Expensess'] + total_row_single['Expensess']
                    grand_total['Production_cost'] = total_row_dtc['Production_cost'] + total_row_non_dtc['Production_cost'] + total_row_single['Production_cost']
                    grand_total['Total_sales_values'] = total_row_dtc['Total_sales_values'] + total_row_non_dtc['Total_sales_values'] + total_row_single['Total_sales_values']
                    grand_total['Profit'] = total_row_dtc['Profit'] + total_row_non_dtc['Profit'] + total_row_single['Profit']
                    grand_total['Profit_Percent'] = f"{(100.0 * grand_total['Profit'] / grand_total['Total_sales_values']):.2f}%"
                    grand_total['ABS_DIFF_VALUE'] = total_row_dtc['ABS_DIFF_VALUE'] + total_row_non_dtc['ABS_DIFF_VALUE'] + total_row_single['ABS_DIFF_VALUE']

            # Ensure data_dtc is a list before sorting
                    data_dtc = list(data_dtc)
                    data_dtc.sort(key=lambda x: x['ABS_DIFF_VALUE'], reverse=True)

                    # Ensure data_non_dtc is a list before sorting
                    data_non_dtc = list(data_non_dtc)
                    data_non_dtc.sort(key=lambda x: x['ABS_DIFF_VALUE'], reverse=True)

                    # Ensure data_single is a list before sorting
                    data_single = list(data_single)
                    data_single.sort(key=lambda x: x['ABS_DIFF_VALUE'], reverse=True)

            cursor.close()

    return render_template('Articlewise.html', data_dtc=data_dtc, data_non_dtc=data_non_dtc, data_single=data_single, total_row_dtc=total_row_dtc, total_row_non_dtc=total_row_non_dtc, total_row_single=total_row_single,  grand_total=grand_total, fmonth_name=fmonth_name, tmonth_name=tmonth_name)

@app.route('/Export_pl', methods=['GET', 'POST'])
def export_pl():
    data = []  # Initialize empty list to hold query results
    unique_months_count = 0
    fmonth_name = ""
    tmonth_name = ""
    pl_type = ""
    grand_total = {
        'Pcs': 0,
        'Polish_CTS': Decimal('0'),
        'COGS': Decimal('0'),
        'Expense': Decimal('0'),
        'Production_cost': Decimal('0'),
        'Provisional': Decimal('0'),
        'Avg_Lock': Decimal('0'),
        'Total_sales_values': Decimal('0'),
        'Profit': Decimal('0'),
        'Profit_Percent': 0.00
    }

    if request.method == 'POST':
        fromMonth = request.form.get('fromMonth')
        toMonth = request.form.get('toMonth')
        pl_type = request.form.get('p_l_type')

        if fromMonth and toMonth and pl_type:
            # Extract year and month from the selected months
            from_year, from_month = map(int, fromMonth.split('-'))
            to_year, to_month = map(int, toMonth.split('-'))

            # Convert month numbers to month names
            fmonth_name = datetime(from_year, from_month, 1).strftime('%B %Y')
            tmonth_name = datetime(to_year, to_month, 1).strftime('%B %Y')

            # Construct the SQL query with formatted month and year
        if pl_type == 'NON-JV':
            query = f"""
           WITH ok AS (
                SELECT
                    p.LOTNO,
                    p.MAIN_PKTNO,
                    p.PKTNO,
                    p.TAG,
                    p.TOT_PKT_VALUE,
                    p.CTS,
                    l.overall_cost,
                    m.non_jv_expense AS Expense,
                    p.AVG_LOCK_VALUE,
                    n.running_percent,
                    p.PROVISIONAL_LOCK_VALUE,
                    p.value_status,
                    p.PROD_MONTH,
                    n.amount,
                    p.io_date,
                    p.JV_Status,
                    SUM(CASE WHEN p.JV_Status != 'Jv' THEN p.TOT_PKT_VALUE ELSE 0 END) OVER (PARTITION BY p.prod_month) AS total_non_jv_month_value
                FROM
                    production p
                    JOIN nns n ON p.TAG = n.TAG_NAME AND p.LOTNO = n.LOTNO AND p.MAIN_PKTNO = n.MAIN_PKTNO
                    JOIN lot_master_table l ON l.LOTNO = p.LOTNO
                    JOIN manufacturing_expense m ON m.Prod_month = p.PROD_MONTH
            ),
            ok2 AS (
                SELECT
                    ok.*,
                    ((ok.TOT_PKT_VALUE) / ok.total_non_jv_month_value) AS PER_for_non_jv,
                    (ok.running_percent * ok.overall_cost / 100.00) AS weightage_cogs
                FROM
                    ok
            ),
            ok3 AS (
                SELECT
                    ok2.*,
                    (PER_for_non_jv * Expense) AS Expense_non_jv
                FROM
                    ok2
                WHERE
                    CONCAT(EXTRACT(year FROM io_date), LPAD(EXTRACT(month FROM io_date), 2, '0')) BETWEEN {from_year}{from_month:02d} AND {to_year}{to_month:02d}
                    AND JV_Status != 'Jv'
            ),
            ok4 AS (
                SELECT
                    DATE_FORMAT(io_date, '%b %Y') AS ProdMonth,
                    COUNT(*) AS Pcs,
                    ROUND(SUM(CTS), 2) AS Polish_CTS,
                    ROUND(SUM(weightage_cogs)) AS COGS,
                    ROUND(SUM(Expense_non_jv)) AS Expensess,
                    ROUND(SUM(CASE WHEN ok3.VALUE_STATUS = 'Provisional' THEN ok3.PROVISIONAL_LOCK_VALUE ELSE 0 END), 0) AS Provisional,
                    ROUND(SUM(CASE WHEN ok3.VALUE_STATUS = 'Avg Lock' THEN ok3.AVG_LOCK_VALUE ELSE 0 END), 0) AS Avg_Lock
                FROM
                    ok3
                GROUP BY
                    ProdMonth
            ),
            ok5 AS (
                SELECT
                    ok4.*,
                    COGS + Expensess AS Production_cost,
                    ROUND(Provisional + Avg_Lock, 2) AS Total_sales_values
                FROM
                    ok4
            ),
            ok6 AS (
                SELECT
                    ok5.*,
                    Total_sales_values - Production_cost AS Profit
                FROM
                    ok5
            )
            SELECT
               ok6.*,
                ROUND((100.00 * Profit / Total_sales_values), 2) AS Profit_Percent
            FROM
                ok6;
            """
        elif pl_type == 'JV':
             query = f"""
            WITH ok AS (
                SELECT
                    p.LOTNO,
                    p.MAIN_PKTNO,
                    p.PKTNO,
                    p.TAG,
                    p.TOT_PKT_VALUE,
                    p.CTS,
                    l.overall_cost,
                    m.jv_expense AS Expense,
                    p.AVG_LOCK_VALUE,
                    n.running_percent,
                    p.PROVISIONAL_LOCK_VALUE,
                    p.value_status,
                    p.PROD_MONTH,
                    n.amount,
                    p.io_date,
                    p.JV_Status,
                    SUM(CASE WHEN p.JV_Status = 'Jv' THEN p.TOT_PKT_VALUE ELSE 0 END) OVER (PARTITION BY p.prod_month) AS total_jv_month_value
                FROM
                    production p
                    JOIN nns n ON p.TAG = n.TAG_NAME AND p.LOTNO = n.LOTNO AND p.MAIN_PKTNO = n.MAIN_PKTNO
                    JOIN lot_master_table l ON l.LOTNO = p.LOTNO
                    JOIN manufacturing_expense m ON m.Prod_month = p.PROD_MONTH
            ),
            ok2 AS (
                SELECT
                    ok.*,
                    ((ok.TOT_PKT_VALUE) / ok.total_jv_month_value) AS PER_for_jv,
                    (ok.running_percent * ok.overall_cost / 100.00) AS weightage_cogs
                FROM
                    ok
            ),
            ok3 AS (
                SELECT
                    ok2.*,
                    (PER_for_jv * Expense) AS Expense_jv
                FROM
                    ok2
                WHERE
                    CONCAT(EXTRACT(year FROM io_date), LPAD(EXTRACT(month FROM io_date), 2, '0')) BETWEEN {from_year}{from_month:02d} AND {to_year}{to_month:02d}
                    AND JV_Status = 'Jv'
            ),
            ok4 AS (
                SELECT
                    DATE_FORMAT(io_date, '%b %Y') AS ProdMonth,
                    COUNT(*) AS Pcs,
                    ROUND(SUM(CTS), 2) AS Polish_CTS,
                    ROUND(SUM(weightage_cogs)) AS COGS,
                    ROUND(SUM(Expense_jv)) AS Expensess,
                    ROUND(SUM(CASE WHEN ok3.VALUE_STATUS = 'Provisional' THEN ok3.PROVISIONAL_LOCK_VALUE ELSE 0 END), 0) AS Provisional,
                    ROUND(SUM(CASE WHEN ok3.VALUE_STATUS = 'Avg Lock' THEN ok3.AVG_LOCK_VALUE ELSE 0 END), 0) AS Avg_Lock
                FROM
                    ok3
                GROUP BY
                    ProdMonth
            ),
            ok5 AS (
                SELECT
                    ok4.*,
                    COGS + Expensess AS Production_cost,
                    ROUND(Provisional + Avg_Lock, 2) AS Total_sales_values
                FROM
                    ok4
            ),
            ok6 AS (
                SELECT
                    ok5.*,
                    Total_sales_values - Production_cost AS Profit
                FROM
                    ok5
            )
            SELECT
               ok6.*,
                ROUND((100.00 * Profit / Total_sales_values), 2) AS Profit_Percent
            FROM
                ok6;
            """
        else:
             query = f"""
           WITH ok AS (
                SELECT
                    p.LOTNO,
                    p.MAIN_PKTNO,
                    p.PKTNO,
                    p.TAG,
                    p.TOT_PKT_VALUE,
                    p.CTS,
                    l.overall_cost,
                   (m.jv_expense + m.non_jv_expense) AS Expense, 
                    p.AVG_LOCK_VALUE,
                    n.running_percent,
                    p.PROVISIONAL_LOCK_VALUE,
                    p.value_status,
                    p.PROD_MONTH,
                    n.amount,
                    p.io_date,
					SUM(p.TOT_PKT_VALUE) OVER (PARTITION BY p.PROD_MONTH) AS total_month_value
                FROM
                    production p
                    JOIN nns n ON p.TAG = n.TAG_NAME AND p.LOTNO = n.LOTNO AND p.MAIN_PKTNO = n.MAIN_PKTNO
                    JOIN lot_master_table l ON l.LOTNO = p.LOTNO
                    JOIN manufacturing_expense m ON m.Prod_month = p.PROD_MONTH
            ),
            ok2 AS (
                SELECT
                    ok.*,
                    ((ok.TOT_PKT_VALUE) / ok.total_month_value) AS PER_for_Exp,
                    (ok.running_percent * ok.overall_cost / 100.00) AS weightage_cogs
                FROM
                    ok
            ),
           ok3 AS (
            SELECT
                ok2.*,
                (PER_for_Exp * Expense) AS Expense_all
            FROM
                ok2
            WHERE
                 CONCAT(EXTRACT(year FROM io_date), LPAD(EXTRACT(month FROM io_date), 2, '0')) BETWEEN {from_year}{from_month:02d} AND {to_year}{to_month:02d}
            ),
            ok4 AS (
            SELECT
                DATE_FORMAT(io_date, '%b %Y') AS ProdMonth,
                COUNT(*) AS Pcs,
                ROUND(SUM(CTS), 2) AS Polish_CTS,
                ROUND(SUM(weightage_cogs)) AS COGS,
                ROUND(SUM(Expense_all)) AS Expensess,
                ROUND(SUM(CASE WHEN ok3.VALUE_STATUS = 'Provisional' THEN ok3.PROVISIONAL_LOCK_VALUE ELSE 0 END), 0) AS Provisional,
                ROUND(SUM(CASE WHEN ok3.VALUE_STATUS = 'Avg Lock' THEN ok3.AVG_LOCK_VALUE ELSE 0 END), 0) AS Avg_Lock
            FROM
                ok3
                GROUP BY
                    ProdMonth
            ),
            ok5 AS (
                SELECT
                    ok4.*,
                    COGS + Expensess AS Production_cost,
                    ROUND(Provisional + Avg_Lock, 2) AS Total_sales_values
                FROM
                    ok4
            ),
            ok6 AS (
                SELECT
                    ok5.*,
                    Total_sales_values - Production_cost AS Profit
                FROM
                    ok5
            )
            SELECT
               ok6.*,
                ROUND((100.00 * Profit / Total_sales_values), 2) AS Profit_Percent
            FROM
                ok6;
            """

            # Execute the SQL query and fetch all rows
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()

        # Calculate grand totals
        for row in data:
            grand_total['Pcs'] += row['Pcs']
            grand_total['Polish_CTS'] += Decimal(row['Polish_CTS'])
            grand_total['COGS'] += Decimal(row['COGS'])
            grand_total['Expense'] += Decimal(row['Expensess'])
            grand_total['Production_cost'] += Decimal(row['Production_cost'])
            grand_total['Provisional'] += Decimal(row['Provisional'])
            grand_total['Avg_Lock'] += Decimal(row['Avg_Lock'])
            grand_total['Total_sales_values'] += Decimal(row['Total_sales_values'])
            grand_total['Profit'] += Decimal(row['Profit'])
        if grand_total['Total_sales_values'] != Decimal('0.00'):
            grand_total['Profit_Percent'] = round(float(100.00 * float(grand_total['Profit']) / float(grand_total['Total_sales_values'])), 2)
        # Calculate the number of unique production months
        unique_months = set(row['ProdMonth'] for row in data)
        unique_months_count = len(unique_months)

    return render_template('Export_pl.html', data=data, unique_months_count=unique_months_count, grand_total=grand_total, fmonth_name=fmonth_name, tmonth_name=tmonth_name, pl_type=pl_type)

print("Ishita")
if __name__ == '__main__':
    app.run(debug=True)
