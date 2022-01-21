[//]: # (This markdown file is open source. Written by Kavster#4400 for the OpenA3xx project.)
[//]: # (Permission is given to use this document for your own templates, etc. We only ask for a reference.)

[//]: # (Main Logo and Begin Document)

<a href="https://opena3xx.dev">
<img src="https://github.com/OpenA3XX/opena3xx.site/blob/main/assets/images/OPENA3XX%20logo%20RGB.png?raw=true" alt="Logo" width="300"/>
</a>

# OpenA3xx Hardware Controller Board (inc MCDU)

Welcome to the 'Hardware Controller' for the OpenA3XX project.  
If you're setting up our <B>MCDU</b>, or our <b>standard controller</b> baord then you're in the right place!

## Let's get started!

Ok, let's jump right into it!  
You will need:  
<ul>
    <li>Raspberry Pi Zero W
        <ul>
            <li> We recommend the <b>'Pi Zero W'</b> so you have the wifi feature. It will make the install much easier. </br> 
                If you can only get a <b>'Pi Zero WH'</b> this is also ok. <i>But you will either need to re-solder the headers, or rotate the board.</i> </br>
                But, if you can only get a <b>'Pi Zero'</b> we will eventually release an image file that you can simply flash to the SD card.
            <li> A computer 
            <li> A wireless internet connection
            <li> A power supply for the Raspbery Pi board
            <li> A MicroSD card. <i>We recommend a 16GB Class 10.</i>
</ul>  

## Step 1

We are assuming you have a brand new board, and an empty SD card.  
> <i>If you already have some experience with Raspbery Pi boards, then setup <b>Raspberry Pi OS Lite</b> and move on to step 2 below.</i>

The first thing we need to do is set up the Raspberry Pi ready for use. So, head over to this [Raspberry Pi](https://www.raspberrypi.com/software/) website and scroll down until you see <b>'Download for xxx'</b> <i>where 'xxx' would be replaced with your opoerating system</i>.
<img src="https://github.com/OpenA3XX/opena3xx.documentation/blob/main/.gitbook/assets/RaspPiToolDownload.jpg">

Download and install this desktop application, then open it. It shouldn't take too long depending on your internet connection.  
With the application open you should see a simple screen with 3 options. Insert your SD card to your PC, ignore any prompts about formatting.
1) Choose <b>Raspbery Pi OS Lite</b>
2) Choose your inserted SD card
3) Click 'Write' and wait for the process to finish.

When the process is finished, remove the SD card from your computer and then reinsert it.
Goto 'My Computer' and open the newly created 'Boot' drive.
Download these two files:
1) [wpa_supplicant.conf](https://github.com/OpenA3XX/opena3xx.hardware.controller/blob/main/wpa_supplicant.conf)
2) [ssh](https://github.com/OpenA3XX/opena3xx.hardware.controller/blob/main/ssh)  

Open up 'wpa_supplicant.conf' in any text editor (<b>NOT</b> Microsoft word! Use Notepad or similar) and replace 'Wi-Fi Name' with your wifi network name. Lastly replace 'Wi-Fi Password' with the password for that wifi netork. Save the file.
Then, simply place these files into the 'Boot' directory.
Remove the SD card, and the setup is complete!  

<b>Congratulations!</b> Let's move on to Step 2 below.

## Step 2

Now that we have the Raspbery Pi setup, we need to conenct to it and talk to it.
For this, we are going to use what's called a <b>'Headless'</b> connection. It is probably much easier, quicker and simple to do it this way, rather than having to try and connect a keyboard, mouse and screen directly to the Pi at this point.  

> If you have never worked with command line before, <b>please</b> do not put off by this. We promise it is easy, and if you follow this guide, you really won't have to do much > at all. We really want this to be accessible to everyone, and although the command line can be a bit daunting and offputing for some people, `we promise that you can do this!`  

<b>Now, let's go!</b>

Let's continue by downloading a program called [PuTTY](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html)
At the time of writting this, V0.76 is the latest release but it shouldn't matter which version you have.
Simply download the relevant file for your operating system and run the installer. If you're using a recent windows copmuter then just download the one highlight in the picture.
<img src="https://github.com/OpenA3XX/opena3xx.documentation/blob/main/.gitbook/assets/PuTTY.jpg">  

Ok, now we have that installed just open up the application and you'll see a screen that looks like this.  
<b>We are only going to type ONE thing here, so ignore everything except this one text box!</b> 
<img src="https://github.com/OpenA3XX/opena3xx.documentation/blob/main/.gitbook/assets/PuTTY_Connect.png" width=400>  
Here we need to type in the IP address of the raspberry pi. There are several ways of finding out what the IP address of the Raspbery Pi is, but the most straight forward way is to login into your home router and look at the devices connected to your network. Each router has a different method for this, so Google how to do this for your specific router.  
It is also possible to download some apps on your phone that will scan your network and show you conencted devices and their IP address.   
Once you have chosen your method, find the connection called <b>'raspberrypi'</b> and find the corresponding IP address.  
`It will be something similar to: <b>'192.168.0.30'</b>`  

Once you have the IP address, type this into the text box in 'PuTTY' and hit 'Enter' on your keyboard.  
You will then see a 'Command Line' window pop open, with text saying `login as` and it will probably look something like this:  
<img src="https://github.com/OpenA3XX/opena3xx.documentation/blob/main/.gitbook/assets/PuTTY_Login.png">  

Type `pi` and hit 'Enter'  
> NOTE: When you type any password in the command line, you will not see ANYTHING appear on the screen. But the keys are being logged.
> You must type your password and then hit enter. Even though you can't see anything being typed on screen, it is.
> If you make a mistake, just hit 'Enter' and start typing again.  

Type `raspberry` (which is the default password) and hit enter.  

If everything has gone right, then you should see a screen that looks like this:  
<img src="https://github.com/OpenA3XX/opena3xx.documentation/blob/main/.gitbook/assets/putty_connected.png">  

> If you're having problems getting to this stage, is is more than likely a connection issue. It's hard for us to diagnose potential problems in this document, and they are likely to be <b>very</b> rare. We would suggest Google and YouTube will have lots of examples of how to do this should you get stuck.  

<b>Congratulations!</b> That is the hardest part done!  
Let's move on to step 3 below.

## Step 3

Now, all you have to do is type some commands everything will done automatically for you! Easy, right?  
Let's go!  

Type the following commands one-by-one and then hit enter. Wait for each one to finish before starting the next.  
You'll know when you can type the next one, because you will the green text that says `pi@raspberrypi ~ $`.  
```
sudo apt update && sudo apt upgrade

sudo apt-install git

sudo apt-get install python

sudo apt install python3-pip

git clone https://github.com/OpenA3XX/opena3xx.hardware.controller.git

cd /home/pi/opena3xx.hardware.controller/setup

sudo chmod +x setup.sh

sudo ./setup.sh
```  

After running the last command you will notice the installer starts.  
<b>You need to be patient with this, especially if your internet connection is slow.</b>  

When you see the `Install Complete!` message. Type the following command:  
`sudo reboot now`  
You will then see an error message saying the connection was lost, and this is to be expected as we have just restarted the Raspberry Pi.  
This is ok, as we have now finished with the command line anyway.  

Everytime you start up the Raspberry Pi, it will automatically run the program (and check for updates) so you won't need to connect to it via command line again. Phew!  

Because it will check for updates when it starts, we recommend powering it up a couple of minuets before starting the software.  

### That's it! Congratulations!

We hope that this guide is useful and clear. If you have any questions, or are unclear on anything please contact one of the team for assistance.
If this document needs changing or clarifying in certain areas, please let us know so we can improve it.  

We hope you enjoy the product, and happy landings!

[//]: # (Use 'htop' to check process and see that it is auto running.)
[//]: # (It will currently check dependancies for udpates before launching the main.py.)
[//]: # (This can be changed to speed up start up at a later date.)
