from app.agent.agent import process_request

for prompt in [
    "find ask_hanam",
    "where is list_files",
    "search for TODO",
    "find provider_score in app",
]:
    print(f"--- {prompt}")
    print(process_request(prompt))
    print()