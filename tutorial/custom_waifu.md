# customize your own waifu!
 > this tutorial will guide you to create your own waifu using chatwaifu.

**requirements:**
 - ChatWaifu installed
 - some text materials for your waifu (lore, story, dialogues, novels, etc.) 
 - description of your waifu's appearance (hair color, eye color, outfit, etc.) or a lora model

## 1. create a yaml file
 all the waifu settings are stored in a yaml file, you can use the template [miku.yaml](./presets/miku.yaml) as a reference.

for example, if you want to create a waifu named `miku`, you can create a file named `miku.yaml` and put it in the `presets` folder.

## 2. (optional) generate description for your waifu
you can put all the txt metarial (lore, story, dialogues, novels, etc.) into chatbox and let your other waifus generate a description for you.
a typical prompt looks like this:
```
You: <materials_1>. According to the above materials, summarize the background story, personality characteristics, speaking style, language habits, and style of dealing with people of <waifu_name>.
AI: <description_1>
You: <materials_2>. According to the above materials, summarize the background story, personality characteristics, speaking style, language habits, and style of dealing with people of <waifu_name>.
AI: <description_2>
...
You: <description_1>, <description_2>, ..., <description_n>. According to the above descriptions, summarize the background story, personality characteristics, speaking style, language habits, and style of dealing with people of <waifu_name>.
```


## 3. fill in the yaml file
 - `id`: the name of our waifu to show in the character list
 - `ai_nickname`: the nickname of your waifu used in the coversation
 - `system_prompt`: system prompt used in the chatgpt, write your waifu's background, personality and tongue here.
 - `diffusion_positive_prompt`: positive prompt for stable diffusion, write your waifu's appearance and outfit here, if a lora is used, put the lora tag here like `<lora:xiao:0.7>`
 - `diffusion_negative_prompt`: negative prompt for stable diffusion, use this accompany with the positive prompt.
