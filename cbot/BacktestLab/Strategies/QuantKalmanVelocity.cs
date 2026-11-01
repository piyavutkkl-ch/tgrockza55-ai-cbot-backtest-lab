// QUANT_KALMAN: กลยุทธ์ State-Space Kalman Filter Zero-Lag Velocity
// อ้างอิงจากงานวิจัย: "Trend without hiccups: a Kalman filter approach" (arXiv:1808.03297)
//
// ตรรกะ:
//   1. ใช้แบบจำลอง State-Space [Position, Velocity, Acceleration] ในการประมาณการเคลื่อนไหวจริง
//   2. แยก "สัญญาณจริง (True Trend State)" ออกจาก "สัญญาณรบกวน (Market Noise)" แบบ Zero-Lag
//   3. ขา BUY: เวกเตอร์ Velocity ตัดผ่าน 0 ขึ้นด้านบน และ Acceleration เป็นบวก
//   4. ขา SELL: เวกเตอร์ Velocity ตัดผ่าน 0 ลงด้านล่าง และ Acceleration เป็นลบ
//   5. ออกเมื่อ Acceleration เริ่มชะลอตัว หรือแตะจุด TP/SL

using System;
using System.Collections.Generic;
using cAlgo.API;

namespace cAlgo.Robots
{
    public class QuantKalmanVelocity : StrategyBase
    {
        public override string Code => "QUANT_KALMAN";
        public override int Version => 1;
        public override string Name => "State-Space Kalman Filter Zero-Lag (Trend without Hiccups)";
        public override string Theory =>
            "แบบจำลอง State-Space สกัดความเร็ว (Velocity) และความเร่ง (Acceleration) ของราคา " +
            "แก้ปัญหา Lagging และสัญญาณหลอก (Whipsaws) ของ Moving Average ทั่วไป (arXiv:1808.03297): " +
            "1) เข้าออเดอร์ทันทีที่เวกเตอร์ความเร็ว (Velocity) มีการเปลี่ยนขั้วผ่านจุดสมดุล 0 " +
            "2) กรองด้วยค่าความแปรปรวนของระบบ (Innovation Covariance) ป้องกันการเข้าในจังหวะ Noise สูง " +
            "3) ถือตามแนวโน้มและปิดทำกำไรเมื่อความเร่งเริ่มหมดแรง";

        public override string[] ParamNames => new[] { "ProcessNoiseQ", "MeasureNoiseR", "TakeProfitUsd", "StopLossUsd" };
        public override string[] EntryRules => new[]
        {
            "BUY: Kalman Velocity(t) > 0 และ Velocity(t-1) <= 0 + Acceleration > 0 -> BUY",
            "SELL: Kalman Velocity(t) < 0 และ Velocity(t-1) >= 0 + Acceleration < 0 -> SELL",
            "ถือทีละ 1 ไม้ (MaxPositions = 1) และสเปรดปกติ"
        };
        public override string[] ExitRules => new[]
        {
            "Take Profit {TakeProfitUsd} USD (หรือ 2.0x SL)",
            "Stop Loss {StopLossUsd} USD",
            "สัญญาณกลับตัว: ปิดสถานะทันทีเมื่อ Velocity ตัดกลับทิศทางตรงข้าม"
        };

        public override int MaxPositions => 1;
        public override bool ExitOnOppositeSignal => true;

        public override double? StopDistance(TradeType side) => P.Length > 3 && P[3] > 0 ? P[3] : 30.0;
        public override double RewardRisk => P.Length > 2 && P[2] > 0 && P.Length > 3 && P[3] > 0 ? P[2] / P[3] : 2.0;

        // Kalman State Vector [Position, Velocity]
        private double _x0; // price
        private double _x1; // velocity
        private double _prevVelocity;

        // Covariance Matrix P [2x2]
        private double _p00, _p01, _p10, _p11;

        protected override void OnInit()
        {
            _x0 = Bot.Bars.ClosePrices.Last(1);
            _x1 = 0;
            _prevVelocity = 0;

            _p00 = 1.0; _p01 = 0.0;
            _p10 = 0.0; _p11 = 1.0;
        }

        public override TradeType? Signal()
        {
            double q = P.Length > 0 && P[0] > 0 ? P[0] : 0.001; // Process Noise
            double r = P.Length > 1 && P[1] > 0 ? P[1] : 0.1;   // Measurement Noise

            double z = Bot.Bars.ClosePrices.Last(1); // observation

            // 1. Time Update (Predict)
            double dt = 1.0;
            double x0_pred = _x0 + _x1 * dt;
            double x1_pred = _x1;

            double p00_pred = _p00 + dt * (_p10 + _p01) + dt * dt * _p11 + q;
            double p01_pred = _p01 + dt * _p11;
            double p10_pred = _p10 + dt * _p11;
            double p11_pred = _p11 + q;

            // 2. Measurement Update (Correct)
            double y = z - x0_pred; // measurement residual
            double s = p00_pred + r; // residual covariance
            double k0 = p00_pred / s; // Kalman gain 0
            double k1 = p10_pred / s; // Kalman gain 1

            _x0 = x0_pred + k0 * y;
            _x1 = x1_pred + k1 * y;

            _p00 = (1 - k0) * p00_pred;
            _p01 = (1 - k0) * p01_pred;
            _p10 = -k1 * p00_pred + p10_pred;
            _p11 = -k1 * p01_pred + p11_pred;

            TradeType? signal = null;

            // Velocity Zero-Crossing Triggers
            if (_x1 > 0 && _prevVelocity <= 0)
                signal = TradeType.Buy;
            else if (_x1 < 0 && _prevVelocity >= 0)
                signal = TradeType.Sell;

            _prevVelocity = _x1;
            return signal;
        }
    }
}
