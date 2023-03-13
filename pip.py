import os
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd

#checkout stripe
stripe_checkout="https://buy.stripe.com/3csg2z50P53B7tedQQ"

#funzioni eCom
def get_customer_metrics(df):
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['order_date'] = df['order_date'].dt.strftime('%Y-%m-%d')
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['order_total'] = round(df['order_total'], 2)

    client = df['customer_id'].nunique()
    client2orders = df[df.groupby('customer_id').order_id.transform('count') > 1].customer_id.nunique()
    repurchaserate = round(client2orders/client*100, 2)
    orders = df['order_id'].count()
    COC = round(orders/client, 2)
    return client, client2orders, repurchaserate, orders, COC

# credenziali Sheet API
base_dir = os.path.dirname(os.path.abspath(__file__))
creds_file_path = os.path.join(base_dir, 'credentials.json')
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(creds_file_path, scopes=scope)
file = gspread.authorize(creds)

# Sheet FIle ID
sheet = file.open_by_key('1tTAfCdqyD7ecXTSnFHmDPLLcdsIdCCcgZzGFIjPhzXk').sheet1

# Sidebar per Login e SignUP
menu = st.sidebar.selectbox('Menu', ['Sign Up', 'Log In'])

if menu == 'Sign Up':
    st.write('Create an account to access your analysis')
    username = st.sidebar.text_input('Username', key='signup_username')
    password = st.sidebar.text_input('Password', type='password', key='signup_password')
    submit = st.sidebar.button('Sign Up')

    # Se lo username è già stato
    if submit:
        cell_list = sheet.findall(username, in_column=1)
        if len(cell_list) > 0:
            st.sidebar.warning('Sorry, that username is already taken. Please try again with a different username.')
        else:
            sheet.append_row([username, password,0])
            st.sidebar.write(f'Successfully signed up as {username}! Please go to the Log In section to continue.')

elif menu == 'Log In':
    login_subheader = st.sidebar.subheader('Enter your username and password to log in:')
    username = st.sidebar.text_input('Username', key='login_username')
    password = st.sidebar.text_input('Password', type='password', key='login_password')
    submit = st.sidebar.checkbox('Log In')

    # Check tra Login data e DB
    if submit:
        cell_list = sheet.findall(username, in_column=1)
        if len(cell_list) == 0:
            st.sidebar.warning('Incorrect username or password. Please try again.')
        else:
            user_row = cell_list[0].row
            upload_count = sheet.cell(user_row, 3).value

            if int(upload_count) >= 2:
                st.warning("You have already uploaded a file. Upgrade your account to upload more files.")
                st.write("If you want upload more files, access the Premium Version. Buy it for $20")
                st.markdown(
                            f'<a href={stripe_checkout} class="button"> :point_right::skin-tone-2: Buy it </a>',unsafe_allow_html=True,
                        )
            else:
                st.title(f"Welcome {username}")
                st.subheader("Start your analysis")

                uploaded_file = st.file_uploader("Choose a file")
                if uploaded_file is not None:
                    try:
                        # Numero eventi
                        sheet.update_cell(user_row, 3, int(upload_count) + 1)

                        df = pd.read_csv(uploaded_file)
                        df['order_date'] = pd.to_datetime(df['order_date'])
                        df['order_date'] = df['order_date'].dt.strftime('%Y-%m-%d')
                        df['order_date'] = pd.to_datetime(df['order_date'])
                        df['order_total'] = round(df['order_total'], 2)

                        client, client2orders, repurchaserate, orders, COC = get_customer_metrics(df)

                        st.write(f"Total number of customers: {client}")
                        st.write(f"Number of customers who made more than one order: {client2orders}")
                        st.write(f"Repurchase rate: {repurchaserate}%")
                        st.write(f"Total number of orders: {orders}")
                        st.write("")
                        st.write("If you want more data, access the Premium Version. Buy it for $20")
                        st.markdown(
                            f'<a href={stripe_checkout} class="button"> :point_right::skin-tone-2: Buy it </a>',unsafe_allow_html=True,
                        )

                    except Exception as e:
                        st.error(e)

    else:
        st.warning('Please Login to access')
