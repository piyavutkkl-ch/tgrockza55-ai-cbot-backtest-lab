// QUANT_HAWKES: กลยุทธ์ Hawkes Self-Exciting Trade Clustering & Burst Momentum
// อ้างอิงจากงานวิจัย: "Hawkes model for price and trades high-frequency dynamics" (arXiv:1301.1135)
//
// ตรรกะ:
//   1. คำนวณความถี่ของคำสั่งซื้อขายแบบ Self-Exciting Point Process:
//      Lambda(t) = mu + sum(alpha * exp(-beta * (t - t_i)))
//   2. เมื่อเกิดการจับกลุ่มของคำสั่งซื้อขายผิดปกติ (Trade Clustering Burst):
//      ค่า Lambda จะพุ่งสูงขึ้นแบบก้าวกระโดด บ่งบอกถึงการแห่ซื้อ/แห่ขาย (Herding Cascade)
//   3. ยิงออเดอร์ตามทิศทางของกระแสคำสั่ง (Directional Delta) ทันที
//   4. จุดออก: ปิดสถานะเมื่อค่า Intensity สลายตัว (Decay) ลงสู่ระดับปกติ หรือครบกรอบเวลาสั้น

using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public class QuantHawkesBurst : StrategyBase
    {
        public override string Code => "QUANT_HAWKES";
        public override int Version => 1;
        public override string Name => "Hawkes Point Process Trade Burst (Bacry et al.)";
        public override string Theory =>
            "แบบจำลอง Hawkes Process ตรวจจับการเกิดลูกโซ่ของคำสั่งซื้อขาย (Order Cascades) ระดับเสี้ยววินาที (arXiv:1301.1135): " +
            "1) การจับคู่ของออเดอร์หนึ่งจะกระตุ้นให้ออเดอร์อื่นตามมาเป็นพายุคำสั่ง (Self-excitation) " +
            "2) ดักจับจังหวะการระเบิดของ Volatility ก่อนที่แท่งเทียนจะขยับเต็มแท่ง " +
            "3) ชิงปิดทำกำไรทันทีเมื่อค่าความหนาแน่น Lambda สลายตัว (Exponential Decay)";

        public override string[] ParamNames => new[] { "BaseMu", "AlphaDecay", "BurstThresh", "TakeProfitUsd" };
        public override string[] EntryRules => new[]
        {
            "BUY: Hawkes Intensity Lambda >= {BurstThresh} + Delta เป็นบวกหนาแน่น -> BUY",
            "SELL: Hawkes Intensity Lambda >= {BurstThresh} + Delta เป็นลบหนาแน่น -> SELL",
            "ถือทีละ 1 ไม้ (MaxPositions = 1) และสเปรดปกติ"
        };
        public override string[] ExitRules => new[]
        {
            "Take Profit {TakeProfitUsd} USD (หรือ 2.0x SL)",
            "Stop Loss ตัดขาดทุนโครงสร้างสั้น",
            "Decay Exit: ปิดสถานะเมื่อค่า Intensity ลดลงต่ำกว่า 50% ของจุดพีค"
        };

        public override int MaxPositions => 1;
        public override bool ExitOnOppositeSignal => true;

        public override double? StopDistance(TradeType side) => 30.0;
        public override double RewardRisk => P.Length > 3 && P[3] > 0 ? P[3] / 30.0 : 2.0;

        private FlowTracker _flow;
        private double _intensity;
        private DateTime _lastTickTime;
        private readonly List<DateTime> _eventTimes = new List<DateTime>();

        protected override void OnInit()
        {
            _flow = Bot.GetFlowTracker();
            _intensity = 0.1;
            _lastTickTime = Bot.Time;
            _eventTimes.Clear();
        }

        public override void OnTick()
        {
            DateTime now = Bot.Time;
            double dt = (now - _lastTickTime).TotalSeconds;
            if (dt < 0) dt = 0;

            double beta = 1.5; // decay rate
            double alpha = 0.8; // excitation jump size
            double mu = P.Length > 0 && P[0] > 0 ? P[0] : 0.2; // base rate

            // Exponential decay
            _intensity = mu + (_intensity - mu) * Math.Exp(-beta * dt) + alpha;
            _lastTickTime = now;
        }

        public override TradeType? Signal()
        {
            double thresh = P.Length > 2 && P[2] > 0 ? P[2] : 2.5;

            double delta = _flow != null ? _flow.Delta : 0;
            double cvd = _flow != null ? _flow.Cvd : 0;

            // Hawkes Burst entry
            if (_intensity >= thresh)
            {
                if (delta > 0 && cvd > 0)
                    return TradeType.Buy;
                if (delta < 0 && cvd < 0)
                    return TradeType.Sell;
            }

            return null;
        }
    }
}
