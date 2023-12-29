import openai
import streamlit as st

# 패키지 추가(오디오 레코더, 파일삭제, 시간정보)
from audiorecorder import audiorecorder
import os
from datetime import datetime

# TTS, 음원재생 패키지 추가
from gtts import gTTS
import base64

# 기능 구현 함수
def STT(audio):
  filename = 'input.mp3'
  audio.export(filename, format='mp3')

  audio_file = open(filename, 'rb')

  # whisper 모델을 활용해 텍스트 얻기
  transcript = openai.Audio.transcribe('whisper-1', audio_file)
  audio_file.close()

  os.remove(filename)
  return transcript['text']

def ask_gpt(prompt, model):
  response = openai.ChatCompletion.create(model=model, messages=prompt)
  system_message = response['choices'][0]['message']
  return system_message['content']

def TTS(response):
  filename = 'output.mp3'
  tts = gTTS(text=response, lang='ko')
  tts.save(filename)

  # 음원 파일 자동 생성
  with open(filename, 'rb') as f:
    data = f.read()
    b64 = base64.b64encode(data).decode()
    md = f"""
        <audio autoplay="True">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """

    st.markdown(md, unsafe_allow_html=True,)
  os.remove(filename)

# 메인 함수
def main():
  st.set_page_config(
      page_title = '음성 비서 프로그램',
      layout='wide')

  # session_state 초기화
  if "chat" not in st.session_state:
    st.session_state["chat"] = []

  if "messages" not in st.session_state:
    st.session_state["messages"]=[{"role":"system",
                                   "content":"You are a thoughtful assistant. Respond to all input in 25 words and answer in korea"}]

  if "check_reset" not in st.session_state:
    st.session_state["check_reset"]=False

  # 제목 생성
  st.header('음성 비서 프로그램')
  st.markdown('---')

  with st.expander('음성비서 프로그램에 관하여', expanded=True):
    st.write(
        '''
        - 음성 비서 프로그램의 UI는 스트림릿을 활용했다.
        - STT(Speech-To-Text)는 OpenAI의 Whisper AI를 활용했다.
        ''')
  # 사이드바 생성
  with st.sidebar:
    openai.api_key = st.text_input(label='OPENAPI API 키', placeholder='Enter Your API Key', value='sk-', type='password')

    st.markdown('---')

    # GPT 모델을 선택하기 위한 라디오 버튼 생성
    model = st.radio(label='GPT 모델', options=['gpt-4','gpt-3.5-turbo'], index=1)

    st.markdown('---')

    # 리셋 버튼 생성
    if st.button(label='초기화'):
      st.session_state['chat']=[]
      st.session_state['message']=[{'role':'system',
                                    'content':'You are a thoughtful assistant. Respond to all input in 25 words and answer in korea'}]
      st.session_state["check_reset"]=True

  # 기능 구현 공간
  col1, col2= st.columns(2) # 두개의 영역으로 분할하기.
  with col1:
    # 왼쪽 영역 작성
    st.subheader('질문하기')
    audio = audiorecorder("클릭하여 녹음하기", "녹음중...") #(start, stop, pause)

    if (audio.duration_seconds > 0) and (st.session_state["check_reset"]==False):
      st.audio(audio.export().read())

      # 음원 파일에서 텍스트 추출
      question = STT(audio)
      # 텍스트 시각화 질문 내용 저장
      now = datetime.now().strftime('%H:%M')
      st.session_state['chat'] = st.session_state['chat'] + [('user', now, question)] # 질문 누적하기.

      # GPT 프롬프트 질문 내용 저장
      st.session_state['messages'] = st.session_state['messages'] + [{'role':'user', 'content': question}] # 응답 누적하기.

  with col2:
    # 오른쪽 영역 작성
    st.subheader('질문/답변')
    if (audio.duration_seconds > 0) and (st.session_state["check_reset"]==False):
      response = ask_gpt(st.session_state['messages'], model)

      # 프롬프트 답변 내용 저장
      st.session_state['messages'] = st.session_state['messages']+[{'role':'system', 'content': response}]

      # 텍스트 시각화 답변 내용 저장
      now = datetime.now().strftime('%H:%M')
      st.session_state['chat'] = st.session_state['chat']+[('bot',now,response)]

      # 채팅 형식으로 시각화 하기
      for sender, time, message in st.session_state['chat']:
        if sender == 'user':
          st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
          st.write("")
        else:
          st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
          st.write("")
      # gTTS를 활용하여 음성 파일 생성 및 재생
      TTS(response)
    else:
      st.session_state["check_reset"]=False



if __name__ == '__main__':
      main()
