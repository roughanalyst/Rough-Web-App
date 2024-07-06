# import pandas as pd
# import numpy as np
# import mysql.connector

# # Read Excel file into DataFrame
# df = pd.read_excel('C://Users//spc5//Desktop//history date data.xlsx')

# # Replace NaN values with None
# df = df.replace({np.nan: None})
# df['Flour'] = df['Flour'].replace({np.nan: 'None'})

# # Establish connection to MySQL database
# connection = mysql.connector.connect(
#     host='127.0.0.1',
#     user='local',
#     password='1234',
#     database='rough_dept'
#     )

# # Create cursor
# cursor = connection.cursor()

# # Define the query
# query = '''
# INSERT INTO history_price
# (level, Lotno, Main_Pktno, Pktno, Tag, Exp_Cts, Shape, Color, Clarity, Cut, Flour, Polish, Symmetry, Girdle, Diameter, Height, tbl,
#     Yahuda_Clr, CR_Ang, CR_Ht, PAV_Ht, PAV_Ang, Curr_Amount, Prev_Amount, Prev_Back_Per, PD_Per, Curr_Rate, Prev_Rate, Prev_Date, Rate_Per_Cts, Rate_Type, Ratiolw,
#     statuss, Back_Per, Curr_Back_Per, Curr_Date, Amount, AF_Curr_PD_Amt, AF_Prev_PD_Amt, Bom_Avg_Value, Org_Cts, Rate_Entry, Article, Length, Width, History_Date,
#     New_Cut)
# VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
#         %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
#         %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
#         %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
#         %s, %s, %s, %s, %s, %s, %s)'''

# # Iterate through DataFrame rows and execute the query for each row
# for row in df.itertuples(index=False):
#     cursor.execute(query,(row.level, row.Lotno, row.Main_Pktno, row.Pktno, row.Tag, row.Exp_Cts, row.Shape, row.Color, row.Clarity, row.Cut, row.Flour, row.Polish, row.Symmetry, row.Girdle, row.Diameter, row.Height, row.tbl, row.Yahuda_Clr, row.CR_Ang, row.CR_Ht, row.PAV_Ht, row.PAV_Ang, row.Curr_Amount, row.Prev_Amount, row.Prev_Back_Per, row.PD_Per, row.Curr_Rate, row.Prev_Rate, row.Prev_Date, row.Rate_Per_Cts, row.Rate_Type, row.Ratiolw, row.statuss, row.Back_Per, row.Curr_Back_Per, row.Curr_Date, row.Amount, row.AF_Curr_PD_Amt, row.AF_Prev_PD_Amt, row.Bom_Avg_Value, row.Org_Cts, row.Rate_Entry, row.Article, row.Length, row.Width, row.History_Date, row.New_Cut))

# # Commit changes and close connection
# connection.commit()
# cursor.close()
# connection.close()
