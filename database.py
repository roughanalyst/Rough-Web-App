import pandas as pd
import numpy as np
import mysql.connector
import datetime as dt

# Read Excel file into DataFrame
df = pd.read_excel('C://Users//spc2//Desktop//NNS DATA.xlsx')

# Replace NaN values with None
df = df.replace({np.nan: None})
df['FLR'] = df['FLR'].replace({np.nan: 'None'})

if 'FLR' in df.columns:
    df.rename(columns={'FLR': 'Flour'}, inplace=True)  

# Establish connection to MySQL database
connection = mysql.connector.connect(host='192.168.227.34',
                                     user='public',
                                     password='1234',
                                     database='rough_dept')

# Create cursor
cursor = connection.cursor()
date = dt.date.today
# Define the query
query = '''
    INSERT INTO  nns(LOTNO, DISPLAY_LOTNO, MAIN_PKTNO, PKTNO, TAG_NAME, SIZE_NAME, ROUGH_UNCUT, LBR_RATE, ORG_CTS, MISTAKE_VAL, STONE_STATUS, POL_TYPE, OS_STATUS, STONE_ID,REMD_LESS_PER, FANCY_CLR, LAB, CTS, DEMAND_CUT, SHP_VAL, CLA_VAL, COL_VAL, CUT_VAL, POL_VAL, SYM_VAL, FLR_VAL, DIA_VAL, CR_ANG_VAL, CR_HGT_VAL, PV_ANG_VAL, PV_HGT_VAL, TBL_VAL, HGT_VAL, LEN_VAL, WDTH_VAL, DEPTH_MM_VAL, GIRDLE_VAL, LW_VALUE, SHP, CLA, COL, CUT, NEW_CUT, POL, SYM, FLR, HGT, TBL, LEN, WDTH, DEPTH_MM, CR_ANG, PV_ANG, CR_HGT, PV_HGT, GIRDLE, L_W, PROG_ID, PROG_NAME, RAPO_RATE, MPM, PD_PER, PD, PD_CNT, MPM_PD, GIA_EXP, TOT_EXP_RATE, POLISH_VAL_PER, RGH_COST_VAL, FINAL_COST, DIFF, CUR_OLD_EXP_RATE, CUR_OLD_CALC_RATE, CUR_NEW_RAPO_RATE, CUR_NEW_EXP_RATE, CUR_NEW_DISC_PER, CUR_NEW_CALC_RATE, CUR_FINAL_RATE, CUR_FINAL_RATE_PD, CUR_PD, DISCOVER_FLG, CUR_PROG_NAME, RATE_TYPE, DEMAND_CHART, CUR_PROG_RATE, CURR_PROG_NAME, PUR_AMT, ARTICLE, SHAPE_GROUP, CLARITY_GROUP, COLOR_GROUP, SIZE_GROUP, TRANS_TYPE, LAB_STD_EXP, ASSORT_TYPE, AVG_VALUE, AVG_MPM_PD, STONE_CATEGORY, ARTICLE_GRP, TRENDPER, TRENDVALUE, SIDTYPE, RATE_TYPE_CUR_FINAL_RATE, MAX_CUR_FINAL_RATE_PD, SI2_I1, SALES_AVG_VALUE, RATE_ENTRY, DISC_PER, ISACTIVE_PROG, S_LAB_STD_EXP, PROG_AMOUNT, YNS_STATUS, LSD_SCORE, LSD_AMT, CSD_SCORE, CSD_AMT, SALES_CALC_VALUE, IS_SALES_VALUE, IS_UPD_FLG, IO_DATE, UPD_DATE, ENT_DATE, ENT_USER, ENT_TERM, upd_AVG_MPM_PD, Upd_MAX_CUR_FINAL_RATE_PD, Upd_time, upd_Username)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s)
'''

# Iterate through DataFrame rows and execute the query for each row
for row in df.itertuples(index=False):
    cursor.execute(query,(row.LOTNO, row.DISPLAY_LOTNO, row.MAIN_PKTNO, row.PKTNO, row.TAG_NAME, row.SIZE_NAME, row.ROUGH_UNCUT, row.LBR_RATE, row.ORG_CTS, row.MISTAKE_VAL, row.STONE_STATUS, row.POL_TYPE, row.OS_STATUS, row.STONE_ID, row.REMD_LESS_PER, row.FANCY_CLR, row.LAB, row.CTS, row.DEMAND_CUT, row.SHP_VAL, row.CLA_VAL, row.COL_VAL, row.CUT_VAL, row.POL_VAL, row.SYM_VAL, row.FLR_VAL, row.DIA_VAL, row.CR_ANG_VAL, row.CR_HGT_VAL, row.PV_ANG_VAL, row.PV_HGT_VAL, row.TBL_VAL, row.HGT_VAL, row.LEN_VAL, row.WDTH_VAL, row.DEPTH_MM_VAL, row.GIRDLE_VAL, row.LW_VALUE, row.SHP, row.CLA, row.COL, row.CUT, row.NEW_CUT, row.POL, row.SYM, row.FLR, row.HGT, row.TBL, row.LEN, row.WDTH, row.DEPTH_MM, row.CR_ANG, row.PV_ANG, row.CR_HGT, row.PV_HGT, row.GIRDLE, row.L_W, row.PROG_ID, row.PROG_NAME, row.RAPO_RATE, row.MPM, row.PD_PER, row.PD, row.PD_CNT, row.MPM_PD, row.GIA_EXP, row.TOT_EXP_RATE, row.POLISH_VAL_PER, row.RGH_COST_VAL, row.FINAL_COST, row.DIFF, row.CUR_OLD_EXP_RATE, row.CUR_OLD_CALC_RATE, row.CUR_NEW_RAPO_RATE, row.CUR_NEW_EXP_RATE, row.CUR_NEW_DISC_PER, row.CUR_NEW_CALC_RATE, row.CUR_FINAL_RATE, row.CUR_FINAL_RATE_PD, row.CUR_PD, row.DISCOVER_FLG, row.CUR_PROG_NAME, row.RATE_TYPE, row.DEMAND_CHART, row.CUR_PROG_RATE, row.CURR_PROG_NAME, row.PUR_AMT, row.ARTICLE, row.SHAPE_GROUP, row.CLARITY_GROUP, row.COLOR_GROUP, row.SIZE_GROUP, row.TRANS_TYPE, row.LAB_STD_EXP, row.ASSORT_TYPE, row.AVG_VALUE, row.AVG_MPM_PD, row.STONE_CATEGORY, row.ARTICLE_GRP, row.TRENDPER, row.TRENDVALUE, row.SIDTYPE, row.RATE_TYPE_CUR_FINAL_RATE, row.MAX_CUR_FINAL_RATE_PD, row.SI2_I1, row.SALES_AVG_VALUE, row.RATE_ENTRY, row.DISC_PER, row.ISACTIVE_PROG, row.S_LAB_STD_EXP, row.PROG_AMOUNT, row.YNS_STATUS, row.LSD_SCORE, row.LSD_AMT, row.CSD_SCORE, row.CSD_AMT, row.SALES_CALC_VALUE, row.IS_SALES_VALUE, row.IS_UPD_FLG, row.IO_DATE, row.UPD_DATE, row.ENT_DATE, row.ENT_USER, row.ENT_TERM, row.AVG_MPM_PD, row.MAX_CUR_FINAL_RATE_PD, dt.date.today, row.upd_Username ))

# Commit changes and close connection
connection.commit()
cursor.close()
connection.close()
