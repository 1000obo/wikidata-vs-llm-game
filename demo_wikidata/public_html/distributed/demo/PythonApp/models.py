#from ctransformers import AutoModelForCausalLM
import openai

def init_openai_key():
	openai.api_key = "TODO"

# Prompt model with specific query and obtain a response
def prompt_model(mod_type: str, model_name: str, prompt: str) -> str:
	# using lamma model
	if (mod_type == "llama"): 
		LLM = AutoModelForCausalLM.from_pretrained("TheBloke/Llama-2-7b-Chat-GGUF", model_file=model_name, model_type=mod_type, gpu_layers=30) 	# Set gpu_layers to the number of layers to offload to GPU. Set to 0 if no GPU acceleration is available on your system.
		response = LLM(prompt, temperature=0.000000001)
		return response
	elif (mod_type == "gpt"):
		messages = [{"role": "user", "content": prompt}]
		response = openai.chat.completions.create(model=model_name, messages=messages, temperature=0.000000001, top_p = 0.000000001)
		return response.choices[0].message.content
	'''elif (mod_type == "mistral"):
		LLM = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
		messages = [{"role": "user", "content": prompt}]
		response = LLM.generate(messages)
		print(response)
		return "test"'''

