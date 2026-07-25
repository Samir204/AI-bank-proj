
#  google:
# api key: AQ.Ab8RN6IbH0_rMxmUpeWVjD0GyRykdLSVyFmekOiSNoZNjLrtRw
# name : Gemini API Key
# project name: projects/444332595660
# project num: 444332595660

# AQ.Ab8RN6IbH0_rMxmUpeWVjD0GyRykdLSVyFmekOiSNoZNjLrtRw

from google import genai

client = genai.Client(api_key="AQ.Ab8RN6IbH0_rMxmUpeWVjD0GyRykdLSVyFmekOiSNoZNjLrtRw")

# hello:
# response = client.models.generate_content(
#     model="gemini-3.1-flash-lite",
#     contents="hi?"
# )

# print(response.text)

history = [] 

def chat():

    while True:
        user_input = input(" --> You: ")
        
        if user_input.lower() in ("quit", "exit"):
            print("bye <3")
            break

        history.append({
            "role" : "user",
            "input: ": user_input
        })

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=user_input
            )

        history.append({
            "role" : "AI",
            "output": response.text
        })

        print(response.text)
        print()
        

def get_history(history):

    for chat in history:
        print()
        print(chat)
        print()




chat()
get_history(history)










 






 






 






 