import argparse
import math
import os
import time
import tkinter
import tkinter.ttk
import winsound

from threading import Thread, Event

if os.path.exists("userConfiguration.py"):
    import userConfiguration  # type: ignore  # ignoring because it's the user's config and might or might not exist
    configurationDicts = userConfiguration.configurationDicts
else:
    configurationDicts: dict = {"default": {
                                    "pauses": 1,
                                    "pauseTime": "00:05:00",
                                    "focusTime": "01:00:00",
                                    "pauseTimeEndSound": "C:\\Windows\\Media\\Alarm02.wav",
                                    "focusTimeEndSound": "C:\\Windows\\Media\\Alarm02.wav"}}

argParser = argparse.ArgumentParser()
argParser.add_argument("-configuration",
                       type=str,
                       help="Configuration to use.",
                       default="default")
argParser.add_argument("-noTopmost",
                       help="Disable topmost attribute (window can covered by others)",
                       default=False,
                       action="store_true")
args = argParser.parse_args()
print("Used arguments are:")
print(args)
configurationDict = configurationDicts[args.configuration]


def pBarLoopThread(slotList: list, event: Event):
    for slotValue in range(len(slotList)):
        # Leave loop if stop event is set.
        if event.is_set():
            print("Thread ended by event.")
            break

        # Set current slot value to bar maximum.
        labelFocusTimeOnBar["text"] = "00:00:00"
        focusPbar["value"] = 0
        focusPbar["maximum"] = slotList[slotValue]

        # Change bar behavior: odd value = increasing, even value = decreasing
        if slotValue % 2 == 0:
            # Progress for focus slots.
            for i in range(1,
                           slotList[slotValue] + 1):
                focusPbar["value"] = i
                # Update time label
                labelFocusTimeOnBar["text"] = time.strftime("%H:%M:%S",
                                                            time.gmtime(i))
                if i == slotList[slotValue]:
                    winsound.PlaySound(configurationDict["focusTimeEndSound"],
                                       winsound.SND_FILENAME | winsound.SND_ASYNC)

                window.update_idletasks()

                # Leave loop if stop event is set.
                if event.is_set():
                    print("Thread ended by event.")
                    break

                time.sleep(1)
        else:
            # Progress for pause slots.
            # For decreasing steps, range must start with upper value and end with lower value; lower value set to -1 to end with zero.
            for i in range(slotList[slotValue],
                           -1,
                           -1):
                focusPbar["value"] = i
                # Update time label
                labelFocusTimeOnBar["text"] = time.strftime("%H:%M:%S",
                                                            time.gmtime(i))
                if i == 0:
                    winsound.PlaySound(configurationDict["pauseTimeEndSound"],
                                       winsound.SND_FILENAME | winsound.SND_ASYNC)

                window.update_idletasks()

                # Leave loop if stop event is set.
                if event.is_set():
                    print("Thread ended by event.")
                    break

                time.sleep(1)

        window.update_idletasks()
    print("Thread ended")
    pBarEvent.clear()
    buttonStart["text"] = "Start"


def startButtonClicked():
    if buttonStart["text"] == "Start":
        # Get focus time
        overallTimeStruct = time.strptime(entryFocusTime.get(),
                                          "%H:%M:%S")
        overallTimeSeconds = overallTimeStruct.tm_hour * 3600 + overallTimeStruct.tm_min * 60 + overallTimeStruct.tm_sec
        # Get pause time
        pauseTimeStruct = time.strptime(entryPauseTime.get(),
                                        "%H:%M:%S")
        pauseTimeSeconds = pauseTimeStruct.tm_hour * 3600 + pauseTimeStruct.tm_min * 60 + pauseTimeStruct.tm_sec
        # Get number of pause
        pauses = int(entryPauses.get())

        # Prepare focus slots
        focusTimeSeconds = overallTimeSeconds - pauseTimeSeconds  # Focus time contains pauses, real focus time is without pauses.
        focusSlots = pauses + 1  # 1 pause = 2 focus parts, 2 pauses = 3 focus parts
        focusTimeSlotSeconds = math.floor(focusTimeSeconds / focusSlots)  # Every slot has floored seconds. Last slot will get the remainder added later in the code.

        slotList = []
        for i in range(1, focusSlots):
            print("Focus time slot #{}: {}".format(i, focusTimeSlotSeconds))
            slotList.append(focusTimeSlotSeconds)
            print("Pause time slot #{}: {}".format(i, pauseTimeSeconds))
            slotList.append(pauseTimeSeconds)
        remainder = overallTimeSeconds - pauses * (focusTimeSlotSeconds + pauseTimeSeconds)
        print("Last slot: {}".format(remainder))
        slotList.append(remainder)
        # Provide list (pause_time, focus_time_1, ..., focus_time_n) to thread function
        Thread(target=pBarLoopThread, args=(slotList, pBarEvent)).start()
        buttonStart["text"] = "Stop"
    else:
        pBarEvent.set()
        buttonStart["text"] = "Start"


# Create GUI
window = tkinter.Tk()
window.title("Focus timer")
window.geometry("230x120")

labelFocusTime = tkinter.Label(master=window,
                               text="Focus time")
labelFocusTime.grid(column=0,
                    row=0)

entryFocusTime = tkinter.Entry(master=window)
entryFocusTime.grid(column=1,
                    row=0)

labelPauseTime = tkinter.Label(master=window,
                               text="Pause time")
labelPauseTime.grid(column=0,
                    row=1)

entryPauseTime = tkinter.Entry(master=window)
entryPauseTime.grid(column=1,
                    row=1)

labelPauses = tkinter.Label(master=window,
                            text="Pauses")
labelPauses.grid(column=0,
                 row=2)

entryPauses = tkinter.Entry(master=window)
entryPauses.grid(column=1,
                 row=2)

buttonStart = tkinter.Button(master=window,
                             text="Start",
                             command=startButtonClicked)
buttonStart.grid(column=0,
                 row=3,
                 columnspan=2)

focusPbar = tkinter.ttk.Progressbar(master=window)
focusPbar.grid(column=0,
               row=4,
               columnspan=2)

labelFocusTimeOnBar = tkinter.Label(master=window,
                                    text="00:00:00")
labelFocusTimeOnBar.grid(column=0,
                         row=4,
                         columnspan=2)

# Now set start time, pause time and end time based on config
entryPauses.insert(index=0,
                   string=configurationDict["pauses"])
entryPauseTime.insert(index=0,
                      string=configurationDict["pauseTime"])
entryFocusTime.insert(index=0,
                      string=configurationDict["focusTime"])

pBarEvent = Event()

if args.noTopmost is False:
    window.attributes("-topmost", True)
window.mainloop()
