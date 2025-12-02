
# This are utils files to process strigs and not directly related the evaluation perse
import os

def remove_short_prompts(text):
    return (len(text.split(' '))>=3) and (len(text)>=10)

def check_all_var():
    check1 = os.getenv("USER_KEY") != None
    check2 = os.getenv("API_BASE") != None
    check3 = os.getenv("OPENAI_API_KEY")!=None

    return check1*check2*check3