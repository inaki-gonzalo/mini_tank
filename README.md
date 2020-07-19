# Mini Tank
A real(not sim) self-driving miniature tank. Input from a camera is uesd to make course corrections and stay on path.
The tank relies on a Tensorflow model for decision making. The model is trained using data from a human controlled run (supervised learning).

# Parts
* Raspberry Pi 3
* [Tank Mobile Platform](https://www.amazon.com/gp/product/B014L1CF1K)
* [USB Webcam](https://www.amazon.com/gp/product/B087P8VJ77)
* Xbee for communications
* USB controllers.
* LiPo Battery.
* L298N Motor Drive Controller Board Module Dual H Bridge.
* 5V power bank to power RPi.

# Software Setup
1. Install Raspbian on RPi.
1. Install python3 and dependencies:
  `sudo pip3 install -r requirements.txt`
1. Install the systemctl service.
  ```
  sudo cp agent.service /lib/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable agent.service
  sudo systemctl start agent.service
  ```

# Data Collection
Start controller on PC.

`cd desktop_side; python3 controller.py`

The car should now be driveable, it will be recording data but it wont commit to disk until you send save.
The collected data will appear on the Pi on /home/pi/.

# Training
Move collected data to PC. This will be significantly faster than training on the Pi.

`cd desktop_side; python3 train.py`

# Run in self-driving mode.
Move trained model (model.h5) back into RPi.
Start the model server on the Pi.

`python3 model_serve.py`

With the controller send the self-diriving command.

# Unit tests
You can run the unit tests by running:
```
export PYTHONPATH=$PYTHONPATH:./src
python -m unittest discover
```
