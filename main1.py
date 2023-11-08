import streamlit as st
import easyocr
import cv2
import numpy as np
import pandas as pd
import re
from streamlit_option_menu import option_menu
import psycopg2
from PIL import Image
import io
import streamlit as st

con = psycopg2.connect(host="localhost", user="postgres", password="sripradeep", port=5432, database="bizcard_data")
sri = con.cursor()
reader = easyocr.Reader(['en'], gpu = False)

st.set_page_config(page_title="Bizcard", page_icon="",layout="wide", initial_sidebar_state="expanded")
st.title(":rainbow[BizCardX: Extracting Business Card Data with OCR]")
def extractdata(data):
    for i in range(len(data)):
        data[i] = data[i].rstrip(' ')
        data[i] = data[i].rstrip(',')
        res = ' '.join(data)
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    website_pattern = r'[www|WWW|wwW]+[\.|\s]+[a-zA-Z0-9]+[\.|\][a-zA-Z]+'
    phone_pattern = r'(?:\+)?\d{3}-\d{3}-\d{4}'
    phone_pattern2 = r"(?:\+91[-\s])?(?:\d{4,5}[-\s])?\d{3}[-\s]?\d{4}"
    address_pattern = r'\d+\s[A-Za-z\s,]+'
    pincode_pattern = r'\b\d{6}\b'
    name = designation = company = email = website = primary = secondary = address = pincode = None
    try:
        email = re.findall(email_pattern, res)[0]
        res = res.replace(email, '')
        email = email.lower()
    except IndexError:
        email = None
    try:
        website = re.findall(website_pattern, res)[0]
        res = res.replace(website, '')
        website = re.sub('[WWW|www|wwW]+ ', 'www.', website)
        website = website.lower()
    except IndexError:
        webstie = None
    phone = re.findall(phone_pattern, res)
    if len(phone) == 0:
        phone = re.findall(phone_pattern2, res)
    primary = None
    secondary = None
    if len(phone) > 1:
        primary = phone[0]
        secondary = phone[1]
        for i in range(len(phone)):
            res = res.replace(phone[i], '')
    elif len(phone) == 1:
        primary = phone[0]
        res = res.replace(phone[0], '')
    try:
        pincode = int(re.findall(pincode_pattern, res)[0])
        res = res.replace(str(pincode), '')
    except:
        pincode = 0
    name = data[0]
    res = res.replace(name, '')
    designation = data[1]
    res = res.replace(designation, '')
    address = ''.join(re.findall(address_pattern, res))
    result = res.replace(address, '')
    company = data[-1]
    res = res.replace(company, '')

    info = [name, designation, company, email, website, primary, secondary, address, pincode, result]
    return (info)
with st.sidebar:
    selected = option_menu(
        menu_title="Navigaton",  # required
        options=["Home","---","Upload", "View/Modify", "---", "About"],  # required
        icons=["house","", "upload","binoculars",  "", "envelope"],  # optional
        menu_icon="person-vcard",  # optional
        default_index=0,  # optional
        styles={"nav-link": {"--hover-color": "brown"}},
        orientation="vertical",
    )
if selected == 'Home':
    st.subheader(":green[Purpose:]")
    st.write("Automates the process of extracting key details from business card images")
    st.subheader(":green[Technologies Used:]")
    st.write("Easy-OCR, Streamlit GUI, SQL, Data Extraction</h1>")
    st.subheader(":green[Approach:]")
    st.markdown(":green[Image Input:]")
    st.write("Users can upload business card images through the application interface.")

    st.markdown(":green[Text Extraction:]")
    st.write("EasyOCR is employed to recognize and extract text from the uploaded images.")

    st.markdown(":green[Data Processing:]")
    st.write(
        "Regular expressions are used to identify and extract specific pieces of information, such as name, designation, company, and contact details from the extracted text.")

    st.markdown(":green[Database Storage:]")
    st.write("Extracted information is stored in a MySQL database.")

    st.markdown(":green[User Interface:]")
    st.write(
        "Streamlit provides a user-friendly interface for users to interact with the application, upload images, and view extracted data.")

    st.markdown(":green[Further Analysis:]")
    st.write(
        "The stored data can be used for various purposes such as lead generation, customer relationship management, or other business analytics.")

elif selected == 'Upload':
    uploaded_file = st.file_uploader("Choose a image file",type=["jpg", "jpeg", "png"])
    if uploaded_file != None:
        image = cv2.imdecode(np.fromstring(uploaded_file.read(), np.uint8), 1)
        col1, col2, col3 = st.columns([2,1,2])
        with col3:
            st.image(image)
        with col1:
            result = reader.readtext(image, detail=0)
            info = extractdata(result)
            #st.table(pd.Series(info, index=['Name', 'Designation', 'Company', 'Email ID', 'Website', 'Primary Contact', 'Secondary Contact', 'Address', 'Pincode', 'Other']))
            name = st.text_input('Name:',info[0])
            desig = st.text_input('Designation:', info[1])
            Com = st.text_input('Company:', info[2])
            mail = st.text_input('Email ID:', info[3])
            url = st.text_input('Website:', info[4])
            m1 = st.text_input('Primary Contact:', info[5])
            m2 = st.text_input('Secondary Contact:', info[6])
            add = st.text_input('Address:', info[7])
            pin = st.number_input('Pincode:', info[8])
            oth = st.text_input('Others(this will not stored):', info[9])
            a = st.button("upload")
            if a:
                sri.execute(
                    """CREATE TABLE IF NOT EXISTS business_cards (name VARCHAR, designation VARCHAR, company VARCHAR, email VARCHAR, website VARCHAR, primary_no VARCHAR,
                    secondary_no VARCHAR, address VARCHAR, pincode int, image bytea)""")
                query = "INSERT INTO business_cards (name, designation, company, email, website, primary_no, secondary_no, " \
                      "address, pincode, image) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                val = (name, desig, Com, mail, url, m1, m2, add, pin, psycopg2.Binary(image))
                sri.execute(query, val)
                con.commit()
                st.success('Contact stored successfully in database')

elif selected == 'View/Modify':
    col1, col2, col3 = st.columns([2,2,4])
    with col1:
        sri.execute('select name from business_cards')
        y = sri.fetchall()
        contact = [x[0] for x in y]
        contact.sort()
        selected_contact = st.selectbox('Name',contact)
    with col2:
        mode_list = ['','View','Modify','Delete']
        selected_mode = st.selectbox('Mode',mode_list,index = 0)

    if selected_mode == 'View':
        col5,col6 = st.columns(2)
        with col5:
            sri.execute(f"select name, designation, company, email, website, primary_no, secondary_no, "
                         f"address, pincode from business_cards where name = '{selected_contact}'")
            y = sri.fetchall()
            st.table(pd.Series(y[0],index=['Name', 'Designation', 'Company', 'Email ID', 'Website', 'Primary Contact', 'Secondary Contact', 'Address', 'Pincode'],name='Card Info'))

    elif selected_mode == 'Modify':
        sri.execute(f"select name, designation, company, email, website, primary_no, secondary_no, "
                     f"address, pincode from business_cards where name = '{selected_contact}'")
        info = sri.fetchone()
        col5, col6 = st.columns(2)
        with col5:
            name = st.text_input('Name:', info[0])
            desig = st.text_input('Designation:', info[1])
            Com = st.text_input('Company:', info[2])
            mail = st.text_input('Email ID:', info[3])
            url = st.text_input('Website:', info[4])
            m1 = st.text_input('Primary Contact:', info[5])
            m2 = st.text_input('Secondary Contact:', info[6])
            add = st.text_input('Address:', info[7])
            pin = st.number_input('Pincode:', info[8])
        a = st.button("Update")
        if a:
            query = f"update business_cards set name = %s, designation = %s, company = %s, email = %s, website = %s, " \
                    f"primary_no = %s, secondary_no = %s, address = %s, pincode = %s where name = '{selected_contact}'"
            val = (name, desig, Com, mail, url, m1, m2, add, pin)
            sri.execute(query, val)
            con.commit()
            st.success('Contact updated successfully in database')

    elif selected_mode == 'Delete':
        st.markdown(
            f'__<p style="text-align:left; font-size: 20px; color: #FAA026">You are trying to remove {selected_contact} '
            f'contact from database.</P>__',
            unsafe_allow_html=True)
        confirm = st.button('Confirm')
        if confirm:
            query = f"DELETE FROM business_cards where name = '{selected_contact}'"
            sri.execute(query)
            con.commit()
            st.success('Contact removed successfully from database')

elif selected == 'About':
    st.markdown('__<p style="text-align:left; font-size: 25px; color: #FAA026">Summary of BizCard Project</P>__',
                unsafe_allow_html=True)
    st.markdown("## Potential Improvements/Extensions:", unsafe_allow_html=True)
    st.markdown("1. **Data Validation:** Implement validation checks to ensure the accuracy of extracted data.")
    st.markdown(
        "2. **Data Enrichment:** Integrate additional APIs or services to enrich extracted data, such as company information based on extracted company names.")
    st.markdown(
        "3. **User Feedback:** Incorporate a feedback mechanism for users to correct any inaccuracies in the extracted data, improving the application's accuracy over time.")
    st.markdown(
        "4. **Export Functionality:** Allow users to export the extracted data in various formats (CSV, Excel) for external use.")
    st.markdown(
        "5. **Security:** Implement security measures to protect sensitive user data stored in the MySQL database.")
    st.markdown(
        "By combining these technologies, your Bizcard Extraction application provides a powerful solution for businesses and professionals seeking an efficient way to process and utilize business card information.",
        unsafe_allow_html=True)