# Rubik_solver
Python program so solve a rubik cube

based on the kociemba 2phase solver which must be installed in the same folder (https://github.com/muodov/kociemba)
TTF :https://www.dafont.com/vcr-osd-mono.font needs to be in the home directory.

Features:

scanning and solving of a Cube with any color configuration (no logo on sticker).

solving to 4 implemented pattern.

scanning and store of own pattern. With this function a copy of a cube can be generated.

scramble cube with given number of moves.

Speedcubing Trainer.
ALL OLL and PLL patterns are implemented:
https://www.speedsolving.com/wiki/index.php/Main_Page

Starting with a solved cube, you can train a specific pattern or train by random generated tasks. Top color is not equal on all patterns - but that is what you need to train as well.
You can change the training database by eding "Speedcubing.txt". 

To start script on boot modify /etc/rc.local and insert following line just before 'exit 0'

sudo -H -u pi python3 /home/pi/rubic_robot_en.py &


Mechanical setup is placed on Thingiverse:
https://www.thingiverse.com/thing:3826740

Second version with PCA9685 PWM driver. Ensures stable servo action (no jitter)
