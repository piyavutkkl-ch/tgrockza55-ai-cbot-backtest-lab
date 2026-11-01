import os
import re

local_cs = r'd:\cbot-atgvt\cbot\BacktestLab\BacktestLab.cs'
onedrive_cs = r'C:\Users\Strong Baesus PC1\OneDrive\เอกสาร\cAlgo\Sources\Robots\BacktestLab\BacktestLab\BacktestLab.cs'

new_body = """void ApplyLiveSettings()
        {
            var file = System.IO.Path.Combine(Reporter.Folder, "live.json");
            if (!System.IO.File.Exists(file))
            {
                Print("No live.json: using the parameters set in cTrader (Strategy code = {0})", StrategyCode);
                return;
            }
            try
            {
                using (var doc = System.Text.Json.JsonDocument.Parse(System.IO.File.ReadAllText(file)))
                {
                    var root = doc.RootElement;
                    System.Text.Json.JsonElement v;
                    if (root.TryGetProperty("strategy", out v)) StrategyCode = v.GetString();
                    if (root.TryGetProperty("lots", out v)) Lots = v.GetDouble();
                    if (root.TryGetProperty("placeOrders", out v)) PlaceOrders = v.GetBoolean();
                    if (root.TryGetProperty("flatTime", out v)) FlatTime = v.GetInt32();
                    if (root.TryGetProperty("p1", out v)) P1 = v.GetDouble();
                    if (root.TryGetProperty("p2", out v)) P2 = v.GetDouble();
                    if (root.TryGetProperty("p3", out v)) P3 = v.GetDouble();
                    if (root.TryGetProperty("p4", out v)) P4 = v.GetDouble();

                    // Symbol-specific override (e.g. symbols["BTCUSD"] or symbols["ETHUSD"])
                    System.Text.Json.JsonElement symObj;
                    bool hasSym = root.TryGetProperty(SymbolName, out symObj);
                    if (!hasSym && root.TryGetProperty("symbols", out var syms))
                        hasSym = syms.TryGetProperty(SymbolName, out symObj);

                    if (hasSym && symObj.ValueKind == System.Text.Json.JsonValueKind.Object)
                    {
                        if (symObj.TryGetProperty("strategy", out v)) StrategyCode = v.GetString();
                        if (symObj.TryGetProperty("lots", out v)) Lots = v.GetDouble();
                        if (symObj.TryGetProperty("placeOrders", out v)) PlaceOrders = v.GetBoolean();
                        if (symObj.TryGetProperty("p1", out v)) P1 = v.GetDouble();
                        if (symObj.TryGetProperty("p2", out v)) P2 = v.GetDouble();
                        if (symObj.TryGetProperty("p3", out v)) P3 = v.GetDouble();
                        if (symObj.TryGetProperty("p4", out v)) P4 = v.GetDouble();
                    }
                }
                Print("Live settings ({0}) from live.json: {1}  P1 {2}  P2 {3}  P3 {4}  P4 {5}  lots {6}  place orders {7}",
                    SymbolName, StrategyCode, P1, P2, P3, P4, Lots, PlaceOrders);
            }
            catch (Exception e)"""

pattern = r'void ApplyLiveSettings\(\)[\s\S]*?catch \(Exception e\)'

for target in [local_cs, onedrive_cs]:
    if os.path.exists(target):
        with open(target, 'r', encoding='utf-8') as f:
            c = f.read()
        if re.search(pattern, c):
            c = re.sub(pattern, new_body, c)
            with open(target, 'w', encoding='utf-8') as f:
                f.write(c)
            print(f"Replaced ApplyLiveSettings in {target}")
        else:
            print(f"Could not find pattern in {target}")
