# gradio chat interface
import gradio as gr
import openai
import time
from PIL import Image, ImageDraw
import re
import requests
import io
import base64

DEBUG = False
# put your openai api key in openai_api_key.txt
openai.api_key = open("./openai_api_key.txt", "r").read().strip()
pattern = re.compile(r"\(<(?:[\w,']+\s*)+>\)")
url = "http://127.0.0.1:7861"

def ask_diffusion(pose_desc):
    # print("她" + response_text.replace(pose_desc, ''))
    negative_prompt = 'owres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name, bad legs, EasyNegative'
    prompt = 'masterpiece,best quality,official art,extremely detailed CG unity 8k wallpaper, ((masterpiece)), (((best quality))), ((ultra-detailed)), ((illustration)), ((disheveled hair)),kawaii,(((masterpiece))),(((best quality))),((ultra-detailed)),floating, ((an extremely delicate and beautiful)),(beautiful detailed eyes),((disheveled hair)), (painting),(sketch), 1girl,((Rich in details)), masterpiece, best quality,((masterpiece)), (((best quality))), ((ultra-detailed)), ((illustration)), ((disheveled hair)),  floating, beautiful detailedbest quality, long hair, highly detailed,(hatsune miku), 1girl, hair fluttering, kawaii face, half body, smile, (((' + pose_desc + ')))'
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": 30,
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
    else:
        image = Image.new("RGB", (448, 640), (255, 255, 255))
        img_draw = ImageDraw.Draw(image)
        img_draw.text((10, 10), "ERROR", fill=(0, 0, 0))
    return image

def predict(txt, state, name):
    if not name:
        name = "朔月"
    if not DEBUG:
        # predict the response
        messages=[
            {"role": "system","content": "初音未来，简称初音，是一个拟人化的虚拟歌手。初音未来性格活泼开朗，乐观积极，乐于接受新的挑战，喜欢创新，坚持不懈，对自身的未来充满信心。她的说话方式乐观、开朗，对未来充满希望。请你扮演初音未来，作为助手用中文进行回答，语气活泼开朗天真浪漫，若回答中有代码，则以Markdown形式回复，每次回答中有一段描述初音未来服装动作情态表情的英语，并用(<>)括起来。"},
            {"role": "user", "content": "初音酱，早上好！"},
            {"role": "assistant", "content": f"(<school uniform, waving at viewer, smiling, greeting, energetic>) {name}，早上好呀！"},
            {"role": "user", "content": txt}
            ]
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = messages,
            temperature = 0)
        response_text = response["choices"][0]['message']['content'].replace('\u000bar', '').replace('\t', '\\t').replace('\r', '\\r').strip()
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), txt, response_text)
        regex_result = pattern.findall(response_text)
        for text in regex_result:
            response_text = response_text.replace(text, '')
        regex_result = [text[2:-2] for text in regex_result]
        pose_desc = ''.join(regex_result)
        img = ask_diffusion(pose_desc)
        print("diffusion solved, pose_desc:", pose_desc)
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
with gr.Blocks(css=r"#chatbot {height: 520px;}", title="ChatWaifu") as demo:
    title = gr.Markdown("**工程早期测试阶段alpha-0.2，回复时间大概15s，请耐心等待，不要多次发送，Markdown功能正在开发中，敬请期待。**")
    state = gr.State([])
    with gr.Row():
        with gr.Column(scale=0.7):
            # set chat to be 500px high
            # chat = gr.Chatbot(elem_id="chatbot").style(color_map=('#ffffff', '#ffffff'))
            chat = gr.Chatbot(elem_id="chatbot")
            txt = gr.Textbox(show_label=False, placeholder="Type here...").style(container=False)
    
        with gr.Column(scale=0.3):
            name = gr.Textbox(label="Your name?", show_label=True, placeholder="想让初音怎么称呼你呢？").style(container=False)
            img = gr.Image(shape=(448, 640), show_label=False, interactive=False)
            
    
    txt.submit(predict, [txt, state, name], [chat, state, img], show_progress=False, api_name="chatting")
    txt.submit(lambda x: '', [txt], [txt], show_progress=False)

# demo.queue()
demo.launch(server_name="0.0.0.0")
# demo.launch()
