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


# put your openai api key in openai_api_key.txt
openai.api_key = open("./openai_api_key.txt", "r").read().strip()
pattern = re.compile(r"\(<(?:[\w,'-]+\s*)+>\)")
url = "http://127.0.0.1:7861"
config_path = "./config.yaml"
default_img = Image.open("./default.png")
# config = yaml.load(open(config_path, "r"), Loader=yaml.FullLoader)

def ask_diffusion(pose_desc, config):
    # print("她" + response_text.replace(pose_desc, ''))
    negative_prompt = config["diffusion_negative_prompt"]
    prompt = config["diffusion_positive_prompt"] + '(((' + pose_desc + ')))'
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": config["diffusion_steps"],
        "cfg_scale": 18,
        "width": 448,
        "height": 640,
        "sampler_index": "Euler a"
    }
    # print("waiting for diffusion...")
    sd_response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
    r = sd_response.json()
    if 'images' in r:
        image = Image.open(io.BytesIO(base64.b64decode(r['images'][0].split(",",1)[0])))
        print("diffusion solved, pose_desc:", pose_desc)
    else:
        image = Image.new("RGB", (448, 640), (255, 255, 255))
        img_draw = ImageDraw.Draw(image)
        img_draw.text((10, 10), "ERROR", fill=(0, 0, 0))
        print("diffusion failed, pose_desc:", pose_desc)
    return image

def predict(txt, state, name, config):
    # print(config)
    if not name:
        name = "朔月"
    if not config["debug"]:
        if config["enable_chatgpt"]:
            # predict the response
            messages=[
                {"role": "system","content": config["system_prompt"]},
                {"role": "user", "content": config["ai_nickname"] + "早上好！"},
                {"role": "assistant", "content": f"(<school uniform, waving at viewer, smiling, greeting, energetic>) {name}，早上好呀！"},
                {"role": "user", "content": txt}
                ]
            response = openai.ChatCompletion.create(
                model = "gpt-3.5-turbo",
                messages = messages,
                temperature = config["chatgpt_temperature"])
            response_text = response["choices"][0]['message']['content'].replace('\u000bar', '').replace('\t', '\\t').replace('\r', '\\r').strip()
            print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), txt, response_text)
            regex_result = pattern.findall(response_text)
            for text in regex_result:
                response_text = response_text.replace(text, '')
            regex_result = [text[2:-2] for text in regex_result]
            pose_desc = ''.join(regex_result)
        else:
            pose_desc = txt
            response_text = "~"
        
        if config["enable_diffusion"]:
            img = ask_diffusion(pose_desc, config)
        else:
            img = Image.new("RGB", (448, 640), (255, 255, 255))
        # img = Image.open("./00067-3417598286-masterpiece,b.png")
    else:
        response_text = "文本测试 **Markdown测试** $\\frac{-b\\pm\\sqrt{b^2-4ac}}{2a}$ 你的名字是：" + name
        # generate a blank image
        img = Image.new("RGB", (448, 640), (255, 255, 255))
        # draw the timestamp usin PIL
        img_draw = ImageDraw.Draw(img)
        img_draw.text((10, 10), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), fill=(0, 0, 0))
    state.append((txt, response_text))
    return state, state, img

# set up the interface
with gr.Blocks(title="ChatWaifu", css=r"#chatbot {height: 500px;}") as main_block:
    config = gr.State(value=yaml.load(open(config_path, "r", encoding='utf-8'), Loader=yaml.FullLoader))
    with gr.Tabs(elem_id="tabs") as tabs:
        with gr.TabItem(label="Chatting"):
            title = gr.Markdown("**工程早期测试阶段alpha-0.3，GPT回复时间大概5s，绘图约为0.5s/step，请耐心等待，不要多次发送，Markdown功能正在开发中，敬请期待。**")
            state = gr.State([])
            with gr.Row():
                with gr.Column(scale=0.7):
                    # set chat to be 500px high
                    # chat = gr.Chatbot(elem_id="chatbot").style(color_map=('#ffffff', '#ffffff'))
                    chat = gr.Chatbot(elem_id="chatbot")
                    txt = gr.Textbox(show_label=False, placeholder="Type here...").style(container=False)
                    # dream = gr.Textbox(show_label=False, placeholder="Only draw image...").style(container=False)
            
                with gr.Column(scale=0.3):
                    name = gr.Textbox(label="Your name?", show_label=True, placeholder="想让初音怎么称呼你呢？").style(container=False)
                    img = gr.Image(value=default_img, shape=(448, 640), show_label=False, interactive=False)
            txt.submit(predict, [txt, state, name, config], [chat, state, img], show_progress=False, api_name="chatting")
            txt.submit(lambda x: '', [txt], [txt], show_progress=False)

        with gr.TabItem(label="Setting"):
            title = gr.Markdown("**设置**")
            button_apply_settings = gr.Button(value="Apply settings", variant='primary', elem_id="button_apply_settings")
            with gr.Row():
                with gr.Column(scale=0.5):
                    checkbox_chatgpt = gr.Checkbox(value=config.value["enable_chatgpt"], label="Enable ChatGPT Response Pass", elem_id="checkbox_chatgpt", interactive=True)
                    checkbox_diffusion = gr.Checkbox(value=config.value["enable_diffusion"], label="Enable Diffusion Image Pass", elem_id="checkbox_diffusion", interactive=True)
                    checkbox_debug = gr.Checkbox(value=config.value["debug"], label="Enable Debug Mode", elem_id="checkbox_debug", interactive=True)
                    slider_steps = gr.Slider(value=config.value["diffusion_steps"], label="Diffusion Steps", minimum=10, maximum=50, step=1, elem_id="slider_steps", interactive=True)
                    slider_temperature = gr.Slider(value=config.value["chatgpt_temperature"], label="ChatGPT Temperature", minimum=0.0, maximum=1.0, step=0.1, elem_id="slider_temperature", interactive=True)
                    text_ai_nickname = gr.Textbox(value=config.value["ai_nickname"], label="AI Nickname", show_label=True, elem_id="text_ai_nickname", interactive=True)
                    text_sys_prompt = gr.Textbox(value=config.value["system_prompt"], label="ChatGPT System Prompt", show_label=True, elem_id="text_sys_prompt", interactive=True)
                    text_pos_prompt = gr.Textbox(value=config.value["diffusion_positive_prompt"], label="Diffusion Positive Prompt", show_label=True, elem_id="text_pos_prompt", interactive=True)
                    text_neg_prompt = gr.Textbox(value=config.value["diffusion_negative_prompt"], label="Diffusion Negative Prompt", show_label=True, elem_id="text_neg_prompt", interactive=True)
                
                with gr.Column(scale=0.5):
                    json = gr.JSON(config.value, show_label=False, interactive=False)

                components = [(checkbox_chatgpt, "enable_chatgpt"), 
                            (checkbox_diffusion, "enable_diffusion"), 
                            (checkbox_debug, "debug"),
                            (slider_steps, "diffusion_steps"),
                            (slider_temperature, "chatgpt_temperature"),
                            (text_ai_nickname, "ai_nickname"),
                            (text_sys_prompt, "system_prompt"),
                            (text_pos_prompt, "diffusion_positive_prompt"),
                            (text_neg_prompt, "diffusion_negative_prompt")]
                
                for component, key in components:
                    component.change(lambda x, config, key=key: config.update({key: x}), [component, config], [], show_progress=False)
                
            button_apply_settings.click(lambda x: x, [config], [json], show_progress=False)
    
                

# demo.queue()
main_block.launch(server_name="0.0.0.0")
# demo.launch()
