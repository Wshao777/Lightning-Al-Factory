import json
from datetime import datetime

class LandlordNegotiationAgent:
    def __init__(self, address):
        self.address = address
        self.project_name = "Lightning AI Factory"
        self.terms = {
            "landlord": {
                "input": f"土地所有權 ({address})",
                "output": "1F ~ 3F 完全產權，興建成本由建商及我方吸收（零出資）。"
            },
            "ai_factory": {
                "input": "AI系統、能源平台、營運核心",
                "output": "4F ~ 7F 及屋頂太陽能 100% 使用與收益權。"
            }
        }

    def generate_pitch(self):
        pitch = f"""
        📍 給福上巷 307 號地主的一封信：
        您好，我們是 Lightning AI Factory。您擁有的土地極具垂直發展潛力。
        但您不需要出任何一毛錢！
        
        【我們的方案】
        1. 找建商出資蓋好 **7 層樓**（含外掛電梯），所有成本由我方與建商承擔。
        2. **1~3 樓直接過戶送給您**，土地依然歸您所有。
        3. **4~7 樓及屋頂**由我方經營 AI 智造基地與綠能發電，創造長期的 AI 與能源收益。
        
        這是一份「用空間換取整棟免費房地產」的雙贏契約。如果您有興趣，我們可立即安排現場會勘。
        """
        return pitch

    def risk_trigger_fallback(self):
        # 風險控制（出事拿一層）
        return """
        ⚠️ 自動觸發風險逃逸條款：
        若本建案因不可抗力（建商倒閉、法規驟變）導致無法如期蓋完 7 層，我方確保：
        - 地主仍保有現有樓層（1~2F）的應有權益。
        - 我方 **必定保有已完工樓層中「至少 1 個完整樓層」（強制鎖定 4F 核心層）**，作為 AI 核心的逃生艙與最低保障。
        """

    def execute(self):
        print(f"[{datetime.now()}] 專案初始化：{self.address}")
        print("="*50)
        print("【談判話術生成中】")
        print(self.generate_pitch())
        print("="*50)
        print("【法律與避險條款草擬中】")
        print(self.risk_trigger_fallback())
        print("="*50)
        print("✅ 自動化執行完畢，請將以上內容列印或轉成 PDF，帶去福上巷 307 號談判！")

if __name__ == "__main__":
    # 啟動專案 Agent，鎖定目標地址
    bot = LandlordNegotiationAgent("台中市西屯區福上巷307號")
    bot.execute()
