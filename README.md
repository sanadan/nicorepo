# nicorepo_feed
Generate atom feed from nicorepo.

## install
For Ubuntu 14.04

    cd /var/www
    git clone https://github.com/sanadan/nicorepo_feed.git
    cd nicorepo_feed
    bundle install
    sudo mkdir /etc/pitcgi
    sudo chgrp www-data /etc/pitcgi
    sudo chmod 770 /etc/pitcgi
    sudo adduser $USER www-data
    ./index.cgi
    sudo ln -s /var/www/nicorepo_feed/nicorepo_feed.conf /etc/apache2/conf-enabled
    sudo service apache2 restart

## Licence
MIT

## Copyright
Copyright (C) 2015 sanadan <jecy00@gmail.com>
