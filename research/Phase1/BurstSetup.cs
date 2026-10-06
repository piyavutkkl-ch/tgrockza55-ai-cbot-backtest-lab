// SETUP + BURST (user request 06/10/2026): enter only when a location with a presumed advantage AND a burst of speed happen together,
// leave fast with a target of 0.5 - 1 USD.
//
// Run: Phase1.exe setup [live-test|live] [from yyyy-MM-dd] [to yyyy-MM-dd] [symbol]
//
// Burst (as in Burst.cs): the first second the move of the mid over 5 s (or 10 s) is >= 3 or 5 times its usual size, spread <= 0.35, 10 s apart.
// Locations, all from data before the signal (trading day from 22:00 UTC; "range" = high / low of the hour that ended 2 minutes ago):
//   LS   liquidity sweep + reversal:   the range high was exceeded in the last 2 minutes, the price is back below it, burst DOWN -> sell
//   SS   session high/low sweep:       the same with yesterday's high/low, the Asia range (after 07:00) or the London range (after 13:00)
//   EXf  extreme extension, fade:      price >= 2 sd from the day's VWAP and the burst pushes further out -> trade AGAINST the burst
//   EXr  extreme extension, return:    price >= 2 sd from the day's VWAP and the burst points back to it -> with the burst
//   FB   failed breakout:              the range of 70..10 minutes ago was broken by >= 0.5 more than a minute ago, price back inside, burst back in
//   SR   support/resistance rejection: the price came within 0.5 of a level (range, yesterday, Asia, London) without breaking it, burst away
//   IP   impulse -> pullback:          a 5-minute move >= 3x usual ended 1-8 minutes ago, 25-75% of it was given back, burst in its direction
//   (mirror images for the other side.)  base+ / base- = every burst, followed / faded, with no location: what the location adds.
// Trade: enter 0.5 s or 1 s after the signal at the ask / bid; target 0.5 or 1.0 USD (filled at the target), stop 1 / 2 / 5 USD (filled at the
// quote that crossed it), closed at the quote after 60 s or 300 s. USD per trade for 0.01 lot, commission 0.08. dev = ..2026-03, test = 2026-04..

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;

static partial class Phase1
{
    static int BurstSetupStudy(string[] args)
    {
        var a = args.Where(x => !x.Contains(":")).ToArray();
        string kind = a.Length > 1 ? a[1] : "live-test", from = a.Length > 2 ? a[2] : "0000-00-00", to = a.Length > 3 ? a[3] : "9999-99-99";
        string symbol = a.Length > 4 ? a[4] : "XAUUSD";
        var dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "BacktestLab", kind, symbol);
        if (!Directory.Exists(dir)) { Console.WriteLine("no recording: " + dir); return 1; }
        var files = Directory.GetFiles(dir, "tick-*.csv*").Select(f => (file: f, day: Path.GetFileName(f).Substring(5, 10)))
            .Where(x => string.CompareOrdinal(x.day, from) >= 0 && string.CompareOrdinal(x.day, to) <= 0).OrderBy(x => x.day).ToList();
        if (files.Count == 0) { Console.WriteLine("no tick files in " + dir); return 1; }

        const double Commission = 0.08, MaxSpread = 0.35, Alpha = 1.0 / 600;
        (int win, double th)[] cfg = { (5000, 3), (5000, 5), (10000, 5) };
        string[] setups = { "LS  liquidity sweep + reversal", "SS  session high/low sweep", "EXf extreme extension, fade", "EXr extreme extension, return", "FB  failed breakout", "SR  level rejection", "IP  impulse -> pullback", "base+ any burst, follow", "base- any burst, fade" };
        int[] delays = { 500, 1000 }; int[] limits = { 60000, 300000 }; double[] tps = { 0.5, 1.0 }, sls = { 1, 2, 5 };
        var exitName = new List<string> { "60s", "300s" };
        foreach (int lim in limits) foreach (double tp in tps) foreach (double sl in sls) exitName.Add($"TP{tp:0.0}/SL{sl:0}/{lim / 1000}s");
        int C = cfg.Length, S = setups.Length, D = delays.Length, E = exitName.Count;
        var st = new double[S, C, D, E, 2, 4];                                     // [dev/test]: n, net, wins, target reached
        var per = new double[S, C, E, 4, 2];                                       // delay 0.5 s by period: n, net
        long[] perEnd = { Unix(2025, 1), Unix(2026, 1), Unix(2026, 4), long.MaxValue };

        // ---- state carried across the files
        const int N = 4500; var rs = new long[N]; var rhi = new double[N]; var rlo = new double[N]; var rmid = new double[N];
        long curTd = -1; double dayH = double.NaN, dayL = double.NaN, prevH = double.NaN, prevL = double.NaN, asiaH = double.NaN, asiaL = double.NaN, lonH = double.NaN, lonL = double.NaN;
        double vSum = 0, vSum2 = 0; long vCnt = 0; double ema5 = 0, ema10 = 0, emaM5 = 0; long warm = 0, totalTicks = 0;

        double Range(long now, int fromAgo, int toAgo, bool high, out int valid)
        {
            double v = high ? double.MinValue : double.MaxValue; valid = 0;
            for (long s = now - fromAgo; s <= now - toAgo; s++) { int k = (int)(s % N); if (rs[k] != s) continue; valid++; if (high) { if (rhi[k] > v) v = rhi[k]; } else if (rlo[k] < v) v = rlo[k]; }
            return v;
        }
        double MidAt(long s) { int k = (int)(s % N); return rs[k] == s ? rmid[k] : double.NaN; }

        var tm = new List<long>(200000); var bid = new List<double>(200000); var ask = new List<double>(200000);
        foreach (var (file, day) in files)
        {
            tm.Clear(); bid.Clear(); ask.Clear();
            {
                using var fs = new FileStream(file, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
                using Stream stream = file.EndsWith(".gz") ? new GZipStream(fs, CompressionMode.Decompress) : fs;
                using var r = new StreamReader(stream);
                r.ReadLine(); string line;
                while ((line = r.ReadLine()) != null)
                {
                    if (line.Length < 16 || line[12] != ',') continue;
                    int c2 = line.IndexOf(',', 13); if (c2 < 0) continue;
                    if (!double.TryParse(line.AsSpan(13, c2 - 13), NumberStyles.Float, Inv, out double b) || !double.TryParse(line.AsSpan(c2 + 1), NumberStyles.Float, Inv, out double k)) continue;
                    long t = ((line[0] - '0') * 10 + (line[1] - '0')) * 3600000L + ((line[3] - '0') * 10 + (line[4] - '0')) * 60000L
                           + ((line[6] - '0') * 10 + (line[7] - '0')) * 1000L + (line[9] - '0') * 100 + (line[10] - '0') * 10 + (line[11] - '0');
                    if (tm.Count > 0 && t < tm[^1]) continue;
                    tm.Add(t); bid.Add(b); ask.Add(k);
                }
            }
            int n = tm.Count; if (n < 1000) continue; totalTicks += n;
            long dayUnix = new DateTimeOffset(DateTime.ParseExact(day, "yyyy-MM-dd", Inv), TimeSpan.Zero).ToUnixTimeSeconds();
            int part = string.CompareOrdinal(day, "2026-04-01") >= 0 ? 1 : 0, period = 0; while (dayUnix >= perEnd[period]) period++;
            double Mid(int i) => (bid[i] + ask[i]) / 2;

            int bp5 = -1, bp10 = -1; var prevIn = new bool[C]; var coolUntil = new long[C]; long nextSample = 0;
            for (int i = 0; i < n; i++)
            {
                long t = tm[i], sec = dayUnix + t / 1000; double mid = Mid(i);

                // ---- every tick: the second's high / low, the day, the sessions, the VWAP
                long td = (sec + 7200) / 86400;
                if (td != curTd) { if (curTd >= 0 && !double.IsNaN(dayH)) { prevH = dayH; prevL = dayL; } curTd = td; dayH = dayL = mid; asiaH = asiaL = lonH = lonL = double.NaN; vSum = vSum2 = 0; vCnt = 0; }
                int hour = (int)(sec / 3600 % 24);
                // the levels and the VWAP used below are those BEFORE this tick
                double useAsiaH = hour >= 7 && hour < 21 ? asiaH : double.NaN, useAsiaL = hour >= 7 && hour < 21 ? asiaL : double.NaN;
                double useLonH = hour >= 13 && hour < 21 ? lonH : double.NaN, useLonL = hour >= 13 && hour < 21 ? lonL : double.NaN;
                double vwap = vCnt > 0 ? vSum / vCnt : double.NaN, vsd = vCnt > 20000 ? Math.Sqrt(Math.Max(0, vSum2 / vCnt - vwap * vwap)) : 0;
                if (mid > dayH) dayH = mid; if (mid < dayL) dayL = mid;
                if (hour >= 22 || hour < 7) { if (double.IsNaN(asiaH) || mid > asiaH) asiaH = mid; if (double.IsNaN(asiaL) || mid < asiaL) asiaL = mid; }
                else if (hour < 13) { if (double.IsNaN(lonH) || mid > lonH) lonH = mid; if (double.IsNaN(lonL) || mid < lonL) lonL = mid; }
                vSum += mid; vSum2 += mid * mid; vCnt++;
                int ri = (int)(sec % N);
                if (rs[ri] != sec) { rs[ri] = sec; rhi[ri] = rlo[ri] = mid; } else { if (mid > rhi[ri]) rhi[ri] = mid; if (mid < rlo[ri]) rlo[ri] = mid; }
                rmid[ri] = mid;

                if (t < nextSample) continue;
                nextSample = t - t % 1000 + 1000;
                while (bp5 + 1 < n && tm[bp5 + 1] <= t - 5000) bp5++;
                while (bp10 + 1 < n && tm[bp10 + 1] <= t - 10000) bp10++;
                bool has5 = bp5 >= 0 && t - tm[bp5] <= 8000, has10 = bp10 >= 0 && t - tm[bp10] <= 13000;
                double mv5 = has5 ? mid - Mid(bp5) : 0, mv10 = has10 ? mid - Mid(bp10) : 0;
                bool ready = warm > 1800 && ema5 > 0 && ema10 > 0;
                double r5 = ready && has5 ? Math.Abs(mv5) / ema5 : 0, r10 = ready && has10 ? Math.Abs(mv10) / ema10 : 0;
                if (has5) ema5 += Alpha * (Math.Abs(mv5) - ema5);
                if (has10) ema10 += Alpha * (Math.Abs(mv10) - ema10);
                double m300 = MidAt(sec - 300), usual5m = emaM5;
                if (!double.IsNaN(m300)) emaM5 += (1.0 / 3000) * (Math.Abs(mid - m300) - emaM5);
                warm++;
                if (tm[n - 1] < t + 302000) continue;
                double spread = ask[i] - bid[i];

                for (int c = 0; c < C; c++)
                {
                    double mv = cfg[c].win == 5000 ? mv5 : mv10, ratio = cfg[c].win == 5000 ? r5 : r10;
                    bool inCond = mv != 0 && ratio >= cfg[c].th && spread <= MaxSpread;
                    bool onset = inCond && !prevIn[c] && t >= coolUntil[c]; prevIn[c] = inCond;
                    if (!onset) continue;
                    coolUntil[c] = t + 10000;
                    int d = Math.Sign(mv);

                    // ---- which locations hold right now? side[s] = +1 buy, -1 sell, 0 none
                    var side = new int[S]; side[7] = d; side[8] = -d;
                    double rngH = Range(sec, 3600, 121, true, out int rv), rngL = Range(sec, 3600, 121, false, out _);
                    double recH = Range(sec, 120, 0, true, out int cv), recL = Range(sec, 120, 0, false, out _);
                    bool rngOk = rv >= 1800 && cv >= 60;
                    if (rngOk)
                    {
                        if (d < 0 && recH > rngH + 0.1 && mid < rngH) side[0] = -1; else if (d > 0 && recL < rngL - 0.1 && mid > rngL) side[0] = 1;
                        foreach (double lv in new[] { prevH, useAsiaH, useLonH }) if (!double.IsNaN(lv) && d < 0 && recH > lv + 0.1 && mid < lv) side[1] = -1;
                        foreach (double lv in new[] { prevL, useAsiaL, useLonL }) if (!double.IsNaN(lv) && d > 0 && recL < lv - 0.1 && mid > lv) side[1] = 1;
                        foreach (double lv in new[] { rngH, prevH, useAsiaH, useLonH }) if (!double.IsNaN(lv) && d < 0 && recH <= lv + 0.1 && recH >= lv - 0.5 && mid < recH) side[5] = -1;
                        foreach (double lv in new[] { rngL, prevL, useAsiaL, useLonL }) if (!double.IsNaN(lv) && d > 0 && recL >= lv - 0.1 && recL <= lv + 0.5 && mid > recL) side[5] = 1;
                    }
                    if (vsd > 0) { double z = (mid - vwap) / vsd; if (Math.Abs(z) >= 2) { if (Math.Sign(z) == d) side[2] = -d; else side[3] = d; } }
                    {
                        double oldH = Range(sec, 4200, 601, true, out int ov), oldL = Range(sec, 4200, 601, false, out _);
                        if (ov >= 1800)
                        {
                            if (d < 0 && Range(sec, 600, 60, true, out _) > oldH + 0.5 && mid < oldH) side[4] = -1;
                            else if (d > 0 && Range(sec, 600, 60, false, out _) < oldL - 0.5 && mid > oldL) side[4] = 1;
                        }
                    }
                    if (usual5m > 0)
                    {
                        double bestImp = 0, endPrice = 0;
                        for (int k = 60; k <= 480; k += 5) { double e1 = MidAt(sec - k), e0 = MidAt(sec - k - 300); if (double.IsNaN(e1) || double.IsNaN(e0)) continue; if (Math.Abs(e1 - e0) > Math.Abs(bestImp)) { bestImp = e1 - e0; endPrice = e1; } }
                        if (Math.Abs(bestImp) >= 3 * usual5m && Math.Sign(bestImp) == d)
                        {
                            double back = Math.Sign(bestImp) * (endPrice - mid) / Math.Abs(bestImp);
                            if (back >= 0.25 && back <= 0.75) side[6] = d;
                        }
                    }

                    // ---- one walk per direction and delay, shared by the locations that trade that way
                    for (int dd = -1; dd <= 1; dd += 2)
                        for (int di = 0; di < D; di++)
                        {
                            bool any = false; for (int s = 0; s < S; s++) if (side[s] == dd && (di == 0 || s < 7)) any = true;
                            if (!any) continue;
                            int e = i; while (e < n && tm[e] < t + delays[di]) e++;
                            if (e >= n) continue;
                            long t0 = tm[e]; double entry = dd > 0 ? ask[e] : bid[e];
                            var res = new double[E]; var done = new bool[E]; var hit = new bool[E]; int open = E;
                            for (int j = e + 1; j < n && open > 0; j++)
                            {
                                long dt = tm[j] - t0;
                                double prev = dd > 0 ? bid[j - 1] - entry : entry - ask[j - 1], now = dd > 0 ? bid[j] - entry : entry - ask[j];
                                if (dt > 60000)
                                {
                                    if (!done[0]) { done[0] = true; res[0] = prev; open--; }
                                    for (int x = 2; x < 8; x++) if (!done[x]) { done[x] = true; res[x] = prev; open--; }
                                }
                                if (dt > 300000) { for (int x = 1; x < E; x++) if (!done[x]) { done[x] = true; res[x] = prev; open--; } break; }
                                for (int x = 2; x < E; x++)
                                {
                                    if (done[x]) continue;
                                    int q = (x - 2) % 6; double tp = tps[q / 3], sl = sls[q % 3];
                                    if (now <= -sl) { done[x] = true; res[x] = now; open--; } else if (now >= tp) { done[x] = true; res[x] = tp; hit[x] = true; open--; }
                                }
                            }
                            if (open > 0) continue;
                            for (int s = 0; s < S; s++)
                            {
                                if (side[s] != dd || (di > 0 && s >= 7)) continue;
                                for (int x = 0; x < E; x++)
                                {
                                    double net = res[x] - Commission;
                                    st[s, c, di, x, part, 0]++; st[s, c, di, x, part, 1] += net; if (net > 0) st[s, c, di, x, part, 2]++; if (hit[x]) st[s, c, di, x, part, 3]++;
                                    if (di == 0) { per[s, c, x, period, 0]++; per[s, c, x, period, 1] += net; }
                                }
                            }
                        }
                }
            }
        }

        string F(double v) => v.ToString("+0.000;-0.000", Inv);
        string Cfg(int c) => $"{cfg[c].win / 1000,2}s>={cfg[c].th:0}";
        double Avg(int s, int c, int di, int x, int part) => st[s, c, di, x, part, 1] / Math.Max(1, st[s, c, di, x, part, 0]);
        Console.WriteLine($"\n==== SETUP + BURST: a location and a burst of speed together ({files[0].day} .. {files[^1].day}, {totalTicks:N0} ticks) ====");
        Console.WriteLine("USD per trade for 0.01 lot, real bid / ask, commission 0.08, entry 0.5 s after the signal. dev = ..2026-03, test = 2026-04..");
        int[] show = { 0, 1, 2 + 1, 2 + 4, 8 + 1, 8 + 2, 8 + 4, 8 + 5 };
        Console.WriteLine("\nlocation                        burst    dev n  test n |" + string.Concat(show.Select(x => $" {exitName[x],14}")) + " | test:" + string.Concat(show.Select(x => $" {exitName[x],14}")));
        for (int s = 0; s < S; s++)
            for (int c = 0; c < C; c++)
                Console.WriteLine($"{setups[s],-31} {Cfg(c)} {st[s, c, 0, 0, 0, 0],8:N0} {st[s, c, 0, 0, 1, 0],7:N0} |" + string.Concat(show.Select(x => $" {F(Avg(s, c, 0, x, 0)),14}")) + " |      " + string.Concat(show.Select(x => $" {F(Avg(s, c, 0, x, 1)),14}")));

        Console.WriteLine("\n-- the best exit of each location on dev (>= 200 dev trades), and what it does on test");
        Console.WriteLine("location                        burst  delay  exit            |   dev n   win%  reached TP    avg  |  test n   win%  reached TP    avg  |  2024    2025   26-Q1  26-04..09");
        int combos = 0, devPos = 0, bothPos = 0;
        for (int s = 0; s < 7; s++)
        {
            (double v, int c, int di, int x) best = (double.MinValue, 0, 0, 0);
            for (int c = 0; c < C; c++) for (int di = 0; di < D; di++) for (int x = 0; x < E; x++)
            {
                if (st[s, c, di, x, 0, 0] < 200) continue;
                combos++; double dv = Avg(s, c, di, x, 0);
                if (dv > 0) { devPos++; if (st[s, c, di, x, 1, 0] >= 30 && Avg(s, c, di, x, 1) > 0) bothPos++; }
                if (dv > best.v) best = (dv, c, di, x);
            }
            if (best.v == double.MinValue) { Console.WriteLine($"{setups[s],-31} (fewer than 200 dev trades)"); continue; }
            double dn = st[s, best.c, best.di, best.x, 0, 0], tn = Math.Max(1, st[s, best.c, best.di, best.x, 1, 0]);
            Console.WriteLine($"{setups[s],-31} {Cfg(best.c)} {delays[best.di],5}  {exitName[best.x],-15} | {dn,7:N0}  {100 * st[s, best.c, best.di, best.x, 0, 2] / dn,5:N1}  {100 * st[s, best.c, best.di, best.x, 0, 3] / dn,9:N1}%  {F(best.v)} | {st[s, best.c, best.di, best.x, 1, 0],7:N0}  {100 * st[s, best.c, best.di, best.x, 1, 2] / tn,5:N1}  {100 * st[s, best.c, best.di, best.x, 1, 3] / tn,9:N1}%  {F(Avg(s, best.c, best.di, best.x, 1))} | " +
                (best.di == 0 ? string.Join("  ", Enumerable.Range(0, 4).Select(p => F(per[s, best.c, best.x, p, 1] / Math.Max(1, per[s, best.c, best.x, p, 0])))) : "(by period only for delay 0.5 s)"));
        }
        Console.WriteLine($"\nall {combos} combinations of location x burst x delay x exit with >= 200 dev trades: positive on dev {devPos}, of those also positive on test {bothPos}");
        return 0;
    }
}
