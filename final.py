import pickle
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np

import streamlit_authenticator as stauth

# --- USER AUTHENTICATION ---
names = ["Sennerikuppam Siva Kamakshi", "Tanveer Alam Shekh"]
usernames = ["ssennerikuppam", "astanveer"]

# load hashed passwords
file_path = Path(__file__).parent / "ssk_hashed.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
    "sales_dashboard", "abcdef", cookie_expiry_days=0)

name, authentication_status, username = authenticator.login("Login with LDAP", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")

if authentication_status:

    # Streamlit app title
    st.title("GTL FWD locations suggestion app")

    # Upload input files
    file1 = st.file_uploader("Upload Live_Inventory_Dump (CSV)", type="csv")
    file2 = st.file_uploader("Upload Is_Bulk file (CSV)", type="csv")
    file3 = st.file_uploader("Upload Drr,MBQ file (CSV)", type="csv")
    file4 = st.file_uploader("Upload WID (CSV)", type="csv")

    # Process files when all files are uploaded
    if file1 and file2 and file3 and file4:
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
        df3 = pd.read_csv(file3)
        df4 = pd.read_csv(file4)

        # st.write("raw live dump:")
        # st.dataframe(df1)  

        # Map "is_bulk_location" from file2 to file1
        df1 = df1.merge(df2[['locations', 'is_bulk_location','Location type','Sort']], left_on='shelf_label', right_on='locations', how='left')
        df1['IsBulk'] = df1['is_bulk_location']
        df1.drop(columns=['locations', 'is_bulk_location'], inplace=True)
        
        # Map "is_bulk_location" from file2 to file1
        df1 = df1.merge(df4[['wid','mfd']], left_on='wid', right_on='wid', how='left')
        
            

        # Split file1 into "FWD Locations" and "Deep Locations"
        fwd_locations = df1[df1['IsBulk'] == 0].copy()
        deep_locations = df1[df1['IsBulk'] == 1].copy()
        
        # Example of aggregation: count of unique 'wid', sum of 'quantity', and minimum 'Sort' for each FSN
        df5 = fwd_locations.groupby('fsn').agg({
            'wid': lambda x: ', '.join(x.astype(str)),  # Concatenate all unique WIDs into a string
            'quantity': 'sum',     # Sum of 'quantity'
        }).reset_index()
        #  # Display df5 to verify the grouping and aggregation
        # st.write("Grouped DataFrame (df5):")
        # st.dataframe(df5)
        
        # Map additional columns from file3 to "FWD Locations"
        df5 = df5.merge(df3[['FSN', 'DRR', 'Classification', 'Case QTY', 'LBH(VOL inches)', 'MBQ', 'Is_RGTL']],
                                            left_on='fsn', right_on='FSN', how='left')
        df5.drop(columns=['FSN'], inplace=True)

        # Ensure the relevant columns are numeric
        cols_to_convert = ['quantity', 'DRR', 'Case QTY', 'MBQ']
        for col in cols_to_convert:
          df5[col] = pd.to_numeric(df5[col], errors='coerce')

        # Add new calculated columns to "FWD Locations"
        df5['Current_FWD_DOH'] = df5['quantity'] / df5['DRR']


        # Define a function for the Expected_DOH column
        def calculate_expected_doh(drr):
            if 0< drr <= 5:
                return 6
            elif drr <= 11:
                return 3
            elif drr <= 40:
                return 3
            elif drr <= 70:
                return 2.5
            elif drr <= 110:
                return 2
            elif drr <= 249.9:
                return 2
            elif drr>= 250:
                return 1.5
            else:
                return "NaN"

        df5['Expected_DOH'] = df5['DRR'].apply(calculate_expected_doh)
        df5['QTY_to_be_filled'] = (df5['Current_FWD_DOH'] - df5['Expected_DOH']) * df5['DRR']
        
        # Now convert 'QTY_to_be_filled' to numeric
        df5['QTY_to_be_filled'] = pd.to_numeric(df5['QTY_to_be_filled'], errors='coerce')

        # Define a function for the Priority column
        def calculate_priority(current_doh):
            if current_doh <= 0.99:
                return "P0"
            elif 1 <= current_doh <= 1.99:
                return "P1"
            elif 2 <= current_doh <= 2.99:
                return "P2"
            elif 3 <= current_doh <= 3.99:
                return "P3"
            else:
                return "P4"
        
        df5['Priority'] = df5['Current_FWD_DOH'].apply(calculate_priority)

        # Calculate "Final Movement(in qty)" and "Final Movement(in no: of cases)"
        df5['Final Movement(in qty)'] = np.where(
            (df5['MBQ'] - (df5['quantity'] + abs(df5['QTY_to_be_filled']))) + abs(df5['QTY_to_be_filled']) <= 0,
            df5['QTY_to_be_filled'],
            (df5['MBQ'] - (df5['quantity'] + abs(df5['QTY_to_be_filled']))) + abs(df5['QTY_to_be_filled'])
        )

        df5['Final Movement(in no: of cases)'] = np.ceil(df5['Final Movement(in qty)'] / df5['Case QTY'])

        # Add Bins Require col
        df5['Bins_required'] = abs(np.ceil(df5['QTY_to_be_filled']/df5['MBQ']))

        # add Final GTL qty col
        df5['Final_GTL_qty']=df5['Final Movement(in no: of cases)'] * df5['Case QTY']

        # Deletion conditions
        location_types_to_delete = ["RC", "Idle", "Mixed", "CB","FNV","Virtual"]
        fwd_locations = fwd_locations[~fwd_locations['Location type'].isin(location_types_to_delete)]
        # fwd_locations = fwd_locations.drop(fwd_locations[fwd_locations['Location type'].isin(['Idle','RC','Mixed','CB','FNV','Virtual'])].index)
        
        # # Display the processed data
        # st.write("processed rawjwegdyj data-FWD:")
        # st.dataframe(fwd_locations)

        # Identify unique WIDs based on the minimum quantity
        unique_wids = fwd_locations.loc[fwd_locations.groupby('wid')['quantity'].idxmin()].reset_index(drop=True)

        # Function to delete specified columns from a DataFrame
        def delete_columns(df, columns_to_delete):
            for col in columns_to_delete:
                if col in df.columns:
                    df.drop(columns=[col], inplace=True)
            return df

        # Specify the columns to be deleted from each DataFrame
        columns_to_delete = ["brand", "vertical", "sku","package_id","storage_location_id","warehouse_id","product_detail_id","storage_zone","updated_by","timestamp","transit_quantity","quantity_in_putlist","quantity_in_gtl"]
        # fwd_cols=["mfd","brand", "vertical", "sku","package_id","storage_location_id","warehouse_id","product_detail_id","storage_zone","updated_by","timestamp","transit_quantity","quantity_in_putlist","quantity_in_gtl"]

        # Apply column deletion to each DataFrame
        # df5 = delete_columns(df5, fwd_cols)
        unique_wids = delete_columns(unique_wids, columns_to_delete)
        deep_locations = delete_columns(deep_locations, columns_to_delete)
        
        # Map "is_bulk_location" from file2 to file1
        unique_wids = unique_wids.merge(df5[['fsn', 'DRR','Classification','Case QTY','LBH(VOL inches)','MBQ','Is_RGTL','Current_FWD_DOH','Expected_DOH','QTY_to_be_filled','Priority','Final Movement(in qty)','Final Movement(in no: of cases)','Bins_required','Final_GTL_qty']], left_on='fsn', right_on='fsn', how='left')
        # df1['IsBulk'] = df1['is_bulk_location']
        # df1.drop(columns=['locations', 'is_bulk_location'], inplace=True)
        

        # Rename the column 'Sort' to 'd_sort'
        deep_locations.rename(columns={'Sort': 'd_sort'}, inplace=True)

        
        Deep2fwd_suggestion = unique_wids.copy()
        # Add a column to store the Location ID in "FWD Locations"
        Deep2fwd_suggestion['Deep_location'] = np.nan
        # st.write("deep2fwd_suggestion:")
        # st.dataframe(Deep2fwd_suggestion)    

        # Iterate over each FSN in the "deep2fwd_suggestion" DataFrame
        for index, row in Deep2fwd_suggestion.iterrows():
            fsn = row['fsn']
            wid_fwd = row['wid']
            sort = row['Sort']  # Assuming f_sort is in the "FWD Locations" file
            
            # Check 1: Search for FSN in "Deep Locations"
            deep_fsn_rows = deep_locations[deep_locations['fsn'] == fsn]
            
            
            if deep_fsn_rows.empty:
                # FSN not found in "Deep Locations"
                Deep2fwd_suggestion.at[index, 'Deep_location'] = "Not actionable"
                continue  # Move to the next FSN
            
            # Check 2: Search for WID in "Deep Locations" with the same FSN
            deep_wid_rows = deep_fsn_rows[deep_fsn_rows['wid'] == wid_fwd]
            
            if not deep_wid_rows.empty:
                
                # Check 3: Select the minimum quantity for the found WID
                min_qty_row = deep_wid_rows.loc[deep_wid_rows['quantity'].idxmin()]
                # Check if multiple rows have the minimum quantity
                min_qty = min_qty_row['quantity']
                min_qty_rows = deep_wid_rows[deep_wid_rows['quantity'] == min_qty]
                
                if len(min_qty_rows) == 1:
                    # Only one row with minimum quantity
                    Deep2fwd_suggestion.at[index, 'Deep_location'] = min_qty_row['shelf_label']
                else:
                    # Multiple rows with the same minimum quantity
                    # Check 5: Handle tie by finding the least abs(d_sort - f_sort)
                    min_qty_rows['sort_diff'] = abs(min_qty_rows['d_sort'] - sort)
                    min_sort_diff_row = min_qty_rows.loc[min_qty_rows['sort_diff'].idxmin()]
                    Deep2fwd_suggestion.at[index, 'Deep_location'] = min_sort_diff_row['shelf_label']
        

            else:
                # Check 4: WID not found, select earliest date from remaining WIDs
                # Filter rows with non-empty 'mfd'
                valid_deep_fsn_rows = deep_fsn_rows[deep_fsn_rows['mfd'].notna()]
                
                if not valid_deep_fsn_rows.empty:
                    # # Convert 'mfd' to datetime for comparison
                    valid_deep_fsn_rows['mfd'] = pd.to_datetime(valid_deep_fsn_rows['mfd'], format='%d/%m/%y', errors='coerce')
                
                    # Find the row with the earliest 'mfd' date
                    earliest_date_row = valid_deep_fsn_rows.loc[valid_deep_fsn_rows['mfd'].idxmin()]
                    
                    # Handle case if 'mfd' is the same for multiple rows
                    earliest_mfd_date = earliest_date_row['mfd']
                    earliest_date_rows = valid_deep_fsn_rows[valid_deep_fsn_rows['mfd'] == earliest_mfd_date]
                    
                    if len(earliest_date_rows) > 1:
                        # Check 5: Handle tie by finding the least abs(d_sort - f_sort)
                        earliest_date_rows['sort_diff'] = abs(earliest_date_rows['d_sort'] - sort)
                        min_sort_diff_row = earliest_date_rows.loc[earliest_date_rows['sort_diff'].idxmin()]
                        Deep2fwd_suggestion.at[index, 'Deep_location'] = min_sort_diff_row['shelf_label']
                    else:
                        # Use the earliest 'mfd' date's Location ID
                        Deep2fwd_suggestion.at[index, 'Deep_location'] = earliest_date_row['shelf_label']
                else:
                    # No valid 'mfd' found, go to Check 3
                    min_qty_row = deep_fsn_rows.loc[deep_fsn_rows['quantity'].idxmin()]
                    # Check if multiple rows have the minimum quantity
                    min_qty = min_qty_row['quantity']
                    min_qty_rows = deep_fsn_rows[deep_fsn_rows['quantity'] == min_qty]
                
                    if len(min_qty_rows) == 1:
                        # Only one row with minimum quantity
                        Deep2fwd_suggestion.at[index, 'Deep_location'] = min_qty_row['shelf_label']
                    else:
                        # Multiple rows with the same minimum quantity
                        # Check 5: Handle tie by finding the least abs(d_sort - f_sort)
                        min_qty_rows['sort_diff'] = abs(min_qty_rows['d_sort'] - sort)
                        min_sort_diff_row = min_qty_rows.loc[min_qty_rows['sort_diff'].idxmin()]
                        Deep2fwd_suggestion.at[index, 'Deep_location'] = min_sort_diff_row['shelf_label']

    # Identify unique WIDs based on the minimum quantity
        Deep2fwd_suggestion2 = Deep2fwd_suggestion.loc[Deep2fwd_suggestion.groupby('fsn')['quantity'].idxmin()].reset_index(drop=True)


        # Download buttons for the generated files
        st.download_button(
            label="Click to Final D2F file",
            data=Deep2fwd_suggestion2.to_csv(index=False).encode('utf-8'),
            file_name='Final_D2F file.csv',
            mime='text/csv'
        )
        st.download_button(
            label="Click to Download FWD Locations",
            data=fwd_locations.to_csv(index=False).encode('utf-8'),
            file_name='FWD_Locations.csv',
            mime='text/csv'
        )
        st.download_button(
            label="Click to Download Unique Wid file",
            data=unique_wids.to_csv(index=False).encode('utf-8'),
            file_name='Unique Wid file.csv',
            mime='text/csv'
        )
        st.download_button(
            label="Click to Download Deep Locations",
            data=deep_locations.to_csv(index=False).encode('utf-8'),
            file_name='Deep_Locations.csv',
            mime='text/csv'
        )

        st.write("Final D2F file:")
        st.dataframe(Deep2fwd_suggestion2)

        # Display the unique WIDs DataFrame
        st.write("Unique WIDs with minimum quantity for each:")
        st.dataframe(unique_wids)

        # Display the processed data
        st.write("processed raw data-FWD:")
        st.dataframe(fwd_locations)

        # Rename the column 'Sort' to 'd_sort'
        deep_locations.rename(columns={'Sort': 'd_sort'}, inplace=True)
        st.write("processed raw data-deep:")
        st.dataframe(deep_locations)    


