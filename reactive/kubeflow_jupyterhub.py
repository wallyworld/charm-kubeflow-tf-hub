import yaml
from pathlib import Path

from charms.reactive import set_flag
from charms.reactive import when_not

from charms import layer
from charms.layer.basic import pod_spec_set


@when_not('charm.kubeflow-jupyterhub.started')
def start_charm():
    layer.status.maintenance('configuring jupyterhub container')

    config_file = Path('files/jupyterhub_config.py')
    pod_spec_set(yaml.dump({
        'containers': [
            {
                'name': 'kubeflow-jupyterhub',
                'image': 'gcr.io/kubeflow/jupyterhub-k8s:1.0.1',
                'ports': [
                    {'containerPort': 8000},
                    {'containerPort': 8081},
                ],
                'files': [
                    {
                        'name': 'configs',
                        'mountPath': '/etc/jupyterhub',
                        'files': {
                            'jupyterhub_config.py': config_file.read_text(),
                        },
                    },
                ],
            },
        ],
    }))

    layer.status.active('ready')
    set_flag('charm.kubeflow-jupyterhub.started')
