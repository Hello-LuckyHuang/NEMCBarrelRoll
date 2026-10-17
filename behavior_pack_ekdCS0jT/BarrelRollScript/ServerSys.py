# -*- coding: UTF-8 -*-
# ServerSystem属于SDK的内部类,用于绑定系统
from mod.server.system.serverSystem import ServerSystem
from mod.server.serverEvent import ServerEvent
import mod.server.extraServerApi as ServerApi
import math


# 继承ServerSystem这个类，并在魔法方法__init__内调用ServerSystem的__init__方法，来初始化这个Main类
class Main(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        namespace = ServerApi.GetEngineNamespace()
        system_name = ServerApi.GetEngineSystemName()

        self.ListenForEvent(namespace, system_name, "ServerChatEvent", self, self.openSetting)
        self.ListenForEvent('BRClient', 'BarrelRollClient', "GetElytraDurability", self, self.getdurability)

    def Destroy(self):
        #销毁监听函数
        namespace = ServerApi.GetEngineNamespace()
        system_name = ServerApi.GetEngineSystemName()
        
        self.UnListenForEvent(namespace, system_name, "ServerChatEvent", self, self.openSetting)
        self.UnListenForEvent('BRClient', 'BarrelRollClient', "GetElytraDurability", self, self.getdurability)

    def openSetting(self, event):
        playerId = event['playerId']
        msg = event['message']
        if msg == "#set barrel roll":
            self.NotifyToClient(playerId, "OpenSetting", {})
    
    def getdurability(self, event):
        playerId = event['playerId']
        icomp = ServerApi.GetEngineCompFactory().CreateItem(playerId)
        durability = icomp.GetItemDurability(ServerApi.GetMinecraftEnum().ItemPosType.ARMOR, 1)
        self.NotifyToClient(playerId, "ReturnDurability", {"durability": durability})

