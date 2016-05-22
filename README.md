weiqi.gs
========
[weiqi.gs](https://weiqi.gs) is an open-source game server for the game of Go, also known as weiqi (围棋) or baduk (바둑).

weiqi.gs tries to be clean, simple and easy-to-use, while still providing all the basic features expected from a go server.

Development environment
-----------------------
- `pip install -r requirements.txt`
- `npm install`
- [vagrant](https://www.vagrantup.com/) to run postgresql and rabbitmq

Besides the dependencies in `requirements.txt` and `package.json` you may also need to install some additional libraries first:
```
$ sudo apt-get install python3-dev libpq-dev libffi-dev libjpeg-dev
```

To run the development server:
```
$ ./gulp.sh
```

License
-------
GNU AGPLv3

Check the [LICENSE](https://gitlab.com/mibitzi/weiqi.gs/blob/master/LICENSE) file for more information.