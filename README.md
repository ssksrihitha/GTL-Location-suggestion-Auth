# GTL-Loaction-suggestion-NLM-BLR-Auth


# ABOUT APP
This app is used to streamline Iventory Management operations especailly the activity called "GTL Movement"

In simple terms, this GTL activity is all about moving products from non-store to store to make them available for picking, packing & dispatch ready.

Currently we dont have any auto suggestion of the products to be moved, Qty to be moved, from which source location to which destination location on warehouse management system used by the company.

My app besides having all the above features and ensures the FIFO by considering MFD of the product and suggests the location from source loc to nearest destination location.

# How to run Locally.
Run these commands in the admin terminal/path: 
1. pip install streamlit
2. pip install streamlit-authenticator
3. pip install pandas

# Used python==3.12

Once after running these commands, copy paste the code present in the file named **"final.py"** in VCS and try running the code locally with the command "streamlit run final.py"

Ensure all the files present in the repo are downloaded and present in the same path as the python3.12(admin path is suggestable)
