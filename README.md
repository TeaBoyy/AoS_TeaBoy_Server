# AoS_TeaBoy_Server
Grenade launchers (and more) PySnip scripts for OpenSpades game server

Contents of this repository is free to use and modify by anyone.

This repository also contains work (in this case scripts) downloaded from other repositories and web-sites.
List of reposities and web-sites (not full list yet) from which work (scripts) were taken from:
* https://github.com/aloha-pk/spades-public
* https://github.com/1AmYF/aos-server-mods
* https://github.com/matpow2/pyspades-userscripts

In general files that are taken from other sources are added to this repository with the first commit message (in file's history) pointing to the source.

# Video demo
Gameplay footage: https://youtu.be/Es9Al90DPzw?si=ZdJWAcANHO6rBPzD

Experiment - trying out ABBS bots with grenade launchers: https://youtu.be/ckY1NPCrrkA?si=yaKykJCBCAD_T2qD

# Environment
1. Scripts are not ported to piqueserver. Runs/tested on PySnip only.
2. Everything should work fine with the run.exe in this repository (can find link to source from which I downloaded executable in file history's commit message).
3. For grenade launchers, rename grenade_launchers_config.txt to config.txt. Should work out of the box.
4. Tested for a while now on Optik Link free hosting. The only issue is often dropping connection to the master server, yet it's PySnip error. Haven't had any grenade launchers related issues for a while (I think fixing infinite loop helped to prevent server getting stuck).

# Scripts
1. grenade_launchers.py. Guns shoot grenades. Grenades penetrate blocks and explode. Can also hold V and shoot to restore destroyed blocks (can be enabled by setting config field "nade_launcher_restore_blocks" to "true").
2. tc_mode_extension.py. Allows to scale down tent placement on a regular TC (Territorial Control) gamemode. Gamemode field in config can be set to any string, it doesn't matter. Also, script reports location of a tent in global chat every time someone is capturing it.
3. And more stuff.

# Known issues
1. grenade_launchers.py:
    1. Shooting grenades doesn't stop after running out of bullets on BetterSpades client. Probably can fix by checking if ammo != 0 and stop loop.
    2. Camping on a mountain/hill/tower gives too much advantage. Can't shoot high enough from the ground, but can easily hit anyone down below. Use build_height.py as a crutch to limit how high players can build.
    3. Increasing projectile speed beyond ~2.0 makes grenades clip through blocks. So, can't really shoot more straight trajectory at the moment.
2. snowflakes.py and/or snow.py:
    1. Might cause errors if added as is with other scripts, like ABBS.py (Advanced Battle Bots) I think.
3. snowflakes.py:
    1. Players, tents (intels?) can spawn on snowflakes sometimes. Especially concerning with grenade_launchers.py - gives way too much advantage.
