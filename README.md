## About
[Tea House](https://teahouse.sethjrothschild.com) is an [open source](https://github.com/Seth-Rothschild/TeaHouse/blob/master/LICENSE) server for the game of Go. It is a fork of [weiqi.gs](https://gitlab.com/mibitzi/weiqi.gs) by Michael Bitzi. While that project resulted in a server that was open to the public, this one does not. Nevertheless, the source code is and will be available here on github.

## How do I make an account?
Account creation is currently disabled for the public site. If you are setting up your own version of this code, you can create accounts using the provided [administrator tools](https://github.com/Seth-Rothschild/TeaHouse/blob/master/admintools.py). 


## Build Instructions 
The backend was written in python3.5, frontend in [Vue.js](https://vuejs.org/). You will need `libpq` and `libjpeg` to get started. On linux, use
```bash
$ sudo apt-get install python3-dev libpq-dev libjpeg-dev
```

The rest of the dependencies can be installed with
- `pip install -r requirements.txt`
- `npm install`

To run the development server you will need to migrate the database. This step also needs to be run every time new DB migrations are created:
```bash
$ alembic upgrade head
```

Finally, the development server can be run with:
```bash
$ ./gulp.sh
$ ./main.py --create-room='Main Room'
```

After this the server will listen on http://localhost:8000 by default.
