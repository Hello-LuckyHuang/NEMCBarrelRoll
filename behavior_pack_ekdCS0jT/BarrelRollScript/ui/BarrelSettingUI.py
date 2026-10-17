# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()


class Main(ScreenNode):
	def __init__(self, namespace, name, param):
		ScreenNode.__init__(self, namespace, name, param)
		self.client_sys = param['client']#获取客户端
		self._closing = False
		self.closeButton = "/setting_title/close_button"#为UI json文件中的路径关系
		self.linminSlider = "/setting_title/barrel_setting_panel/linmin_slider"
		self.strengSlider = "/setting_title/barrel_setting_panel/streng_slider"
		self.YOverTurnToggle = "/setting_title/barrel_setting_panel/Y_overturn_switch_toggle"
		self.linminlabel = "/setting_title/barrel_setting_panel/linmin_num"
		self.strenglabel = "/setting_title/barrel_setting_panel/streng_num"
		self.YOverTurnlabel = "/setting_title/barrel_setting_panel/Y_overturn_num"
		self.saveButton = "/setting_title/barrel_setting_panel/save_button"
		self.cancelButton = "/setting_title/barrel_setting_panel/cancel_button"
		self.huanButton = "/setting_title/barrel_setting_panel/huanyuan_button"
		self.flySettingButton = "/setting_title/to_elytra_button"
		self.lisenceButton = "/setting_title/lisence_button"

	def Create(self):
		self.closeButtonItem = self.GetBaseUIControl(self.closeButton).asButton()
		self.linminSliderItem = self.GetBaseUIControl(self.linminSlider).asSlider()
		self.strengSliderItem = self.GetBaseUIControl(self.strengSlider).asSlider()
		self.YOverTurnToggleItem = self.GetBaseUIControl(self.YOverTurnToggle).asSwitchToggle()
		self.linminlabelItem = self.GetBaseUIControl(self.linminlabel).asLabel()
		self.strenglabelItem = self.GetBaseUIControl(self.strenglabel).asLabel()
		self.YOverTurnlabelItem = self.GetBaseUIControl(self.YOverTurnlabel).asLabel()
		self.saveButtonItem = self.GetBaseUIControl(self.saveButton).asButton()
		self.cancelButtonItem = self.GetBaseUIControl(self.cancelButton).asButton()
		self.huanButtonItem = self.GetBaseUIControl(self.huanButton).asButton()
		self.flySettingButtonItem = self.GetBaseUIControl(self.flySettingButton).asButton()
		self.lisenceButton = self.GetBaseUIControl(self.lisenceButton).asButton()

		self.closeButtonItem.AddTouchEventParams({"isSwallow": True})
		self.saveButtonItem.AddTouchEventParams({"isSwallow": True})
		self.cancelButtonItem.AddTouchEventParams({"isSwallow": True})
		self.huanButtonItem.AddTouchEventParams({"isSwallow": True})
		self.flySettingButtonItem.AddTouchEventParams({"isSwallow": True})
		self.lisenceButton.AddTouchEventParams({"isSwallow": True})

		self.closeButtonItem.SetButtonTouchUpCallback(self.closeSettingPanel)#按钮按下时触发
		self.saveButtonItem.SetButtonTouchUpCallback(self.saveSetting)#按钮按下时触发
		self.cancelButtonItem.SetButtonTouchUpCallback(self.closeSettingPanel)#按钮按下时触发
		self.huanButtonItem.SetButtonTouchUpCallback(self.reset)#按钮按下时触发
		self.flySettingButtonItem.SetButtonTouchUpCallback(self.openFlySetting)#按钮按下时触发
		self.lisenceButton.SetButtonTouchUpCallback(self.showlisence)#按钮按下时触发


		self.linminSliderValue = (self.client_sys.linminValue - 1.0) / (2.5 - 1.0)
		self.StrengthSliderValue = (self.client_sys.strengValue - 2.0) / (6.0 - 2.0)
		self.YOverTurnIsOpen = self.client_sys.openYOverturn

		self.linminlabelItem.SetText(str(round(self.lerp(self.linminSliderValue, 1.0, 2.5), 2)))
		self.strenglabelItem.SetText(str(round(self.lerp(self.StrengthSliderValue, 2.0, 6.0), 2)))
		self.linminSliderItem.SetSliderValue(self.linminSliderValue)
		self.strengSliderItem.SetSliderValue(self.StrengthSliderValue)
		self.YOverTurnToggleItem.SetToggleState(self.client_sys.openYOverturn)
		if self.client_sys.openYOverturn == True:
			self.YOverTurnlabelItem.SetText("开启")
		else:
			self.YOverTurnlabelItem.SetText("关闭")

	def Destroy(self):
		self._closing = True
		if self.client_sys.settingPanel is self:
			self.client_sys.settingPanel = None

	def OnActive(self):
		pass

	def OnDeactive(self):
		pass

	def closeSettingPanel(self, event):
		if self._closing:
			return
		self._closing = True
		self.SetRemove()
	
	def saveSetting(self, event):
		if self._closing:
			return
		self.client_sys.linminValue = self.lerp(self.linminSliderValue, 1.0, 2.5)
		self.client_sys.strengValue = self.lerp(self.StrengthSliderValue, 2.0, 6.0)
		self.client_sys.openYOverturn = self.YOverTurnToggleItem.GetToggleState()
		self.client_sys.saveConfig()
		self.closeSettingPanel(event)

	def reset(self, event):
		# 还原只修改界面草稿，保存前不影响正在使用的配置。
		self.linminSliderValue = (1.8 - 1.0) / (2.5 - 1.0)
		self.StrengthSliderValue = 0.5
		self.YOverTurnIsOpen = False

		self.linminlabelItem.SetText("1.8")
		self.strenglabelItem.SetText("4.0")
		self.linminSliderItem.SetSliderValue(self.linminSliderValue)
		self.strengSliderItem.SetSliderValue(self.StrengthSliderValue)
		self.YOverTurnToggleItem.SetToggleState(False)
		self.YOverTurnlabelItem.SetText("关闭")

	def openFlySetting(self, event):
		if not self._closing:
			self.client_sys.openFlySettingPanel(event, source=self)

	def showlisence(self, event):
		comp = clientApi.GetEngineCompFactory().CreateTextNotifyClient(clientApi.GetLevelId())
		comp.SetLeftCornerNotify(clientApi.GenerateColor("RED")+"终极翻滚+飞行信息显示组件使用GPL 3.0许可开源")
		comp.SetLeftCornerNotify(clientApi.GenerateColor("RED")+"组件开源地址:https://github.com/HXzhitang/netease-MC-addon-Barrel-Roll")
		self.closeSettingPanel(event)

	@ViewBinder.binding(ViewBinder.BF_SliderChanged | ViewBinder.BF_SliderFinished)
	def OnlinminSliderChange(self, value, isFinish, _unused):
		self.linminSliderValue = value
		self.linminlabelItem.SetText(str(round(self.lerp(value, 1.0, 2.5), 2)))
		return ViewRequest.Refresh
	
	@ViewBinder.binding(ViewBinder.BF_SliderChanged | ViewBinder.BF_SliderFinished)
	def OnStrengthSliderChange(self, value, isFinish, _unused):
		self.StrengthSliderValue = value
		self.strenglabelItem.SetText(str(round(self.lerp(value, 2.0, 6.0), 2)))
		return ViewRequest.Refresh
	
	@ViewBinder.binding(ViewBinder.BF_ToggleChanged)
	def SwitchYOverturn(self, args):
		self.YOverTurnIsOpen = args["state"]
		if self.YOverTurnIsOpen == True:
			self.YOverTurnlabelItem.SetText("开启")
		else:
			self.YOverTurnlabelItem.SetText("关闭")
		return ViewRequest.Refresh
	
	def lerp(self, delta, start, end):
		return start + delta * (end - start)
