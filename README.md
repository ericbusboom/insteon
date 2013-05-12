insteon
=======

Control program for Insteon ethernet controllers

Devel
=====

python setup.py sdist; scp dist/Insteon-1.0.tar.gz  root@horror:/proj/src; \
ssh root@horror "cd /proj/src; \
/proj/bin/pip  uninstall -y insteon; /proj/bin/pip install Insteon-1.0.tar.gz" 