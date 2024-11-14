# AnkiAnnoyer Plugin
## What it does:
- Used to slowly display the kanji on your screen to annoy you to complete that card.
- You can use keybinds or answer on the card
- Many different easy to edit options in the toolbar under AnkiAnnoyer

## Instructions:
1. download and place into a folder under AppData/Roaming/Anki2/addons21 (or by "View Files" in addon menu)
2. enable the plugin and start studying
3. edit settings like question/answer size

# Linux

Directory: ~/.local/share/Anki2/addons21/ (or by "View Files" in addon menu)

Apps cannot set their own window opacity on wayland:
Force anki to use XWayland by running anki with QT_QPA_PLATFORM="xcb" 

keyboard permissions should work fine on X11, for wayland you probably need to run sudo usermod -a -G input USERNAME (untested)

To add it to your desktop file you probably want to
Copy the anki desktop file to your user cp /usr/share/applications/anki.desktop ~/.local/share/applications
Set the exec line to Exec=QT_QPA_PLATFORM="xcb" anki %f 

For KDE Plasma my window rules look like this, adjust to taste
![linuxmomentspng](https://github.com/user-attachments/assets/a385bf41-f7fc-4e4a-9e9e-1e45513648aa)
For Gnome, good luck I guess

# AnkiAnnoyer External

## What it does:
- Used to slowly display the kanji on your screen to annoy you to complete that card.
- You have to use keybinds for everything to work properly
- Grace period, time to be fully visible, keybinds, deck path, and kanji or english are configurable.

## Instructions:
1. Install AnkiConnect addon (2055492159)
2. Set and save options at top of code (find the field names for the deck you want)
3. Open a deck and start studying
4. Run the code in AnkiAnnoyer.py
