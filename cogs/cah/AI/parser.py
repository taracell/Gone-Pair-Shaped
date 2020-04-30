import json

with open("Answers.json") as answers:
    ans = {bin(index)[2:].zfill(12): answer for index, answer in enumerate(json.load(answers))}
    # print(dict(list(ans.items())[:20]))

with open("Questions.json") as questions:
    que = {bin(index)[2:].zfill(12): question for index, question in enumerate(json.load(questions))}
    # print(dict(list(que.items())[:20]))
