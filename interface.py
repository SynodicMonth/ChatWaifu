# gradio chat interface
import gradio as gr
import openai
import time
from PIL import Image, ImageDraw
import re
import requests
import io
import base64
import yaml
import os
import copy
from mychatbot import MyChatbot
from chatgpt import ask_chatgpt

# put your openai api key in openai_api_key.txt
if not os.path.exists("./presets"):
    raise Exception("Put your openai api key in ./openai_api_key.txt")
openai.api_key = open("./openai_api_key.txt", "r").read().strip()
# regex to find pose_desc
pattern = re.compile(r"\(<(?:[\w,'-]+\s*)+>\)")
# url of the diffusion webui server
url = "http://127.0.0.1:7861"
# config file path
config_path = "./config.yaml"
# default image when no image is provided
default_img = Image.open("./pics/default.png")
# log file path
log_file = "./log.txt"
# text to be displayed in debug mode
debug_text = """文本测试 **Markdown测试** 空集 $\\varnothing$
$\\frac{-b\\pm\\sqrt{b^2-4ac}}{2a}$
 - list
 - list
    - list
```python
def load_presets():
    # if there is a directory named "presets", load all the presets
    if not os.path.exists("./presets"):
        raise Exception("no presets directory found")
    else:
        for file in os.listdir("./presets"):
            if file.endswith(".yaml"):
                with open(f"./presets/{file}", "r", encoding='utf-8') as f:
                    yaml_content = yaml.load(f, Loader=yaml.FullLoader)
                    presets[yaml_content["id"]] = yaml_content
        if len(presets) == 0:
            raise Exception("no presets found, please put yaml files in the presets directory")
    print(f"loaded {len(presets)} presets")
```
 1. list
 2. list
    1. list
"""
max_interaction = 5

# notice to be displayed in the interface
notice = "**工程早期测试阶段alpha-0.4，GPT回复时间大概5s，绘图约为0.5s/step，请耐心等待，不要多次发送，代码高亮已经实现，latex还未实现，敬请期待。**"
# additional css file path
additional_css = "./additional.css"
presets = {}

def load_presets():
    # if there is a directory named "presets", load all the presets
    if not os.path.exists("./presets"):
        raise Exception("no presets directory found")
    else:
        for file in os.listdir("./presets"):
            if file.endswith(".yaml"):
                with open(f"./presets/{file}", "r", encoding='utf-8') as f:
                    yaml_content = yaml.load(f, Loader=yaml.FullLoader)
                    presets[yaml_content["id"]] = yaml_content
        if len(presets) == 0:
            raise Exception("no presets found, please put yaml files in the presets directory")
    print(f"loaded {len(presets)} presets")

def ask_diffusion(description, config):
    prompt = presets[config["character_preset"]]["diffusion_positive_prompt"] + '(((' + description + ')))'
    negative_prompt = presets[config["character_preset"]]["diffusion_negative_prompt"]
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": config["diffusion_steps"],
        "cfg_scale": config["diffusion_cfg_scale"],
        "width": config["diffusion_width"],
        "height": config["diffusion_height"],
        "sampler_index": config["diffusion_sampler"],
    }
    sd_response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
    r = sd_response.json()
    if 'images' in r:
        image = Image.open(io.BytesIO(base64.b64decode(r['images'][0].split(",",1)[0])))
        print("diffusion solved, pose_desc:", description)
    else:
        # generate a error image
        image = Image.new("RGB", (448, 640), (255, 255, 255))
        img_draw = ImageDraw.Draw(image)
        img_draw.text((10, 10), "ERROR", fill=(0, 0, 0))
        print("diffusion failed, pose_desc:", description)
    return image

def write_log(log_file: str, user_text: str, response_text: str):
    with open(log_file, 'a', encoding='utf-8') as file:
        file.writelines(['[Time]: ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n', 
                        '[User]: ' + user_text + '\n',
                        '[Response]: ' + response_text + '\n'])
    
def predict(txt, raw_history, name, config):
    if not name:
        name = "朔月"
    if config["debug"]: # debug mode
        response_text = debug_text + "你的名字是：" + name
        # generate a blank image with time
        img = Image.new("RGB", (448, 640), (255, 255, 255))
        img_draw = ImageDraw.Draw(img)
        img_draw.text((10, 10), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), fill=(0, 0, 0))
    else:
        if config["enable_chatgpt"]:
            # predict the response
            system_prompt = presets[config["character_preset"]]["system_prompt"]
            example = (presets[config["character_preset"]]["ai_nickname"] + "你好！",
                       f"(<school uniform, waving at viewer, smiling, greeting, energetic>) 你好呀，{name}！")
            history = raw_history[-max_interaction:] if len(raw_history) > max_interaction else raw_history
            temperature = config["chatgpt_temperature"]
            try:
                raw_response = ask_chatgpt(system_prompt, txt, example, history, temperature)
                # write log
                write_log(log_file, txt, raw_response)
                print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), txt, raw_response)

                regex_result = pattern.findall(raw_response)
                response_text = raw_response
                for text in regex_result:
                    response_text = response_text.replace(text, '')
                regex_result = [text[2:-2] for text in regex_result]
                pose_desc = ''.join(regex_result)
            except Exception as e:
                print(e)
                response_text = str(e)
                pose_desc = ""
        else:
            pose_desc = txt
            response_text = "~"
        
        if config["enable_diffusion"]:
            try:
                img = ask_diffusion(pose_desc, config)
            except Exception as e:
                print(e)
                img = Image.new("RGB", (448, 640), (255, 255, 255))
                img_draw = ImageDraw.Draw(img)
                img_draw.text((10, 10), str(e), fill=(0, 0, 0), language='zh')
        else:
            # img = Image.new("RGB", (448, 640), (255, 255, 255))
            img = default_img

    raw_history.append((txt, response_text))
    return copy.deepcopy(raw_history), raw_history, img

def clear_state(state, chat):
    return [], []

if __name__ == "__main__":
    # load presets
    load_presets()
    # set up the interface
    with gr.Blocks(title="ChatWaifu", css=additional_css) as main_block:
        config = gr.State(value=yaml.load(open(config_path, "r", encoding='utf-8'), Loader=yaml.FullLoader))
        with gr.Tabs(elem_id="tabs") as tabs:
            with gr.TabItem(label="Chatting"):
                title = gr.Markdown(notice)
                raw_history = gr.State([])
                with gr.Row():
                    with gr.Column(scale=0.7):
                        chat = MyChatbot(elem_id="chatbot")
                        txt = gr.Textbox(show_label=False, placeholder="Type here...").style(container=False)
                        # dream = gr.Textbox(show_label=False, placeholder="Only draw image...").style(container=False)
                
                    with gr.Column(scale=0.3):
                        name = gr.Textbox(label="Your name?", show_label=True, placeholder="想让AI怎么称呼你呢？")
                        img = gr.Image(value=default_img, shape=(448, 640), show_label=False, interactive=False)
                txt.submit(predict, [txt, raw_history, name, config], [chat, raw_history, img], show_progress=False, api_name="chatting")
                txt.submit(lambda x: '', [txt], [txt], show_progress=False)

            with gr.TabItem(label="Setting"):
                title = gr.Markdown("**设置**")
                button_apply_settings = gr.Button(value="Apply settings", variant='primary', elem_id="button_apply_settings")
                with gr.Row():
                    with gr.Column(scale=0.5):
                        dropdown_character = gr.Dropdown(value=config.value["character_preset"], label="Character", choices=list(presets.keys()), elem_id="dropdown_character", interactive=True)
                        checkbox_chatgpt = gr.Checkbox(value=config.value["enable_chatgpt"], label="Enable ChatGPT Response Pass", elem_id="checkbox_chatgpt", interactive=True)
                        checkbox_diffusion = gr.Checkbox(value=config.value["enable_diffusion"], label="Enable Diffusion Image Pass", elem_id="checkbox_diffusion", interactive=True)
                        checkbox_debug = gr.Checkbox(value=config.value["debug"], label="Enable Debug Mode", elem_id="checkbox_debug", interactive=True)
                        
                        slider_steps = gr.Slider(value=config.value["diffusion_steps"], label="Diffusion Steps", minimum=10, maximum=50, step=1, elem_id="slider_steps", interactive=True)
                        slider_cfg = gr.Slider(value=config.value["diffusion_cfg_scale"], label="Diffusion Cfg Scale", minimum=0, maximum=30, step=1, elem_id="slider_cfg", interactive=True)
                        slider_width = gr.Slider(value=config.value["diffusion_width"], label="Diffusion Image Width", minimum=64, maximum=768, step=64, elem_id="slider_width", interactive=True)
                        slider_height = gr.Slider(value=config.value["diffusion_height"], label="Diffusion Image Height", minimum=64, maximum=768, step=64, elem_id="slider_height", interactive=True)
                        sampler_option = ['Euler a', 'Euler', 'LMS', 'Heun', 'DPM2', 'DPM2 a', 'DPM++ 2S a', 'DPM++ 2M', 'DPM++ SDE', 'DPM fast', 'DPM adaptive', 'LMS Karras', 'DPM2 Karras', 'DPM2 a Karras', 'DPM++ 2S a Karras', 'DPM++ 2M Karras', 'DPM++ SDE Karras', 'DDIM', 'PLMS']
                        dropdown_sampler = gr.Dropdown(value=config.value["diffusion_sampler"], label="Diffusion Sampler", choices=sampler_option, elem_id="dropdown_sampler", interactive=True)

                        # text_pos_prompt = gr.Textbox(value=config.value["diffusion_positive_prompt"], label="Diffusion Positive Prompt", show_label=True, elem_id="text_pos_prompt", interactive=True)
                        # text_neg_prompt = gr.Textbox(value=config.value["diffusion_negative_prompt"], label="Diffusion Negative Prompt", show_label=True, elem_id="text_neg_prompt", interactive=True)
                        # text_ai_nickname = gr.Textbox(value=config.value["ai_nickname"], label="AI Nickname", show_label=True, elem_id="text_ai_nickname", interactive=True)
                        # text_sys_prompt = gr.Textbox(value=config.value["system_prompt"], label="ChatGPT System Prompt", show_label=True, elem_id="text_sys_prompt", interactive=True)

                        slider_temperature = gr.Slider(value=config.value["chatgpt_temperature"], label="ChatGPT Temperature", minimum=0.0, maximum=1.0, step=0.1, elem_id="slider_temperature", interactive=True)


                    
                    with gr.Column(scale=0.5):
                        json = gr.JSON(config.value, show_label=False, interactive=False)

                    components = [(dropdown_character, "character_preset"),
                                    (checkbox_chatgpt, "enable_chatgpt"),
                                    (checkbox_diffusion, "enable_diffusion"),
                                    (checkbox_debug, "debug"),
                                    (slider_steps, "diffusion_steps"),
                                    (slider_cfg, "diffusion_cfg_scale"),
                                    (slider_width, "diffusion_width"),
                                    (slider_height, "diffusion_height"),
                                    (dropdown_sampler, "diffusion_sampler"),
                                    # (text_pos_prompt, "diffusion_positive_prompt"),
                                    # (text_neg_prompt, "diffusion_negative_prompt"),
                                    # (text_ai_nickname, "ai_nickname"),
                                    # (text_sys_prompt, "system_prompt"),
                                    (slider_temperature, "chatgpt_temperature")]
                    
                    for component, key in components:
                        component.change(lambda x, config, key=key: config.update({key: x}), [component, config], [], show_progress=False)
                    dropdown_character.change(clear_state, [raw_history, chat], [raw_history, chat], show_progress=False)

                button_apply_settings.click(lambda x: x, [config], [json], show_progress=False)

    # Link Start!!!!!!!!
    main_block.launch(server_name="0.0.0.0")
