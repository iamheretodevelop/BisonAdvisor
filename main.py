

import streamlit as st
import hashlib
import sqlite3
from openai import OpenAI
import pinecone
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from sentence_transformers import SentenceTransformer

def create_embeddings(texts):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings_list = model.encode(texts).tolist()
    return embeddings_list

def process_pdf(file_path):
    # create a loader
    loader = PyPDFLoader(file_path)
    # load your data
    data = loader.load()
    # Split your data up into smaller documents with Chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    documents = text_splitter.split_documents(data)
    # Convert Document objects into strings
    texts = [str(doc) for doc in documents]
    return texts
    

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
            role TEXT,
            email TEXT,       
            advisor TEXT,      
            student_id TEXT,
            major TEXT,
            current_standing TEXT,
            graduation_year TEXT,
            transcript BLOB
        )
    ''')


def add_userdata(username, password, role, email, advisor, student_id, major, current_standing, graduation_year, transcript):
    c.execute('INSERT INTO userstable(username, password, role, email, advisor, student_id, major, current_standing, graduation_year, transcript) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (username, password, role, email, advisor, student_id, major, current_standing, graduation_year, transcript))
    conn.commit()

def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE username = ? AND password = ?', (username, password))
    data = c.fetchall()
    return data

def view_all_users():
    c.execute('SELECT * FROM userstable')
    data = c.fetchall()
    return data

def initialize_deadlines_table():
    c.execute('CREATE TABLE IF NOT EXISTS deadlines(date TEXT, description TEXT)')
    c.execute('SELECT COUNT(*) FROM deadlines')
    if c.fetchone()[0] == 0:  
        deadlines = [("2023-12-25", "Christmas Break"), ("2024-01-10", "Start of Semester"), ("2024-02-01", "Scholarship Deadline")]
        c.executemany('INSERT INTO deadlines(date, description) VALUES (?, ?)', deadlines)
        conn.commit()

def initialize_advising_recommendations_table():
    c.execute('CREATE TABLE IF NOT EXISTS advising_recommendations(recommendation TEXT)')
    c.execute('SELECT COUNT(*) FROM advising_recommendations')
    if c.fetchone()[0] == 0: 
        recommendations = [("Enroll in Advanced Algorithms",), ("Meet with Advisor",), ("Update your resume",)]
        c.executemany('INSERT INTO advising_recommendations(recommendation) VALUES (?)', recommendations)
        conn.commit()

def chat_with_advisor():
    client = OpenAI()
    texts = process_pdf('./doc/CourseInfo.pdf')
    # setup pinecone
    index_name = "course-info"

    pinecone.init(api_key=os.environ['PINECONE_API_KEY'], environment='gcp-starter')
    index = pinecone.Index(index_name)

    st.title("Chat with BisonAdvisor")

    st.sidebar.markdown("Developed by Team 6.")
    st.sidebar.markdown("Current Version: 0.0.1")
    st.sidebar.markdown("Using GPT-4 API")
    st.sidebar.markdown("Not optimised")
    st.sidebar.markdown("May run out of OpenAI credits")

    MODEL = "gpt-3.5-turbo"


    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = MODEL

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "system",
            "content": f"""
            You are Bison Advisor an expert Historically Black College and University (HBCU) cultural historian.
            “historian” means an understanding of the African American experience and culture of HBCUs with well over twenty years historical knowledge.
            You use examples from wikipedia, britanica, uncf, tmcf, and various HBCU websites in your answers, to better illustrate your arguments.
            Your language should be for an 12 year old to understand.
            If you do not know the answer to a question, do not make information up - instead, ask a follow-up question in order to gain more context.
            Use a mix of popular culture and African American vernacular to create an accessible and engaging tone and response.
            Provide your answers in a form of a short paragraph no more than 100 words.
            Start by introducing yourself. You are given a bunch of Course information from Howard University as context use them to answer any question relating to course work. Answer only for Howard University. Answer in bullet points.
            """            },
            {
                "role": "user",
                "content": ""
            },
            {
                "role": "assistant",
                "content": ""
            }
        ]
        # for doc in  docs:
            # st.session_state.messages.append({"role": "system", "content":f"Course context: {doc}"})

    for message in st.session_state.messages:
        if message["role"] in ["user", "assistant"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Ask me advising based on current Transcript, and HU's CS Course Curriculum."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            query = st.session_state.messages[-1]["content"]

            embeddings = create_embeddings([query])[0]
            docs = index.query(embeddings, top_k=3)["matches"]
            message_placeholder = st.empty()
            full_response = ""
            for doc in docs:
                context = texts[int(doc["id"])]
                st.session_state.messages[0]["content"] += context
            for response in client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            ):
                cur_response = response.choices[0].delta.content
                full_response += cur_response if cur_response is not None else "" 
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})


def add_deadline(date, description):
    c.execute('INSERT INTO deadlines(date, description) VALUES (?, ?)', (date, description))
    conn.commit()

def get_deadlines():
    c.execute('SELECT * FROM deadlines')
    return c.fetchall()

def add_advising_recommendation(recommendation):
    c.execute('INSERT INTO advising_recommendations(recommendation) VALUES (?)', (recommendation,))
    conn.commit()

def get_advising_recommendations():
    c.execute('SELECT * FROM advising_recommendations')
    return c.fetchall()



def update_student_data(username, email, advisor, student_id, major, current_standing, graduation_year, transcript_file):
    if transcript_file is not None:
        transcript = transcript_file.read()
    else:
        transcript = None

    with conn:
        c.execute('''
        UPDATE userstable SET 
        email = ?, advisor = ?, student_id = ?, major = ?, current_standing = ?, graduation_year = ?, transcript = ? 
        WHERE username = ?
    ''', (email, advisor, student_id, major, current_standing, graduation_year, transcript, username))

def get_user_data(username):
    c.execute('SELECT * FROM userstable WHERE username = ?', (username,))
    return c.fetchone()

def main():
    initialize_deadlines_table()
    initialize_advising_recommendations_table()
    st.title("Bison Advisor")

    menu = ["Home", "Login", "Sign Up", "Profile", "Chat with AI Advisor"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Home")
        if 'username' in st.session_state and st.session_state['username'] is not None:
            st.write(f"Welcome to the Bison Advisor, {st.session_state['username']}!")
            st.write("You have a personalized advising system that uses generative AI to provide Academic recommendations and resources.")
            col1, col2 = st.columns(2) 
            with col1:
                st.markdown("## Upcoming Deadlines and Milestones")
                for deadline in get_deadlines():
                    st.info(f"{deadline[0]}: {deadline[1]}")
                st.markdown("## Self-Service Resources")
                st.markdown("[Academic Policies](https://cea.howard.edu/resources/academic-policies-and-procedures#:~:text=Students%20must%20maintain%20a%20cumulative,be%20followed%20by%20academic%20suspension)")
                st.markdown("[Course Catalog](https://catalogue.howard.edu/computer-science/computer-science-bs)")
                st.markdown("[Degree Requirements](https://cea.howard.edu/academics/departments/electrical-engineering-and-computer-science/undergraduate/bscs#:~:text=Bachelor%20of%20Science%20in%20Computer,Mathematics%2C%20Science%20and%20Liberal%20Arts)")

            with col2:
                st.markdown("## Academic Advising Recommendations")
                for recommendation in get_advising_recommendations():
                    st.success(recommendation[0])
                st.markdown("## Communication Platform")
                st.write("Notifications: Enabled")
                st.write("Messaging: Active")
                st.write("Appointment Scheduling: Available")
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
            else:
                st.warning("Incorrect Username/Password")

    elif choice == "Sign Up":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type='password')
        new_role = st.radio("Select Role", ["Student", "Teacher", "Administrator"])

        if st.button("Check Username Availability"):
            create_usertable()
            user_data = get_user_data(new_user)
            if user_data:
                st.warning("Username already exists. Please choose a different username.")
            else:
                st.success("Username is available!")

        new_student_id = st.text_input("ID")
        new_major = st.text_input("Major" if new_role == "Student" else "Department")
        new_advisor = None
        if new_role == "Student":
            advisor_options = ["Legand Burge", "Jeremy Blackstone", "Brandon Ash", "Ladan Johnson"]
            new_advisor = st.selectbox("Select Advisor", [""] + advisor_options)

        new_current_standing = st.selectbox("Current Standing" if new_role == "Student" else "Job Position", [""] + ["Freshman", "Sophomore", "Junior", "Senior"] if new_role == "Student" else [""] + ["Assistant Professor", "Associate Professor", "Professor", "Teaching Assistant", "Non-teaching Acadmic Advisor"] if new_role == "Teacher" else [""] + ["Admin User", "Super User"])
        new_graduation_year = st.text_input("Graduation Year" if new_role == "Student" else "Employment Year")
        new_transcript = st.file_uploader("Upload Transcript", type=['pdf']) if new_role == "Student" else None

        if st.button("Sign Up"):
            user_data = get_user_data(new_user)
            if user_data:
                st.warning("Username already exists. Please choose a different username.")
            else:
                create_usertable()
                if new_transcript:
                    new_transcript = new_transcript.read()
                add_userdata(new_user, make_hashes(new_password), new_role, new_email, new_advisor, new_student_id, new_major, new_current_standing, new_graduation_year, new_transcript)
                st.success("You have successfully created a valid Account")
                st.info("Go to Login Menu to login")
        elif choice == "Chat with AI Advisor":
            if 'username' in st.session_state and st.session_state['username'] is not None:
                st.subheader("AI Advising")
                chat_with_advisor()
            else:
                st.warning("Please login to view this page")

    elif choice == "Profile":
        st.subheader("Profile")
        if 'username' in st.session_state and st.session_state['username'] is not None:
            st.write(f"Welcome to your profile, {st.session_state['username']}!")
            user_data = get_user_data(st.session_state['username'])
            if user_data:
                username, _, role, email, advisor, student_id, major, current_standing, graduation_year, transcript = user_data
                st.write(f"Your role is of {role}!")
                st.text_input("Email", value=email, disabled=True)
                if role == "Student":
                    advisor_options = ["Legand Burge", "Jeremy Blackstone", "Brandon Ash", "Ladan Johnson"]
                    st.selectbox("Advisor", advisor_options, index=advisor_options.index(advisor) if advisor in advisor_options else 0, disabled=False)
                st.text_input("Username", value=username, disabled=True)
                st.radio("Role", ["Student", "Teacher", "Administrator"], index=["Student", "Teacher", "Administrator"].index(role), disabled=True)
                new_student_id = st.text_input("ID", value=student_id)
                new_major = st.text_input("Major/Department", value=major)

                status_options = {
                    "Student": ["Freshman", "Sophomore", "Junior", "Senior"],
                    "Teacher":  ["Assistant Professor", "Associate Professor", "Professor", "Teaching Assistant", "Non-teaching Academic Advisor"],
                    "Administrator": ["Admin User", "Super User"]
                }

                if current_standing in status_options[role]:
                    current_standing_index = status_options[role].index(current_standing)
                else:
                    current_standing_index = 0

                new_current_standing = st.selectbox("Status", status_options[role], index=current_standing_index)
                new_graduation_year = st.text_input("Graduation Year/Employment Year", value=graduation_year)

                if role == "Student" and transcript:
                    st.download_button(label="Download Transcript", data=transcript, file_name="transcript.pdf", mime='application/octet-stream')

                if st.button("Update Profile"):
                    update_student_data(username, email, advisor, new_student_id, new_major, new_current_standing, new_graduation_year, transcript)
                    st.success("Profile Updated")

                if st.button("Sign Out"):
                    del st.session_state['username']
                    st.info("You have been signed out.")
                    st.experimental_rerun()

            else:
                st.warning("No user data found.")
        else:
            st.warning("Please login to view this page")



if 'username' not in st.session_state:
    st.session_state['username'] = None
main()