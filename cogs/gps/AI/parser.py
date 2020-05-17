import json

with open("Answers.json") as answers:
    ans = json.load(answers)
    length = len(bin(len(ans))[2:])
    answers.seek(0)
    ans = {bin(index)[2:].zfill(length): answer for index, answer in enumerate(ans)}
    #print(dict(list(ans.items())[:20]))

with open("../../../data/answers.json", "w") as answers:
    json.dump(ans, answers)

with open("Questions.json") as questions:
    que = json.load(questions)
    length = len(bin(len(que))[2:])
    questions.seek(0)
    que = {bin(index)[2:].zfill(length): question for index, question in enumerate(que)}
    #print(dict(list(que.items())[:20]))

with open("../../../data/questions.json", "w") as questions:
    json.dump(que, questions)
