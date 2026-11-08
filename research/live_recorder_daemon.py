"""
24/7 Live Recorder & cBot Fleet Watchdog Daemon (Production Grade)
------------------------------------------------------------------
Supervises continuous market data recording and execution on cTrader:
- Supervises BTCUSD, ETHUSD (24/7) and XAUUSD (Active sessions)
- Monitors file update timestamps in %LOCALAPPDATA%\\BacktestLab\\live\\<symbol>\\
- Correctly distinguishes initial warmup (up to 300s) from live inactivity (>180s)
- Detects hangs: if no fresh tick arrives for > 180s during live mode, restarts
- Automatically manages weekend transitions for XAUUSD (Sunday 22:00 UTC open)
- Writes real-time telemetry to docs/data/watchdog_status.json
"""

import os
import sys
import time
import json
import signal
import subprocess
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

APPDATA = os.environ.get('LOCALAPPDATA', '')
LIVE_BASE = os.path.join(APPDATA, 'BacktestLab', 'live')
LOGS_BASE = os.path.join(APPDATA, 'BacktestLab', 'logs')
os.makedirs(LOGS_BASE, exist_ok=True)

STATUS_JSON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'data', 'watchdog_status.json')
os.makedirs(os.path.dirname(STATUS_JSON), exist_ok=True)

# CLI Configuration
CLI_CONFIG_PATH = os.path.expanduser(r'~\OneDrive\เอกสาร\BacktestLab\cli.json')
if not os.path.exists(CLI_CONFIG_PATH):
    CLI_CONFIG_PATH = os.path.expanduser(r'~\Documents\BacktestLab\cli.json')

with open(CLI_CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
    cli_cfg = json.load(f)

with open(cli_cfg['ctidFile'], 'r', encoding='utf-8') as f:
    CTID = f.read().strip()

PWD_FILE = cli_cfg['pwdFile']
ACCOUNT = cli_cfg['account']
ALGO_FILE = os.path.expanduser(r'~\OneDrive\เอกสาร\cAlgo\Sources\Robots\BacktestLab.algo')
if not os.path.exists(ALGO_FILE):
    ALGO_FILE = os.path.expanduser(r'~\Documents\cAlgo\Sources\Robots\BacktestLab.algo')

CLI_EXE = os.path.expandvars(r'%LOCALAPPDATA%\Programs\cTrader CLI\ctrader-cli.exe')

def is_market_open(symbol):
    if symbol in ['BTCUSD', 'ETHUSD']:
        return True # Crypto 24/7
    # For Forex / Metals (XAUUSD): Closes Friday 21:55 UTC, Reopens Sunday 22:00 UTC
    now_utc = datetime.now(timezone.utc)
    weekday = now_utc.weekday() # Monday is 0, Sunday is 6
    hour = now_utc.hour
    minute = now_utc.minute
    
    if weekday == 4 and (hour > 21 or (hour == 21 and minute >= 55)):
        return False
    if weekday == 5:
        return False
    if weekday == 6 and hour < 22:
        return False
        
    return True

class SymbolSupervisor:
    def __init__(self, symbol, max_inactivity_sec=180, warmup_timeout_sec=300):
        self.symbol = symbol
        self.max_inactivity_sec = max_inactivity_sec
        self.warmup_timeout_sec = warmup_timeout_sec
        self.process = None
        self.log_file = None
        self.start_time = None
        self.restart_count = 0
        self.last_stoppage_time = None
        self.baseline_file_mtime = 0
        self.last_fresh_mtime = 0
        self.has_received_fresh_tick = False
        self.status = "INITIALIZING"

    def get_latest_file_mtime(self):
        sym_dir = os.path.join(LIVE_BASE, self.symbol)
        if not os.path.exists(sym_dir):
            return 0
        files = [os.path.join(sym_dir, f) for f in os.listdir(sym_dir)]
        if not files:
            return 0
        return max(os.path.getmtime(f) for f in files)

    def start(self):
        if not is_market_open(self.symbol):
            self.status = "WEEKEND_STANDBY"
            return
            
        self.baseline_file_mtime = self.get_latest_file_mtime()
        self.has_received_fresh_tick = False
        self.last_fresh_mtime = 0

        log_path = os.path.join(LOGS_BASE, f"{self.symbol}-cli.log")
        self.log_file = open(log_path, 'a', encoding='utf-8', errors='replace')
        self.log_file.write(f"\n[{datetime.now(timezone.utc).isoformat()}] === LAUNCHING INSTANCE FOR {self.symbol} ===\n")
        self.log_file.flush()

        cmd = [
            CLI_EXE,
            'run',
            ALGO_FILE,
            f'--ctid={CTID}',
            f'--pwd-file={PWD_FILE}',
            f'--account={ACCOUNT}',
            f'--symbol={self.symbol}',
            '--period=m1',
            '--full-access',
            '--RecordMarket=true',
            '--PlaceOrders=true',
            '--Lots=0.01'
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=self.log_file,
                stderr=subprocess.STDOUT,
                text=True
            )
            self.start_time = time.time()
            self.status = "WARMING_UP"
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] Started {self.symbol} instance (PID: {self.process.pid})")
        except Exception as e:
            self.status = f"START_FAILED: {str(e)[:30]}"
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] Failed to start {self.symbol}: {e}")

    def stop(self, reason="RESTART"):
        if self.process:
            self.last_stoppage_time = datetime.now(timezone.utc).isoformat()
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] Stopping {self.symbol} (PID: {self.process.pid}) - Reason: {reason}")
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

        if self.log_file:
            try:
                self.log_file.close()
            except Exception:
                pass
            self.log_file = None

    def poll_and_recover(self):
        now = time.time()
        market_open = is_market_open(self.symbol)

        # 1. Market Closed Transition
        if not market_open:
            if self.process is not None:
                self.stop(reason="MARKET_CLOSED")
            self.status = "WEEKEND_STANDBY"
            return

        # 2. Market Open but Process Not Running
        if self.process is None:
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] {self.symbol} is open but not running. Launching...")
            self.restart_count += 1
            self.start()
            return

        # 3. Check if Process Terminated unexpectedly
        exit_code = self.process.poll()
        if exit_code is not None:
            self.last_stoppage_time = datetime.now(timezone.utc).isoformat()
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] [ALERT] {self.symbol} exited with code {exit_code}. Resuming now...")
            self.stop(reason=f"EXIT_CODE_{exit_code}")
            self.restart_count += 1
            time.sleep(3)
            self.start()
            return

        # 4. Check Fresh File Updates
        current_mtime = self.get_latest_file_mtime()
        
        # Check if fresh tick arrived after start
        if current_mtime > self.baseline_file_mtime:
            self.has_received_fresh_tick = True
            self.last_fresh_mtime = current_mtime
            self.status = "RECORDING_ACTIVE"

        if not self.has_received_fresh_tick:
            # During initial startup & history warmup (allow up to warmup_timeout_sec)
            self.status = "WARMING_UP"
            warmup_age = now - self.start_time
            if warmup_age > self.warmup_timeout_sec:
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] [WARMUP TIMEOUT] {self.symbol} exceeded {self.warmup_timeout_sec}s warmup without fresh tick. Restarting...")
                self.stop(reason="WARMUP_TIMEOUT")
                self.restart_count += 1
                time.sleep(3)
                self.start()
                return
        else:
            # Fresh ticks are active! Check live inactivity timeout
            inactivity = now - self.last_fresh_mtime
            if inactivity > self.max_inactivity_sec:
                stoppage_dt = datetime.fromtimestamp(self.last_fresh_mtime, timezone.utc).isoformat()
                self.last_stoppage_time = stoppage_dt
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] [LIVE INACTIVITY ALERT] {self.symbol} inactive for {inactivity:.0f}s (Stopped at {stoppage_dt}). Resuming recording...")
                self.stop(reason="LIVE_INACTIVITY_TIMEOUT")
                self.restart_count += 1
                time.sleep(3)
                self.start()
                return

    def get_info(self):
        now = time.time()
        if self.has_received_fresh_tick and self.last_fresh_mtime:
            inact_sec = int(now - self.last_fresh_mtime)
        elif self.process and self.start_time:
            inact_sec = int(now - self.start_time) # seconds spent warming up
        else:
            inact_sec = None

        return {
            'symbol': self.symbol,
            'status': self.status,
            'pid': self.process.pid if self.process else None,
            'uptime_seconds': int(now - self.start_time) if (self.process and self.start_time) else 0,
            'restart_count': self.restart_count,
            'has_fresh_ticks': self.has_received_fresh_tick,
            'last_fresh_mtime_utc': datetime.fromtimestamp(self.last_fresh_mtime, timezone.utc).isoformat() if self.last_fresh_mtime else None,
            'last_stoppage_utc': self.last_stoppage_time,
            'inactivity_or_warmup_seconds': inact_sec
        }

def run_watchdog():
    print("================================================================================")
    print("STARTING 24/7 LIVE RECORDER & FLEET SUPERVISOR WATCHDOG (FIXED WARMUP)")
    print(f"Account: {ACCOUNT} | CTID: {CTID}")
    print(f"Target Symbols: BTCUSD (24/7), ETHUSD (24/7), XAUUSD (Autosync)")
    print(f"Live Output: {LIVE_BASE}")
    print("================================================================================")

    supervisors = {
        'BTCUSD': SymbolSupervisor('BTCUSD', max_inactivity_sec=180, warmup_timeout_sec=300),
        'ETHUSD': SymbolSupervisor('ETHUSD', max_inactivity_sec=180, warmup_timeout_sec=300),
        'XAUUSD': SymbolSupervisor('XAUUSD', max_inactivity_sec=300, warmup_timeout_sec=300)
    }

    # Initial start
    for s in supervisors.values():
        s.start()

    daemon_start_time = time.time()

    def handle_exit(signum, frame):
        print("\nWatchdog received shutdown signal. Stopping all instances cleanly...")
        for s in supervisors.values():
            s.stop(reason="WATCHDOG_SHUTDOWN")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    iteration = 0
    while True:
        try:
            iteration += 1
            for s in supervisors.values():
                s.poll_and_recover()

            status_payload = {
                'watchdog_heartbeat_utc': datetime.now(timezone.utc).isoformat(),
                'daemon_uptime_seconds': int(time.time() - daemon_start_time),
                'active_supervisors': len(supervisors),
                'symbols': {sym: s.get_info() for sym, s in supervisors.items()}
            }

            with open(STATUS_JSON, 'w', encoding='utf-8') as f:
                json.dump(status_payload, f, indent=2)

            if iteration % 6 == 0:
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] Heartbeat: " +
                      " | ".join(f"{sym}: {s.status} (Fresh: {s.has_received_fresh_tick}, Sec: {s.get_info()['inactivity_or_warmup_seconds']}s)" for sym, s in supervisors.items()))

            time.sleep(15)

        except Exception as e:
            print(f"[WATCHDOG LOOP ERROR]: {e}")
            time.sleep(10)

if __name__ == '__main__':
    run_watchdog()
