import streamlit as st
import pandas as pd
import hashlib
import sqlite3


def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

conn = sqlite3.connect('data.db', check_same_thread=False)
c = conn.cursor()

def create_usertable():
    c.execute('''
        CREATE TABLE IF NOT EXISTS userstable(
            username TEXT, 
            password TEXT, 
            student_id TEXT, 
            major TEXT, 
            current_standing TEXT, 
            graduation_year TEXT, 
            transcript BLOB
        )
    ''')

def add_userdata(username, password, student_id, major, current_standing, graduation_year, transcript):
    c.execute('INSERT INTO userstable(username, password, student_id, major, current_standing, graduation_year, transcript) VALUES (?, ?, ?, ?, ?, ?, ?)', (username, password, student_id, major, current_standing, graduation_year, transcript))
    conn.commit()

def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE username = ? AND password = ?', (username, password))
    data = c.fetchall()
    return data

def view_all_users():
    c.execute('SELECT * FROM userstable')
    data = c.fetchall()
    return data

def update_student_data(username, student_id, major, current_standing, graduation_year, transcript_file):
    if transcript_file is not None:
        transcript = transcript_file.read()
    else:
        transcript = None

    with conn:
        c.execute('''
            UPDATE userstable SET 
            student_id = ?, major = ?, current_standing = ?, graduation_year = ?, transcript = ? 
            WHERE username = ?
        ''', (student_id, major, current_standing, graduation_year, transcript, username))

def main():
    """Bison Advisor App"""
    st.title("Bison Advisor")

    menu = ["Home", "Login", "SignUp", "Profile"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        if 'username' in st.session_state and st.session_state['username'] is not None:
            st.write("Welcome to the Bison Advisor!")
        else:
            st.warning("Please login to view this page")

    elif choice == "Login":
        st.subheader("Login Section")
        username = st.text_input("User Name")
        password = st.text_input("Password", type='password')

        if st.checkbox("Login"):
            create_usertable()
            hashed_pswd = make_hashes(password)

            result = login_user(username, check_hashes(password, hashed_pswd))
            if result:
                st.session_state['username'] = username
                st.success(f"Logged In as {username}")

                task = st.selectbox("Task", ["Add Post", "Analytics", "Profiles"])
                if task == "Add Post":
                    st.subheader("Add Your Post")
                elif task == "Analytics":
                    st.subheader("Analytics")
                elif task == "Profiles":
                    st.subheader("User Profiles")
                    user_result = view_all_users()
                    clean_db = pd.DataFrame(user_result, columns=["Username", "Password"])
                    st.dataframe(clean_db)
            else:
                st.warning("Incorrect Username/Password")

    elif choice == "SignUp":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')
        new_student_id = st.text_input("Student ID")
        new_major = st.text_input("Major")
        new_current_standing = st.selectbox("Current Standing", ["", "Freshman", "Sophomore", "Junior", "Senior", "Graduate"])
        new_graduation_year = st.text_input("Graduation Year")
        new_transcript = st.file_uploader("Upload Transcript", type=['pdf'])

        if st.button("Signup"):
            if new_user and new_password and new_student_id and new_major and new_current_standing and new_graduation_year and new_transcript:
                create_usertable()
                new_transcript = new_transcript.read()
                add_userdata(new_user, make_hashes(new_password), new_student_id, new_major, new_current_standing, new_graduation_year, new_transcript)
                st.success("You have successfully created a valid Account")
                st.info("Go to Login Menu to login")
            else:
                st.error("All fields are required, including uploading the transcript.")


    elif choice == "Profile":
        st.subheader("Profile")
        if 'username' in st.session_state and st.session_state['username'] is not None:
            st.write(f"Welcome to your profile, {st.session_state['username']}!")

            user_data = get_user_data(st.session_state['username'])
            if user_data:
                user_student_id, user_major, user_current_standing, user_graduation_year, user_transcript = user_data
                student_id = st.text_input("Student ID", value=user_student_id)
                major = st.text_input("Major", value=user_major)
                current_standing_index = ["Freshman", "Sophomore", "Junior", "Senior", "Graduate"].index(user_current_standing)
                current_standing = st.selectbox("Current Standing", ["Freshman", "Sophomore", "Junior", "Senior", "Graduate"], index=current_standing_index)
                graduation_year = st.text_input("Graduation Year", value=user_graduation_year)

                if user_transcript:
                    st.download_button(label="Download Transcript", data=user_transcript, file_name="transcript.pdf", mime='application/octet-stream')
                else:
                    transcript = st.file_uploader("Upload Transcript", type=['pdf'])

                if st.button("Update Profile"):
                    if transcript is not None:
                        transcript = transcript.read()
                    else:
                        transcript = user_transcript

                    update_student_data(st.session_state['username'], student_id, major, current_standing, graduation_year, transcript)
                    st.success("Profile Updated")
            else:
                st.warning("No user data found.")

        else:
            st.warning("Please login to view this page")


def get_user_data(username):
    c.execute('SELECT student_id, major, current_standing, graduation_year, transcript FROM userstable WHERE username = ?', (username,))
    return c.fetchone()

if __name__ == '__main__':
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    main()
