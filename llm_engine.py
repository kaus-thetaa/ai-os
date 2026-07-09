#import  
import ollama
import json
import config

class LLMConnectionError(Exception):
    pass


#client
_client = ollama.Client(host=config.OLLAMA_BASE_URL)


#core
def ask_llm(prompt: str, system_instruction: str = "") -> str:
   
    if not prompt or not prompt.strip():
        raise ValueError("ask_llm() was called with an empty prompt.")
    messages = []

    if system_instruction.strip():
        messages.append({
            "role": "system",
            "content": system_instruction.strip(),
        })

    messages.append({
        "role": "user",
        "content": prompt.strip(),
    })

    try:
        response = _client.chat(
            model=config.OLLAMA_MODEL_NAME,
            messages=messages,
            options={
                "temperature": config.OLLAMA_TEMPERATURE,
            },
        )

        return response["message"]["content"].strip()

    except ollama.ResponseError as error:
       
        raise LLMConnectionError(
            f"Ollama returned an error. This usually means the model "
            f"'{config.OLLAMA_MODEL_NAME}' has not been pulled yet. "
            f"Run 'ollama pull {config.OLLAMA_MODEL_NAME}' in your "
            f"terminal. Original error: {error}"
        )

    except Exception as error:
        raise LLMConnectionError(
            f"Could not reach the Ollama server at {config.OLLAMA_BASE_URL}. "
            f"Make sure Ollama is installed and running in the background. "
            f"Original error: {error}"
        )



def ask_llm_for_json(prompt: str, system_instruction: str = "") -> dict:
 
   
    json_instruction = (
        "You must respond with ONLY a valid JSON object. "
        "Do not include any explanation, preamble, or markdown code "
        "fences. Your entire response must be parseable by a JSON "
        "parser with no modification."
    )

    combined_system_instruction = (
        f"{system_instruction.strip()} {json_instruction}"
        if system_instruction.strip()
        else json_instruction
    )

    raw_response = ask_llm(prompt, system_instruction=combined_system_instruction)

    cleaned_response = raw_response.strip()
    if cleaned_response.startswith("```"):
      
        first_newline_index = cleaned_response.find("\n")
        if first_newline_index != -1:
            cleaned_response = cleaned_response[first_newline_index + 1:]
        # remove a trailing ``` fence if present.
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

    try:
        parsed = json.loads(cleaned_response)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"The LLM did not return valid JSON. This can happen "
            f"occasionally with small local models — try rephrasing "
            f"the request or running it again. Raw response was: "
            f"{raw_response!r}. Parse error: {error}"
        )

    if not isinstance(parsed, dict):
        raise ValueError(
            f"The LLM returned valid JSON, but it wasn't a JSON object "
            f"(dictionary) as expected — it was a {type(parsed).__name__}. "
            f"Raw response was: {raw_response!r}"
        )

    return parsed


#check ollama availability
def is_ollama_available() -> bool:
    
    try:
        
        _client.list()
        return True
    except Exception:
       
        return False


#test
if __name__ == "__main__":
    print("llm_engine.py self-test")
    print("-" * 50)

    print("Checking if Ollama is reachable...")
    if is_ollama_available():
        print("OK — Ollama is running and reachable.")
    else:
        print("FAILED — Ollama is not reachable.")
        print("Make sure Ollama is installed and running, then try again.")
        # We stop here since every test below would fail anyway.
        exit(1)

    print("-" * 50)
    print("Sending a simple test prompt to Phi-3 Mini...")
    try:
        test_response = ask_llm(
            prompt="Reply with exactly one sentence confirming you are working.",
            system_instruction="You are a helpful assistant running locally.",
        )
        print(f"Model response: {test_response}")
    except LLMConnectionError as error:
        print(f"FAILED — {error}")
        exit(1)

    print("-" * 50)
    print("Sending a test prompt requesting JSON output...")
    try:
        test_json_response = ask_llm_for_json(
            prompt=(
                "Respond with a JSON object with exactly two keys: "
                '"status" (the string "ok") and "message" (a short '
                "string saying the JSON test worked)."
            ),
            system_instruction="You are a helpful assistant that responds only in JSON.",
        )
        print(f"Parsed JSON response: {test_json_response}")

        
        if "status" in test_json_response and "message" in test_json_response:
            print("OK — JSON response has expected keys.")
        else:
            print("WARNING — JSON response is valid JSON, but missing expected keys.")

    except (LLMConnectionError, ValueError) as error:
        print(f"FAILED — {error}")
        exit(1)

    print("-" * 50)
    print("llm_engine.py self-test complete. All checks passed.")