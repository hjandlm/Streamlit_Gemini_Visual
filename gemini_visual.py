'''
Description:  
Author: HJ
Date: 2023-12-17 09:53:34
'''
import streamlit as st
import google.generativeai as genai
import dataclasses
from PIL import Image

def clear_btn():
    del st.session_state.messages
    del st.session_state.image
    
@dataclasses.dataclass
class GenerationConfig:
    max_output_tokens: int
    temperature: float
    top_p: float
    top_k: int

def set_config():
    model_config = {}
    model_image = {'model_name':'', 'image':None,'chat_turn':None,'safety_settings':{}}
    with st.sidebar:
        model_name = st.selectbox(
            'Select gemini model:',
            ['Gemini Pro', 'Gemini Pro Vision'],
            index = 0
        )
        if model_name=='Gemini Pro':
            chat_turn = st.selectbox(
                'Select conversation turn',
                ('Single-turn Conversation', 'Multi-turn Conversation'),
                index=0
            )
            model_image['chat_turn'] = chat_turn
        with st.expander("Safety settings"):
            harassment = st.selectbox(
                "Harassment", 
                ['unspecified', 'low', 'medium', 'high', 'block_none'],
                index = 2
            )
            hate = st.selectbox(
                "Hate Speech",
                ['unspecified', 'low', 'medium', 'high', 'block_none'],
                index = 2
            )
            sexual = st.selectbox(
                "Sexually Explicit", 
                ['unspecified', 'low', 'medium', 'high', 'block_none'],
                index = 2
            )
            danger = st.selectbox(
                "Dangerous Content", 
                ['unspecified', 'low', 'medium', 'high', 'block_none'],
                index = 2
            )
        
        output_len = st.slider(
            'Output Length',0, 4096, 1024,step=1
        )
        temperature = st.slider(
            'Temperature', 0.0, 2.0, 0.8, step=0.01
        )
        top_p = st.slider(
            'Top P', 0.0, 1.0, 0.9, step=0.01
        )
        top_k = st.slider(
            'Top K', 0, 64, 16, step=1
        )
        st.button("Clear Chat History", on_click=clear_btn)
        if model_name=='Gemini Pro Vision':
            image_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
            model_image['image'] = image_file
            
    model_image['model_name'] = model_name
    model_image['safety_settings']['harassment'] = harassment
    model_image['safety_settings']['hate'] = hate
    model_image['safety_settings']['sexual'] = sexual
    model_image['safety_settings']['danger'] = danger
    model_config['max_output_tokens'] = output_len
    model_config['temperature'] = temperature
    model_config['top_p'] = top_p
    model_config['top_k'] = top_k
    
    return model_config,model_image
    
def chat(query,model_name,model_config,api_key,safety_settings,history=None):
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(model_name=model_name,generation_config=model_config)
    if history is not None:
        history.append({'role':'user','parts':[query]})
        response = model.generate_content(history, safety_settings=safety_settings)
    else:
        response = model.generate_content(query,safety_settings=safety_settings)

    return response.text
        
if __name__=="__main__":
    GOOGLE_API_KEY=''
    
    user_avator = "🧑‍💻"
    robot_avator = "🤖"
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if 'image' not in st.session_state:
        st.session_state.image = []
        
    model_config, model_image = set_config()
    model_name = model_image['model_name']
    image_file = model_image['image']
    safety_settings = model_image['safety_settings']
    chat_turn = model_image['chat_turn']
    if st.session_state.messages and model_name != st.session_state.messages[-1].get("model_name"):
        st.session_state.messages = []
    
    st.header(f'Google: Gemini Model')
    if model_name=='Gemini Pro':
        history = []
        if chat_turn=='Multi-turn Conversation':
            for message in st.session_state.messages:
                with st.chat_message(message["role"], avatar=message.get("avatar")):
                    st.markdown(message["content"])
                    role = message['role']
                    if role=='robot':
                        role = 'model'
                    history.append({'role':role,'parts':[message["content"]]})
        else:
            for message in st.session_state.messages:
                with st.chat_message(message["role"], avatar=message.get("avatar")):
                    st.markdown(message["content"])
        if user_query := st.chat_input("Please enter content......"):
            with st.chat_message("user", avatar=user_avator):
                st.markdown(user_query)
            st.session_state.messages.append({"role": "user", "content": user_query, "avatar": user_avator, "model_name":model_name})
            with st.chat_message("robot", avatar=robot_avator):
                message_placeholder = st.empty()
                if chat_turn=='Single-turn Conversation':
                    cur_response = chat(query=user_query,model_name=model_name,model_config=model_config,api_key=GOOGLE_API_KEY)
                elif chat_turn=='Multi-turn Conversation':
                    history.append({'role':'user','parts':user_query})
                    cur_response = chat(query=user_query,model_name=model_name,model_config=model_config,api_key=GOOGLE_API_KEY,history=history)
                message_placeholder.markdown(cur_response)
            st.session_state.messages.append({"role": "robot", "content": cur_response, "avatar": robot_avator, "model_name":model_name})
    elif model_name=='Gemini Pro Vision':
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar=message.get("avatar")):
                try:
                    image = Image.open(message["content"])
                    st.image(image, use_column_width=True)
                except Exception:
                    st.markdown(message["content"])
        if user_query := st.chat_input("Please enter content......"):
            with st.chat_message("user", avatar=user_avator):
                if not st.session_state.image and image_file is not None:
                    st.session_state.image.append(image_file)
                    image = Image.open(image_file)
                    st.image(image, use_column_width=True)
                    st.markdown(user_query)
                    st.session_state.messages.append({"role": "user", "content": image_file, "avatar": user_avator, "model_name":model_name})
                    st.session_state.messages.append({"role": "user", "content": user_query, "avatar": user_avator, "model_name":model_name})
                    
                elif isinstance(image_file,st.runtime.uploaded_file_manager.UploadedFile) and image_file!=st.session_state.image[-1]:
                    st.session_state.image.append(image_file)
                    image_file = st.session_state.image[-1]
                    image = Image.open(image_file)
                    st.image(image, use_column_width=True)
                    st.markdown(user_query)
                    st.session_state.messages.append({"role": "user", "content": image_file, "avatar": user_avator, "model_name":model_name})
                    st.session_state.messages.append({"role": "user", "content": user_query, "avatar": user_avator, "model_name":model_name})
                else:
                    st.markdown(user_query)
                    st.session_state.messages.append({"role": "user", "content": user_query, "avatar": user_avator, "model_name":model_name})
            if st.session_state.messages!=[]:
                
                if not isinstance(st.session_state.messages[0]['content'],st.runtime.uploaded_file_manager.UploadedFile):
                    st.session_state.messages = []
                    st.error('Add an image to use Gemini Pro Vision, or switch your model to a text model (Gemini Pro)', icon="🚨")
                else:
                    with st.chat_message("robot", avatar=robot_avator):
                        message_placeholder = st.empty()
                        image_file = st.session_state.image[-1]
                        image = Image.open(image_file)
                        cur_response = chat(query=[user_query,image],model_name=model_name,model_config=model_config,api_key=GOOGLE_API_KEY)
                        message_placeholder.markdown(cur_response)
                    st.session_state.messages.append({"role": "robot", "content": cur_response, "avatar": robot_avator,"model_name":model_name})
        


