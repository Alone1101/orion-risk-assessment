from orion.llm import OllamaProvider

provider = OllamaProvider()

response = provider.generate("Reply with exactly: ORION READY")

print(response)