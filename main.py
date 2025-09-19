import os
import sys
import torch
import torchaudio
from fireredtts2.fireredtts2 import FireRedTTS2

device = "cuda"

fireredtts2 = FireRedTTS2(
    pretrained_dir="./pretrained_models/FireRedTTS2",
    gen_type="dialogue",
    device=device,
)

text_list = [
    "[S1]嗯，最近发现了一个很厉害的TTS系统叫FireRedTTS2。它最大的特点就是可以generate long conversational speech，支持multi-speaker dialogue generation。",
    "[S2]真的吗？那它跟其他的TTS有什么不同呢？",
    "[S1]这个system很特别，它可以支持3分钟的dialogue with 4 speakers，而且还有ultra-low latency。在L20 GPU上，first-packet latency只要140ms。最重要的是它支持multi lingual，包括English、Chinese、Japanese、Korean、French、German还有Russian。",
    "[S2]听起来很powerful啊。那它还有什么其他features吗？",
    "[S1]对，它还有zero-shot voice cloning功能，可以做cross-lingual和code-switching scenarios。而且还有random timbre generation，这个对creating ASR data很有用。最关键是stability很强，在monologue和dialogue tests里都有high similarity和low WER/CER。",
    "[S2]那这个是open source的吗？",
    "[S1]是的，它基于Apache 2.0 license。你可以在GitHub上找到FireRedTeam/FireRedTTS2，还有pre-trained checkpoints在Hugging Face上。不过要注意，voice cloning功能只能用于academic research purposes。",
]
prompt_wav_list = [
    "examples/chat_prompt/zh/S1.flac",
    "examples/chat_prompt/zh/S2.flac",
]

prompt_text_list = [
    "[S1]啊，可能说更适合美国市场应该是什么样子。那这这个可能说当然如果说有有机会能亲身的去考察去了解一下，那当然是有更好的帮助。",
    "[S2]比如具体一点的，他觉得最大的一个跟他预想的不一样的是在什么地方。",
]

all_audio, srt_text = fireredtts2.generate_dialogue(
    text_list=text_list,
    prompt_wav_list=prompt_wav_list,
    prompt_text_list=prompt_text_list,
    temperature=0.9,
    topk=30,
)
torchaudio.save("chat_clone.wav", all_audio, 24000)

# Save SRT file
with open("chat_clone.srt", "w", encoding="utf-8") as f:
    f.write(srt_text)
