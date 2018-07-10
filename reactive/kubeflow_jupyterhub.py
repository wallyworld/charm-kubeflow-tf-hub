import yaml
from pathlib import Path

from charms.reactive import set_flag
from charms.reactive import when_not

from charms import layer
from charms.layer.basic import pod_spec_set


@when_not('charm.kubeflow-jupyterhub.started')
def start_charm():
    layer.status.maintenance('configuring container')

    config_file = Path('files/jupyterhub_config.py')
    pod_spec_set(yaml.dump({
        'containers': [
            {
                'name': 'tf-hub',
                'image': 'gcr.io/kubeflow/jupyterhub-k8s:1.0.1',
                'ports': [
                    {
                        'name': 'hub',
                        'containerPort': 8000,
                    },
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

    layer.status.maintenance('creating container')
    set_flag('charm.kubeflow-jupyterhub.started')
