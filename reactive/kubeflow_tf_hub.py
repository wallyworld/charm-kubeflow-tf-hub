import yaml
from pathlib import Path

from charmhelpers.core import hookenv
from charmhelpers.core import unitdata
from charms.reactive import set_flag
from charms.reactive import when, when_not

from charms import layer
from charms.layer.basic import pod_spec_set


@when_not('charm.kubeflow-tf-hub.image.available')
def get_image():
    layer.status.maintenance('fetching container image')
    try:
        image_info_filename = hookenv.resource_get('jupyterhub-image')
        if not image_info_filename:
            raise ValueError('no filename returned for resource')
        image_info = yaml.safe_load(Path(image_info_filename).read_text())
        if not image_info:
            raise ValueError('no data returned for resource')
    except Exception as e:
        hookenv.log('unable to fetch container image: {}'.format(e),
                    level=hookenv.ERROR)
        layer.status.blocked('unable to fetch container image')
    else:
        unitdata.kv().set('charm.kubeflow-tf-hub.image-info', image_info)
        set_flag('charm.kubeflow-tf-hub.image.available')


@when('charm.kubeflow-tf-hub.image.available')
@when_not('charm.kubeflow-tf-hub.started')
def start_charm():
    layer.status.maintenance('configuring container')

    config = hookenv.config()
    image_info = unitdata.kv().get('charm.kubeflow-tf-hub.image-info')
    application_name = hookenv.service_name()
    jh_config_src = Path('files/jupyterhub_config.py')
    jh_config_dst = Path('/etc/config/jupyterhub_config.py')

    pod_spec_set(yaml.dump({
        'containers': [
            {
                'name': 'tf-hub',
                'imageDetails': {
                    'imagePath': image_info['registrypath'],
                    'username': image_info['username'],
                    'password': image_info['password'],
                },
                'command': [
                    'jupyterhub',
                    '-f',
                    str(jh_config_dst),
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
                'config': {
                    # we have to explicitly specify the k8s service name for
                    # use in the API URL because otherwise JupyterHub uses the
                    # pod name, which in our case doesn't just happen to match
                    # the service name; the k8s service name will always be the
                    # application name with a "juju-" prefix
                    'K8S_SERVICE_NAME': 'juju-{}'.format(application_name),
                    'NOTEBOOK_STORAGE_SIZE': config['notebook-storage-size'],
                    'NOTEBOOK_STORAGE_CLASS': config['notebook-storage-class'],
                    'CLOUD': '',  # is there a way to detect this?
                    'REGISTRY': config['notebook-image-registry'],
                    'REPO_NAME': config['notebook-image-repo-name'],
                },
                'files': [
                    {
                        'name': 'configs',
                        'mountPath': str(jh_config_dst.parent),
                        'files': {
                            'jupyterhub_config.py': jh_config_src.read_text(),
                        },
                    },
                ],
            },
        ],
    }))

    layer.status.maintenance('creating container')
    set_flag('charm.kubeflow-tf-hub.started')
