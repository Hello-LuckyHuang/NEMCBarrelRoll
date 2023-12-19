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
        self.ListenForEvent(namespace, system_name, "EntityDefinitionsEventServerEvent", self, self.entityEvent)
        self.ListenForEvent(namespace, system_name, "ItemReleaseUsingServerEvent", self, self.ItemEvent)

    def Destroy(self):
        #销毁监听函数
        namespace = ServerApi.GetEngineNamespace()
        system_name = ServerApi.GetEngineSystemName()
        
        self.UnListenForEvent(namespace, system_name, "ServerChatEvent", self, self.openSetting)
        self.UnListenForEvent('BRClient', 'BarrelRollClient', "GetElytraDurability", self, self.getdurability)
        self.UnListenForEvent(namespace, system_name, "EntityDefinitionsEventServerEvent", self, self.entityEvent)
        self.UnListenForEvent(namespace, system_name, "ItemReleaseUsingServerEvent", self, self.ItemEvent)

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

    def ItemEvent(self, event):
        item_dict = event['itemDict']#获取物品词典
        item_name = event['itemName']
        playerId = event['playerId']#获取玩家id
        if item_name == "zcvss:mpad":
            game_type = ServerApi.GetEngineCompFactory().CreateGame(ServerApi.GetLevelId()).GetPlayerGameType(playerId)
            item_comp = ServerApi.GetEngineCompFactory().CreateItem(playerId)
            if game_type != 1:
                item_pos_type = ServerApi.GetMinecraftEnum().ItemPosType.INVENTORY#背包位置
                #遍历背包寻找消耗物品
                for slot in xrange(36):
                    slot_item_dict = item_comp.GetPlayerItem(item_pos_type, slot)
                    if slot_item_dict and slot_item_dict['itemName'] == "minecraft:arrow" and slot_item_dict['count'] >= 2:
                        item_comp.SetInvItemNum(slot, slot_item_dict['count'] - 2)#消耗对应数量的物品
                        break
                else:
                    return
                item_comp.SetItemDurability(item_pos_type, item_comp.GetSelectSlotId(), item_dict['durability'] - 1)#掉耐久
            #发射箭矢功能
            projectile_comp = ServerApi.GetEngineCompFactory().CreateProjectile(ServerApi.GetLevelId())
            pos = ServerApi.GetEngineCompFactory().CreatePos(playerId).GetPos()
            rot = ServerApi.GetEngineCompFactory().CreateRot(playerId).GetRot()
            #发射弹射物
            projectile_comp.CreateProjectileEntity(playerId, "zcvss:mpad", {
                'position': pos,
                'direction': ServerApi.GetDirFromRot(rot),
                'damage': 10
            })
        elif item_name == "zcvss:fly_yi":
             #发射箭矢功能
            projectile_comp = ServerApi.GetEngineCompFactory().CreateProjectile(ServerApi.GetLevelId())
            pos = ServerApi.GetEngineCompFactory().CreatePos(playerId).GetPos()
            rot = ServerApi.GetEngineCompFactory().CreateRot(playerId).GetRot()
            #发射弹射物
            projectile_comp.CreateProjectileEntity(playerId, "zcvss:fly_yi", {
                'position': pos,
                'direction': ServerApi.GetDirFromRot(rot),
                'damage': 10
            })
        elif item_name == "zcvss:barrel_item":
             #发射箭矢功能
            projectile_comp = ServerApi.GetEngineCompFactory().CreateProjectile(ServerApi.GetLevelId())
            pos = ServerApi.GetEngineCompFactory().CreatePos(playerId).GetPos()
            rot = ServerApi.GetEngineCompFactory().CreateRot(playerId).GetRot()
            #发射弹射物
            projectile_comp.CreateProjectileEntity(playerId, "tklyn:fo_light", {
                'position': pos,
                'direction': ServerApi.GetDirFromRot(rot),
                'damage': 10
            })

    #响应生物事件
    def entityEvent(self, event):
        if event['eventName'] == "fo:light" or event['eventName'] == "initial_finish":
            r = 10
            fo_id = event['entityId']
            ECF = ServerApi.GetEngineCompFactory()
            
            en_comp = ECF.CreateGame(ServerApi.GetLevelId())
            en_list = en_comp.GetEntitiesAroundByType(fo_id, r, ServerApi.GetMinecraftEnum().EntityType.Monster)
            if en_list:
                for id in en_list:
                    source_id = ECF.CreateBulletAttributes(fo_id).GetSourceEntityId()
                    epos = ECF.CreatePos(id).GetFootPos()
                    rot = ECF.CreateRot(id).GetRot()
                    #发射激光
                    projectile_comp = ECF.CreateProjectile(ServerApi.GetLevelId())
                    projectile_comp.CreateProjectileEntity(source_id, "tklyn:big_light", {
                        'position': epos,
                        'direction': ServerApi.GetDirFromRot(rot),
                        'damage': 8
                    })
            else:
                if event['eventName'] == "initial_finish":
                    self.DestroyEntity(fo_id)
            
        if event['eventName'] == "fz:light_end":
            not_player_filters = {
                "any_of": [
                    {
                        "subject" : "other",
                        "test" :  "is_family",
                        "operator" : "not",
                        "value" :  "player"
                    }
                ]
            }
            r = 5
            light_id = event['entityId']
            ECF = ServerApi.GetEngineCompFactory()
            #对非玩家实体造成伤害
            en_comp = ECF.CreateGame(ServerApi.GetLevelId())
            source_comp = ECF.CreateBulletAttributes(light_id)
            source_id = source_comp.GetSourceEntityId()
            for id in en_comp.GetEntitiesAround(light_id, r, not_player_filters):
                #伤害+点燃
                hurt_comp = ECF.CreateHurt(id)
                hurt_comp.Hurt(10, ServerApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, source_id, None, True)
                fire_comp = ECF.CreateAttr(id)
                fire_comp.SetEntityOnFire(10, 2)
            #对玩家造成伤害
            player_comp = ServerApi.GetEngineCompFactory().CreatePlayer(source_id)
            spos = ServerApi.GetEngineCompFactory().CreatePos(source_id).GetPos()
            for id in player_comp.GetRelevantPlayer([source_id]):
                ppos = ServerApi.GetEngineCompFactory().CreatePos(id).GetPos()
                l = math.sqrt((ppos[0]**2-spos[0]**2)+(ppos[1]**2-spos[1]**2)+(ppos[2]**2-spos[2]**2))
                if l <= r:
                    #伤害+点燃
                    hurt_comp = ECF.CreateHurt(id)
                    hurt_comp.Hurt(10, ServerApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, source_id, None, True)
                    fire_comp = ECF.CreateAttr(id)
                    fire_comp.SetEntityOnFire(10, 2)
            self.DestroyEntity(light_id)

