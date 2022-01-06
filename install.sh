cd /home/pi/Downloads

# setup screen
DIR="/home/pi/Downloads/LCD-show"
if ![ -d "$DIR" ]; then
  # Take action if $DIR not exists. #
  echo "Setting up touchscreen..."
  sudo rm -rf LCD-show
  git clone https://github.com/goodtft/LCD-show.git
  chmod -R 755 LCD-show
  cd LCD-show/
  sudo ./LCD35-show
fi
cd ..

if ! command -v conda &> /dev/null then
  # install anaconda
  sudo apt-get update
  curl "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-armv7l.sh" -o "Miniconda.sh"
  bash ./Miniconda.sh
fi

cd ..

DIR="/home/pi/dt01_gui"
if ![ -d "$DIR" ]; then
  # Take action if $DIR not exists. #
  echo "Downloading synth code..."
  git clone https://github.com/julianfl0w/dt01_gui
  cd dt01_gui
  conda create --name synth
  source activate synth
  conda install --file requirements.txt
fi


