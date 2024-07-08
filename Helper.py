import pickle
from pathlib import Path

import streamlit_authenticator as stauth

names = ["Sennerikuppam Siva Kamakshi", "Tanveer Alam Shekh"]
usernames = ["ssennerikuppam", "astanveer"]
passwords = ["xxx", "xxx"]

hashed_passwords = stauth.Hasher(passwords).generate()

file_path = Path(__file__).parent / "ssk_hashed.pkl"
with file_path.open("wb") as file:
    pickle.dump(hashed_passwords, file)















# import pickle
# from pathlib import Path

# import streamlit_authenticator as stauth
# # from streamlit_authenticator.utilities.hasher import Hasher

# names = ["Sennerikuppam Siva Kamakshi", "Tanveer Alam Shekh"]
# usernames = ["ssennerikuppam", "astanveer"]
# passwords = ["Siva@2001", "Tanveer@2001"]

# hashed_passwords = stauth.Hasher(passwords).generate()


# file_path = Path(__file__).parent / "hashed_pw.pkl"
# with file_path.open("wb") as file:
#     pickle.dump(hashed_passwords, file)

# # # Pass the list of passwords directly to the 
# # # Hasher constructor and generate the hashes
# # passwords_to_hash = ['fashion@123', 'increff@fashion']
# # hashed_passwords = Hasher(passwords_to_hash).generate()

# # print(hashed_passwords)