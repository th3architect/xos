MYIP:=$(shell hostname -i)

frontend:
	sudo make -f ../common/Makefile.prereqs
	sudo docker-compose up -d
	bash ../common/wait_for_xos.sh
	sudo docker-compose run xos python /opt/xos/tosca/run.py none /opt/xos/configurations/common/fixtures.yaml
	sudo docker-compose run xos python /opt/xos/tosca/run.py none /opt/xos/configurations/common/mydeployment.yaml
	sudo docker-compose run xos python /opt/xos/tosca/run.py padmin@vicci.org /opt/xos/configurations/frontend/sample.yaml

containers:
	cd ../../../containers/xos; make devel

stop:
	sudo docker-compose stop

showlogs:
	sudo docker-compose logs

rm: stop
	sudo docker-compose rm

ps:
	sudo docker-compose ps

enter-xos:
	sudo docker exec -ti frontend_xos_1 bash

django-restart:
	sudo docker exec frontend_xos_1 touch /opt/xos/xos/settings.py

clean-config-folder:
	sudo docker exec frontend_xos_1 rm -f /opt/xos/xos_configuration/xos_mcord_config
	sudo docker exec frontend_xos_1 rm -f /opt/xos/xos_configuration/xos_cord_config

mock-cord-pod:
	sudo docker-compose run xos python /opt/xos/tosca/run.py padmin@vicci.org /opt/xos/configurations/common/fixtures.yaml
	sudo docker-compose run xos python /opt/xos/tosca/run.py padmin@vicci.org /opt/xos/configurations/cord-pod/mgmt-net.yaml
	#sudo docker-compose run xos bash -c "echo somekey > /opt/xos/synchronizers/vcpe/vcpe_public_key; python /opt/xos/tosca/run.py padmin@vicci.org /opt/xos/configurations/cord-pod/cord-vtn-vsg.yaml"
	sudo docker-compose run xos python /opt/xos/tosca/run.py padmin@vicci.org /opt/xos/configurations/cord-pod/cord-volt-devices.yaml
	sudo docker exec frontend_xos_1 cp /opt/xos/configurations/cord-pod/xos_cord_config /opt/xos/xos_configuration/
	sudo docker exec frontend_xos_1 touch /opt/xos/xos/settings.py



mock-mcord:
	# check this
	sudo docker-compose run xos python /opt/xos/tosca/run.py padmin@vicci.org /opt/xos/configurations/common/fixtures.yaml
	sudo docker-compose run xos python /opt/xos/tosca/run.py padmin@vicci.org /opt/xos/configurations/cord-pod/mgmt-net.yaml
	sudo docker-compose run xos python /opt/xos/tosca/run.py padmin@vicci.org /opt/xos/configurations/frontend/mocks/mcord.yaml
	sudo docker exec frontend_xos_1 cp /opt/xos/configurations/mcord/xos_mcord_config /opt/xos/xos_configuration/
	sudo docker exec frontend_xos_1 touch /opt/xos/xos/settings.py
