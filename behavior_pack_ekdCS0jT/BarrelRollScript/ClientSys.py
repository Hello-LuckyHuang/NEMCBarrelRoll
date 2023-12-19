# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi
import math
import time
ClientSystem = clientApi.GetClientSystemCls()


class Main(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        namespace = clientApi.GetEngineNamespace()
        system_name = clientApi.GetEngineSystemName()

        self.barrelflySwitch = True

        self.TORAD = math.pi / 180
        self.TODEG = 1 / self.TORAD
        self.player_comp = clientApi.GetEngineCompFactory().CreatePlayer(clientApi.GetLocalPlayerId())
        self.camera_comp = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())

        self.tick = 0
        self.lt = [0.0,0.0]
        self.bt = [0.0,0.0]

        self.mouseTurnVec = [0.0, 0.0]

        self.delta = 1.0/30

        self.pitchSmoother = self.SmoothUtil()
        self.yawSmoother = self.SmoothUtil()
        self.rollSmoother = self.SmoothUtil()

        self.facing = None
        self.left = None

        self.config_comp = clientApi.GetEngineCompFactory().CreateConfigClient(clientApi.GetLevelId())
        #设置配置数据
        self.linminValue = 0.0
        self.strengValue = 0.0
        self.openYOverturn = False
        rollConfigDict = self.config_comp.GetConfigData("barrelroll_rollconfig_rolldata", True)
        if rollConfigDict:
            self.linminValue = rollConfigDict["linminValue"]
            self.strengValue = rollConfigDict["strengthValue"]
            self.openYOverturn = rollConfigDict["openYOverturn"]
        else:
            self.linminValue = 1.8
            self.strengValue = 4.0
            self.openYOverturn = False
            data = {"linminValue": 1.8, "strengthValue": 4.0, "openYOverturn": False}
            #保存一下数据
            self.config_comp.SetConfigData("barrelroll_rollconfig_rolldata", data, True)

        #设置配置数据
        self.HUDScreen = False
        self.angleshow = False
        self.flyHUDshow = False
        self.elytradurabilityshow = False
        self.flyspeedshow = False
        self.directionshow = False
        self.mapshow = False
        flyShowconfigDict = self.config_comp.GetConfigData("barrelroll_flyshowconfig_flyshowdata", True)
        if flyShowconfigDict:
            self.HUDScreen = flyShowconfigDict["HUDScreen"]
            self.angleshow = flyShowconfigDict["angleshow"]
            self.flyHUDshow = flyShowconfigDict["flyHUDshow"]
            self.elytradurabilityshow = flyShowconfigDict["elytradurability"]
            self.flyspeedshow = flyShowconfigDict["flyspeedshow"]
            self.directionshow = flyShowconfigDict["directionshow"]
            self.mapshow = flyShowconfigDict["mapshow"]
        else:
            data = {
                "HUDScreen": False,
                "angleshow": False,
                "flyHUDshow": False,
                "elytradurability": False,
                "flyspeedshow": False,
                "directionshow": False,
                "mapshow": False
            }
            self.config_comp.SetConfigData("barrelroll_flyshowconfig_flyshowdata", data, True)

        self.ListenForEvent(namespace, system_name, "UiInitFinished", self, self.UiInit)#监听处理UI
        self.ListenForEvent('BRServer', 'BarrelRollServer', "OpenSetting", self, self.openSettingPanel)
            
    def saveConfig(self):
        data = {"linminValue": self.linminValue, "strengthValue": self.strengValue, "openYOverturn": self.openYOverturn}
        self.config_comp.SetConfigData("barrelroll_rollconfig_rolldata", data, True)
    
    def saveflyHUDConfig(self):
        data = {
            "HUDScreen": self.HUDScreen,
            "angleshow": self.angleshow,
            "flyHUDshow": self.flyHUDshow,
            "elytradurability": self.elytradurabilityshow,
            "flyspeedshow": self.flyspeedshow,
            "directionshow": self.directionshow,
            "mapshow": self.mapshow
        }
        self.config_comp.SetConfigData("barrelroll_flyshowconfig_flyshowdata", data, True)

    def openSettingPanel(self, event):
        self.settingPanel = clientApi.CreateUI('BarrelUI', 'barrelsetting',{"isHud" : 0, "client" : self})

    def UiInit(self, event):
        clientApi.RegisterUI('BarrelUI', 'barrelswitch', 'BarrelRollScript.ui.BarrelSwitchUI.Main', 'barrelSwitch.main')
        self.switchPanel = clientApi.CreateUI('BarrelUI', 'barrelswitch',{"isHud" : 1, "client" : self})

        clientApi.RegisterUI('BarrelUI', 'flyshowHUD', 'BarrelRollScript.ui.FlyHUDUI.Main', 'fly_HUD.main')
        self.flyHUDPanel = clientApi.CreateUI('BarrelUI', 'flyshowHUD',{"isHud" : 1, "client" : self})

        clientApi.RegisterUI('BarrelUI', 'barrelsetting', 'BarrelRollScript.ui.BarrelSettingUI.Main', 'barrelSetting.main')

        clientApi.RegisterUI('BarrelUI', 'flyshowsetting', 'BarrelRollScript.ui.FlyShowSettingUI.Main', 'elytraShow.main')

    # 监听引擎OnScriptTickClient事件，引擎会执行该tick回调，1秒钟30帧
    def OnTickClient(self):
        """
        Driven by event, One tick way
        """
        pass

    # 被引擎直接执行的父类的重写函数，引擎会执行该Update回调，1秒钟30帧
    def Update(self):
        pmcomp = clientApi.GetEngineCompFactory().CreateOperation(clientApi.GetLevelId())
        if self.barrelflySwitch == True:
            if self.player_comp.isGliding():
                if self.facing == None or self.left == None:
                    #获取玩家视角，在鞘翅开启时启用。
                    facingDEG = self.camera_comp.GetCameraRotation()
                    self.facing = clientApi.GetDirFromRot((facingDEG[0], facingDEG[1]))#获取视向向量
                    self.left = clientApi.GetDirFromRot((facingDEG[2], facingDEG[1]+90))#获取左向量
                    # 不响应屏幕拖动
                    pmcomp.SetCanDrag(False)
                
                move = [0.0, 0.0]
                #获取触摸坐标(测试时F11管用)
                touchX, touchY = clientApi.GetTouchPos()
                self.lt = [touchX, touchY]
                if self.lt != [0.0,0.0] and self.bt != [0.0,0.0]:
                    move = [self.lt[0]-self.bt[0], self.lt[1]-self.bt[1]]
                    if math.sqrt(move[0]**2+move[1]**2) <= 120:
                        self.changeElytraLook(move[1]*self.linminValue, 0, move[0]*self.linminValue)
                else:
                    self.mouseTurnVec = [0, 0]
                    self.changeElytraLook(0, 0, 0)
                    
                self.bt = [touchX, touchY]
            else:
                if self.facing or self.left:
                    self.facing = None
                    self.left = None
                    #初始化平滑器
                    self.pitchSmoother.clear()
                    self.yawSmoother.clear()
                    self.rollSmoother.clear()
                    # 响应屏幕拖动
                    pmcomp.SetCanDrag(True)
                    facingDEG = self.camera_comp.GetCameraRotation()
                    self.camera_comp.SetCameraRotation((facingDEG[0], facingDEG[1], 0))
        else:
            if self.facing or self.left:
                self.facing = None
                self.left = None
                #初始化平滑器
                self.pitchSmoother.clear()
                self.yawSmoother.clear()
                self.rollSmoother.clear()
                # 响应屏幕拖动
                pmcomp.SetCanDrag(True)
                facingDEG = self.camera_comp.GetCameraRotation()
                self.camera_comp.SetCameraRotation((facingDEG[0], facingDEG[1], 0))

                
    def Destroy(self):
        namespace = clientApi.GetEngineNamespace()
        system_name = clientApi.GetEngineSystemName()

        self.UnListenForEvent(namespace, system_name, "UiInitFinished", self, self.UiInit)#监听处理UI
        self.UnListenForEvent('BRServer', 'BarrelRollServer', "OpenSetting", self, self.openSettingPanel)

    def changeElytraLook(self, pitch, yaw, roll):
        rotDelta = [pitch, yaw, roll]
        
        rotDelta = self.sensitivity(rotDelta)
        rotDelta = self.applyInvertPitch(rotDelta, self.openYOverturn)#Y反转
        rotDelta = self.smooth(self.pitchSmoother, self.yawSmoother, self.rollSmoother, rotDelta)
        rotDelta = self.banking(rotDelta)
        self.changeElytraLookDirectly(rotDelta)

    def changeElytraLookDirectly(self, rot):
        pitch = rot[0]
        yaw = rot[1]
        roll = rot[2]

        #pitch
        self.facing = self.norm3D(self.rotateAxisAngle(self.facing, self.left, -0.45 * pitch * self.TORAD))
        #yaw
        up = self.crossProduct(self.facing, self.left)
        self.facing = self.norm3D(self.rotateAxisAngle(self.facing, up, 0.45 * yaw * self.TORAD))
        self.left = self.norm3D(self.rotateAxisAngle(self.left, up, 0.45 * yaw * self.TORAD))
        #roll
        self.left = self.norm3D(self.rotateAxisAngle(self.left, self.facing, 0.45 * roll * self.TORAD))

        self.changeFacingCamera(self.facing, self.left)

    #专门处理摄像机角度的函数
    def changeFacingCamera(self, facingVec, left):
        pitch = -math.asin(facingVec[1]) * self.TODEG
        yaw = -math.atan2(facingVec[0], facingVec[2]) * self.TODEG
        roll = -self.getRoll(yaw, left)

        # pcomp = clientApi.GetEngineCompFactory().CreatePos(clientApi.GetLocalPlayerId())
        # pos = pcomp.GetPos()

        self.camera_comp.SetCameraRotation((pitch, yaw, roll))
        # self.camera_comp.SetCameraPos(pos)
       

        
        

    def smooth(self, pitchSmoother, yawSmoother, rollSmoother, rot):
        return (
                pitchSmoother.smooth(rot[0], self.delta), 
                yawSmoother.smooth(rot[1], 0.4*self.delta), 
                rollSmoother.smooth(rot[2], self.delta)
                )

    def banking(self, rotDelta):
        #获取玩家视角
        comp = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())
        facing = comp.GetCameraRotation()
        currentRoll = facing[2] * self.TORAD
        #消除误差
        if currentRoll < 2E-5 and currentRoll > -2E-5:
            currentRoll = 0

        strength = 10 * math.cos(facing[0] * self.TORAD) * self.strengValue
        dX = math.sin(currentRoll) * strength
        dY = -strength + math.cos(currentRoll) * strength
        if (math.isnan(dX)):
            dX = 0
        if (math.isnan(dY)):
            dY = 0

        return self.addAbsolute(rotDelta, dX * self.delta, dY * self.delta, currentRoll)

    def getRoll(self, yaw, left):
        angle = -math.acos(self.clamp(self.dotProduct(self.getAssumedLeft(yaw), left), -1, 1)) * self.TODEG
        if (left[1] < 0):
            angle *= -1
        return angle

    def clamp(self, value, min, max):
        if value < min:
            return min
        elif value > max:
            return max
        return value
    
    def getAssumedLeft(self, yaw):
        yaw *= self.TORAD
        return (-math.cos(yaw), 0, -math.sin(yaw))

    def rotateAxisAngle(self, v, axis, angle):
        c = math.cos(angle)
        s = math.sin(angle)
        t = 1.0 - c

        x = (c + axis[0]*axis[0]*t) * v[0]
        y = (c + axis[1]*axis[1]*t) * v[1]
        z = (c + axis[2]*axis[2]*t) * v[2]
        tmp1 = axis[0]*axis[1]*t
        tmp2 = axis[2]*s
        y += (tmp1 + tmp2) * v[0]
        x += (tmp1 - tmp2) * v[1]
        tmp1 = axis[0]*axis[2]*t
        tmp2 = axis[1]*s
        z += (tmp1 - tmp2) * v[0]
        x += (tmp1 + tmp2) * v[2]
        tmp1 = axis[1]*axis[2]*t
        tmp2 = axis[0]*s
        z += (tmp1 + tmp2) * v[1]
        y += (tmp1 - tmp2) * v[2]

        return (x, y, z)

    def applyInvertPitch(self, rot, switch):
        if switch:
            return [-rot[0], rot[1], rot[2]]
        return rot

    def addAbsolute(self, rot, x, y, roll):
        cos = math.cos(roll)
        sin = math.sin(roll)
        return [rot[0] - y * cos - x * sin, -(rot[1] - y * sin + x * cos), rot[2]]

    def sensitivity(self, rot):
        return [rot[0]*1, rot[1]*0.4, rot[2]*1]

    def dotProduct(self, vec0, vec1):
        return vec0[0]*vec1[0]+vec0[1]*vec1[1]+vec0[2]*vec1[2]
    
    def crossProduct(self, vec0, vec1):
        return [vec0[1]*vec1[2]-vec0[2]*vec1[1],vec0[2]*vec1[0]-vec0[0]*vec1[2],vec0[0]*vec1[1]-vec0[1]*vec1[0]]

    def addVec(self, vec0, vec1):
        return [vec0[0]+vec1[0], vec0[1]+vec1[1], vec0[2]+vec1[2]]
    
    def mul(self, vec0, num):
        return [vec0[0]*num, vec0[1]*num, vec0[2]*num]
    
    def norm3D(self, vec0):
        l = vec0[0]**2+vec0[1]**2+vec0[2]**2
        if l != 0:
            m = math.sqrt(l)
            return (vec0[0]/m, vec0[1]/m, vec0[2]/m)
        return (0, 0, 0)
    
    def norm2D(self, vec0):
        l = vec0[0]**2+vec0[1]**2
        if l != 0:
            m = math.sqrt(l)
            return (vec0[0]/m, vec0[1]/m)
        return (0, 0)
    
    class SmoothUtil:
        def __init__(self):
            self.actualSum = 0.0
            self.smoothedSum = 0.0
            self.movementLatency = 0.0

        def smooth(self, original, smoother):
            self.actualSum += original
            d = self.actualSum - self.smoothedSum
            e = self.lerp(0.5, self.movementLatency, d)
            f = self.signum(d)
            if (f * d > f * self.movementLatency):
                d = e

            self.movementLatency = e
            self.smoothedSum += d * smoother
            return d * smoother
        
        def clear(self):
            self.actualSum = 0.0
            self.smoothedSum = 0.0
            self.movementLatency = 0.0

        def signum(self, num):
            if num > 0:
                return 1
            elif num < 0:
                return -1
            return 0
        
        def lerp(self, delta, start, end):
            return start + delta * (end - start)