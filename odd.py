Last login: Mon May 25 10:23:40 on ttys002
lioncrown@lioncrowndeMacBook-Neo ~ % cd weinstein_scanner 
lioncrown@lioncrowndeMacBook-Neo weinstein_scanner % ls -tlr
total 152
-rw-r--r--  1 lioncrown  staff  6933 25  5 10:43 weinstein_scanner.py
-rw-r--r--  1 lioncrown  staff  7564 25  5 10:49 wei2.py
-rw-r--r--  1 lioncrown  staff   939 25  5 11:02 t1.py
-rw-r--r--  1 lioncrown  staff  8185 25  5 11:08 wei.py
-rw-r--r--  1 lioncrown  staff  7347 25  5 11:10 wei3.py
-rw-r--r--  1 lioncrown  staff  6731 25  5 11:11 w6.py
-rw-r--r--  1 lioncrown  staff   175 25  5 11:14 weinstein_stage2_20260522.csv
-rw-r--r--  1 lioncrown  staff   175 25  5 11:17 weinstein_stage2_20260525.csv
-rw-r--r--  1 lioncrown  staff   251 25  5 11:24 weinstein_stage2_20260523.csv
-rw-r--r--  1 lioncrown  staff  6944 25  5 11:26 w2.py
-rw-r--r--  1 lioncrown  staff   175 25  5 11:27 weinstein_stage2_20260530.csv
-rw-r--r--  1 lioncrown  staff  7181 25  5 11:35 w.py
lioncrown@lioncrowndeMacBook-Neo weinstein_scanner % vi wgui.py
lioncrown@lioncrowndeMacBook-Neo weinstein_scanner % python3 wgui.py
2026-05-25 12:25:50,259 | 2021 | 6154989568 | [open_context_base.py:410] _init_connect_sync: New connect ready: conn=7464532155844564071(1) context=<futu.quote.open_quote_context.OpenQuoteContext object at 0x10bd10d70>
2026-05-25 12:26:22,958 | 2021 | 6188642304 | [open_context_base.py:518] on_disconnect: Disconnected: conn=0(1) reason=CallClose
lioncrown@lioncrowndeMacBook-Neo weinstein_scanner % 
lioncrown@lioncrowndeMacBook-Neo weinstein_scanner % ls -tlr
total 216
-rw-r--r--  1 lioncrown  staff   6933 25  5 10:43 weinstein_scanner.py
-rw-r--r--  1 lioncrown  staff   7564 25  5 10:49 wei2.py
-rw-r--r--  1 lioncrown  staff    939 25  5 11:02 t1.py
-rw-r--r--  1 lioncrown  staff   8185 25  5 11:08 wei.py
-rw-r--r--  1 lioncrown  staff   7347 25  5 11:10 wei3.py
-rw-r--r--  1 lioncrown  staff   6731 25  5 11:11 w6.py
-rw-r--r--  1 lioncrown  staff    175 25  5 11:14 weinstein_stage2_20260522.csv
-rw-r--r--  1 lioncrown  staff    175 25  5 11:17 weinstein_stage2_20260525.csv
-rw-r--r--  1 lioncrown  staff    251 25  5 11:24 weinstein_stage2_20260523.csv
-rw-r--r--  1 lioncrown  staff   6944 25  5 11:26 w2.py
-rw-r--r--  1 lioncrown  staff    175 25  5 11:27 weinstein_stage2_20260530.csv
-rw-r--r--  1 lioncrown  staff   7181 25  5 11:35 w.py
-rw-r--r--  1 lioncrown  staff  28563 25  5 12:31 wgui.py
-rw-r--r--  1 lioncrown  staff   1574 25  5 15:24 weinstein_stage2_20260524.csv
lioncrown@lioncrowndeMacBook-Neo weinstein_scanner % view weinstein_stage2_20260524.csv 
lioncrown@lioncrowndeMacBook-Neo weinstein_scanner % top
lioncrown@lioncrowndeMacBook-Neo weinstein_scanner % ls -tlr
total 216
-rw-r--r--  1 lioncrown  staff   6933 25  5 10:43 weinstein_scanner.py
-rw-r--r--  1 lioncrown  staff   7564 25  5 10:49 wei2.py
-rw-r--r--  1 lioncrown  staff    939 25  5 11:02 t1.py
-rw-r--r--  1 lioncrown  staff   8185 25  5 11:08 wei.py
-rw-r--r--  1 lioncrown  staff   7347 25  5 11:10 wei3.py
-rw-r--r--  1 lioncrown  staff   6731 25  5 11:11 w6.py
-rw-r--r--  1 lioncrown  staff    175 25  5 11:14 weinstein_stage2_20260522.csv
-rw-r--r--  1 lioncrown  staff    175 25  5 11:17 weinstein_stage2_20260525.csv
-rw-r--r--  1 lioncrown  staff    251 25  5 11:24 weinstein_stage2_20260523.csv
-rw-r--r--  1 lioncrown  staff   6944 25  5 11:26 w2.py
-rw-r--r--  1 lioncrown  staff    175 25  5 11:27 weinstein_stage2_20260530.csv
-rw-r--r--  1 lioncrown  staff   7181 25  5 11:35 w.py
-rw-r--r--  1 lioncrown  staff  28563 25  5 12:31 wgui.py
-rw-r--r--  1 lioncrown  staff   1574 25  5 15:24 weinstein_stage2_20260524.csv
lioncrown@lioncrowndeMacBook-Neo weinstein_scanner %     
lioncrown@lioncrowndeMacBook-Neo weinstein_scanner % top

Processes: 657 total, 3 running, 654 sleeping, 2623 threads                                                    18:23:48
Load Avg: 1.84, 1.42, 1.39  CPU usage: 18.32% user, 19.43% sys, 62.24% idle
SharedLibs: 513M resident, 112M data, 77M linkedit. MemRegions: 0 total, 0B resident, 0B private, 1046M shared.
PhysMem: 7554M used (1585M wired, 1819M compressor), 169M unused.
VM: 285T vsize, 6144M framework vsize, 0(0) swapins, 0(0) swapouts. Networks: packets: 739794/338M in, 617371/136M out.
Disks: 1457218/31G read, 721613/13G written.

PID   COMMAND      %CPU      TIME     #TH    #WQ  #PORT MEM    PURG   CMPRS  PGRP PPID STATE    BOOSTS
1432  FTNN         33.4      10:06.38 27     4    684-  444M-  0B     180M-  1432 1    sleeping *2+[2530]
405   WindowServer 31.6      46:37.67 18     5    2544- 389M-  25M+   188M-  405  1    sleeping *0[1]
0     kernel_task  18.3      31:11.19 474/6  0    0     45M+   0B     0B     0    0    running   0[0]
336   fseventsd    11.1      00:51.40 12     1    167   4816K+ 0B     1440K- 336  1    sleeping *0[1]
408   loginwindow  9.7       00:48.71 6      5    652+  49M+   0B     23M-   408  1    sleeping *0[561]
606   WindowManage 5.6       01:15.08 6      3    324-  16M+   0B     5856K- 606  1    sleeping *0[16278+]
3646  top          5.0       09:13.95 1/1    0    38-   8416K  0B     3264K  3646 1723 running  *0[1]
4720  top          5.0       00:05.90 1/1    0    30    7568K  0B     0B     4720 1729 running  *0[1]
730   Finder       4.6       01:58.63 7      4    505   127M+  64K-   48M-   730  1    sleeping *0[864+]
3859  Google Chrom 4.4       17:59.18 17     1    206   415M   0B     64M+   657  657  sleeping *39294+[655]
361   mds          4.0       01:10.26 11     8    319+  29M+   0B     19M-   361  1    sleeping *0[1]
657   Google Chrom 3.3       05:59.13 45     3    883   177M   0B     64M-   657  1    sleeping *2460[2153]
752   replayd      2.9       00:02.07 6      5    109-  8513K+ 0B     4240K- 752  1    sleeping  0[52]
574   mds_stores   2.9       02:35.51 8      6    133   19M-   0B     11M-   574  1    sleeping *0[1]
413   runningboard 2.7       01:21.53 7      6    801-  9344K+ 0B     1200K- 413  1    sleeping *9+[1]
719   Calendar     2.6       01:04.66 6      4    344   54M+   0B     24M-   719  1    sleeping *0[3255]
669   Terminal     2.4       03:23.96 11     4    445-  119M-  21M+   25M    669  1    sleeping *0[2506+]
375   launchservic 2.3       00:16.27 8      7    538-  6032K+ 0B     768K-  375  1    sleeping *1+[51150+]
727   ControlCente 2.3       00:08.63 10     6    563+  31M    0B     14M-   727  1    sleeping *3+[2993+]
534   com.apple.Ap 1.9       04:49.24 12     10   2232+ 32M    0B     9184K  534  1    sleeping  0[1]
332   logd         1.8       01:21.26 5      4    2101- 21M-   0B     24M-   332  1    sleeping *0[1]
726   Dock         1.6       00:10.22 4      2    470-  54M-   0B     48M-   726  1    sleeping *1[9205]
  [已還原2026年5月25日 下午7:51:31]
Last login: Mon May 25 19:51:27 on console
Restored session: 2026年 5月25日 星期一 18時23分48秒 CST
lioncrown@lioncrowndeMacBook-Neo weinstein_scanner % 
lioncrown@lioncrowndeMacBook-Neo weinstein_scanner % ls -tlkr
total 180
-rw-r--r--  1 lioncrown  staff   6933 25  5 10:43 weinstein_scanner.py
-rw-r--r--  1 lioncrown  staff   7564 25  5 10:49 wei2.py
-rw-r--r--  1 lioncrown  staff    939 25  5 11:02 t1.py
-rw-r--r--  1 lioncrown  staff   8185 25  5 11:08 wei.py
-rw-r--r--  1 lioncrown  staff   7347 25  5 11:10 wei3.py
-rw-r--r--  1 lioncrown  staff   6731 25  5 11:11 w6.py
-rw-r--r--  1 lioncrown  staff    175 25  5 11:14 weinstein_stage2_20260522.csv
-rw-r--r--  1 lioncrown  staff    175 25  5 11:17 weinstein_stage2_20260525.csv
-rw-r--r--  1 lioncrown  staff    251 25  5 11:24 weinstein_stage2_20260523.csv
-rw-r--r--  1 lioncrown  staff   6944 25  5 11:26 w2.py
-rw-r--r--  1 lioncrown  staff    175 25  5 11:27 weinstein_stage2_20260530.csv
-rw-r--r--  1 lioncrown  staff   7181 25  5 11:35 w.py
-rw-r--r--  1 lioncrown  staff  28563 25  5 12:31 wgui.py
-rw-r--r--  1 lioncrown  staff   1574 25  5 15:24 weinstein_stage2_20260524.csv
-rw-r--r--  1 lioncrown  staff  34557 25  5 15:45 wgui2.py
-rw-r--r--  1 lioncrown  staff   1279 25  5 16:31 t.py
-rw-r--r--  1 lioncrown  staff  32250 25  5 18:15 wgui3.py
lioncrown@lioncrowndeMacBook-Neo weinstein_scanner % cd ..
lioncrown@lioncrowndeMacBook-Neo ~ % ls -tlr
total 1344
drwxr-xr-x+  4 lioncrown  staff    128 12  5 20:13 Public
drwx------   3 lioncrown  staff     96 12  5 20:13 Movies
drwx------+  3 lioncrown  staff     96 12  5 20:13 Documents
drwx------+  4 lioncrown  staff    128 12  5 20:13 Pictures
drwx------+  5 lioncrown  staff    160 17  5 11:23 Desktop
drwx------+  4 lioncrown  staff    128 17  5 15:48 Music
-rw-r--r--   1 lioncrown  staff   3703 17  5 16:50 odd1.py
-rw-r--r--   1 lioncrown  staff  13179 17  5 18:31 app1.py
-rw-r--r--   1 lioncrown  staff  16451 17  5 19:08 odd8.py
drwx------@ 86 lioncrown  staff   2752 17  5 21:22 Library
-rw-r--r--   1 lioncrown  staff  16449 18  5 20:57 railway.py
-rw-r--r--@  1 lioncrown  staff  19022 19  5 20:32 odd2.py
-rw-r--r--@  1 lioncrown  staff  22093 19  5 21:18 odd3.py
-rw-r--r--@  1 lioncrown  staff  22290 20  5 21:58 odd.bak
-rw-r--r--   1 lioncrown  staff   4476 21  5 21:16 money_flow.py
-rw-r--r--   1 lioncrown  staff   3231 21  5 21:23 money.py
-rw-r--r--   1 lioncrown  staff   3792 21  5 21:27 scraper.py
drwxr-xr-x   4 lioncrown  staff    128 21  5 21:28 __pycache__
-rw-r--r--   1 lioncrown  staff  23573 21  5 21:59 odd.v2.py
-rw-r--r--   1 lioncrown  staff  25618 21  5 22:31 odd.norci.py
-rw-r--r--   1 lioncrown  staff  37773 21  5 23:37 q.py
-rw-r--r--   1 lioncrown  staff  24774 22  5 22:00 odd.py.nolog
-rw-r--r--   1 lioncrown  staff     19 23  5 12:49 Procfile
-rw-r--r--   1 lioncrown  staff     42 23  5 15:55 requirements.txt
-rw-r--r--   1 lioncrown  staff    150 23  5 15:55 nixpacks.toml
-rw-r--r--   1 lioncrown  staff    160 23  5 16:04 railway.json
-rw-r--r--@  1 lioncrown  staff  32214 23  5 16:13 odd.py.railway
-rw-r--r--   1 lioncrown  staff    709 23  5 16:19 Dockerfile
-rw-r--r--   1 lioncrown  staff  31761 24  5 13:26 odd.py.old
drwxr-xr-x   8 lioncrown  staff    256 24  5 13:31 my-odds-app
-rw-r--r--@  1 lioncrown  staff  31324 24  5 14:20 odd.py.20260524.1
-rw-r--r--   1 lioncrown  staff   8413 24  5 14:33 odd.py.railway.cpgz
-rw-r--r--   1 lioncrown  staff  31384 24  5 16:29 odd.py.ok
-rw-r--r--   1 lioncrown  staff  33736 24  5 17:44 odd.py.freeze
-rw-r--r--   1 lioncrown  staff  35029 24  5 18:37 odd.ok
-rw-r--r--   1 lioncrown  staff  30221 24  5 19:07 odd.py.graphql
-rw-r--r--   1 lioncrown  staff  35192 24  5 19:28 odd.py.graphql2
-rw-r--r--   1 lioncrown  staff     78 24  5 19:40 package.json
-rw-r--r--   1 lioncrown  staff  33108 24  5 19:40 package-lock.json
drwxr-xr-x  77 lioncrown  staff   2464 24  5 19:40 node_modules
-rw-r--r--   1 lioncrown  staff  31513 24  5 19:51 odd.py.night
drwxr-xr-x   8 lioncrown  staff    256 24  5 20:18 hkjc-bridge
drwxr-xr-x  30 lioncrown  staff    960 24  5 23:06 logs
-rw-r--r--   1 lioncrown  staff  32998 24  5 23:11 odd.py
drwxr-xr-x  26 lioncrown  staff    832 24  5 23:51 templates
drwxr-xr-x  19 lioncrown  staff    608 25  5 18:22 weinstein_scanner
drwx------@ 29 lioncrown  staff    928 25  5 19:53 Downloads
lioncrown@lioncrowndeMacBook-Neo ~ % cd hkjc-bridge 
lioncrown@lioncrowndeMacBook-Neo hkjc-bridge % ls -tlr
total 104
-rw-r--r--   1 lioncrown  staff   3054 24  5 19:48 server.js.old
drwxr-xr-x  77 lioncrown  staff   2464 24  5 20:06 node_modules
-rw-r--r--   1 lioncrown  staff    382 24  5 20:06 package.json
-rw-r--r--   1 lioncrown  staff  33758 24  5 20:06 package-lock.json
-rw-r--r--   1 lioncrown  staff   5235 24  5 20:12 server.js
lioncrown@lioncrowndeMacBook-Neo hkjc-bridge % node server.js
✅ HKJC bridge running on http://localhost:3000
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R2 2026-05-27
[INFO] HV R2 2026-05-27
[INFO] HV R2 2026-05-27
[INFO] HV R2 2026-05-27
[INFO] HV R2 2026-05-27
[INFO] HV R2 2026-05-27
[INFO] HV R2 2026-05-27
[INFO] HV R2 2026-05-27
[INFO] HV R2 2026-05-27
[INFO] HV R2 2026-05-27
[INFO] HV R2 2026-05-27
[INFO] HV R2 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
[INFO] HV R1 2026-05-27
^C
lioncrown@lioncrowndeMacBook-Neo hkjc-bridge % pwd
/Users/lioncrown/hkjc-bridge
lioncrown@lioncrowndeMacBook-Neo hkjc-bridge % cd ..
lioncrown@lioncrowndeMacBook-Neo ~ % ls -tlr
total 1344
drwxr-xr-x+  4 lioncrown  staff    128 12  5 20:13 Public
drwx------   3 lioncrown  staff     96 12  5 20:13 Movies
drwx------+  3 lioncrown  staff     96 12  5 20:13 Documents
drwx------+  4 lioncrown  staff    128 12  5 20:13 Pictures
drwx------+  5 lioncrown  staff    160 17  5 11:23 Desktop
drwx------+  4 lioncrown  staff    128 17  5 15:48 Music
-rw-r--r--   1 lioncrown  staff   3703 17  5 16:50 odd1.py
-rw-r--r--   1 lioncrown  staff  13179 17  5 18:31 app1.py
-rw-r--r--   1 lioncrown  staff  16451 17  5 19:08 odd8.py
drwx------@ 86 lioncrown  staff   2752 17  5 21:22 Library
-rw-r--r--   1 lioncrown  staff  16449 18  5 20:57 railway.py
-rw-r--r--@  1 lioncrown  staff  19022 19  5 20:32 odd2.py
-rw-r--r--@  1 lioncrown  staff  22093 19  5 21:18 odd3.py
-rw-r--r--@  1 lioncrown  staff  22290 20  5 21:58 odd.bak
-rw-r--r--   1 lioncrown  staff   4476 21  5 21:16 money_flow.py
-rw-r--r--   1 lioncrown  staff   3231 21  5 21:23 money.py
-rw-r--r--   1 lioncrown  staff   3792 21  5 21:27 scraper.py
drwxr-xr-x   4 lioncrown  staff    128 21  5 21:28 __pycache__
-rw-r--r--   1 lioncrown  staff  23573 21  5 21:59 odd.v2.py
-rw-r--r--   1 lioncrown  staff  25618 21  5 22:31 odd.norci.py
-rw-r--r--   1 lioncrown  staff  37773 21  5 23:37 q.py
-rw-r--r--   1 lioncrown  staff  24774 22  5 22:00 odd.py.nolog
-rw-r--r--   1 lioncrown  staff     19 23  5 12:49 Procfile
-rw-r--r--   1 lioncrown  staff     42 23  5 15:55 requirements.txt
-rw-r--r--   1 lioncrown  staff    150 23  5 15:55 nixpacks.toml
-rw-r--r--   1 lioncrown  staff    160 23  5 16:04 railway.json
-rw-r--r--@  1 lioncrown  staff  32214 23  5 16:13 odd.py.railway
-rw-r--r--   1 lioncrown  staff    709 23  5 16:19 Dockerfile
-rw-r--r--   1 lioncrown  staff  31761 24  5 13:26 odd.py.old
drwxr-xr-x   8 lioncrown  staff    256 24  5 13:31 my-odds-app
-rw-r--r--@  1 lioncrown  staff  31324 24  5 14:20 odd.py.20260524.1
-rw-r--r--   1 lioncrown  staff   8413 24  5 14:33 odd.py.railway.cpgz
-rw-r--r--   1 lioncrown  staff  31384 24  5 16:29 odd.py.ok
-rw-r--r--   1 lioncrown  staff  33736 24  5 17:44 odd.py.freeze
-rw-r--r--   1 lioncrown  staff  35029 24  5 18:37 odd.ok
-rw-r--r--   1 lioncrown  staff  30221 24  5 19:07 odd.py.graphql
-rw-r--r--   1 lioncrown  staff  35192 24  5 19:28 odd.py.graphql2
-rw-r--r--   1 lioncrown  staff     78 24  5 19:40 package.json
-rw-r--r--   1 lioncrown  staff  33108 24  5 19:40 package-lock.json
drwxr-xr-x  77 lioncrown  staff   2464 24  5 19:40 node_modules
-rw-r--r--   1 lioncrown  staff  31513 24  5 19:51 odd.py.night
drwxr-xr-x   8 lioncrown  staff    256 24  5 20:18 hkjc-bridge
drwxr-xr-x  30 lioncrown  staff    960 24  5 23:06 logs
-rw-r--r--   1 lioncrown  staff  32998 24  5 23:11 odd.py
drwxr-xr-x  26 lioncrown  staff    832 24  5 23:51 templates
drwxr-xr-x  19 lioncrown  staff    608 25  5 18:22 weinstein_scanner
drwx------@ 29 lioncrown  staff    928 25  5 19:53 Downloads
lioncrown@lioncrowndeMacBook-Neo ~ % ls -tlr odd.py
-rw-r--r--  1 lioncrown  staff  32998 24  5 23:11 odd.py
lioncrown@lioncrowndeMacBook-Neo ~ % top
lioncrown@lioncrowndeMacBook-Neo ~ % ls -tlr
total 1344
drwxr-xr-x+  4 lioncrown  staff    128 12  5 20:13 Public
drwx------   3 lioncrown  staff     96 12  5 20:13 Movies
drwx------+  3 lioncrown  staff     96 12  5 20:13 Documents
drwx------+  4 lioncrown  staff    128 12  5 20:13 Pictures
drwx------+  5 lioncrown  staff    160 17  5 11:23 Desktop
drwx------+  4 lioncrown  staff    128 17  5 15:48 Music
-rw-r--r--   1 lioncrown  staff   3703 17  5 16:50 odd1.py
-rw-r--r--   1 lioncrown  staff  13179 17  5 18:31 app1.py
-rw-r--r--   1 lioncrown  staff  16451 17  5 19:08 odd8.py
drwx------@ 86 lioncrown  staff   2752 17  5 21:22 Library
-rw-r--r--   1 lioncrown  staff  16449 18  5 20:57 railway.py
-rw-r--r--@  1 lioncrown  staff  19022 19  5 20:32 odd2.py
-rw-r--r--@  1 lioncrown  staff  22093 19  5 21:18 odd3.py
-rw-r--r--@  1 lioncrown  staff  22290 20  5 21:58 odd.bak
-rw-r--r--   1 lioncrown  staff   4476 21  5 21:16 money_flow.py
-rw-r--r--   1 lioncrown  staff   3231 21  5 21:23 money.py
-rw-r--r--   1 lioncrown  staff   3792 21  5 21:27 scraper.py
drwxr-xr-x   4 lioncrown  staff    128 21  5 21:28 __pycache__
-rw-r--r--   1 lioncrown  staff  23573 21  5 21:59 odd.v2.py
-rw-r--r--   1 lioncrown  staff  25618 21  5 22:31 odd.norci.py
-rw-r--r--   1 lioncrown  staff  37773 21  5 23:37 q.py
-rw-r--r--   1 lioncrown  staff  24774 22  5 22:00 odd.py.nolog
-rw-r--r--   1 lioncrown  staff     19 23  5 12:49 Procfile
-rw-r--r--   1 lioncrown  staff     42 23  5 15:55 requirements.txt
-rw-r--r--   1 lioncrown  staff    150 23  5 15:55 nixpacks.toml
-rw-r--r--   1 lioncrown  staff    160 23  5 16:04 railway.json
-rw-r--r--@  1 lioncrown  staff  32214 23  5 16:13 odd.py.railway
-rw-r--r--   1 lioncrown  staff    709 23  5 16:19 Dockerfile
-rw-r--r--   1 lioncrown  staff  31761 24  5 13:26 odd.py.old
drwxr-xr-x   8 lioncrown  staff    256 24  5 13:31 my-odds-app
-rw-r--r--@  1 lioncrown  staff  31324 24  5 14:20 odd.py.20260524.1
-rw-r--r--   1 lioncrown  staff   8413 24  5 14:33 odd.py.railway.cpgz
-rw-r--r--   1 lioncrown  staff  31384 24  5 16:29 odd.py.ok
-rw-r--r--   1 lioncrown  staff  33736 24  5 17:44 odd.py.freeze
-rw-r--r--   1 lioncrown  staff  35029 24  5 18:37 odd.ok
-rw-r--r--   1 lioncrown  staff  30221 24  5 19:07 odd.py.graphql
-rw-r--r--   1 lioncrown  staff  35192 24  5 19:28 odd.py.graphql2
-rw-r--r--   1 lioncrown  staff     78 24  5 19:40 package.json
-rw-r--r--   1 lioncrown  staff  33108 24  5 19:40 package-lock.json
drwxr-xr-x  77 lioncrown  staff   2464 24  5 19:40 node_modules
-rw-r--r--   1 lioncrown  staff  31513 24  5 19:51 odd.py.night
drwxr-xr-x   8 lioncrown  staff    256 24  5 20:18 hkjc-bridge
drwxr-xr-x  30 lioncrown  staff    960 24  5 23:06 logs
-rw-r--r--   1 lioncrown  staff  32998 24  5 23:11 odd.py
drwxr-xr-x  26 lioncrown  staff    832 24  5 23:51 templates
drwxr-xr-x  19 lioncrown  staff    608 25  5 18:22 weinstein_scanner
drwx------@ 29 lioncrown  staff    928 25  5 19:53 Downloads
lioncrown@lioncrowndeMacBook-Neo ~ % vi odd.py

import os
import json
import time
import threading
from datetime import datetime
from collections import defaultdict, deque

import requests
from flask import Flask, render_template, jsonify, request, send_file

app = Flask(__name__)

NODE_API = os.environ.get("NODE_API", "http://localhost:3000/odds")

def _deque5():
    return deque(maxlen=5)

def _deque60():
    return deque(maxlen=60)

def _inf():
    return float("inf")

state = {
    "running": False,
    "data": [],
    "base_data": {},
    "base_time": "",
    "base_est_bet": {},
"odd.py" 870L, 32998B
