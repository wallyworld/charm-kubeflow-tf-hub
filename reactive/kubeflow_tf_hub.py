import yaml
from pathlib import Path

from charmhelpers.core import hookenv
from charms.reactive import set_flag
from charms.reactive import when_not
from charms.templating.jinja2 import render

from charms import layer
from charms.layer.basic import pod_spec_set


@when_not('charm.kubeflow-tf-hub.started')
def start_charm():
    layer.status.maintenance('configuring container')

    config_src = Path('files/jupyterhub_config.py')
    config_dst = Path('/etc/config/jupyterhub_config.py')
    # we have to explicitly specify the k8s service name for use in the API
    # URL because otherwise JupyterHub uses the pod name, which in our case
    # doesn't just happen to match the service name; the k8s service name
    # will always be the application name with a "juju-" prefix
    application_name = hookenv.service_name()
    config_data = render(template=config_src.read_text(), context={
        'k8s_service_name': 'juju-{}'.format(application_name),
    })
    pod_spec_set(yaml.dump({
        'containers': [
            {
                'name': 'tf-hub',
                'image': 'gcr.io/kubeflow/jupyterhub-k8s:1.0.1',
                'command': [
                    'jupyterhub',
                    '-f',
                    str(config_dst),
                ],
                'ports': [
                    {
                        'name': 'hub',
                        'containerPort': 8000,
                    },
                    {
                        'name': 'api',
                        'containerPort': 8081,
                    },
                ],
                'files': [
                    {
                        'name': 'configs',
                        'mountPath': str(config_dst.parent),
                        'files': {
                            'jupyterhub_config.py': config_data,
                        },
                    },
                ],
            },
        ],
    }))

    layer.status.maintenance('creating container')
    set_flag('charm.kubeflow-tf-hub.started')
