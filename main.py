from openai import OpenAI
import asyncio
import os
import streamlit as st
from dotenv import load_dotenv
from agents import (
    Runner,
    SQLiteSession,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)
from agents.voice import AudioInput, VoicePipeline
from models import UserAccountContext
from my_agents.triage_agent import triage_agent
from my_agents.account_agent import account_agent
from my_agents.billing_agent import billing_agent
from my_agents.order_agent import order_agent
from my_agents.technical_agent import technical_agent
import numpy as np
import wave, io
from workflow import CustomWorkflow
import sounddevice as sd

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

user_account_ctx = UserAccountContext(
    customer_id=1,
    name="henry",
    email="henry@example.com",
    tier="basic",
)


if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "customer-support-memory.db",
    )
session = st.session_state["session"]

if "agent" not in st.session_state:
    st.session_state["agent"] = triage_agent


def convert_audio(audio_input):
    audio_data = audio_input.getvalue()
    with wave.open(io.BytesIO(audio_data), "rb") as wav_file:
        audio_frames = wav_file.readframes(-1)
    return np.frombuffer(
        audio_frames,
        dtype=np.int16,
    )


async def run_agent(audio_input):
    with st.chat_message("ai"):
        status_container = st.status("⏳ Processing voice message...")
        try:
            audio_array = convert_audio(audio_input)
            audio = AudioInput(buffer=audio_array)
            workflow = CustomWorkflow(context=user_account_ctx)
            pipeline = VoicePipeline(workflow=workflow)

            status_container.update(label="Running workflow", state="running")

            result = await pipeline.run(audio)

            player = sd.OutputStream(
                samplerate=24000,
                channels=1,
                dtype=np.int16,
            )
            player.start()

            status_container.update(state="complete")

            async for event in result.stream():
                if event.type == "voice_stream_event_audio":
                    player.write(event.data)

        except InputGuardrailTripwireTriggered:
            st.write("I can't help you with that.")
        except OutputGuardrailTripwireTriggered:
            st.write("Cant show you that answer.")
            st.session_state["text_placeholder"].empty()


audio_input = st.audio_input(
    "Record your message",
)

if audio_input:
    with st.chat_message("human"):
        st.audio(audio_input)
    asyncio.run(run_agent(audio_input))


with st.sidebar:
    reset = st.button("Reset memory")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))