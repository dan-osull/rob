Is your SSD full of games that you don't want to delete?

Do you have a slow or metered internet connection that means it's impractical to download games on demand?

`rob` is a command line tool that frees up space on your SSD by moving data to a library of folders on another disk.

`rob` creates a [symlink](https://en.wikipedia.org/wiki/Symbolic_link) from the original location to the library so that games continue to work and can be updated.

The process is reversible: `rob` can move a game back to your fast disk on demand. This is quicker than downloading it again and doesn't use any of your data allowance.

While `rob` was designed with games in mind it works with folders of any type.

## How to use

### Add a folder to your `rob` library

In this example, I'm going to use `rob` to move GTA5 from a small fast SSD (drive C) to a big slow disk (drive D).

1. Create a folder on your big disk for your `rob` library. This will be the destination for data. I'm using **D:\rob_library**.

2. Download **rob.exe** and put it in your `rob` library folder.

3. Search the Start menu for **cmd**. Right click the **Command Prompt** result and select **Run as Administrator**.

4. In the command prompt, change directory to your `rob` library by typing:

        pushd "d:\rob_library"

5. Make sure that the game you're moving and its app store are not running. (Check the notification area/system tray in the bottom right of your screen.)

6. Add the GTA5 folder to `rob`, using dry run mode to check for any problems:

        rob add "C:\Program Files\Epic Games\GTAV" --dry-run

    Enclose paths containing spaces in double quotes, as shown.

    *Hint: use a utility like [WinDirStat](https://windirstat.net/) to find the biggest folders on your SSD.*

7. Run the same command without `--dry-run` to move data:

        rob add "C:\Program Files\Epic Games\GTAV"

8. Done! The game data is now stored in a subfolder of your `rob` library. The original path is a symlink and continues to work.

### Example: remove a folder from your `rob` library

1. Search the Start menu for **cmd**. Right click the **Command Prompt** result and select **Run as Administrator**.

2. In the command prompt, change directory to your `rob` library by typing:

        pushd "d:\rob_library"

3. See what's in your `rob` library:

        rob list

4. Make sure that the game you're moving and its app store are not running. (Check the notification area/system tray in the bottom right of your screen.)

5. Run `rob remove` in dry run mode to check for problems:

        rob remove "C:\Program Files\Epic Games\GTAV" --dry-run

6. Run the same command without `--dry-run` to move data:

        rob remove "C:\Program Files\Epic Games\GTAV"

7. Done! The game data is back in its original location.

## Reference

```
               __
   _________  / /_
  / ___/ __ \/ __ \
 / /  / /_/ / /_/ /
/_/   \____/_.___/

Help: https://github.com/dan-osull/rob/

Usage: rob [OPTIONS] COMMAND [ARGS]...

  rob is a command line tool that frees up space on your SSD by moving data to
  a library of folders on another disk.

  rob creates a symlink from the original location to the library so that
  games continue to work and can be updated.

Options:
  -l, --library-folder DIRECTORY  The path of the library. The current folder
                                  is used by default.
  -h, --help                      Show this message and exit.

Commands:
  add     Add FOLDER_PATH to library
  list    List folders in library and show their size
  remove  Remove FOLDER_PATH from library
```

## Is this malware?

No. But you may get a false positive, in which case you need to tell your security software to unblock/allow `rob`.

Feel free to browse the code and make your own exe with **build_exe.cmd**

## Does `rob` need Administrator access?

In short: yes.

The long answer is that `rob` can work without admin access if:

1. You have enabled [Windows Developer Mode](https://docs.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development), which lets normal users create symlinks.
2. You are not copying from a protected area of the operating system, like Program Files.
3. You run **rob add** with the **--dont-copy-permissions** flag, as typically only admins can set permissions. This could have negative implications for security.

Because `rob` is designed for games, which are usually in Program Files, in practice it is easiest to run the tool from an admin Command Prompt.

## Can't I just copy a folder and make a symlink myself?

Shut up.

## Thanks

This software is dedicated to Comcast, the worst company in the history of the world.