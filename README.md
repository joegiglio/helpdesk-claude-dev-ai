This project is an attempt to use AI tools to build a simple ticketing help desk application. 

AI tools used: Claude 3.5, Google Gemini and VS Code extensions Claude-Dev and Aider.

Follow this journey here: https://dev.to/chiefremote/using-claude-claude-dev-and-aider-to-build-a-ticketing-system-4aek

Author: Joe Giglio

If you want to install it and play along: 

Tech stack:

Python 3.12.2, Flask, SQLite

## Install

1.  Install Python 3.12.2. Use whatever manner is recommended for your operating system.
2.  Clone project using git
3.  From project home directory (where app.py sits), create a virtual environment for dependencies. Use https://flask.palletsprojects.com/en/1.1.x/installation/ as a reference. I recommend naming it _venv_, which has already been added to the .gitignore file.
4.  Activate the virtual environment directory
5.  Use _pip3 install -r requirements.txt_ to install all dependencies. If installing this project on a Mac, beware that some of the Python packages may complain during this step. You may need to install Homebrew, XCode and Python in some magical combination.

(See https://help.dreamhost.com/hc/en-us/articles/115000699011-Using-pip3-to-install-Python3-modules for Python3 / pip3 tips.)

6.  Run the following commands from the application's home directory while the virtual environment is activated:

flask db init

flask db migrate -m "Initial migration.”

flask db upgrade

Check for the creation of a database.db in the project's directory.  It should contain tables such as: `ticket` and `integration_setting`.

6. Start the server from the home directory while the virtual environment is activated: `python3 app.py` or use your IDE to start the server.
7. If all went well, you should be able to view the site: http://127.0.0.1:5000/.
8. Run a basic test by submitting a new ticket.
