import torch
import torch.nn as nn
import random
import tools
import numpy

class NET(nn.Module):
    def __init__(self, start, s_hid, e_hid, depth, end):
        super(NET, self).__init__()
        self.s = start
        self.sh = s_hid
        self.eh = e_hid
        self.e = end
        self.d = depth

        self.layer_step = (abs(self.sh-self.eh)/self.d) #calculates the difference between layer sizes

        self.start = nn.Linear(self.s, self.sh) #sets up the correct amount of weights
        self.hlayers = [nn.Linear(round(self.layer_step*i) + self.sh, round(self.layer_step*(i+1))+self.sh) for i in range(self.d)] #list of all hidden layers
        self.end = nn.Linear(round(self.layer_step*(depth)) + self.sh, self.e)

        self.criterion = torch.nn.MSELoss() #guess minus the target squared
        self.optimizer = torch.optim.Adam(self.parameters(), lr=0.02, weight_decay=0.001) #passes parameters

    def forward(self, x): #input of the NN
        x = torch.relu(self.start(x))
        for layer in self.hlayers:
            x = torch.sigmoid(layer(x))
        return torch.relu(self.end(x))

    def toList(self, data): #List representation of presented data (utility)
        if type(data) is list:
            return(data)
        else:
            return(data.tolist())

    def toTensor(self, data): # (Utility)
        listdata = [d for d in data]
        return(torch.tensor(listdata))

    def fPass(self, data): # (Utility)
        return(self.toList(self.forward(self.toTensor(tools.flatten(data)))))

    def replay(self, mem, batchsize=None): #training area
        batchsize = len(mem) if batchsize is None else batchsize
        minibatch = random.sample(mem, min(len(mem), batchsize))
        for state, action, reward, next_state, done in minibatch:
            target = self.fPass(state)
            if done:
                target[action] = 0
            else:
                target[action] = reward + self.gamma * numpy.max(self.fPass(next_state))
            guess = self.forward(self.toTensor(tools.flatten(state)))
            loss = self.criterion(guess, self.toTensor(target))
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
