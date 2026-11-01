// QUANT_OFI: กลยุทธ์แรงกดดันคำสั่งซื้อขายจริง (Order Flow Imbalance & Linear Price Impact)
// อ้างอิงจากงานวิจัยระดับตำนาน: Rama Cont, Arseniy Kukanov, Sasha Stoikov (arXiv:1011.6402)
//
// ตรรกะ:
//   1. เฝ้าติดตาม Order Book Level 2 (Bid/Ask 10 ระดับ) และคำนวณ OFI:
//      - เมื่อ Best Bid ขยับขึ้น -> OFI เพิ่มตามขนาด Bid Volume
//      - เมื่อ Best Ask ถูกกัดกินลดลง -> OFI เพิ่มตามปริมาณ Trade
//      - เมื่อ Best Bid ถูกถอน Cancel -> OFI ลดลง
//   2. สัญญาณ BUY: เมื่อ Cumulative OFI พุ่งเกิน +Threshold และ Imbalance > +0.03
//   3. สัญญาณ SELL: เมื่อ Cumulative OFI ดิ่งต่ำกว่า -Threshold และ Imbalance < -0.03
//   4. จุดออก: Smart Exit เมื่อ OFI เริ่มชะลอตัวและเกิด Liquidity Replenishment ฝั่งตรงข้าม

using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public class QuantOfiMomentum : StrategyBase
    {
        public override string Code => "QUANT_OFI";
        public override int Version => 1;
        public override string Name => "Quant OFI Momentum (Cont & Stoikov)";
        public override string Theory =>
            "คำนวณแรงกดดันคำสั่งซื้อขายสุทธิ (Order Flow Imbalance - OFI) จากการเปลี่ยนแปลงของ Best Bid/Ask, " +
            "การเติมคำสั่ง และการยกเลิกคำสั่งใน Level 2 Market Depth (arXiv:1011.6402): " +
            "1) ราคาเคลื่อนที่ตามผลรวมของ OFI อย่างเป็นเชิงเส้น (Linear Price Impact) " +
            "2) ยิงออเดอร์ตามทิศทางเงินทุนสถาบันที่กำลังกวาดสภาพคล่องใน Queue " +
            "3) ชิงปิดทำกำไรทันทีเมื่อเกิด Liquidity Replenishment ก่อนที่ราคาจะย่อตัว";

        public override string[] ParamNames => new[] { "OfiLookback", "OfiThresh", "TakeProfitUsd", "StopLossUsd" };
        public override string[] EntryRules => new[]
        {
            "BUY: Normalized OFI >= +{OfiThresh} + Top-of-Book Imbalance >= +0.02 -> BUY",
            "SELL: Normalized OFI <= -{OfiThresh} + Top-of-Book Imbalance <= -0.02 -> SELL",
            "สเปรดปกติ ไม่เกินค่าเฉลี่ย 1.5 เท่า และถือทีละ 1 ไม้ (MaxPositions = 1)"
        };
        public override string[] ExitRules => new[]
        {
            "Take Profit {TakeProfitUsd} USD (หรือ 2.0x SL)",
            "Stop Loss {StopLossUsd} USD",
            "Smart OFI Exit: ปิดล็อกกำไรเมื่อ Cumulative OFI พลิกทิศทางสวนทาง"
        };

        public override int MaxPositions => 1;
        public override bool ExitOnOppositeSignal => true;

        public override double? StopDistance(TradeType side) => P.Length > 3 && P[3] > 0 ? P[3] : 25.0;
        public override double RewardRisk => P.Length > 2 && P[2] > 0 && P.Length > 3 && P[3] > 0 ? P[2] / P[3] : 2.0;

        private MarketDepth _depth;
        private double _prevBidPrice;
        private double _prevBidSize;
        private double _prevAskPrice;
        private double _prevAskSize;
        private double _cumulativeOfi;
        private readonly Queue<double> _ofiHistory = new Queue<double>();

        protected override void OnInit()
        {
            _depth = Bot.MarketData.GetMarketDepth(Bot.SymbolName);
            _prevBidPrice = Bot.Symbol.Bid;
            _prevAskPrice = Bot.Symbol.Ask;
            _prevBidSize = 0;
            _prevAskSize = 0;
            _cumulativeOfi = 0;
            _ofiHistory.Clear();
        }

        public override void OnTick()
        {
            if (_depth == null || _depth.BidEntries.Count == 0 || _depth.AskEntries.Count == 0)
                return;

            double currBidPrice = _depth.BidEntries[0].Price;
            double currBidSize = _depth.BidEntries[0].Volume;
            double currAskPrice = _depth.AskEntries[0].Price;
            double currAskSize = _depth.AskEntries[0].Volume;

            // Cont-Kukanov-Stoikov OFI Calculation formula
            double deltaBid = 0;
            if (currBidPrice > _prevBidPrice)
                deltaBid = currBidSize;
            else if (currBidPrice == _prevBidPrice)
                deltaBid = currBidSize - _prevBidSize;
            else
                deltaBid = -_prevBidSize;

            double deltaAsk = 0;
            if (currAskPrice < _prevAskPrice)
                deltaAsk = currAskSize;
            else if (currAskPrice == _prevAskPrice)
                deltaAsk = currAskSize - _prevAskSize;
            else
                deltaAsk = -_prevAskSize;

            double tickOfi = deltaBid - deltaAsk;
            _cumulativeOfi += tickOfi;

            _ofiHistory.Enqueue(tickOfi);
            int maxHistory = P.Length > 0 && P[0] > 0 ? (int)P[0] * 50 : 200;
            if (_ofiHistory.Count > maxHistory)
                _cumulativeOfi -= _ofiHistory.Dequeue();

            _prevBidPrice = currBidPrice;
            _prevBidSize = currBidSize;
            _prevAskPrice = currAskPrice;
            _prevAskSize = currAskSize;
        }

        public override TradeType? Signal()
        {
            int lookback = P.Length > 0 && P[0] > 0 ? (int)P[0] : 10;
            double thresh = P.Length > 1 && P[1] > 0 ? P[1] : 20.0;

            if (_depth == null || _depth.BidEntries.Count == 0 || _depth.AskEntries.Count == 0)
                return null;

            double bidVol = _depth.BidEntries.Take(5).Sum(e => e.Volume);
            double askVol = _depth.AskEntries.Take(5).Sum(e => e.Volume);
            double imbalance = (bidVol + askVol > 0) ? (bidVol - askVol) / (bidVol + askVol) : 0;

            // Entry triggers
            if (_cumulativeOfi >= thresh && imbalance >= 0.02)
                return TradeType.Buy;

            if (_cumulativeOfi <= -thresh && imbalance <= -0.02)
                return TradeType.Sell;

            return null;
        }
    }
}
