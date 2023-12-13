# Bison Advisor

This is an undergraduate advising assistant whose goal is to streamline and enhance the academic advising experience for students, advisors, and institutions by leveraging the power of generative AI to create a personalized interface for each user.

## Features
- This chatbot utilizes the GPT-4 API from OpenAI.
- It is designed to provide responses in the context of undergraduate advising at Howard University.
- All interactions are kept in a session state, ensuring conversation continuity during the user's session.

## How to Run
1. Clone the repository.
2. Set the OpenAI API key in the Streamlit secrets manager.
3. Run the streamlit app using the command ```streamlit run app.py```

## Dependencies
To run this code, you need the following Python packages:

- openai
- streamlit
- streamlit-chat
- hashlib
- sqlite3
- pinecone
- os
- langchain
- sentence-transformers

### API Keys
The application uses the OpenAI API. You will need to obtain an API key from OpenAI and set it in the Streamlit secrets manager.

## Using the Application
Once the application is running, you can access the chatbot and use the input box to ask your question. After entering your question, hit Enter (or return) and the application will generate an answer and display it on the screen.

## Developer Info
This application is developed by three Howard University students: Hrishav Sapkota, Suprabhat Rijal and Biraj Dahal.

## Version Info
The current version of this application is 0.0.1.

## Disclaimer
This application is not optimized and may run out of OpenAI credits. 

Please use responsibly and in accordance with OpenAI's use-case policy.

## License
This project is licensed under Creative Commons Attribution Share-Alike.
