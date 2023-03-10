import openai
from typing import List, Dict, Any, Tuple

def ask_chatgpt(system_prompt: str, txt: str, example: List[Tuple[str, str]] = None,
                history: List[Tuple[str, str]] = None, temperature: float = 0.0) -> str:
    """ask chatgpt to generate a response 

    Args:
        system_prompt (str): system prompt to tell chatgpt what to do
        txt (str): user input
        example (List[Tuple[str, str]], optional): example conversation in the form of [(user, assistant), ...]. Defaults to None.
        history (List[Tuple[str, str]], optional): history conversation in the form of [(user, assistant), ...]. Defaults to None.
        temperature (float, optional): chatgpt temperature. Defaults to 0.0.

    Returns:
        str: chatgpt response content
    """
    
    messages=[{"role": "system", "content": system_prompt}]
    if example:
        if isinstance(example, tuple):
            messages.append({"role": "user", "content": example[0]})
            messages.append({"role": "assistant", "content": example[1]})
        else:
            for i in range(len(example)):
                messages.append({"role": "user", "content": example[i][0]})
                messages.append({"role": "assistant", "content": example[i][1]})
    if history:
        for i in range(len(history)):
            messages.append({"role": "user", "content": history[i][0]})
            messages.append({"role": "assistant", "content": history[i][1]})
    messages.append({"role": "user", "content": txt})
    response=openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = messages,
        temperature = temperature)
    
    return response["choices"][0]['message']['content']

if __name__ == "__main__":
    openai.api_key_path = "openai_api_key.txt"
    system_prompt = "This is a chatbot that can generate a response to a user input. You can ask it to do anything, but it's best at answering questions about the world. Try asking it about the weather, or about the coronavirus. You can also ask it to tell you a joke, or to sing you a song. It's also good at playing games like tic-tac-toe. If you want to play a game, just say 'play a game'. If you want to stop playing a game, just say 'stop'."
    example = ("晚上好！", "晚上好啊~")
    history = [("我叫AAA", "你好AAA")]
    print(ask_chatgpt(system_prompt, "你好", example, history))
    print(ask_chatgpt(system_prompt, "Hello"))