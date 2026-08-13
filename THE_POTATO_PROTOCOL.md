# 🥔 THE POTATO PROTOCOL 🥔
### The official Norac Projects guide for absolute beginners
*If you can microwave a potato, you can run this app. No tech knowledge assumed. None. Zero.*

---

Welcome, potato. Today you're going to run **Easy Why** — an app that tells you why your computer is hot, slow, or loud. Follow the steps in order. Don't skip any. Don't improvise. Potatoes who improvise end up on Stack Overflow at 3am.

---

## Step 1 — Get Python (the thing that runs the app)

Python is a program that runs other programs. Easy Why is written in it. You need **Python 3.13**.

**Windows:**
1. Go to https://www.python.org/downloads/
2. Click the big yellow download button
3. Run the installer. **STOP. LOOK AT THE FIRST SCREEN.** There's a checkbox that says **"Add Python to PATH"**. ✅ **TICK IT.** This is the single most important click of your day. Untick it and nothing below will work and you'll blame me.
4. Click Install, let it finish, close it.

**Linux:** you probably already have Python. Open a terminal and type `python3 --version`. If it says 3.13-something, you're golden.

**Raspberry Pi:** same as Linux. Your Pi came with Python. It's fine.

## Step 2 — Get the project

**The easy way:** on the GitHub page, click the green **`< > Code`** button → **Download ZIP**. Unzip it somewhere you can find again, like your Desktop. Not your Downloads folder where files go to die.

**The cool way (optional):**
```bash
git clone https://github.com/Norac-projects/easy-why.git
```

## Step 3 — Open a terminal *inside* the project folder

This is where potatoes usually get lost, so read carefully.

**Windows:** open the `easy-why` folder in File Explorer, click the address bar at the top, type `cmd`, press Enter. A black window appears. That's the terminal. It's not hacking, it's just typing.

**Linux / Pi:** right-click inside the `easy-why` folder → "Open Terminal Here". Or open a terminal and type `cd ` (with a space) then drag the folder onto the window and press Enter.

**Checkpoint 🥔:** type `dir` (Windows) or `ls` (Linux/Pi) and press Enter. If you see `main.py` in the list, you're in the right place. If not, you're lost in the filesystem — go back to the start of Step 3.

## Step 4 — Install the ingredients

The app needs a few libraries. One command fetches all of them:

```bash
pip install -r requirements.txt
```

Press Enter. Text will scroll. This is normal. Wait for it to stop (a minute or two). If it ends without angry red errors, you win.

> 🥔 *If Windows says pip isn't recognized:* you skipped the PATH checkbox in Step 1. Reinstall Python and tick the box this time. I'm not mad, just disappointed.
>
> 🥔 *If Linux complains about "externally-managed-environment":* run
> `pip install -r requirements.txt --break-system-packages`
> (it sounds scary, it's fine here).

## Step 5 — Launch it 🚀

```bash
python main.py
```

(On Linux/Pi it might be `python3 main.py`.)

A dark dashboard opens with gauges and a big verdict at the top telling you what's going on. **You did it.** You are no longer a potato. You are a potato *with a diagnostic tool*.

## Step 6 (optional) — Unlock full power mode

Some things (certain sensors, capping the CPU speed, killing stubborn processes) need admin rights. The app works without them and shows a yellow banner telling you exactly what's limited. To unlock everything:

- **Windows:** close the app, then start the terminal itself as admin (search "cmd" in the Start menu → right-click → **Run as administrator**), go back to the folder like in Step 3, and run `python main.py` again
- **Linux / Pi:** `sudo python3 main.py`

## Now what?

- **The big banner at the top** = your answer. Read it. It tells you what's wrong AND how to fix it.
- **Top Offenders panel (right side)** = the processes hogging your machine, worst first. Select one → **Kill** (with your confirmation, nothing happens by surprise).
- **History tab** = fans went crazy 10 minutes ago? Hover over the timeline and catch the culprit red-handed.
- **Network tab** = internet crawling? See which app is hogging your connection and who it's talking to.
- **Refresh Now (toolbar)** = impatient potato? Click it to grab a fresh reading this instant instead of waiting.
- **Throttle-safe mode (toolbar)** = laptop cooking itself? Click this. It calmly slows the CPU so temps stabilize. Click again to restore full speed.
- **Generate report (toolbar)** = saves a text file with the full diagnosis. Perfect for repair shops, forums, or that one friend who "knows computers".

---

## 🥔 Potato Troubleshooting Corner 🥔

| Symptom | Cure |
|---|---|
| `python` is not recognized | The PATH checkbox. Step 1. We've been over this. |
| `No module named PySide6` | You skipped Step 4, you rascal. Run the pip command. |
| Window opens then closes instantly | Run it from the terminal (Step 5) instead of double-clicking, so you can see the error message it's trying to show you |
| No temperatures on Windows | Normal on some machines — install and run [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) and Easy Why picks it up automatically |
| "Access denied" on some button | That feature needs admin — see Step 6 |
| It says my Pi is undervolted | That's not a bug, that's the app doing its job. Buy the official power supply. Your SD card will thank you. |

---

*THE POTATO PROTOCOL™ — a Norac Projects signature. If a step failed, you skipped a step. Potatoes never skip steps.* 🥔
