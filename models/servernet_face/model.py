# ServerFace is base on ResNetFace
# from: https://github.com/ronghuaiyang/arcface-pytorch/blob/master/models/resnet.py


import torch.nn as nn


class ServerFace(nn.Module):
    def __init__(self, use_se=True, **kwargs):
        self.use_se = use_se
        super().__init__()

        self.fc5 = nn.Linear(512 * 8 * 8, 512)
        self.bn5 = nn.BatchNorm1d(512)

        for m in self.modules():
            if isinstance(m, nn.BatchNorm2d) or isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        x = self.fc5(x)
        x = self.bn5(x)
        return x
