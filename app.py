# First
import openai 
import streamlit as st
import requests
import json
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
openai_api_key = st.secrets.OPENAI_API_KEY
vectara_key = st.secrets.VECTARA_KEY
st.title("LAW-IO-BUDDY ⚖️ ")

st.session_state.k1 = 0

st.sidebar.title("Customization Options")

st.subheader(
    "Legal-related PDF personified as your own :blue[Law assistant]",
)
    

customization_options = {
        "country": st.sidebar.selectbox("Select Country", ["INDIA", "USA", "UK"]),
        "info":st.sidebar.info('Select ChatGPT option to merge both document and legal database of the Country', icon="ℹ️"),
        "use_chatgpt":st.sidebar.radio("Use ChatGPT", ["No", "Yes"]),
        "words": st.sidebar.slider("Number of words", 0, 750, 50),
        "src": st.sidebar.radio("Show Source of Text", ["No", "Yes"])
    }

if st.button("Clear Cache"):
    st.cache_data.clear()
    st.write("Cache has been cleared")

country_cid = {"INDIA": 5, "USA": 6, "UK": 7}
all_country_api = "zwt_h_p6lWnM5xwLO7Cd-3T6HPyphP7F78VOtZTPTg"

doc_api = 'zqt_h_p6lQhsZWuoy4Sqp095iRReJOJhH3c6D7m1og'


llm = ChatOpenAI(temperature=0.9, openai_api_key = openai_api_key)

def query_gpt(lawtext, text, query):
    nwords = customization_options['words']
    prompt = "Using the above " + lawtext + "and the current information related to it " + text + "answer the queestion given below {query} in " + str(nwords) + " do not say you dont have enough information, answer with provided information"
    prompt = ChatPromptTemplate.from_template(prompt)

    chain = LLMChain(llm=llm, prompt=prompt)

    output = chain.run(query)

    return output



def query_vectara(corpus_id, query, api):
    url = "https://api.vectara.io/v1/query"
    payload = json.dumps({
    "query": [
        {
        "query": query,
        "start": 0,
        "numResults": 3,
        "contextConfig": {
            "charsBefore": 30,
            "charsAfter": 30,
            "sentencesBefore": 3,
            "sentencesAfter": 3,
            "startTag": "<b>",
            "endTag": "</b>"
        },
        "corpusKey": [
            {
            "customerId": 0,
            "corpusId": corpus_id,
            "semantics": "DEFAULT",
            "dim": [
                {
                "name": "string",
                "weight": 0
                }
            ],
            "metadataFilter": "part.lang = 'eng'",
            "lexicalInterpolationConfig": {
                "lambda": 0
            }
            }
        ],
        "rerankingConfig": {
            "rerankerId": 272725717
        },
        "summary": [
        {
          "summarizerPromptName": "vectara-summary-ext-v1.2.0",
          "maxSummarizedResults": 5,
          "responseLang": "en"
        }
        ]
        }
    ]
    })
    headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'customer-id': '2281339541',
    'x-api-key': api
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    k = response.text
    k = json.loads(k)

    return k 

# extract summary and all text 

def extract_from_vectara(vectera_response):
    summary = vectera_response['responseSet'][0]['summary'][0]['text']

    # all text
    all_text = ""
    for i in vectera_response['responseSet'][0]['response']:
        all_text = all_text + i['text'] + '\n'

    return summary, all_text

def reset_corpus(corpus_id):
    url = "https://api.vectara.io/v1/reset-corpus"
    payload = json.dumps({
    "corpusId": corpus_id
    })
    headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'customer-id': '2281339541',
    'Authorization': 'Bearer {}'.format(vectara_key)
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response


def upload_file(file, filename):
    post_headers = {
        "Authorization": "Bearer {}".format(vectara_key),
    }
    response = requests.post(
        f"https://api.vectara.io/v1/upload?c=2281339541&o=4",
        files={"file": (filename ,file , 'application/octet-stream')},
        verify=True,
        headers=post_headers)

    if response.status_code != 200:
        return response, False
    return response, True

@st.cache_data()
def uploader(uploaded_file):
    
    if uploaded_file and st.session_state.k1 == 0:

        progress_bar = st.progress(0)
        res = reset_corpus(4)
        progress_bar.progress(30)
        # st.write(res)
        progress_bar.progress(45)
        binary_file = uploaded_file.read()

        filename = uploaded_file.name 

        response = upload_file(binary_file, filename)
        progress_bar.progress(75)
        # st.write(response)

        st.session_state.k1 +=1
        progress_bar.progress(100)
        info = st.info('If your questions do not load please wait a few seconds for the document to get processed in the backend', icon="ℹ️")
        return True


def main():
    k = 0
    uploaded_file = st.file_uploader("Upload a file", type=["txt", "pdf", "png", "jpg", "jpeg"])

    m = uploader(uploaded_file)

    if 1:
    # st.write(response)
        if "messages" not in st.session_state.keys(): # Initialize the chat messages history
            st.session_state.messages = [{"role": "assistant", "content": "Ask me anything about the law!"}]

        if prompt := st.chat_input("Your question"): # Prompt for user input and save to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

        for message in st.session_state.messages: # Display the prior chat messages
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # If last message is not from assistant, generate a new response
        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    resp = query_vectara(4, prompt, doc_api)
                    msg, texts = extract_from_vectara(resp)
                    # st.write(resp)
                    cid = country_cid[customization_options['country']]
                    # resp = query_vectara(cid, prompt, all_country_api)
                    # msg, texts = extract_from_vectara(resp)
                    if customization_options["use_chatgpt"] == "Yes":
                        cid = country_cid[customization_options['country']]
                        resp1 = query_vectara(cid, prompt, all_country_api)
                        msg1, texts1 = extract_from_vectara(resp1)
                        msg = query_gpt(texts1[:1024], texts[:1024], prompt)

                    st.write(msg)
                    message = {"role": "assistant", "content": msg}
                    st.session_state.messages.append(message) 



if __name__ == "__main__":
    main()
